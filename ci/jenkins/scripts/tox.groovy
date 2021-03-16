def getToxEnvs(){
    def envs
    if(isUnix()){
        envs = sh(
                label: "Getting Tox Environments",
                returnStdout: true,
                script: "tox -l"
            ).trim().split('\n')
    } else{
        envs = bat(
                label: "Getting Tox Environments",
                returnStdout: true,
                script: "@tox -l"
            ).trim().split('\r\n')
    }
    envs.collect{
        it.trim()
    }
    return envs
}

def getToxEnvs2(tox){
    def envs
    if(isUnix()){
        envs = sh(returnStdout: true, script: "${tox} -l").trim().split('\n')
    } else{
        envs = bat(returnStdout: true, script: "@${tox} -l").trim().split('\n')
    }
    envs.collect{
        it.trim()
    }
    return envs
}

def generateToxPackageReport(testEnv){

        def packageReport = "\n**Installed Packages:**"
        testEnv['installed_packages'].each{
            packageReport =  packageReport + "\n ${it}"
        }

        return packageReport
}

def getBasicToxMetadataReport(toxResultFile){
    def tox_result = readJSON(file: toxResultFile)
    def testingEnvReport = """# Testing Environment

**Tox Version:** ${tox_result['toxversion']}
**Platform:**   ${tox_result['platform']}
"""
    return testingEnvReport
}
def getPackageToxMetadataReport(tox_env, toxResultFile){
    def tox_result = readJSON(file: toxResultFile)

    if(! tox_result['testenvs'].containsKey(tox_env)){
        def w = tox_result['testenvs']
        tox_result['testenvs'].each{key, test_env->
            test_env.each{
                echo "${it}"
            }
        }
        error "No test env for ${tox_env} found in ${toxResultFile}"
    }
    def tox_test_env = tox_result['testenvs'][tox_env]
    def packageReport = generateToxPackageReport(tox_test_env)
    return packageReport
}
def getErrorToxMetadataReport(tox_env, toxResultFile){
    def tox_result = readJSON(file: toxResultFile)
    def testEnv = tox_result['testenvs'][tox_env]
    def errorMessages = []
    def tests = testEnv["test"] ? testEnv["test"] : []
    testEnv["test"].each{
        if (it['retcode'] != 0){
            echo "Found error ${it}"
            def errorOutput =  it['output']
            def failedCommand = it['command']
            errorMessages += "**${failedCommand}**\n${errorOutput}"
        }
    }
    def resultsReport = "# Results"
    if (errorMessages.size() > 0){
         return resultsReport + "\n" + errorMessages.join("\n")
    }
    return ""
}

def generateToxReport(tox_env, toxResultFile){
    if(!fileExists(toxResultFile)){
        error "No file found for ${toxResultFile}"
    }
    def reportSections = []

    try{
        reportSections += getBasicToxMetadataReport(toxResultFile)
        try{
            reportSections += getPackageToxMetadataReport(tox_env, toxResultFile)
        }catch(e){
            echo "Unable to parse installed packages info"

        }
        reportSections += getErrorToxMetadataReport(tox_env, toxResultFile)
    } catch (e){
        echo "Unable to parse json file, Falling back to reading the file as text. \nReason: ${e}"
        def data =  readFile(toxResultFile)
        reportSections += "``` json\n${data}\n```"
    }
    return reportSections.join("\n")
}

