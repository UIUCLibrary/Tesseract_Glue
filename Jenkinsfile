SONARQUBE_CREDENTIAL_ID = 'sonarcloud-uiucprescon.ocr'
SUPPORTED_MAC_VERSIONS = ['3.8', '3.9']
SUPPORTED_LINUX_VERSIONS = ['3.7', '3.8', '3.9']
SUPPORTED_WINDOWS_VERSIONS = ['3.7', '3.8', '3.9']
def get_sonarqube_unresolved_issues(report_task_file){
    script{

        def props = readProperties  file: '.scannerwork/report-task.txt'
        def response = httpRequest url : props['serverUrl'] + "/api/issues/search?componentKeys=" + props['projectKey'] + "&resolved=no"
        def outstandingIssues = readJSON text: response.content
        return outstandingIssues
    }
}

def sonarcloudSubmit(metadataFile, outputJson, sonarCredentials){
    def props = readProperties interpolate: true, file: metadataFile
    withSonarQubeEnv(installationName:"sonarcloud", credentialsId: sonarCredentials) {
        if (env.CHANGE_ID){
            sh(
                label: "Running Sonar Scanner",
                script:"sonar-scanner -Dsonar.projectVersion=${props.Version} -Dsonar.buildString=\"${env.BUILD_TAG}\" -Dsonar.pullrequest.key=${env.CHANGE_ID} -Dsonar.pullrequest.base=${env.CHANGE_TARGET}"
                )
        } else {
            sh(
                label: "Running Sonar Scanner",
                script: "sonar-scanner -Dsonar.projectVersion=${props.Version} -Dsonar.buildString=\"${env.BUILD_TAG}\" -Dsonar.branch.name=${env.BRANCH_NAME}"
                )
        }
    }
     timeout(time: 1, unit: 'HOURS') {
         def sonarqube_result = waitForQualityGate(abortPipeline: false)
         if (sonarqube_result.status != 'OK') {
             unstable "SonarQube quality gate: ${sonarqube_result.status}"
         }
         def outstandingIssues = get_sonarqube_unresolved_issues(".scannerwork/report-task.txt")
         writeJSON file: outputJson, json: outstandingIssues
     }
}
def build_wheel(platform){
    if(isUnix()){
        sh(
            label: 'Building Python Wheel',
            script: "python -m pep517.build --binary --out-dir dist/ ."
        )
        if( platform == 'linux'){
            sh "auditwheel repair ./dist/*.whl -w ./dist"
        }
    } else {
        bat(
            label: 'Building Python Wheel',
            script: "python -m pip wheel --no-deps -w dist\\ ."
//             script: "python -m pep517.build --binary --out-dir dist\\ ."
        )
    }
}

def getDevPiStagingIndex(){

    if (env.TAG_NAME?.trim()){
        return "tag_staging"
    } else{
        return "${env.BRANCH_NAME}_staging"
    }
}
def buildAndTestWheel(pythonVersions){
// TODO: build inmto
    def packages
    node(){
        checkout scm
        packages = load 'ci/jenkins/scripts/packaging.groovy'
    }
    def windowsStages = [:]
    pythonVersions.each{ pythonVersion ->
        windowsStages["Windows - Python ${pythonVersion}: wheel"] = {
            stage('Build Wheel'){
                packages.buildPkg(
                    agent: [
                        dockerfile: [
                            label: 'windows && docker',
                            filename: 'ci/docker/windows/tox/Dockerfile',
                            additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE'
                        ]
                    ],
                        buildCmd: {
                            bat "py -${pythonVersion} -m pip wheel -v --no-deps -w ./dist ."
                        },
                    post:[
                        cleanup: {
                            cleanWs(
                                patterns: [
                                        [pattern: './dist/', type: 'INCLUDE'],
                                    ],
                                notFailBuild: true,
                                deleteDirs: true
                            )
                        },
                        success: {
//                                             archiveArtifacts artifacts: 'dist/*.whl'
                            stash includes: 'dist/*.whl', name: "python${pythonVersion} windows wheel"
                        }
                    ]
                )
            }
            stage('Test Wheel'){
//                             TODO test with something other than the tox
                packages.testPkg(
                    agent: [
                        dockerfile: [
                            label: 'windows && docker',
                            filename: 'ci/docker/windows/tox/Dockerfile',
                            additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE'
                        ]
                    ],
                    glob: 'dist/*.whl',
                    stash: "python${pythonVersion} windows wheel",
                    pythonVersion: pythonVersion
                )
            }
        }
    }
    return windowsStages
}
              
def deploy_docs(pkgName, prefix){
    script{
        try{
            timeout(30) {
                input "Update project documentation to https://www.library.illinois.edu/dccdocs/${pkgName}"
            }
            sshPublisher(
                publishers: [
                    sshPublisherDesc(
                        configName: 'apache-ns - lib-dccuser-updater', 
                        sshLabel: [label: 'Linux'], 
                        transfers: [sshTransfer(excludes: '', 
                        execCommand: '', 
                        execTimeout: 120000, 
                        flatten: false, 
                        makeEmptyDirs: false, 
                        noDefaultExcludes: false, 
                        patternSeparator: '[, ]+', 
                        remoteDirectory: "${pkgName}",
                        remoteDirectorySDF: false, 
                        removePrefix: "${prefix}",
                        sourceFiles: "${prefix}/**")],
                    usePromotionTimestamp: false, 
                    useWorkspaceInPromotion: false, 
                    verbose: true
                    )
                ]
            )
        } catch(exc){
            echo "User response timed out. Documentation not published."
        }
    }
}

def test_package_on_mac(glob){
    script{
        findFiles(glob: glob).each{
            sh(
                label: "Testing ${it}",
                script: """python3 -m venv venv
                           venv/bin/python -m pip install pip --upgrade
                           venv/bin/python -m pip install wheel
                           venv/bin/python -m pip install --upgrade setuptools
                           venv/bin/python -m pip install tox
                           venv/bin/tox --installpkg=${it.path} -e py -vv --recreate
                           """
            )
        }
    }
}


def get_package_name(stashName, metadataFile){
    ws {
        unstash "${stashName}"
        script{
            def props = readProperties interpolate: true, file: "${metadataFile}"
            deleteDir()
            return props.Name
        }
    }
}

