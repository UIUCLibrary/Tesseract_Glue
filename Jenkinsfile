@Library(["devpi", "PythonHelpers"]) _


def remove_files(artifacts){
    script{
        def files = findFiles glob: "${artifacts}"
        files.each { file_name ->
            bat "del ${file_name}"
        }
    }
}


def remove_from_devpi(devpiExecutable, pkgName, pkgVersion, devpiIndex, devpiUsername, devpiPassword){
    script {
            try {
                bat "${devpiExecutable} login ${devpiUsername} --password ${devpiPassword}"
                bat "${devpiExecutable} use ${devpiIndex}"
                bat "${devpiExecutable} remove -y ${pkgName}==${pkgVersion}"
            } catch (Exception ex) {
                echo "Failed to remove ${pkgName}==${pkgVersion} from ${devpiIndex}"
        }

    }
}

pipeline {
    agent {
        label "Windows && VS2015 && Python3 && longfilenames"
    }

    triggers {
        cron('@daily')
    }

    options {
        disableConcurrentBuilds()  //each branch has 1 job running at a time
        timeout(60)  // Timeout after 60 minutes. This shouldn't take this long but it hangs for some reason
        checkoutToSubdirectory("source")
        preserveStashes()
    }
    environment {
        PKG_NAME = pythonPackageName(toolName: "CPython-3.6")
        PKG_VERSION = pythonPackageVersion(toolName: "CPython-3.6")
        DOC_ZIP_FILENAME = "${env.PKG_NAME}-${env.PKG_VERSION}.doc.zip"
        DEVPI = credentials("DS_devpi")
        PIPENV_NOSPIN="DISABLED"
        build_number = VersionNumber(projectStartDate: '2018-7-30', versionNumberString: '${BUILD_DATE_FORMATTED, "yy"}${BUILD_MONTH, XX}${BUILDS_THIS_MONTH, XX}', versionPrefix: '', worstResultForIncrement: 'SUCCESS')
        PIPENV_CACHE_DIR="${WORKSPACE}\\..\\.virtualenvs\\cache\\"
        WORKON_HOME ="${WORKSPACE}\\pipenv\\"
        
    }
    parameters {
        booleanParam(name: "FRESH_WORKSPACE", defaultValue: false, description: "Purge workspace before staring and checking out source")
//        booleanParam(name: "BUILD_DOCS", defaultValue: true, description: "Build documentation")
        booleanParam(name: "TEST_RUN_DOCTEST", defaultValue: true, description: "Test documentation")
        booleanParam(name: "TEST_RUN_PYTEST", defaultValue: true, description: "Run PyTest unit tests")
        booleanParam(name: "TEST_RUN_FLAKE8", defaultValue: true, description: "Run Flake8 static analysis")
        booleanParam(name: "TEST_RUN_MYPY", defaultValue: true, description: "Run MyPy static analysis")
        booleanParam(name: "TEST_RUN_TOX", defaultValue: true, description: "Run Tox Tests")

        booleanParam(name: "DEPLOY_DEVPI", defaultValue: true, description: "Deploy to devpi on http://devpy.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}")
        booleanParam(name: "DEPLOY_DEVPI_PRODUCTION", defaultValue: false, description: "Deploy to https://devpi.library.illinois.edu/production/release")
        // choice(choices: 'None\nrelease', description: "Release the build to production. Only available in the Master branch", name: 'RELEASE')
        string(name: 'DEPLOY_DOCS_URL_SUBFOLDER', defaultValue: "ocr", description: 'The directory that the docs should be saved under')
        booleanParam(name: "DEPLOY_DOCS", defaultValue: false, description: "Update online documentation")
    }
    stages {
        stage("Configure") {
            environment {
                PATH = "${tool 'CPython-3.6'};${tool 'CPython-3.7'};$PATH"
            }
            stages{
                stage("Purge all existing data in workspace"){
                    when{
                        equals expected: true, actual: params.FRESH_WORKSPACE
                    }
                    steps{
                        deleteDir()
                        dir("source"){
                            checkout scm
                        }
                    }
                }
                stage("Installing Required System Level Dependencies"){
                    steps{
                        lock("system_python_${NODE_NAME}"){
                            bat "python -m pip install pip --upgrade --quiet && python -m pip install --upgrade pipenv --quiet"
                        }

                        bat "python.exe -m pip list > logs/pippackages_system_${NODE_NAME}.log"

                    }
                    post{
                        success{
                            archiveArtifacts artifacts: "logs/pippackages_system_${NODE_NAME}.log"
                        }
                    }

                }
                stage("Installing Pipfile"){
                    options{
                        timeout(5)
                    }
                    steps {
                        dir("source"){
                            bat "python.exe -m pipenv install --dev --deploy && python.exe -m pipenv check"
                            bat "python.exe -m pipenv run pip list > ${WORKSPACE}/logs/pippackages_pipenv_${NODE_NAME}.log"
                        }
                    }
                    post{
                        success{
                            archiveArtifacts artifacts: "logs/pippackages_pipenv_${NODE_NAME}.log"
                        }
                    }
                }
                stage("Creating Virtualenv for Building"){
                    steps {
                        bat "python.exe -m venv venv"

                        script {
                            try {
                                bat "venv\\Scripts\\python.exe -m pip install -U pip"
                            }
                            catch (exc) {
                                bat "python.exe -m venv venv"
                                bat "call venv\\Scripts\\python.exe -m pip install -U pip --no-cache-dir"
                            }
                        }

                        bat "venv\\Scripts\\pip.exe install devpi-client pytest pytest-cov pytest-bdd --upgrade-strategy only-if-needed"                    }
                    post{
                        success{
                            bat "venv\\Scripts\\pip.exe list > logs/pippackages_venv_${NODE_NAME}.log"
                            archiveArtifacts artifacts: "logs/pippackages_system_${NODE_NAME}.log"
                        }

                    }
                }
                // TODO: Remove login devpi stage
                stage("Logging into DevPi"){
                    environment{
                        DEVPI_PSWD = credentials('devpi-login')
                    }
                    steps{
                        bat "venv\\Scripts\\devpi use https://devpi.library.illinois.edu --clientdir ${WORKSPACE}\\certs\\"
                        bat "venv\\Scripts\\devpi.exe login DS_Jenkins --password ${env.DEVPI_PSWD} --clientdir ${WORKSPACE}\\certs\\"
                    }
                }
            }
            post{
                success{
                    echo "Configured ${env.PKG_NAME}, version ${env.PKG_VERSION}, for testing."
                }
                failure {
                    deleteDir()
                }
            }

        }
        stage("Building") {
                        
            stages{
                stage("Building Python Package"){
                    environment {
                        PATH = "${WORKSPACE}\\venv\\Scripts;${tool 'cmake3.13'};$PATH"
                    }
                    steps {

                        dir("source"){

                            powershell "& python setup.py build -b ${WORKSPACE}\\build -j${env.NUMBER_OF_PROCESSORS} --build-lib ../build/lib | tee ${WORKSPACE}\\logs\\build.log"

                        }

                        dir("build\\lib\\tests"){
                            bat "copy ${WORKSPACE}\\source\\tests\\*.py"

                        }
                        dir("build\\lib\\tests\\feature"){
                                bat "copy ${WORKSPACE}\\source\\tests\\feature\\*.py"
                                bat "copy ${WORKSPACE}\\source\\tests\\feature\\*.feature"
                        }
                    }
                    post{
                        always{
                            warnings canRunOnFailed: true, parserConfigurations: [[parserName: 'MSBuild', pattern: "logs\\build.log"]]
                        }
                        cleanup{
                            cleanWs(
                                patterns: [
                                        [pattern: 'logs/build.log', type: 'INCLUDE'],
                                        [pattern: "logs/tree_postbuild_failed.log", type: 'INCLUDE'],
                                        [pattern: "logs/tree_home_postbuild_failed.log", type: 'INCLUDE'],
                                        [pattern: "logs/env_vars.log", type: 'INCLUDE'],
                                    ],
                                notFailBuild: true
                                )


                        }
                    }
                }
                stage("Building Documentation"){
                    environment {
                        PATH = "${tool 'CPython-3.6'};${tool 'CPython-3.7'};$PATH"
                    }
                    steps{
                        echo "Building docs on ${env.NODE_NAME}"
//#                        script{
//#                            // Add a line to config file so auto docs look in the build folder
//#                            def sphinx_config_file = "${WORKSPACE}/source/docs/source/conf.py"
//#                            def extra_line = "sys.path.insert(0, os.path.abspath('${WORKSPACE}/build/lib'))"
//#                            def readContent = readFile "${sphinx_config_file}"
//#                            echo "Adding \"${extra_line}\" to ${sphinx_config_file}."
//#                            writeFile file: "${sphinx_config_file}", text: readContent+"\r\n${extra_line}\r\n"
//#                        }
                        dir("source"){
                            bat "python -m pipenv run sphinx-build docs/source ${WORKSPACE}\\build\\docs\\html -d ${WORKSPACE}\\build\\docs\\.doctrees -w ${WORKSPACE}\\logs\\build_sphinx.log"
                        }
//#                        dir("build/lib"){
//#                            bat "python -m pipenv run sphinx-build -b html ${WORKSPACE}\\source\\docs\\source ${WORKSPACE}\\build\\docs\\html -d ${WORKSPACE}\\build\\docs\\doctrees"
//#                        }
                    }
                    post{
                        always {
                            warnings canRunOnFailed: true, parserConfigurations: [[parserName: 'Pep8', pattern: 'logs/build_sphinx.log']]
                            archiveArtifacts artifacts: 'logs/build_sphinx.log', allowEmptyArchive: true

                        }
                        success{
                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'build/docs/html', reportFiles: 'index.html', reportName: 'Documentation', reportTitles: ''])
//                            script{
//                                // // Multibranch jobs add the slash and add the branch to the job name. I need only the job name
//                                // def alljob = env.JOB_NAME.tokenize("/") as String[]
//                                // def project_name = alljob[0]
//                                // dir("${WORKSPACE}/dist"){
//                                //     zip archive: true, dir: "${WORKSPACE}/build/docs/html", glob: '', zipFile: "${env.DOC_ZIP_FILENAME}"
//                                // }
//                                script{
                            zip archive: true, dir: "${WORKSPACE}/build/docs/html", glob: '', zipFile: "dist/${env.DOC_ZIP_FILENAME}"
                            stash includes: 'build/docs/html/**', name: 'docs'
//#                                }
//                            }
                        }
                        failure{
                            echo "Failed to build Python package"
                        }
//#                        cleanup{
//#                            script{
//#                                if(fileExists("logs/build_sphinx.log")){
//#                                    bat "del logs\\build_sphinx.log"
//#                                }
//#                            }
//#
//#                        }
                    }
                }
            }
        }

        stage("Testing") {
            parallel {
                stage("Run Tox test") {
                    agent{
                        node {
                            label "Windows && VS2015 && Python3 && longfilenames"
                            customWorkspace "c:/Jenkins/temp/${JOB_NAME}/tox/"
                        }
                    }
                    when {
                       equals expected: true, actual: params.TEST_RUN_TOX
                    }
                    environment {
                        PATH = "${tool 'cmake3.13'}\\;$PATH"
                        CL = "/MP"

                    }
                    stages{
                        stage("Removing Previous Tox Environment"){
                            when{
                                equals expected: true, actual: params.FRESH_WORKSPACE
                            }
                            steps{
                                dir(".tox"){
                                    deleteDir()
                                }
                            }

                        }
                        stage("Configuring Tox Environment"){
                            steps{
                                dir("source"){
                                    bat "${tool 'CPython-3.6'}\\python.exe -m pipenv install --dev --deploy"
                                }
                            }
                        }
                        stage("Run Tox"){
                            steps {

                                dir("source"){
                                    lock("cppan_${NODE_NAME}"){
                                        script{
                                            try{
                                                bat "pipenv run tox --workdir ..\\.tox\\PyTest"

                                            } catch (exc) {
                                                bat "pipenv run tox -vv --recreate --workdir ..\\.tox\\PyTest"
                                            }

                                        }
                                    }
                                }
                            }
                        }

                    }
                }
                stage("Run Pytest Unit Tests"){
                    when {
                       equals expected: true, actual: params.TEST_RUN_PYTEST
                    }
                    environment{
                        junit_filename = "junit-${env.NODE_NAME}-${env.GIT_COMMIT.substring(0,7)}-pytest.xml"
                    }
                    steps{
                        dir("build\\lib"){
                            bat "${WORKSPACE}\\venv\\Scripts\\python.exe -m pytest --junitxml=${WORKSPACE}/reports/pytest/${env.junit_filename} --junit-prefix=${env.NODE_NAME}-pytest --cov-report html:${WORKSPACE}/reports/pytestcoverage/  --cov-report xml:${WORKSPACE}/reports/coverage.xml --cov=uiucprescon --integration --cov-config=${WORKSPACE}/source/setup.cfg"
                        }
                    }
                    post {
                        always {
                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: "reports/pytestcoverage", reportFiles: 'index.html', reportName: 'Coverage.py', reportTitles: ''])
                            junit "reports/pytest/${env.junit_filename}"
                            script {
                                try{
                                    publishCoverage
                                        autoDetectPath: 'coverage*/*.xml'
                                        adapters: [
                                            cobertura(coberturaReportFile:"reports/coverage.xml")
                                        ]
                                } catch(exc){
                                    echo "cobertura With Coverage API failed. Falling back to cobertura plugin"
                                    cobertura autoUpdateHealth: false, autoUpdateStability: false, coberturaReportFile: "reports/coverage.xml", conditionalCoverageTargets: '70, 0, 0', failUnhealthy: false, failUnstable: false, lineCoverageTargets: '80, 0, 0', maxNumberOfBuilds: 0, methodCoverageTargets: '80, 0, 0', onlyStable: false, sourceEncoding: 'ASCII', zoomCoverageChart: false
                                }
                            }
                            bat "del reports\\coverage.xml"

                        }
                        failure{
                            dir("build"){
                                bat "tree /A /F"
                            }
                        }
                    }
                }
                stage("Run Doctest Tests"){
                    when {
                        equals expected: true, actual: params.TEST_RUN_DOCTEST
                    }
                    steps {
                        dir("${WORKSPACE}/reports/doctests"){
                            echo "Cleaning doctest reports directory"
                            deleteDir()
                        }
                        dir("source"){
                            bat "pipenv run sphinx-build -b doctest docs\\source ${WORKSPACE}\\build\\docs -d ${WORKSPACE}\\build\\docs\\doctrees -v"
                        }
                        bat "move ${WORKSPACE}\\build\\docs\\output.txt ${WORKSPACE}\\reports\\doctest.txt"
                    }
                    post{
                        always {
                            archiveArtifacts allowEmptyArchive: true, artifacts: "reports/doctest.txt"
                        }
                    }
                }
                stage("Run Flake8 Static Analysis") {
                    when {
                        equals expected: true, actual: params.TEST_RUN_FLAKE8
                    }
                    steps{
                        script{
                            try{
                                // tee('reports/flake8.log') {
                                dir("source"){
                                    powershell "& pipenv run flake8 uiucprescon --format=pylint | tee ${WORKSPACE}\\logs\\flake8.log"
                                }
                                // }
                            } catch (exc) {
                                echo "flake8 found some warnings"
                            }
                        }
                    }
                    post {
                        always {
                            warnings canRunOnFailed: true, parserConfigurations: [[parserName: 'PyLint', pattern: 'reports/flake8.log']], unHealthy: ''
                        }
                    }
                }
                stage("Run MyPy Static Analysis") {
                    when {
                        equals expected: true, actual: params.TEST_RUN_MYPY
                    }
                    steps{
                        dir("reports/mypy/html"){
                            deleteDir()
                            bat "dir"
                        }
                        script{
                            // tee("logs/mypy.log") {
                            try{
                                dir("source"){
                                    bat "dir"
                                    bat "pipenv run mypy ${WORKSPACE}\\build\\lib\\uiucprescon --html-report ${WORKSPACE}\\reports\\mypy\\html --cobertura-xml-report ${WORKSPACE}\\reports\\mypy > ${WORKSPACE}\\logs\\mypy.log"
                                }
                            } catch (exc) {
                                echo "MyPy found some warnings"
                            }
                            dir("${WORKSPACE}/reports/mypy"){
                                if(fileExists("mypy_cobertura.xml")){
                                    bat "del mypy_cobertura.xml"
                                }

                                bat "ren cobertura.xml mypy_cobertura.xml"
                            }
                            // }
                        }
                    }
                    post {
                        always {
                            cobertura(
                                autoUpdateHealth: false,
                                autoUpdateStability: false,
                                coberturaReportFile: 'reports/mypy/mypy_cobertura.xml',
                                // conditionalCoverageTargets: '70, 0, 0',
                                enableNewApi: false,
                                failUnhealthy: false,
                                failUnstable: false,
                                lineCoverageTargets: '80, 0, 0',
                                maxNumberOfBuilds: 0,
                                methodCoverageTargets: '80, 0, 0',
                                onlyStable: false,
                                sourceEncoding: 'ASCII',
                                zoomCoverageChart: false
                            )
                            warnings canRunOnFailed: true, parserConfigurations: [[parserName: 'MyPy', pattern: 'logs/mypy.log']], unHealthy: ''
                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: "reports/mypy/html/", reportFiles: 'index.html', reportName: 'MyPy HTML Report', reportTitles: ''])
                        }
                        cleanup{
                            script{
                                if(fileExists('reports/mypy/mypy_cobertura.xml')){
                                    bat "del reports\\mypy\\mypy_cobertura.xml"
                                }
                            }
                        }
                    }
                }
            }

        }
        stage("Packaging") {
            environment {
                PATH = "${tool 'cmake3.13'};$PATH"
            }
            steps {
                dir("source"){
                    lock("cppan_${NODE_NAME}"){
                        bat "pipenv run python setup.py build -b ..\\build  sdist -d ${WORKSPACE}\\dist bdist_wheel -d ..\\dist"
                    }
                }
            }
            post{
                success{
                    archiveArtifacts artifacts: "dist/*.whl,dist/*.tar.gz,dist/*.zip", fingerprint: true
                    stash includes: 'dist/*.*', name: "dist"
                }
                cleanup{
                    remove_files("dist/*.whl,dist/*.tar.gz,dist/*.zip")
                }
            }
        }
        stage("Upload to DevPi staging") {
            when {
                allOf{
                    equals expected: true, actual: params.DEPLOY_DEVPI
                    anyOf {
                        equals expected: "master", actual: env.BRANCH_NAME
                        equals expected: "dev", actual: env.BRANCH_NAME
                    }
                }
            }
            steps {
                unstash "dist"
                unstash "docs"
                bat "venv\\Scripts\\devpi.exe use DS_Jenkins/${env.BRANCH_NAME}_staging --clientdir ${WORKSPACE}\\certs\\"
                script {
                    bat "venv\\Scripts\\devpi.exe upload --clientdir ${WORKSPACE}\\certs\\ --from-dir dist "
                    try {
                        bat "venv\\Scripts\\devpi.exe upload --clientdir ${WORKSPACE}\\certs\\ --only-docs ${WORKSPACE}\\dist\\${env.DOC_ZIP_FILENAME}"
                    } catch (exc) {
                        echo "Unable to upload to devpi with docs."
                    }
                }
            }
        }
        stage("Test DevPi packages") {
            when {
                allOf{
                    equals expected: true, actual: params.DEPLOY_DEVPI
                    anyOf {
                        equals expected: "master", actual: env.BRANCH_NAME
                        equals expected: "dev", actual: env.BRANCH_NAME
                    }
                }
            }


            parallel {
                stage("Source Distribution: .tar.gz") {
                    agent {
                        node {
                            label "Windows && Python3 && VS2015"
//                            customWorkspace "c:/Jenkins/temp/${JOB_NAME}/devpi_testing/"
                        }
                    }
                    options {
                        skipDefaultCheckout(true)
                    }
                    environment {
                        PATH = "${tool 'cmake3.13'};$PATH"
                        CL = "/MP"
                    }
                    stages {
                        stage("Building DevPi Testing venv for tar.gz"){
                            steps{
                                bat "${tool 'CPython-3.6'}\\python.exe -m venv venv"
                                bat "venv\\Scripts\\pip.exe install tox devpi-client"
                            }
                        }
                        stage("DevPi Testing tar.gz Package "){
                            steps {
                                script {
                                    lock("cppan_${NODE_NAME}"){
                                        devpiTest(
                                            devpiExecutable: "venv\\Scripts\\devpi.exe",
                                            url: "https://devpi.library.illinois.edu",
                                            index: "${env.BRANCH_NAME}_staging",
                                            pkgName: "${env.PKG_NAME}",
                                            pkgVersion: "${env.PKG_VERSION}",
                                            pkgRegex: "tar.gz"
                                        )
                                    }
                                }
                            }
                        }
                    }

                }
//                stage("Source Distribution: .zip") {
//                     agent {
//                        node {
//                            label "Windows && Python3 && VS2015"
////                            customWorkspace "c:/Jenkins/temp/${JOB_NAME}/devpi_testing/"
//                        }
//                    }
//                    options {
//                        skipDefaultCheckout(true)
//                    }
//
//                    environment {
//                        PATH = "${tool 'cmake3.12'};$PATH"
//                        CL = "/MP"
//                    }
//                    stages{
//                        stage("Building DevPi Testing venv for Zip"){
//                            steps{
//                                echo "installing DevPi test env"
//                                bat "${tool 'CPython-3.6'} -m venv venv"
//                                bat "venv\\Scripts\\pip.exe install tox devpi-client"
//                            }
//                        }
//                        stage("DevPi Testing zip Package"){
//                            steps {
//                                script {
//                                    lock("cppan_${NODE_NAME}"){
//                                        devpiTest(
//                                            devpiExecutable: "venv\\Scripts\\devpi.exe",
//                                            url: "https://devpi.library.illinois.edu",
//                                            index: "${env.BRANCH_NAME}_staging",
//                                            pkgName: "${env.PKG_NAME}",
//                                            pkgVersion: "${env.PKG_VERSION}",
//                                            pkgRegex: "zip"
//                                        )
//                                    }
//                                }
//                            }
//                        }
//                    }
//                }
                stage("Built Distribution: .whl") {
                    agent {
                        node {
                            label "Windows && Python3"
                            customWorkspace "c:/Jenkins/temp/${JOB_NAME}/devpi_testing/"
                        }
                    }
                    options {
                        skipDefaultCheckout(true)
                    }
                    stages{
                        stage("Building DevPi Testing venv"){
                            steps{
                                bat "${tool 'CPython-3.6'}\\python.exe -m venv venv"
                                bat "venv\\Scripts\\pip.exe install tox devpi-client"
                            }
                        }
                        stage("DevPi Testing Whl"){
                            steps {
                                devpiTest(
                                    devpiExecutable: "venv\\Scripts\\devpi.exe",
                                    url: "https://devpi.library.illinois.edu",
                                    index: "${env.BRANCH_NAME}_staging",
                                    pkgName: "${env.PKG_NAME}",
                                    pkgVersion: "${env.PKG_VERSION}",
                                    pkgRegex: "whl"
                                )
                                echo "Finished testing Built Distribution: .whl"
                            }
                        }
                    }
                }
            }
            post {
                success {
                    echo "it Worked. Pushing file to ${env.BRANCH_NAME} index"
                    bat "venv\\Scripts\\devpi.exe login ${env.DEVPI_USR} --password ${env.DEVPI_PSW} && venv\\Scripts\\devpi.exe use /${env.DEVPI_USR}/${env.BRANCH_NAME}_staging && venv\\Scripts\\devpi.exe push ${env.PKG_NAME}==${env.PKG_VERSION} ${env.DEVPI_USR}/${env.BRANCH_NAME}"
                }
                failure {
                    echo "At least one package format on DevPi failed."
                }
            }
        }
        stage("Deploy"){
            parallel {
                stage("Deploy Online Documentation") {
                    when{
                        equals expected: true, actual: params.DEPLOY_DOCS
                    }
                    steps{
                        dir("build/docs/html/"){
                            script{
                                try{
                                    timeout(30) {
                                        input 'Update project documentation?'
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
                                                remoteDirectory: "${params.DEPLOY_DOCS_URL_SUBFOLDER}",
                                                remoteDirectorySDF: false,
                                                removePrefix: '',
                                                sourceFiles: '**')],
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
                    }
                }
                stage("Deploy to DevPi Production") {
                    when {
                        allOf{
                            equals expected: true, actual: params.DEPLOY_DEVPI_PRODUCTION
                            branch "master"
                        }
                    }
                    steps {
                        script {
                            try{
                                timeout(30) {
                                    input "Release ${env.PKG_NAME} ${env.PKG_VERSION} (https://devpi.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}_staging/${env.PKG_NAME}/${env.PKG_VERSION}) to DevPi Production? "
                                }

                                bat "venv\\Scripts\\devpi.exe use /DS_Jenkins/${env.BRANCH_NAME}_staging --clientdir ${WORKSPACE}\\certs\\"
                                bat "venv\\Scripts\\devpi.exe push ${env.PKG_NAME}==${env.PKG_VERSION} production/release --clientdir ${WORKSPACE}\\certs\\"
                            } catch(err){
                                echo "User response timed out. Packages not deployed to DevPi Production."
                            }
                        }
                    }
                }
            }
        }
    }
    post {
        cleanup{
            remove_from_devpi("venv\\Scripts\\devpi.exe", "${env.PKG_NAME}", "${env.PKG_VERSION}", "/${env.DEVPI_USR}/${env.BRANCH_NAME}_staging", "${env.DEVPI_USR}", "${env.DEVPI_PSW}")
            cleanWs(
                deleteDirs: true,
                disableDeferredWipeout: true,
                patterns: [
                    [pattern: 'dist', type: 'INCLUDE'],
//                    [pattern: 'build', type: 'INCLUDE'],
                    [pattern: 'reports', type: 'INCLUDE'],
                    [pattern: 'logs', type: 'INCLUDE'],
                    [pattern: 'certs', type: 'INCLUDE'],
                    [pattern: '*tmp', type: 'INCLUDE'],
                    [pattern: "source/**/*.dll", type: 'INCLUDE'],
                    [pattern: "source/**/*.pyd", type: 'INCLUDE'],
                    [pattern: "source/**/*.exe", type: 'INCLUDE'],
                    [pattern: "source/**/*.exe", type: 'INCLUDE']
                    ]
                )
        }
    }
}