def getToxTestsParallel(args = [:]){
    def envNamePrefix = args['envNamePrefix']
    def label = args['label']
    def dockerfile = args['dockerfile']
    def dockerArgs = args['dockerArgs']
    script{
        def TOX_RESULT_FILE_NAME = "tox_result.json"
        def envs
        def originalNodeLabel
        def dockerImageName = "${currentBuild.fullProjectName}:tox".replaceAll("-", "_").replaceAll('/', "_").replaceAll(' ', "").toLowerCase()
        node(label){
            originalNodeLabel = env.NODE_NAME
            checkout scm
            def dockerImage = docker.build(dockerImageName, "-f ${dockerfile} ${dockerArgs} .")
            dockerImage.inside{
                envs = getToxEnvs()
            }
            if(isUnix()){
                sh(
                    label: "Removing Docker Image used to run tox",
                    script: "docker image ls ${dockerImageName}"
                )
            } else {
                bat(
                    label: "Removing Docker Image used to run tox",
                    script: """docker image ls ${dockerImageName}
                               """
                )
            }
        }
        echo "Found tox environments for ${envs.join(', ')}"
        def dockerImageForTesting
        node(originalNodeLabel){
            checkout scm
            dockerImageForTesting = docker.build(dockerImageName, "-f ${dockerfile} ${dockerArgs} . ")

        }
        echo "Adding jobs to ${originalNodeLabel}"
        def jobs = envs.collectEntries({ tox_env ->
            def tox_result
            def githubChecksName = "Tox: ${tox_env} ${envNamePrefix}"
            def jenkinsStageName = "${envNamePrefix} ${tox_env}"

            [jenkinsStageName,{
                node(originalNodeLabel){
                    ws{
                        checkout scm
                        dockerImageForTesting.inside{
                            def toxReturnCode
                            try{
                                publishChecks(
                                    conclusion: 'NONE',
                                    name: githubChecksName,
                                    status: 'IN_PROGRESS',
                                    summary: 'Use Tox to test installed package',
                                    title: 'Running Tox'
                                )
                                withEnv(['PY_COLORS=0', 'TOX_PARALLEL_NO_SPINNER=1']){
                                    if(isUnix()){
                                        toxReturnCode = sh(
                                            label: "Running Tox with ${tox_env} environment",
                                            script: "tox -vvv --result-json=${TOX_RESULT_FILE_NAME} --workdir=/tmp/tox -e $tox_env",
                                            returnStatus: true
                                        )
                                    } else {
                                        toxReturnCode = bat(
                                            label: "Running Tox with ${tox_env} environment",
                                            script: "tox  -vvv --result-json=${TOX_RESULT_FILE_NAME} --workdir=%TEMP%\\tox -e ${tox_env}",
                                            returnStatus: true
                                        )
                                    }
                                    if(toxReturnCode == 1){
                                        error("Tox failed with return code ${toxReturnCode}")
                                    }
                                }
                            } finally {
                                if(toxReturnCode == 1){
                                    if(isUnix()){
                                        sh(
                                            label: "Running Tox with showconfig",
                                            script: "tox --showconfig --workdir=/tmp/tox -e ${tox_env}",

                                            returnStatus: true
                                        )
                                    } else {
                                        bat(
                                            label: "Running Tox with showconfig",
                                            script: "tox --showconfig --workdir=%TEMP%\\tox -e ${tox_env}",
                                            returnStatus: true
                                        )
                                    }
                                    def text
                                    try{
                                        text = generateToxReport(tox_env, 'tox_result.json')
                                    }
                                    catch (ex){
                                        text = "No details given. Unable to read tox_result.json"
                                    }
                                    publishChecks(
                                        name: githubChecksName,
                                        summary: 'Use Tox to test installed package',
                                        text: text,
                                        conclusion: 'FAILURE',
                                        title: 'Failed'
                                    )
                                } else {
                                    def checksReportText = generateToxReport(tox_env, TOX_RESULT_FILE_NAME)
                                    publishChecks(
                                            name: githubChecksName,
                                            summary: 'Use Tox to test installed package',
                                            text: "${checksReportText}",
                                            title: 'Passed'
                                        )
                                }
                                cleanWs(
                                    patterns: [
                                            [pattern: '*.egg-info/', type: 'INCLUDE'],
                                            [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                            [pattern: TOX_RESULT_FILE_NAME, type: 'INCLUDE'],
                                        ],
                                    deleteDirs: true
                                )
                            }
                        }
                    }
                }
            }]
        })
        return jobs
    }
}

return this