def devpiRunTest(devpiClient, pkgPropertiesFile, devpiIndex, devpiSelector, devpiUsername, devpiPassword, toxEnv){
    script{
        if(!fileExists(pkgPropertiesFile)){
            error "${pkgPropertiesFile} does not exist"
        }
        def props = readProperties interpolate: false, file: pkgPropertiesFile
        if (isUnix()){
            sh(
                label: "Running test",
                script: """${devpiClient} use https://devpi.library.illinois.edu --clientdir certs/
                           ${devpiClient} login ${devpiUsername} --password ${devpiPassword} --clientdir certs/
                           ${devpiClient} use ${devpiIndex} --clientdir certs/
                           ${devpiClient} test --index ${devpiIndex} ${props.Name}==${props.Version} -s ${devpiSelector} --clientdir certs/ -e ${toxEnv} --tox-args=\"-vv\"
                """
            )
        } else {
            bat(
                label: "Running tests on Devpi",
                script: """devpi use https://devpi.library.illinois.edu --clientdir certs\\
                           devpi login ${devpiUsername} --password ${devpiPassword} --clientdir certs\\
                           devpi use ${devpiIndex} --clientdir certs\\
                           devpi test --index ${devpiIndex} ${props.Name}==${props.Version} -s ${devpiSelector} --clientdir certs\\ -e ${toxEnv} --tox-args=\"-vv\"
                           """
            )
        }
    }
}
wheelStashes = []
configurations = loadConfigs()
def loadConfigs(){
    node(){
        echo "loading configurations"
        checkout scm
        return load("ci/jenkins/scripts/configs.groovy").getConfigurations()
    }
}


def test_pkg(glob, timeout_time){

    findFiles( glob: glob).each{
        cleanWs(
            deleteDirs: true,
            disableDeferredWipeout: true,
            patterns: [
                [pattern: 'dist/', type: 'EXCLUDE'],
                [pattern: 'tests/', type: 'EXCLUDE'],
                [pattern: 'tox.ini', type: 'EXCLUDE'],
                [pattern: 'setup.cfg', type: 'EXCLUDE'],
            ]
        )
        timeout(timeout_time){
            if(isUnix()){
                sh(label: "Testing ${it}",
                   script: """python --version
                              tox --installpkg=${it.path} -e py -vv
                              """
                )
            } else {
                bat(label: "Testing ${it}",
                    script: """python --version
                               tox --installpkg=${it.path} -e py -vv
                               """
                )
            }
        }
    }
}

def getMacDevpiName(pythonVersion, format){
    if(format == "wheel"){
        return "${pythonVersion.replace('.','')}-*macosx*.*whl"
    } else if(format == "sdist"){
        return "tar.gz"
    } else{
        error "unknown format ${format}"
    }
}
def run_tox_envs(){
    script {
        def cmds
        def envs
        if(isUnix()){
            envs = sh(returnStdout: true, script: "tox -l").trim().split('\n')
            cmds = envs.collectEntries({ tox_env ->
                [tox_env, {
                    sh( label: "Running Tox with ${tox_env} environment", script: "tox  -vv -e $tox_env --parallel--safe-build")
                }]
            })
        } else{
            envs = bat(returnStdout: true, script: "@tox -l").trim().split('\n')
            cmds = envs.collectEntries({ tox_env ->
                [tox_env, {
                    bat( label: "Running Tox with ${tox_env} environment", script: "tox  -vv -e $tox_env")
                }]
            })
        }
        echo "Setting up tox tests for ${envs.join(', ')}"
        parallel(cmds)
    }
}
defaultParameterValues = [
    USE_SONARQUBE: false
]

