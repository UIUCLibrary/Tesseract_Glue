@Library("devpi") _

def PKG_NAME = "unknown"
def PKG_VERSION = "unknown"
def DOC_ZIP_FILENAME = "doc.zip"
def junit_filename = "junit.xml"
def REPORT_DIR = ""
def VENV_ROOT = ""
def VENV_PYTHON = ""
def VENV_PIP = ""

def remove_files(artifacts){
    script{
        def files = findFiles glob: "${artifacts}"
        files.each { file_name ->
            bat "del ${file_name}"
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
                stage("Cleanup"){
                    steps {
                        dir("logs"){
                            deleteDir()
                            bat "dir > nul"
                        }
                        dir("build"){
                            deleteDir()
                            echo "Cleaned out build directory"
                            bat "dir > nul"
                        }
                        dir("dist"){
                            deleteDir()
                            echo "Cleaned out dist directory"
                            bat "dir > nul"
                        }

                        dir("reports"){
                            deleteDir()
                            echo "Cleaned out reports directory"
                            bat "dir > nul"
                        }
                        dir("certs"){
                            deleteDir()
                            echo "Cleaned out certs directory"
                            bat "dir > nul"
                        }
                    }
                    post{
                        failure {
                            deleteDir()
                        }
                    }
                }
                stage("Installing required system level dependencies"){
                    steps{
                        lock("system_python_${NODE_NAME}"){
                            bat "${tool 'CPython-3.6'} -m pip install pip --upgrade --quiet && ${tool 'CPython-3.6'} -m pip install --upgrade pipenv --quiet"
                        }

                        bat "${tool 'CPython-3.6'} -m pip list > logs/pippackages_system_${NODE_NAME}.log"

                    }
                    post{
                        success{
                            archiveArtifacts artifacts: "logs/pippackages_system_${NODE_NAME}.log"
                        }
                        failure {
                            deleteDir()
                        }
                    }

                }
                stage("Installing Pipfile"){
                    options{
                        timeout(5)
                    }
                    steps {
                        dir("source"){
                            bat "${tool 'CPython-3.6'} -m pipenv install --dev --deploy"
                            bat "${tool 'CPython-3.6'} -m pipenv run pip list > ${WORKSPACE}/logs/pippackages_pipenv_${NODE_NAME}.log"

                        }
                    }
                    post{
                        success{
                            archiveArtifacts artifacts: "logs/pippackages_pipenv_${NODE_NAME}.log"
                        }
                    }
                }
                stage("Creating virtualenv for building"){
                    steps {
                        bat "${tool 'CPython-3.6'} -m venv venv"

                        script {
                            try {
                                bat "call venv\\Scripts\\python.exe -m pip install -U pip"
                            }
                            catch (exc) {
                                bat "${tool 'CPython-3.6'} -m venv venv"
                                bat "call venv\\Scripts\\python.exe -m pip install -U pip --no-cache-dir"
                            }
                        }

                        bat "venv\\Scripts\\pip.exe install devpi-client pytest pytest-cov pytest-bdd --upgrade-strategy only-if-needed"                    }
                    post{
                        success{
                            bat "venv\\Scripts\\pip.exe list > logs/pippackages_venv_${NODE_NAME}.log"
                            archiveArtifacts artifacts: "logs/pippackages_system_${NODE_NAME}.log"
                        }
                        failure {
                            deleteDir()
                        }
                    }
                }
                stage("Logging into DevPi"){
                    environment{
                        DEVPI_PSWD = credentials('devpi-login')
                    }
                    steps{
                        bat "venv\\Scripts\\devpi use https://devpi.library.illinois.edu --clientdir ${WORKSPACE}\\certs\\"
                        bat "venv\\Scripts\\devpi.exe login DS_Jenkins --password ${env.DEVPI_PSWD} --clientdir ${WORKSPACE}\\certs\\"
                    }
                }
                stage("Setting variables used by the rest of the build"){
                    steps{

                        script {
                            // Set up the reports directory variable
                            REPORT_DIR = "${WORKSPACE}\\reports"
                            dir("source"){
                                PKG_NAME = bat(returnStdout: true, script: "@${tool 'CPython-3.6'}  setup.py --name").trim()
                                PKG_VERSION = bat(returnStdout: true, script: "@${tool 'CPython-3.6'} setup.py --version").trim()
                            }
                        }

                        script{
                            DOC_ZIP_FILENAME = "${PKG_NAME}-${PKG_VERSION}.doc.zip"
                            junit_filename = "junit-${env.NODE_NAME}-${env.GIT_COMMIT.substring(0,7)}-pytest.xml"
                        }




                        script{
                            VENV_ROOT = "${WORKSPACE}\\venv\\"

                            VENV_PYTHON = "${WORKSPACE}\\venv\\Scripts\\python.exe"
                            bat "${VENV_PYTHON} --version"

                            VENV_PIP = "${WORKSPACE}\\venv\\Scripts\\pip.exe"
                            bat "${VENV_PIP} --version"
                        }



                        bat "tree /A /F > ${WORKSPACE}/logs/tree_postconfig.log"
                    }
                }
            }
            post{
                always{
                    echo """Name                            = ${PKG_NAME}
Version                         = ${PKG_VERSION}
Report Directory                = ${REPORT_DIR}
documentation zip file          = ${DOC_ZIP_FILENAME}
Python virtual environment path = ${VENV_ROOT}
VirtualEnv Python executable    = ${VENV_PYTHON}
VirtualEnv Pip executable       = ${VENV_PIP}
junit_filename                  = ${junit_filename}
"""

                }

            }

        }
        stage("Building") {
            stages{
                stage("Building Python Package"){
                    environment {
                        PATH = "${tool 'cmake3.12'}\\;$PATH"
                    }
                    steps {
                        bat "tree /A /F > ${WORKSPACE}/logs/tree_prebuild.log"
                        // tee("logs/build.log") {
                            dir("source"){
                                lock("cppan_${NODE_NAME}"){
                                    powershell "& ${VENV_PYTHON} setup.py build -b ${WORKSPACE}\\build -j${env.NUMBER_OF_PROCESSORS} --build-lib ../build/lib --build-temp ${WORKSPACE}\\build\\temp | tee ${WORKSPACE}\\logs\\build.log"
                                    // bat "pipenv run python setup.py build -b ${WORKSPACE}\\build -j ${NUMBER_OF_PROCESSORS} --build-lib ..\\build\\lib -t ..\\build\\temp\\"
                                }
                            }
                        // }
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
                            script{
                                if(fileExists("logs\\build.log")){
                                    bat "del logs\\build.log"
                                }
                            }
                        }
                        failure{
                            echo "${WORKSPACE}"
                            echo "locating cppan.yml files"
                            script{
                                def cppan_files = findFiles glob: '**/cppan.yml'
                                cppan_files.each { cppan_file ->
                                    echo "Found ${cppan_file}"
                                    archiveArtifacts artifacts: "${cppan_file}"
                                }
                            }
                            bat "set > ${WORKSPACE}/logs/env_vars.log"
                            bat "tree /A /F > ${WORKSPACE}/logs/tree_postbuild_failed.log"
                            bat "tree ${user.home} /A /F >  ${WORKSPACE}/logs/tree_home_postbuild_failed.log"

                        }
                    }
                }
                stage("Building Documentation"){
                    steps{
                        echo "Building docs on ${env.NODE_NAME}"
                        script{
                            // Add a line to config file so auto docs look in the build folder
                            def sphinx_config_file = "${WORKSPACE}/source/docs/source/conf.py"
                            def extra_line = "sys.path.insert(0, os.path.abspath('${WORKSPACE}/build/lib'))"
                            def readContent = readFile "${sphinx_config_file}"
                            echo "Adding \"${extra_line}\" to ${sphinx_config_file}."
                            writeFile file: "${sphinx_config_file}", text: readContent+"\r\n${extra_line}\r\n"
                        }
                        
                        dir("build/lib"){
                            powershell "& pipenv run sphinx-build.exe -b html ${WORKSPACE}\\source\\docs\\source ${WORKSPACE}\\build\\docs\\html -d ${WORKSPACE}\\build\\docs\\doctrees | tee ${WORKSPACE}\\logs\\build_sphinx.log"
                        }
                    }
                    post{
                        always {
                            warnings canRunOnFailed: true, parserConfigurations: [[parserName: 'Pep8', pattern: 'logs/build_sphinx.log']]
                            archiveArtifacts artifacts: 'logs/build_sphinx.log', allowEmptyArchive: true

                        }
                        success{
                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'build/docs/html', reportFiles: 'index.html', reportName: 'Documentation', reportTitles: ''])
                            script{
                                // // Multibranch jobs add the slash and add the branch to the job name. I need only the job name
                                // def alljob = env.JOB_NAME.tokenize("/") as String[]
                                // def project_name = alljob[0]
                                // dir("${WORKSPACE}/dist"){
                                //     zip archive: true, dir: "${WORKSPACE}/build/docs/html", glob: '', zipFile: "${DOC_ZIP_FILENAME}"
                                // }
                                script{
                                    zip archive: true, dir: "${WORKSPACE}/build/docs/html", glob: '', zipFile: "dist/${DOC_ZIP_FILENAME}"
                                    stash includes: 'build/docs/html/**', name: 'docs'
                                }
                            }
                        }
                        failure{
                            echo "Failed to build Python package"
                        }
                        cleanup{
                            script{
                                if(fileExists("logs/build_sphinx.log")){
                                    bat "del logs\\build_sphinx.log"
                                }
                            }

                        }
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
                        PATH = "${tool 'cmake3.12'}\\;$PATH"
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
                                    bat "${tool 'CPython-3.6'} -m pipenv install --dev --deploy"
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
                //                                    bat "pipenv run tox -vv --workdir ${WORKSPACE}\\.tox\\PyTest -- --junitxml=${REPORT_DIR}\\${junit_filename} --junit-prefix=${env.NODE_NAME}-pytest --cov-report html:${REPORT_DIR}/coverage/ --cov=ocr"
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
                            bat "${WORKSPACE}\\venv\\Scripts\\python.exe -m pytest --junitxml=${WORKSPACE}/reports/pytest/${junit_filename} --junit-prefix=${env.NODE_NAME}-pytest --cov-report html:${WORKSPACE}/reports/pytestcoverage/  --cov-report xml:${WORKSPACE}/reports/coverage.xml --cov=uiucprescon --integration --cov-config=${WORKSPACE}/source/setup.cfg"
                        }
                    }
                    post {
                        always {
                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: "reports/pytestcoverage", reportFiles: 'index.html', reportName: 'Coverage.py', reportTitles: ''])
                            junit "reports/pytest/${junit_filename}"
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
                        dir("${REPORT_DIR}/doctests"){
                            echo "Cleaning doctest reports directory"
                            deleteDir()
                        }
                        dir("source"){
                            dir("${REPORT_DIR}/doctests"){
                                echo "Cleaning doctest reports directory"
                                deleteDir()
                            }
                            bat "pipenv run sphinx-build -b doctest docs\\source ${WORKSPACE}\\build\\docs -d ${WORKSPACE}\\build\\docs\\doctrees -v"
                        }
                        bat "move ${WORKSPACE}\\build\\docs\\output.txt ${REPORT_DIR}\\doctest.txt"
                    }
                    post{
                        always {
                            dir("${REPORT_DIR}"){
                                archiveArtifacts artifacts: "doctest.txt"
                            }
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
                        dir("${REPORT_DIR}/mypy/html"){
                            deleteDir()
                            bat "dir"
                        }
                        script{
                            // tee("logs/mypy.log") {
                            try{
                                dir("source"){
                                    bat "dir"
                                    bat "pipenv run mypy ${WORKSPACE}\\build\\lib\\uiucprescon --html-report ${REPORT_DIR}\\mypy\\html --cobertura-xml-report ${WORKSPACE}\\reports\\mypy > ${WORKSPACE}\\logs\\mypy.log"
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
                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: "${REPORT_DIR}/mypy/html/", reportFiles: 'index.html', reportName: 'MyPy HTML Report', reportTitles: ''])
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
                PATH = "${tool 'cmake3.12'}\\;$PATH"
            }
            steps {
                dir("source"){
                    lock("cppan_${NODE_NAME}"){
                        bat "pipenv run python setup.py build -b ..\\build -t ..\\build\\temp sdist -d ${WORKSPACE}\\dist bdist_wheel -d ..\\dist"
                    }
                }

                // dir("dist") {
                //     archiveArtifacts artifacts: "*.whl", fingerprint: true
                //     archiveArtifacts artifacts: "*.zip", fingerprint: true
                //     archiveArtifacts artifacts: "*.tar.gz", fingerprint: true
                // }
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
                        bat "venv\\Scripts\\devpi.exe upload --clientdir ${WORKSPACE}\\certs\\ --only-docs ${WORKSPACE}\\dist\\${DOC_ZIP_FILENAME}"
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
                        PATH = "${tool 'cmake3.12'};$PATH"
                        CL = "/MP"
                    }
                    stages {
                        stage("Building DevPi Testing venv for tar.gz"){
                            steps{
                                bat "${tool 'CPython-3.6'} -m venv venv"
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
                                            pkgName: "${PKG_NAME}",
                                            pkgVersion: "${PKG_VERSION}",
                                            pkgRegex: "tar.gz"
                                        )
                                        // def devpi_test_return_code = bat returnStatus: true, script: "venv\\Scripts\\devpi.exe test --index https://devpi.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}_staging ${PKG_NAME} -s tar.gz  --verbose --clientdir ${WORKSPACE}\\certs\\ --debug"
                                        // if(devpi_test_return_code != 0){
                                        //     error "DevPi exit code for tar.gz was ${devpi_test_return_code}"
                                        // }
                                    }
                                }
                            }
                        }
                    }

                }
                stage("Source Distribution: .zip") {
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
                        PATH = "${tool 'cmake3.12'};$PATH"
                        CL = "/MP"
                    }
                    stages{
                        stage("Building DevPi Testing venv for Zip"){
                            steps{
                                echo "installing DevPi test env"
                                bat "${tool 'CPython-3.6'} -m venv venv"
                                bat "venv\\Scripts\\pip.exe install tox devpi-client"
                            }
                        }
                        stage("DevPi Testing zip Package"){
                            steps {
                                script {
                                    lock("cppan_${NODE_NAME}"){
                                        devpiTest(
                                            devpiExecutable: "venv\\Scripts\\devpi.exe",
                                            url: "https://devpi.library.illinois.edu",
                                            index: "${env.BRANCH_NAME}_staging",
                                            pkgName: "${PKG_NAME}",
                                            pkgVersion: "${PKG_VERSION}",
                                            pkgRegex: "zip"
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
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
                                bat "${tool 'CPython-3.6'} -m venv venv"
                                bat "venv\\Scripts\\pip.exe install tox devpi-client"
                            }
                        }
                        stage("DevPi Testing Whl"){
                            steps {
                                devpiTest(
                                    devpiExecutable: "venv\\Scripts\\devpi.exe",
                                    url: "https://devpi.library.illinois.edu",
                                    index: "${env.BRANCH_NAME}_staging",
                                    pkgName: "${PKG_NAME}",
                                    pkgVersion: "${PKG_VERSION}",
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
                    bat "venv\\Scripts\\devpi.exe use http://devpy.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}_staging --clientdir ${WORKSPACE}\\certs\\"
//                        withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {
//                        }
                    withCredentials([usernamePassword(credentialsId: 'DS_devpi', usernameVariable: 'DEVPI_USERNAME', passwordVariable: 'DEVPI_PASSWORD')]) {
//                        bat "venv\\Scripts\\devpi.exe login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD}"
                        bat "venv\\Scripts\\devpi.exe login ${DEVPI_USERNAME} --password ${DEVPI_PASSWORD} --clientdir ${WORKSPACE}\\certs\\"
                        bat "venv\\Scripts\\devpi.exe use /${DEVPI_USERNAME}/${env.BRANCH_NAME}_staging --clientdir ${WORKSPACE}\\certs\\"
                    }
                    bat "venv\\Scripts\\devpi.exe push ${PKG_NAME}==${PKG_VERSION} DS_Jenkins/${env.BRANCH_NAME} --clientdir ${WORKSPACE}\\certs\\"
//                    script {

//                    }
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
                                    input "Release ${PKG_NAME} ${PKG_VERSION} (https://devpi.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}_staging/${PKG_NAME}/${PKG_VERSION}) to DevPi Production? "
                                }

                                bat "venv\\Scripts\\devpi.exe use /DS_Jenkins/${env.BRANCH_NAME}_staging --clientdir ${WORKSPACE}\\certs\\"
                                bat "venv\\Scripts\\devpi.exe push ${PKG_NAME}==${PKG_VERSION} production/release --clientdir ${WORKSPACE}\\certs\\"
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


            script {
                if(fileExists('source/setup.py')){
                    dir("source"){
                        try{
                            retry(3) {
                                bat "${WORKSPACE}\\venv\\Scripts\\python.exe setup.py clean --all"
                            }
                        } catch (Exception ex) {
                            echo "Unable to successfully run clean. Purging source directory."
                            deleteDir()
                        }
                    }
                }

                if (env.BRANCH_NAME == "master" || env.BRANCH_NAME == "dev"){
                    bat "venv\\Scripts\\devpi.exe use https://devpi.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}_staging --clientdir ${WORKSPACE}\\certs\\"
                    def devpi_remove_return_code = bat returnStatus: true, script:"venv\\Scripts\\devpi.exe remove -y ${PKG_NAME}==${PKG_VERSION} --clientdir ${WORKSPACE}\\certs\\ "
                    echo "Devpi remove exited with code ${devpi_remove_return_code}."
                }
            }
            dir("certs"){
                deleteDir()
            }
            dir("build"){
                deleteDir()
            }
            dir("dist"){
                deleteDir()
            }
            dir("logs"){
                deleteDir()
            }
            bat "tree /A /F"
        }
    }
}