def get_props(){
    stage("Reading Package Metadata"){
        node() {
            try{
                unstash "DIST-INFO"
                def metadataFile = findFiles(excludes: '', glob: '*.dist-info/METADATA')[0]
                def package_metadata = readProperties interpolate: true, file: metadataFile.path
                echo """Metadata:

    Name      ${package_metadata.Name}
    Version   ${package_metadata.Version}
    """
                return package_metadata
            } finally {
                cleanWs(
                    patterns: [
                            [pattern: '*.dist-info/**', type: 'INCLUDE'],
                        ],
                    notFailBuild: true,
                    deleteDirs: true
                )
            }
        }
    }
}
def startup(){
    def SONARQUBE_CREDENTIAL_ID = SONARQUBE_CREDENTIAL_ID
    node(){
        checkout scm
        tox = load("ci/jenkins/scripts/tox.groovy")
        mac = load("ci/jenkins/scripts/mac.groovy")
        devpiLib = load("ci/jenkins/scripts/devpi.groovy")
    }
    parallel(
        [
            failFast: true,
            'Checking sonarqube Settings': {
                node(){
                    try{
                        withCredentials([string(credentialsId: SONARQUBE_CREDENTIAL_ID, variable: 'dddd')]) {
                            echo 'Found credentials for sonarqube'
                        }
                        defaultParameterValues.USE_SONARQUBE = true
                    } catch(e){
                        echo "Setting defaultValue for USE_SONARQUBE to false. Reason: ${e}"
                        defaultParameterValues.USE_SONARQUBE = false
                    }
                }
            },
            'Getting Distribution Info': {
                node('linux && docker') {
                    timeout(2){
                        ws{
                            checkout scm
                            try{
                                docker.image('python:3.8').inside {
                                    sh(
                                       label: "Running setup.py with dist_info",
                                       script: """python --version
                                                  python setup.py dist_info
                                               """
                                    )
                                    stash includes: "*.dist-info/**", name: 'DIST-INFO'
                                    archiveArtifacts artifacts: "*.dist-info/**"
                                }
                            } finally{
                                cleanWs(
                                    patterns: [
                                            [pattern: '*.dist-info/**', type: 'INCLUDE'],
                                            [pattern: '.eggs/', type: 'INCLUDE'],
                                            [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                        ],
                                    notFailBuild: true,
                                    deleteDirs: true
                                    )
                            }
                        }
                    }
                }
            }
        ]
    )
}
startup()
def props = get_props()
pipeline {
    agent none
    options {
        timeout(time: 1, unit: 'DAYS')
    }
    parameters {
        booleanParam(name: "RUN_CHECKS", defaultValue: true, description: "Run checks on code")
        booleanParam(name: "TEST_RUN_TOX", defaultValue: false, description: "Run Tox Tests")
        booleanParam(name: "USE_SONARQUBE", defaultValue: defaultParameterValues.USE_SONARQUBE, description: "Send data test data to SonarQube")
        booleanParam(name: "BUILD_PACKAGES", defaultValue: false, description: "Build Python packages")
        booleanParam(name: "BUILD_MAC_PACKAGES", defaultValue: false, description: "Test Python packages on Mac")
        booleanParam(name: "TEST_PACKAGES", defaultValue: true, description: "Test Python packages by installing them and running tests on the installed package")
        booleanParam(name: "DEPLOY_DEVPI", defaultValue: false, description: "Deploy to devpi on http://devpy.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}")
        booleanParam(name: "DEPLOY_DEVPI_PRODUCTION", defaultValue: false, description: "Deploy to https://devpi.library.illinois.edu/production/release")
        booleanParam(name: "DEPLOY_DOCS", defaultValue: false, description: "Update online documentation")
    }
    stages {
        stage("Building") {
            agent {
                dockerfile {
                    filename 'ci/docker/linux/build/Dockerfile'
                    label 'linux && docker'
                    additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) --build-arg PYTHON_VERSION=3.8'
                }
            }
            stages{
                stage("Building Python Package"){
                    steps {
                        timeout(20){
                            tee("logs/python_build.log"){
                                sh(
                                    label: "Build python package",
                                    script: 'CFLAGS="--coverage -fprofile-arcs -ftest-coverage" LFLAGS="-lgcov --coverage" python setup.py build -b build --build-lib build/lib/ build_ext -j $(grep -c ^processor /proc/cpuinfo) --inplace'
                                )
                            }
                        }
                    }
                    post{
                        always{
                            stash includes: 'uiucprescon/**/*.dll,uiucprescon/**/*.pyd,uiucprescon/**/*.exe,uiucprescon/**/*.so,build/**', name: "COMPILED_BINARIES"
                            recordIssues(filters: [excludeFile('build/*'), ], tools: [gcc(pattern: 'logs/python_build.log')])
                        }
                    }
                }
                stage("Building Documentation"){
                    steps{
                        timeout(3){
                            sh '''mkdir -p logs
                                  python -m sphinx docs/source build/docs/html -d build/docs/.doctrees -w logs/build_sphinx.log
                                  '''
                        }
                    }
                    post{
                        always {
                            recordIssues(tools: [sphinxBuild(name: 'Sphinx Documentation Build', pattern: 'logs/build_sphinx.log', id: 'sphinx_build')])

                        }
                        success{
                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'build/docs/html', reportFiles: 'index.html', reportName: 'Documentation', reportTitles: ''])
                            script{
                                echo "props = ${props}"
                                def DOC_ZIP_FILENAME = "${props.Name}-${props.Version}.doc.zip"
                                zip archive: true, dir: "build/docs/html", glob: '', zipFile: "dist/${DOC_ZIP_FILENAME}"
                                stash includes: "dist/${DOC_ZIP_FILENAME},build/docs/html/**", name: 'DOCS_ARCHIVE'
                            }
                        }
                    }
                }
            }
            post{
                cleanup{
                    cleanWs(
                        patterns: [
                                [pattern: 'build/', type: 'INCLUDE'],
                                [pattern: 'logs/', type: 'INCLUDE'],
                            ],
                        notFailBuild: true,
                        deleteDirs: true
                        )
                }
            }
        }
        stage("Checks"){
            when{
                equals expected: true, actual: params.RUN_CHECKS
            }
            stages{
                stage("Code Quality") {
                    agent {
                        dockerfile {
                            filename 'ci/docker/linux/build/Dockerfile'
                            label 'linux && docker'
                            additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) --build-arg PYTHON_VERSION=3.8'
                        }
                    }
                    failFast true
                    stages{
                        stage("Setting up Tests"){
                            steps{
                                timeout(3){
                                    unstash "COMPILED_BINARIES"
                                    unstash "DOCS_ARCHIVE"
                                    sh '''mkdir -p logs
                                          mkdir -p reports
                                          '''
                                }
                            }
                        }
                        stage("Running Tests"){
                            parallel {
                                stage("Run Pytest Unit Tests"){
                                    steps{
                                        timeout(10){
                                            sh(
                                                label: "Running pytest",
                                                script: '''mkdir -p reports/pytestcoverage
                                                           coverage run --parallel-mode --source=uiucprescon -m pytest --junitxml=./reports/pytest/junit-pytest.xml
                                                           '''
                                            )
                                        }
                                    }
                                    post {
                                        always {
                                            junit "reports/pytest/junit-pytest.xml"
                                            stash includes: "reports/pytest/junit-pytest.xml", name: 'PYTEST_REPORT'

                                        }
                                    }
                                }
                                stage("Run Doctest Tests"){
                                    steps {
                                        timeout(3){
                                            sh "python -m sphinx -b doctest docs/source build/docs -d build/docs/doctrees -w logs/doctest_warnings.log"
                                        }
                                    }
                                    post{
                                        always {
                                            recordIssues(tools: [sphinxBuild(name: 'Doctest', pattern: 'logs/doctest_warnings.log', id: 'doctest')])
                                        }
                                    }
                                }
                                stage("Run Flake8 Static Analysis") {
                                    steps{
                                        timeout(2){
                                            catchError(buildResult: "SUCCESS", message: 'Flake8 found issues', stageResult: "UNSTABLE") {
                                                sh(
                                                    label: "Running Flake8",
                                                    script: "flake8 uiucprescon --tee --output-file logs/flake8.log"
                                                )
                                            }
                                        }
                                    }
                                    post {
                                        always {
                                            stash includes: "logs/flake8.log", name: 'FLAKE8_REPORT'
                                            recordIssues(tools: [flake8(name: 'Flake8', pattern: 'logs/flake8.log')])
                                        }
                                    }
                                }
                                stage("Run MyPy Static Analysis") {
                                    steps{
                                        timeout(3){
                                            sh(
                                                label: "Running MyPy",
                                                script: """stubgen uiucprescon -o mypy_stubs
                                                           mkdir -p reports/mypy/html
                                                           MYPYPATH="${WORKSPACE}/mypy_stubs" mypy -p uiucprescon --cache-dir=nul --html-report reports/mypy/html > logs/mypy.log
                                                           """
                                            )
                                        }
                                    }
                                    post {
                                        always {
                                            recordIssues(tools: [myPy(name: 'MyPy', pattern: 'logs/mypy.log')])
                                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: "reports/mypy/html/", reportFiles: 'index.html', reportName: 'MyPy HTML Report', reportTitles: ''])
                                        }
                                    }
                                }
                                stage("Run Pylint Static Analysis") {
                                    steps{
                                        catchError(buildResult: 'SUCCESS', message: 'Pylint found issues', stageResult: 'UNSTABLE') {
                                            sh(label: "Running pylint",
                                                script: '''mkdir -p logs
                                                           mkdir -p reports
                                                           pylint uiucprescon -r n --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}" > reports/pylint.txt
                                                           '''

                                            )
                                        }
                                        sh(
                                            script: 'pylint   -r n --msg-template="{path}:{module}:{line}: [{msg_id}({symbol}), {obj}] {msg}" > reports/pylint_issues.txt',
                                            label: "Running pylint for sonarqube",
                                            returnStatus: true
                                        )
                                    }
                                    post{
                                        always{
                                            recordIssues(tools: [pyLint(pattern: 'reports/pylint.txt')])
                                            stash includes: "reports/pylint_issues.txt,reports/pylint.txt", name: 'PYLINT_REPORT'
                                        }
                                    }
                                }
                            }
                        }
                    }
                    post{
                        always{
                            sh(script:'''coverage combine
                                         coverage xml -o ./reports/coverage-python.xml
                                         gcovr --filter uiucprescon/ocr --print-summary --xml -o reports/coverage_cpp.xml
                                         '''
                                )
                            stash includes: "reports/coverage*.xml", name: 'COVERAGE_REPORT'
                            publishCoverage(
                                adapters: [
                                    coberturaAdapter(mergeToOneReport: true, path: 'reports/coverage*.xml')
                                ],
                                sourceFileResolver: sourceFiles('STORE_ALL_BUILD')
                            )
                        }
                        cleanup{
                            deleteDir()
                        }
                    }
                }
                stage("Run Tox test") {
                    when {
                       equals expected: true, actual: params.TEST_RUN_TOX
                    }
                    steps {
                        script{
                            def windowsJobs = [:]
                            def linuxJobs = [:]
                            stage("Scanning Tox Environments"){
                                parallel(
                                    "Linux":{
                                        linuxJobs = tox.getToxTestsParallel(
                                                envNamePrefix: "Tox Linux",
                                                label: "linux && docker",
                                                dockerfile: 'ci/docker/linux/tox/Dockerfile',
                                                dockerArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL'
                                            )
                                    },
                                    "Windows":{
                                        windowsJobs = tox.getToxTestsParallel(
                                                envNamePrefix: "Tox Windows",
                                                label: "windows && docker",
                                                dockerfile: 'ci/docker/windows/tox/Dockerfile',
                                                dockerArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE'
                                         )
                                    },
                                    failFast: true
                                )
                            }
                            parallel(windowsJobs + linuxJobs)
                        }
                    }
                }
                stage("Sonarcloud Analysis"){
                    agent {
                      dockerfile {
                        filename 'ci/docker/linux/build/Dockerfile'
                        label 'linux && docker'
                        additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) --build-arg PYTHON_VERSION=3.8'
                        args '--mount source=sonar-cache-ocr,target=/opt/sonar/.sonar/cache'
                      }
                    }
                    options{
                        lock("uiucprescon.ocr-sonarcloud")
                    }
                    when{
                        equals expected: true, actual: params.USE_SONARQUBE
                        beforeAgent true
                        beforeOptions true
                    }
                    steps{
                        unstash "COVERAGE_REPORT"
                        unstash "PYTEST_REPORT"
        // //                 unstash "BANDIT_REPORT"
                        unstash "PYLINT_REPORT"
                        unstash "FLAKE8_REPORT"
                        unstash "DIST-INFO"
                        sonarcloudSubmit("uiucprescon.ocr.dist-info/METADATA", "reports/sonar-report.json", 'sonarcloud-uiucprescon.ocr')
                    }
                    post {
                      always{
                           recordIssues(tools: [sonarQube(pattern: 'reports/sonar-report.json')])
                        }
                    }
                }
            }
        }
        stage("Python Packaging"){
            when{
                anyOf{
                    equals expected: true, actual: params.BUILD_PACKAGES
                    equals expected: true, actual: params.DEPLOY_DEVPI
                    equals expected: true, actual: params.DEPLOY_DEVPI_PRODUCTION
                }
                beforeAgent true
            }
            stages{
                stage('Building'){
                    steps{
                        script{
                            def packages
                            node(){
                                checkout scm
                                packages = load 'ci/jenkins/scripts/packaging.groovy'
                            }
                            def macBuildStages = [:]
                            SUPPORTED_MAC_VERSIONS.each{ pythonVersion ->
                                macBuildStages["MacOS - Python ${pythonVersion}: wheel"] = {
                                    packages.buildPkg(
                                        agent: [
                                            label: "mac && python${pythonVersion}",
                                        ],
                                        buildCmd: {
                                            sh "python${pythonVersion} -m pip wheel -v --no-deps -w ./dist ."
                                        },
                                        post:[
                                            cleanup: {
                                                cleanWs(
                                                    patterns: [
                                                            [pattern: 'dist/', type: 'INCLUDE'],
                                                        ],
                                                    notFailBuild: true,
                                                    deleteDirs: true
                                                )
                                            },
                                            success: {
        //                                             archiveArtifacts artifacts: 'dist/*.whl'
                                                stash includes: 'dist/*.whl', name: "python${pythonVersion} mac wheel"
                                            }
                                        ]
                                    )
                                }
                            }
                            def windowsBuildStages = [:]
                            SUPPORTED_WINDOWS_VERSIONS.each{ pythonVersion ->
                                windowsBuildStages["Windows - Python ${pythonVersion}: wheel"] = {
                                    packages.buildPkg(
                                        agent: [
                                            dockerfile: [
                                                label: 'windows && docker',
                                                filename: 'ci/docker/windows/tox/Dockerfile',
                                                additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE'
                                            ]
                                        ],
                                        buildCmd: {
                                            bat "py -${pythonVersion} -m pip wheel -v --no-deps -w ./dist ."
                                        },
                                        post:[
                                            cleanup: {
                                                cleanWs(
                                                    patterns: [
                                                            [pattern: 'dist/', type: 'INCLUDE'],
                                                        ],
                                                    notFailBuild: true,
                                                    deleteDirs: true
                                                )
                                            },
                                            success: {
                                                stash includes: 'dist/*.whl', name: "python${pythonVersion} windows wheel"
                                            }
                                        ]
                                    )
                                }
                            }
                            def buildStages =  [
                                'Source Distribution': {
                                    packages.buildPkg(
                                        agent: [
                                            dockerfile: [
                                                label: 'linux && docker',
                                                filename: 'ci/docker/linux/tox/Dockerfile',
                                                additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL'
                                            ]
                                        ],
                                        buildCmd: {
                                            sh "python3 -m pep517.build --source --out-dir dist/ ."
                                        },
                                        post:[
                                            success: {
                                                stash includes: 'dist/*.tar.gz,dist/*.zip', name: "python sdist"
                                            },
                                            cleanup: {
                                                cleanWs(
                                                    patterns: [
                                                            [pattern: 'dist/', type: 'INCLUDE'],
                                                        ],
                                                    notFailBuild: true,
                                                    deleteDirs: true
                                                )
                                            }
                                        ]
                                    )
                                }
                            ]
                            buildStages = buildStages + windowsBuildStages
                            if(params.BUILD_MAC_PACKAGES == true){
                                buildStages = buildStages + macBuildStages
                            }
                            parallel(buildStages)
                        }

                    }
                }
                stage("Testing"){
                    when{
                        equals expected: true, actual: params.TEST_PACKAGES
                    }
                    steps{
                        script{
                            def packages
                            node(){
                                checkout scm
                                packages = load 'ci/jenkins/scripts/packaging.groovy'
                            }
                            def macTestStages = [:]
                            SUPPORTED_MAC_VERSIONS.each{ pythonVersion ->
                                macTestStages["MacOS - Python ${pythonVersion}: wheel"] = {
                                    packages.testPkg2(
                                        agent: [
                                            label: "mac && python${pythonVersion}",
                                        ],
                                        testSetup: {
                                            checkout scm
                                            unstash "python${pythonVersion} mac wheel"
                                        },
                                        testCommand: {
                                            findFiles(glob: 'dist/*.whl').each{
                                                sh(label: "Running Tox",
                                                   script: """python${pythonVersion} -m venv venv
                                                   ./venv/bin/python -m pip install --upgrade pip
                                                   ./venv/bin/pip install tox
                                                   ./venv/bin/tox --installpkg ${it.path} -e py${pythonVersion.replace('.', '')}"""
                                                )
                                            }

                                        },
                                        post:[
                                            cleanup: {
                                                cleanWs(
                                                    patterns: [
                                                            [pattern: 'dist/', type: 'INCLUDE'],
                                                            [pattern: 'venv/', type: 'INCLUDE'],
                                                            [pattern: '.tox/', type: 'INCLUDE'],
                                                        ],
                                                    notFailBuild: true,
                                                    deleteDirs: true
                                                )
                                            },
                                            success: {
                                                archiveArtifacts artifacts: 'dist/*.whl'
                                            }
                                        ]
                                    )
                                }
                            }
                            def windowsTestStages = [:]
                            SUPPORTED_WINDOWS_VERSIONS.each{ pythonVersion ->
                                windowsTestStages["Windows - Python ${pythonVersion}: wheel"] = {
                                    packages.testPkg2(
                                        agent: [
                                            dockerfile: [
                                                label: 'windows && docker',
                                                filename: 'ci/docker/windows/tox/Dockerfile',
                                                additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE'
                                            ]
                                        ],
                                        testSetup: {
                                            checkout scm
                                            unstash "python${pythonVersion} windows wheel"
                                        },
                                        testCommand: {
                                            findFiles(glob: 'dist/*.whl').each{
                                                bat(label: "Running Tox", script: "tox --workdir %TEMP%\\tox --installpkg ${it.path} -e py${pythonVersion.replace('.', '')}")
                                            }

                                        },
                                        post:[
                                            cleanup: {
                                                cleanWs(
                                                    patterns: [
                                                            [pattern: 'dist/', type: 'INCLUDE'],
                                                        ],
                                                    notFailBuild: true,
                                                    deleteDirs: true
                                                )
                                            },
                                            success: {
                                                archiveArtifacts artifacts: 'dist/*.whl'
                                            }
                                        ]
                                    )
                                }
                                windowsTestStages["Windows - Python ${pythonVersion}: sdist"] = {
                                    packages.testPkg2(
                                        agent: [
                                            dockerfile: [
                                                label: 'windows && docker',
                                                filename: 'ci/docker/windows/tox/Dockerfile',
                                                additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE'
                                            ]
                                        ],
                                        testSetup: {
                                            checkout scm
                                            unstash 'python sdist'
                                        },
                                        testCommand: {
                                            findFiles(glob: 'dist/*.tar.gz').each{
                                                bat(label: "Running Tox", script: "tox --workdir %TEMP%\\tox --installpkg ${it.path} -e py${pythonVersion.replace('.', '')}")
                                            }

                                        },
                                        post:[
                                            cleanup: {
                                                cleanWs(
                                                    patterns: [
                                                            [pattern: 'dist/', type: 'INCLUDE'],
                                                        ],
                                                    notFailBuild: true,
                                                    deleteDirs: true
                                                )
                                            },
                                        ]
                                    )
                                }
                            }
                            def testingStages = windowsTestStages
                            if(params.BUILD_MAC_PACKAGES == true){
                                testingStages = testingStages + macTestStages
                            }
                            parallel(testingStages)
                        }
                    }
                }
            }
        }
//             stages{
//                 stage("Windows"){
//                 }
//             }
//             steps{
//                 script{
// //                     def packages
// //                     node(){
// //                         checkout scm
// //                         packages = load 'ci/jenkins/scripts/packaging.groovy'
// //                     }
// //                     def windowsStages = [:]
//                     def windowsStages = buildAndTestWheel(SUPPORTED_WINDOWS_VERSIONS)
// //                     SUPPORTED_WINDOWS_VERSIONS.each{ pythonVersion ->
// //                         windowsStages["Windows - Python ${pythonVersion}: wheel"] = {
// //                             return [
// //                                 stage('Build Wheel'){
// //                                     packages.buildPkg(
// //                                         agent: [
// //                                             dockerfile: [
// //                                                 label: 'windows && docker',
// //                                                 filename: 'ci/docker/windows/tox/Dockerfile',
// //                                                 additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE'
// //                                             ]
// //                                         ],
// //                                             buildCmd: {
// //                                                 bat "py -${pythonVersion} -m pip wheel -v --no-deps -w ./dist ."
// //                                             },
// //                                         post:[
// //                                             cleanup: {
// //                                                 cleanWs(
// //                                                     patterns: [
// //                                                             [pattern: './dist/', type: 'INCLUDE'],
// //                                                         ],
// //                                                     notFailBuild: true,
// //                                                     deleteDirs: true
// //                                                 )
// //                                             },
// //                                             success: {
// //         //                                             archiveArtifacts artifacts: 'dist/*.whl'
// //                                                 stash includes: 'dist/*.whl', name: "python${pythonVersion} windows wheel"
// //                                             }
// //                                         ]
// //                                     )
// //                                 },
// //                                 stage('Test Wheel'){
// //     //                             TODO test with something other than the tox
// //                                     packages.testPkg(
// //                                         agent: [
// //                                             dockerfile: [
// //                                                 label: 'windows && docker',
// //                                                 filename: 'ci/docker/windows/tox/Dockerfile',
// //                                                 additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE'
// //                                             ]
// //                                         ],
// //                                         glob: 'dist/*.whl',
// //                                         stash: "python${pythonVersion} windows wheel",
// //                                         pythonVersion: pythonVersion
// //                                     )
// //                                 }
// //                             ]
// //
// //                         }
// //                     }
//                     def macStages = [:]
//                     SUPPORTED_MAC_VERSIONS.each{ pythonVersion ->
//                         macStages["Mac - Python ${pythonVersion}: wheel"] = {
//                             def stashName = "python${pythonVersion} MacOS wheel"
//                             stage('Build Wheel'){
//                                 packages.buildPkg(
//                                         agent: [
//                                             dockerfile: [
//                                                 label: 'windows && docker',
//                                                 filename: 'ci/docker/windows/tox/Dockerfile',
//                                                 additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE'
//                                             ]
//                                         ],
//                                             buildCmd: {
//                                                 bat "py -${pythonVersion} -m pip wheel -v --no-deps -w ./dist ."
//                                             },
//                                         post:[
//                                             cleanup: {
//                                                 cleanWs(
//                                                     patterns: [
//                                                             [pattern: './dist/', type: 'INCLUDE'],
//                                                         ],
//                                                     notFailBuild: true,
//                                                     deleteDirs: true
//                                                 )
//                                             },
//                                             success: {
//         //                                             archiveArtifacts artifacts: 'dist/*.whl'
//                                                 stash includes: 'dist/*.whl', name: "python${pythonVersion} windows wheel"
//                                             }
//                                         ]
//                                     )
//                                 }
//     //                         packages.testPkg(
//     //                             agent: [
//     //                                 label: "mac && python${pythonVersion}",
//     //                             ],
//     //                             glob: 'dist/*.tar.gz,dist/*.zip',
//     //                             stash: 'PYTHON_PACKAGES',
//     //                             pythonVersion: pythonVersion,
//     //                             toxExec: 'venv/bin/tox',
//     //                             testSetup: {
//     //                                 checkout scm
//     //                                 unstash 'PYTHON_PACKAGES'
//     //                                 sh(
//     //                                     label:'Install Tox',
//     //                                     script: '''python3 -m venv venv
//     //                                                venv/bin/pip install pip --upgrade
//     //                                                venv/bin/pip install tox
//     //                                                '''
//     //                                 )
//     //                             },
//     //                             testTeardown: {
//     //                                 sh 'rm -r venv/'
//     //                             }
//     //                         )
//                         }
//                     }
//                     def linuxStages = [:]
//                     SUPPORTED_LINUX_VERSIONS.each{ pythonVersion ->
// //                         TODO: Make work with ci/docker/linux/package/Dockerfile
//                         linuxStages["Linux - Python ${pythonVersion}: wheel"] = {
//                             def stashName = "python${pythonVersion} linux wheel"
//                             stage('Build Wheel'){
//                                 packages.buildPkg(
//                                     agent: [
//                                         dockerfile: [
//                                             label: 'linux && docker',
//                                             filename: 'ci/docker/linux/tox/Dockerfile',
//                                             additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL'
//                                         ]
//                                     ],
//                                     buildCmd: {
//                                         sh "python${pythonVersion} -m pip wheel -v --no-deps -w ./dist ."
//                                     },
//                                     post:[
//                                         cleanup: {
//                                             cleanWs(
//                                                 patterns: [
//                                                         [pattern: './dist/', type: 'INCLUDE'],
//                                                     ],
//                                                 notFailBuild: true,
//                                                 deleteDirs: true
//                                             )
//                                         },
//                                         success: {
// //                                             archiveArtifacts artifacts: 'dist/*.whl'
//                                             stash includes: 'dist/*.whl', name: stashName
//                                         }
//                                     ]
//                                 )
//                             }
//                             stage('Test Wheel'){
//                                 packages.testPkg(
//                                     agent: [
//                                         dockerfile: [
//                                             label: 'linux && docker',
//                                             filename: 'ci/docker/python/linux/tox/Dockerfile',
//                                             additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL'
//                                         ]
//                                     ],
//                                     glob: 'dist/*.tar.gz',
//                                     stash: 'PYTHON_PACKAGES',
//                                     pythonVersion: pythonVersion
//                                 )
//                             }
//                             linuxTests["Linux - Python ${pythonVersion}: wheel"] = {
//                                 packages.testPkg(
//                                     agent: [
//                                         dockerfile: [
//                                             label: 'linux && docker',
//                                             filename: 'ci/docker/python/linux/tox/Dockerfile',
//                                             additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
//                                         ]
//                                     ],
//                                     glob: 'dist/*.whl',
//                                     stash: 'PYTHON_PACKAGES',
//                                     pythonVersion: pythonVersion
//                                 )
//                             }
//                         }
// //                         TODO: Make linux sdist tests
// //                             linuxTests["Linux - Python ${pythonVersion}: sdist"] = {
// //                                 packages.testPkg(
// //                                     agent: [
// //                                         dockerfile: [
// //                                             label: 'linux && docker',
// //                                             filename: 'ci/docker/python/linux/tox/Dockerfile',
// //                                             additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL'
// //                                         ]
// //                                     ],
// //                                     glob: 'dist/*.tar.gz',
// //                                     stash: 'PYTHON_PACKAGES',
// //                                     pythonVersion: pythonVersion
// //                                 )
// //                             }
// //                             linuxTests["Linux - Python ${pythonVersion}: wheel"] = {
// //                                 packages.testPkg(
// //                                     agent: [
// //                                         dockerfile: [
// //                                             label: 'linux && docker',
// //                                             filename: 'ci/docker/python/linux/tox/Dockerfile',
// //                                             additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
// //                                         ]
// //                                     ],
// //                                     glob: 'dist/*.whl',
// //                                     stash: 'PYTHON_PACKAGES',
// //                                     pythonVersion: pythonVersion
// //                                 )
// //                             }
//                         }
//                     def packageStages =  windowsStages + macStages
// //                     def packageStages = linuxStages + windowsStages + macStages
// //                     parallel(packageStages)
//                     parallel(windowsStages)
//                 }
//             }
//         }
//         stage("Python Packaging"){
//             when{
//                 anyOf{
//                     equals expected: true, actual: params.BUILD_PACKAGES
//                     equals expected: true, actual: params.DEPLOY_DEVPI
//                     equals expected: true, actual: params.DEPLOY_DEVPI_PRODUCTION
//                 }
//                 beforeAgent true
//             }
//             stages{
//                 stage("Build sdist"){
//                     agent {
//                         dockerfile {
//                             filename 'ci/docker/linux/build/Dockerfile'
//                             label 'linux && docker'
//                             additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) --build-arg PYTHON_VERSION=3.8'
//                         }
//                     }
//                     steps {
//                         sh "python -m pep517.build --source --out-dir dist/ ."
//                     }
//                     post{
//                         always{
//                             stash includes: 'dist/*.zip,dist/*.tar.gz', name: "sdist"
//                         }
//                     }
//                 }
//                 stage("Mac Versions"){
//                     when{
//                         equals expected: true, actual: params.BUILD_MAC_PACKAGES
//                         beforeAgent true
//                     }
//                     matrix{
//                         agent none
//                         axes{
//                             axis {
//                                 name "PYTHON_VERSION"
//                                 values(
//                                     "3.8",
//                                     '3.9'
//                                 )
//                             }
//                         }
//                         stages{
//                             stage("Build"){
//                                 steps{
//                                     script{
//                                         def stashName = "MacOS 10.14 py${PYTHON_VERSION} wheel"
//                                         mac.build_mac_package(
//                                             label: "mac && 10.14 && python${PYTHON_VERSION}",
//                                             pythonPath: "python${PYTHON_VERSION}",
//                                             stash: [
//                                                 includes: 'dist/*.whl',
//                                                 name: stashName
//                                             ]
//                                         )
//                                         wheelStashes << stashName
//                                     }
//                                 }
//                             }
//                             stage("Test Packages"){
//                                 when{
//                                      equals expected: true, actual: params.TEST_PACKAGES
//                                 }
//                                 stages{
//                                     stage("Test wheel"){
//                                         steps{
//                                             script{
//                                                 mac.test_mac_package(
//                                                     label: "mac && 10.14 && python${PYTHON_VERSION}",
//                                                     pythonPath: "python${PYTHON_VERSION}",
//                                                     stash: "MacOS 10.14 py${PYTHON_VERSION} wheel",
//                                                     glob: "dist/*.whl"
//                                                 )
//                                             }
//                                         }
//                                     }
//                                     stage("Test sdist"){
//                                         steps{
//                                             script{
//                                                 mac.test_mac_package(
//                                                     label: "mac && 10.14 && python${PYTHON_VERSION}",
//                                                     pythonPath: "python${PYTHON_VERSION}",
//                                                     stash: "sdist",
//                                                     glob: "dist/*.tar.gz,dist/*.zip"
//                                                 )
//                                             }
//                                         }
//                                     }
//                                 }
//                             }
//                         }
//                     }
//                 }
//                 stage("Packages on Windows and Linux"){
//                     matrix{
//                         axes {
//                             axis {
//                                 name 'PYTHON_VERSION'
//                                 values(
//                                     '3.6',
//                                     '3.7',
//                                     '3.8',
//                                     '3.9'
//                                 )
//                             }
//                             axis {
//                                 name 'PLATFORM'
//                                 values(
//                                     "windows",
//                                     "linux"
//                                 )
//                             }
//                         }
//                         stages {
//                             stage("Building Wheel"){
//                                 agent {
//                                     dockerfile {
//                                         filename "${configurations[PYTHON_VERSION].os[PLATFORM].agents.package.dockerfile.filename}"
//                                         label "${PLATFORM} && docker"
//                                         additionalBuildArgs "${configurations[PYTHON_VERSION].os[PLATFORM].agents.package.dockerfile.additionalBuildArgs}"
//                                      }
//                                 }
//                                 steps{
//                                     build_wheel(PLATFORM)
//                                 }
//                                 post {
//                                     always{
//                                         script{
//                                             def stashName = "whl ${PYTHON_VERSION}-${PLATFORM}"
//                                             if( PLATFORM == 'linux'){
//                                                 stash includes: 'dist/*manylinux*.whl', name: stashName
//                                             } else {
//                                                 stash includes: "dist/*.whl", name: stashName
//                                             }
//                                             wheelStashes << stashName
//                                         }
//                                     }
//                                     success{
//                                         archiveArtifacts allowEmptyArchive: true, artifacts: "dist/${configurations[PYTHON_VERSION].os[PLATFORM].pkgRegex['whl']}"
//                                         script{
//                                             if(!isUnix()){
//                                                 findFiles(excludes: '', glob: '**/*.pyd').each{
//                                                     bat(
//                                                         label: "Scanning dll dependencies of ${it.name}",
//                                                         script:"dumpbin /DEPENDENTS ${it.path}"
//                                                         )
//                                                 }
//                                             }
//                                         }
//                                     }
//                                     cleanup{
//                                         cleanWs(
//                                                 deleteDirs: true,
//                                                 patterns: [
//                                                     [pattern: 'dist/', type: 'INCLUDE'],
//                                                     [pattern: 'build/', type: 'INCLUDE']
//                                                 ]
//                                             )
//                                     }
//                                 }
//                             }
//                             stage("Testing Packages"){
//                                 when{
//                                     anyOf{
//                                         equals expected: true, actual: params.TEST_PACKAGES
//                                     }
//                                     beforeAgent true
//                                 }
//                                 stages{
//                                     stage("Testing Wheel Package"){
//                                         agent {
//                                             dockerfile {
//                                                 filename "${configurations[PYTHON_VERSION].os[PLATFORM].agents.test['whl'].dockerfile.filename}"
//                                                 label "${PLATFORM} && docker"
//                                                 additionalBuildArgs "${configurations[PYTHON_VERSION].os[PLATFORM].agents.test['whl'].dockerfile.additionalBuildArgs}"
//                                              }
//                                         }
//                                         steps{
//                                             unstash "whl ${PYTHON_VERSION}-${PLATFORM}"
//                                             test_pkg("dist/**/${configurations[PYTHON_VERSION].os[PLATFORM].pkgRegex['whl']}", 20)
//                                         }
//                                         post{
//                                             cleanup{
//                                                 cleanWs(
//                                                     notFailBuild: true,
//                                                     deleteDirs: true,
//                                                     patterns: [
//                                                             [pattern: 'dist', type: 'INCLUDE'],
//                                                             [pattern: 'build', type: 'INCLUDE'],
//                                                             [pattern: '.tox', type: 'INCLUDE'],
//                                                         ]
//                                                 )
//                                             }
//                                         }
//                                     }
//                                     stage("Testing sdist package"){
//                                         agent {
//                                             dockerfile {
//                                                 filename "${configurations[PYTHON_VERSION].os[PLATFORM].agents.test['sdist'].dockerfile.filename}"
//                                                 label "${PLATFORM} && docker"
//                                                 additionalBuildArgs "${configurations[PYTHON_VERSION].os[PLATFORM].agents.test['sdist'].dockerfile.additionalBuildArgs}"
//                                              }
//                                         }
//                                         steps{
//                                             catchError(stageResult: 'FAILURE') {
//                                                 unstash "sdist"
//                                                 test_pkg("dist/**/${configurations[PYTHON_VERSION].os[PLATFORM].pkgRegex['sdist']}", 20)
//                                             }
//                                         }
//                                     }
//                                 }
//                             }
//                         }
//                     }
//                 }
//             }
//         }
        stage("Deploy to DevPi") {
            agent none
            options{
                lock("uiucprescon.ocr-devpi")
            }
            when {
                allOf{
                    equals expected: true, actual: params.DEPLOY_DEVPI
                    anyOf {
                        equals expected: "master", actual: env.BRANCH_NAME
                        equals expected: "dev", actual: env.BRANCH_NAME
                        tag "*"
                    }
                }
                beforeAgent true
            }
            environment{
//                 DEVPI = credentials("DS_devpi")
                devpiStagingIndex = getDevPiStagingIndex()
            }
            stages{
                stage("Upload to DevPi Staging"){
                    agent {
                        dockerfile {
                            filename 'ci/docker/deploy/devpi/deploy/Dockerfile'
                            label 'linux&&docker'
                            additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                          }
                    }
                    steps {
                        script{
                            unstash "sdist"
                            unstash "DOCS_ARCHIVE"
                            wheelStashes.each{
                                unstash it
                            }
                            devpiLib.upload(
                                server: "https://devpi.library.illinois.edu",
                                credentialsId: "DS_devpi",
                                index: getDevPiStagingIndex(),
                                clientDir: "./devpi"
                            )
                        }
                    }
                    post{
                        cleanup{
                            cleanWs(
                                notFailBuild: true
                            )
                        }
                    }
                }
                stage("Test DevPi packages mac") {
                    when{
                        equals expected: true, actual: params.BUILD_MAC_PACKAGES
                        beforeAgent true
                    }
                    matrix {
                        axes{
                            axis {
                                name "PYTHON_VERSION"
                                values(
                                    "3.7",
                                    "3.8",
                                    '3.9'
                                )
                            }
                            axis {
                                name "FORMAT"
                                values(
                                    "wheel",
                                    'sdist'
                                )
                            }
                        }
                        excludes{
                            exclude{
                                axis{
                                    name 'PYTHON_VERSION'
                                    values '3.7'
                                }
                                axis{
                                    name 'FORMAT'
                                    values 'wheel'
                                }
                            }
                        }
                        agent none
                        stages{
                            stage("Test devpi Package"){
                                agent {
                                    label "mac && 10.14 && python${PYTHON_VERSION}"
                                }
                                steps{
                                    timeout(10){
                                        sh(
                                            label: "Installing devpi client",
                                            script: '''python${PYTHON_VERSION} -m venv venv
                                                       venv/bin/python -m pip install --upgrade pip
                                                       venv/bin/pip install devpi-client
                                                       venv/bin/devpi --version
                                            '''
                                        )
                                        script{
                                            devpiLib.testDevpiPackage(
                                                devpiExec: "venv/bin/devpi",
                                                devpiIndex: getDevPiStagingIndex(),
                                                server: "https://devpi.library.illinois.edu",
                                                credentialsId: "DS_devpi",
                                                pkgName: props.Name,
                                                pkgVersion: props.Version,
                                                pkgSelector: getMacDevpiName(PYTHON_VERSION, FORMAT),
                                                toxEnv: "py${PYTHON_VERSION.replace('.','')}"
                                            )
                                        }
                                    }
                                }
                                post{
                                    cleanup{
                                        cleanWs(
                                            notFailBuild: true,
                                            deleteDirs: true,
                                            patterns: [
                                                [pattern: 'venv/', type: 'INCLUDE'],
                                            ]
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
                stage("Test DevPi packages") {
                    matrix{
                        axes {
                            axis {
                                name 'PYTHON_VERSION'
                                values(
                                    '3.6',
                                    '3.7',
                                    '3.8',
                                    "3.9"
                                )
                            }
                            axis {
                                name 'PLATFORM'
                                values(
                                    "windows",
                                    "linux"
                                )
                            }
                        }
                        stages {
                            stage("Testing DevPi Wheel Package"){
                                agent {
                                    dockerfile {
                                        filename "${configurations[PYTHON_VERSION].os[PLATFORM].agents.devpi['wheel'].dockerfile.filename}"
                                        label "${PLATFORM} && docker"
                                        additionalBuildArgs "${configurations[PYTHON_VERSION].os[PLATFORM].agents.devpi['wheel'].dockerfile.additionalBuildArgs}"
                                     }
                                }
                                options {
                                    warnError('Package Testing Failed')
                                }
                                steps{
                                    timeout(10){
                                        script{
                                            devpiLib.testDevpiPackage(
                                                devpiIndex: getDevPiStagingIndex(),
                                                server: "https://devpi.library.illinois.edu",
                                                credentialsId: "DS_devpi",
                                                pkgName: props.Name,
                                                pkgVersion: props.Version,
                                                pkgSelector: configurations[PYTHON_VERSION].os[PLATFORM].devpiSelector["wheel"],
                                                toxEnv: configurations[PYTHON_VERSION].tox_env
                                            )
                                        }
                                    }
                                }
                            }
                            stage("Testing DevPi sdist Package"){
                                agent {
                                    dockerfile {
                                        filename "${configurations[PYTHON_VERSION].os[PLATFORM].agents.devpi['sdist'].dockerfile.filename}"
                                        label "${PLATFORM} && docker"
                                        additionalBuildArgs "${configurations[PYTHON_VERSION].os[PLATFORM].agents.devpi['sdist'].dockerfile.additionalBuildArgs}"
                                     }
                                }
                                options {
                                    warnError('Package Testing Failed')
                                }
                                steps{
                                    timeout(10){
                                    script{
                                            devpiLib.testDevpiPackage(
                                                devpiIndex: getDevPiStagingIndex(),
                                                server: "https://devpi.library.illinois.edu",
                                                credentialsId: "DS_devpi",
                                                pkgName: props.Name,
                                                pkgVersion: props.Version,
                                                pkgSelector: "tar.gz",
                                                toxEnv: configurations[PYTHON_VERSION].tox_env
                                            )
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                stage("Deploy to DevPi Production") {
                    when {
                        allOf{
                            equals expected: true, actual: params.DEPLOY_DEVPI_PRODUCTION
                            anyOf {
                                branch "master"
                                tag "*"
                            }
                        }
                        beforeAgent true
                        beforeInput true
                    }
                    options{
                      timeout(time: 1, unit: 'DAYS')
                    }
                    input {
                      message 'Release to DevPi Production?'
                    }
                    agent {
                        dockerfile {
                            filename 'ci/docker/deploy/devpi/deploy/Dockerfile'
                            label 'linux&&docker'
                            additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                        }
                    }
                    steps {
                        script{
                            echo "Pushing to production/release index"
                            devpiLib.pushPackageToIndex(
                                pkgName: props.Name,
                                pkgVersion: props.Version,
                                server: "https://devpi.library.illinois.edu",
                                indexSource: "DS_Jenkins/${getDevPiStagingIndex()}",
                                indexDestination: "production/release",
                                credentialsId: 'DS_devpi'
                            )
                        }
                    }
                }
            }
            post {
                success{
                    node('linux && docker') {
                        script{
                            if (!env.TAG_NAME?.trim()){
                                docker.build("ocr:devpi",'-f ./ci/docker/deploy/devpi/deploy/Dockerfile --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) .').inside{
                                    devpiLib.pushPackageToIndex(
                                        pkgName: props.Name,
                                        pkgVersion: props.Version,
                                        server: "https://devpi.library.illinois.edu",
                                        indexSource: "DS_Jenkins/${getDevPiStagingIndex()}",
                                        indexDestination: "DS_Jenkins/${env.BRANCH_NAME}",
                                        credentialsId: 'DS_devpi'
                                    )
                                }
                            }
                        }
                    }
                }
                cleanup{
                    node('linux && docker') {
                        script{
                            docker.build("ocr:devpi",'-f ./ci/docker/deploy/devpi/deploy/Dockerfile --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) .').inside{
                                devpiLib.removePackage(
                                    pkgName: props.Name,
                                    pkgVersion: props.Version,
                                    index: "DS_Jenkins/${getDevPiStagingIndex()}",
                                    server: "https://devpi.library.illinois.edu",
                                    credentialsId: 'DS_devpi',

                                )
                            }
                        }
                    }
                }
            }
        }
        stage("Deploy"){
            parallel{
                stage("Deploy Online Documentation") {
                    when{
                        equals expected: true, actual: params.DEPLOY_DOCS
                        beforeAgent true
                    }
                    agent {
                        dockerfile {
                            filename 'ci/docker/linux/build/Dockerfile'
                            label 'linux && docker'
                            additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                        }
                    }
                    steps{
                        unstash "DOCS_ARCHIVE"
                        deploy_docs(get_package_name("DIST-INFO", "uiucprescon.ocr.dist-info/METADATA"), "build/docs/html")
                    }
                }
            }
        }
    }
}
