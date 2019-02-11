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
                    }
                    post{
                        success{
                            bat "(if not exist logs mkdir logs) && python.exe -m pip list > logs/pippackages_system_${NODE_NAME}.log"
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
                        bat "python.exe -m venv venv\\36"

                        script {
                            try {
                                bat "venv\\36\\Scripts\\python.exe -m pip install -U pip"
                            }
                            catch (exc) {
                                bat "python.exe -m venv venv\\36"
                                bat "call venv\\36\\Scripts\\python.exe -m pip install -U pip --no-cache-dir"
                            }
                        }

                        bat "venv\\36\\Scripts\\pip.exe install devpi-client mypy lxml sphinx pytest flake8 pytest-cov pytest-bdd --upgrade-strategy only-if-needed"
                        bat 'venv\\36\\Scripts\\pip.exe install "tox>=3.7"'
                    }
                    post{
                        success{
                            bat "venv\\36\\Scripts\\pip.exe list > logs/pippackages_venv_${NODE_NAME}.log"
                            archiveArtifacts artifacts: "logs/pippackages_system_${NODE_NAME}.log"
                        }

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
                        PATH = "${WORKSPACE}\\venv\\36\\Scripts;${tool 'cmake3.13'};$PATH"
                    }
                    steps {

                        dir("source"){

                            powershell "& python setup.py build -b ${WORKSPACE}\\build\\36 -j${env.NUMBER_OF_PROCESSORS} --build-lib ../build/36/lib build_ext --inplace | tee ${WORKSPACE}\\logs\\build.log"

                        }

                        dir("build\\36\\lib\\tests"){
                            bat "copy ${WORKSPACE}\\source\\tests\\*.py"

                        }
                        dir("build\\36\\lib\\tests\\feature"){
                                bat "copy ${WORKSPACE}\\source\\tests\\feature\\*.py"
                                bat "copy ${WORKSPACE}\\source\\tests\\feature\\*.feature"
                        }
                    }
                    post{
                        always{
                            recordIssues(tools: [
                                    pyLint(name: 'Setuptools Build: PyLint', pattern: 'logs/build.log'),
                                    msBuild(name: 'Setuptools Build: MSBuild', pattern: 'logs/build.log')
                                ]
                                )
//                            warnings canRunOnFailed: true, parserConfigurations: [[parserName: 'MSBuild', pattern: "logs\\build.log"]]
                            dir("source"){
                                bat "tree /F /A > ${WORKSPACE}\\logs\\built_package.log"
                            }
                            archiveArtifacts "logs/built_package.log"
                        }
                        cleanup{
                            cleanWs(
                                patterns: [
                                        [pattern: 'logs/build.log', type: 'INCLUDE'],
                                        [pattern: "logs/built_package.log", type: 'INCLUDE'],
//                                        [pattern: "logs/tree_postbuild_failed.log", type: 'INCLUDE'],
//                                        [pattern: "logs/tree_home_postbuild_failed.log", type: 'INCLUDE'],
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
                            recordIssues(tools: [sphinxBuild(name: 'Sphinx Documentation Build', pattern: 'logs/build_sphinx.log', id: 'sphinx_build')])
//                            warnings canRunOnFailed: true, parserConfigurations: [[parserName: 'Pep8', pattern: 'logs/build_sphinx.log']]
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
            environment{
                PATH = "${WORKSPACE}\\venv\\36\\Scripts;${tool 'CPython-3.6'}\\Scripts;${tool 'cmake3.13'};$PATH"
            }
//            options{
//                parallelsAlwaysFailFast()
//            }

//            environment{
//                PATH = ";$PATH"
//            }
            failFast true
            parallel {
                stage("Run Tox test") {
//                    agent{
//                        node {
//                            label "Windows && VS2015 && Python3 && longfilenames"
//                            customWorkspace "c:/Jenkins/temp/${JOB_NAME}/tox/"
//                        }
//                    }
                    when {
                       equals expected: true, actual: params.TEST_RUN_TOX
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
                        stage("Run Tox"){
                            environment {
                                PATH = "${WORKSPACE}\\venv\\36\\Scripts;${tool 'CPython-3.6'};${tool 'CPython-3.7'};${tool 'cmake3.13'}\\;$PATH"
                                CL = "/MP"
                            }

                            steps {
                                dir("source"){
                                    script{
                                        try{
                                            bat "tox --parallel=auto --parallel-live --workdir ${WORKSPACE}\\.tox -vv"
                                        } catch (exc) {
                                            bat "tox --parallel=auto --parallel-live --workdir ${WORKSPACE}\\.tox --recreate -vv"
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
                        dir("build\\36\\lib"){
                            bat "${WORKSPACE}\\venv\\36\\Scripts\\python.exe -m pytest --junitxml=${WORKSPACE}/reports/pytest/${env.junit_filename} --junit-prefix=${env.NODE_NAME}-pytest --cov-report html:${WORKSPACE}/reports/pytestcoverage/  --cov-report xml:${WORKSPACE}/reports/coverage.xml --cov=uiucprescon --integration --cov-config=${WORKSPACE}/source/setup.cfg"
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
//                        dir("${WORKSPACE}/reports/doctests"){
//                            echo "Cleaning doctest reports directory"
//                            deleteDir()
//                        }
                        dir("source"){
                            bat "pipenv run sphinx-build -b doctest docs\\source ${WORKSPACE}\\build\\docs -d ${WORKSPACE}\\build\\docs\\doctrees -w ${WORKSPACE}/logs/doctest_warnings.log"
                        }
//                        bat "move ${WORKSPACE}\\build\\docs\\output.txt ${WORKSPACE}\\reports\\doctest.txt"
                    }
                    post{
                        always {
                            archiveArtifacts artifacts: "reports/doctest/output.txt", allowEmptyArchive: true
                            recordIssues(tools: [sphinxBuild(name: 'Doctest', pattern: 'logs/doctest_warnings.log', id: 'doctest')])
                        }
                    }
                }
                stage("Run Flake8 Static Analysis") {
                    when {
                        equals expected: true, actual: params.TEST_RUN_FLAKE8
                    }
                    steps{
                        bat returnStatus: true, script: "venv\\36\\Scripts\\flake8 uiucprescon --tee --output-file ${WORKSPACE}\\logs\\flake8.log"
//                        script{
//                            try{
//                                // tee('reports/flake8.log') {
//                                dir("source"){
////                                    powershell "& pipenv run flake8 uiucprescon --format=pylint | tee ${WORKSPACE}\\logs\\flake8.log"
//                                }
//                                // }
//                            } catch (exc) {
//                                echo "flake8 found some warnings"
//                            }
//                        }
                    }
                    post {
                        always {
                            recordIssues(tools: [flake8(name: 'Flake8', pattern: 'logs/flake8.log')])
//                            warnings canRunOnFailed: true, parserConfigurations: [[parserName: 'PyLint', pattern: 'reports/flake8.log']], unHealthy: ''
                        }
                    }
                }
                stage("Run MyPy Static Analysis") {
                    when {
                        equals expected: true, actual: params.TEST_RUN_MYPY
                    }
                    stages{
                        stage("Generate Stubs") {
                            steps{
                                dir("source"){
                                  bat "stubgen -p uiucprescon -o ${WORKSPACE}\\mypy_stubs"
                                }
                            }

                        }
                        stage("Running MyPy"){
                            environment{
                                MYPYPATH = "${WORKSPACE}\\mypy_stubs"
                            }

                            steps{
                                bat "if not exist reports\\mypy\\html mkdir reports\\mypy\\html"
                                dir("source"){
                                    bat returnStatus: true, script: "mypy -p uiucprescon --cache-dir=nul --html-report ${WORKSPACE}\\reports\\mypy\\html > ${WORKSPACE}\\logs\\mypy.log"
                                }
                            }
                            post {
                                always {
                                    recordIssues(tools: [myPy(name: 'MyPy', pattern: 'logs\\mypy.log')])
                                    publishHTML(
                                        [
                                            allowMissing: true,
                                            alwaysLinkToLastBuild: false,
                                            keepAll: false,
                                            reportDir: 'reports/mypy/html/',
                                            reportFiles: 'index.html',
                                            reportName: 'MyPy HTML Report', reportTitles: ''
                                        ]
                                    )
                                }
                            }
                        }
                    }
                    post {
                        always {
//                            warnings canRunOnFailed: true, parserConfigurations: [[parserName: 'MyPy', pattern: 'logs/mypy.log']], unHealthy: ''
                            recordIssues(tools: [myPy(name: 'MyPy', pattern: 'logs/mypy.log')])
                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: "reports/mypy/html/", reportFiles: 'index.html', reportName: 'MyPy HTML Report', reportTitles: ''])
                        }
                    }
                }
            }

        }
        stage("Packaging") {
            environment {
                CMAKE_PATH = "${tool 'cmake3.13'}"
                PATH = "${env.CMAKE_PATH};$PATH"
                CL = "/MP"
            }
            parallel{
                stage("Python 3.6 whl"){
                    stages{
                        stage("Create venv for 3.6"){
                            environment {
                                PATH = "${tool 'CPython-3.6'};$PATH"
                            }

                            steps {
                                bat "python -m venv venv\\36 && venv\\36\\Scripts\\python.exe -m pip install pip --upgrade && venv\\36\\Scripts\\pip.exe install wheel setuptools --upgrade"
                            }
                        }
                        stage("Creating bdist wheel for 3.6"){
                            environment {
                                PATH = "${WORKSPACE}\\venv\\36\\scripts;${tool 'CPython-3.6'};$PATH"
                            }
                            steps {
                                dir("source"){
                                    bat "python setup.py build -b ../build/36/ -j${env.NUMBER_OF_PROCESSORS} --build-lib ../build/36/lib --build-temp ../build/36/temp build_ext --inplace --cmake-exec=${env.CMAKE_PATH}\\cmake.exe bdist_wheel -d ${WORKSPACE}\\dist"
                                }
                            }
                            post{
                               success{
                                    stash includes: 'dist/*.whl', name: "whl 3.6"
                                }
                            }
                        }
                    }
                }
                stage("Python sdist"){
                    environment {
                        PATH = "${tool 'CPython-3.6'};$PATH"
                    }
                    steps {
                        dir("source"){
                            bat "python setup.py sdist -d ${WORKSPACE}\\dist --format zip"
                        }
                    }
                    post{
                        success{
                            stash includes: 'dist/*.zip,dist/*.tar.gz', name: "sdist"
                        }
                    }
                }
                stage("Python 3.7 whl"){
                    agent {
                        node {
                            label "Windows && Python3 && VS2015"
                        }
                    }
                    environment {
                        CMAKE_PATH = "${tool 'cmake3.13'}"
                        PATH = "${env.CMAKE_PATH};${tool 'CPython-3.7'};$PATH"
                        CL = "/MP"
                    }
                    stages{
                        stage("create venv for 3.7"){
                            steps {
                                bat "python -m venv venv\\37"
                                bat "venv\\37\\Scripts\\python.exe -m pip install pip --upgrade && venv\\37\\Scripts\\pip.exe install wheel setuptools --upgrade"
                            }
                        }

                        stage("Creating bdist wheel for 3.7"){
                            environment {
                                PATH = "${WORKSPACE}\\venv\\37\\scripts;${tool 'CPython-3.6'};$PATH"
                            }
                            steps {
                                dir("source"){
                                    bat "python setup.py build -b ../build/37/ -j${env.NUMBER_OF_PROCESSORS} --build-lib ../build/37/lib/ --build-temp ../build/37/temp build_ext --cmake-exec=${env.CMAKE_PATH}\\cmake.exe bdist_wheel -d ${WORKSPACE}\\dist"
                                }
                            }
                            post{
                                success{
                                    stash includes: 'dist/*.whl', name: "whl 3.7"
                                }
                                cleanup{
                                    cleanWs(
                                        deleteDirs: true,
                                        disableDeferredWipeout: true,
                                        patterns: [
                                            [pattern: 'dist', type: 'INCLUDE'],
                                            [pattern: 'source', type: 'INCLUDE'],
                                            [pattern: '*tmp', type: 'INCLUDE'],
                                            [pattern: 'venv37', type: 'INCLUDE'],
                                            ]
                                        )
                                }
                            }
                        }
                    }
                }
            }
            post{
                success{
                    unstash "whl 3.7"
                    unstash "whl 3.6"
                    unstash "sdist"
                    archiveArtifacts artifacts: "dist/*.whl,dist/*.tar.gz,dist/*.zip", fingerprint: true
                }
            }
        }
//        stage("Packaging") {
//
//            environment {
//                PATH = "${tool 'CPython-3.6'};${tool 'cmake3.13'};$PATH"
//            }
//            steps {
//                dir("source"){
////                    lock("cppan_${NODE_NAME}"){
//                    bat "python -m pipenv run python setup.py build -b ..\\build  sdist -d ${WORKSPACE}\\dist bdist_wheel -d ..\\dist"
////                    }
//                }
//            }
//            post{
//                success{
//                    archiveArtifacts artifacts: "dist/*.whl,dist/*.tar.gz,dist/*.zip", fingerprint: true
//                    stash includes: 'dist/*.*', name: "dist"
//                }
//                cleanup{
//                    remove_files("dist/*.whl,dist/*.tar.gz,dist/*.zip")
//                }
//            }
//        }
//        stage("Upload to DevPi staging") {
//            when {
//                allOf{
//                    equals expected: true, actual: params.DEPLOY_DEVPI
//                    anyOf {
//                        equals expected: "master", actual: env.BRANCH_NAME
//                        equals expected: "dev", actual: env.BRANCH_NAME
//                    }
//                }
//            }
//            steps {
//                unstash "dist"
//                unstash "docs"
//                bat "venv\\36\\Scripts\\devpi.exe use DS_Jenkins/${env.BRANCH_NAME}_staging --clientdir ${WORKSPACE}\\certs\\"
//                script {
//                    bat "venv\\36\\Scripts\\devpi.exe upload --clientdir ${WORKSPACE}\\certs\\ --from-dir dist "
//                    try {
//                        bat "venv\\36\\Scripts\\devpi.exe upload --clientdir ${WORKSPACE}\\certs\\ --only-docs ${WORKSPACE}\\dist\\${env.DOC_ZIP_FILENAME}"
//                    } catch (exc) {
//                        echo "Unable to upload to devpi with docs."
//                    }
//                }
//            }
//        }
//        stage("Test DevPi packages") {
//            when {
//                allOf{
//                    equals expected: true, actual: params.DEPLOY_DEVPI
//                    anyOf {
//                        equals expected: "master", actual: env.BRANCH_NAME
//                        equals expected: "dev", actual: env.BRANCH_NAME
//                    }
//                }
//            }
//
//
//            parallel {
//                stage("Source Distribution: .tar.gz") {
//                    agent {
//                        node {
//                            label "Windows && Python3 && VS2015"
////                            customWorkspace "c:/Jenkins/temp/${JOB_NAME}/devpi_testing/"
//                        }
//                    }
//                    options {
//                        skipDefaultCheckout(true)
//                    }
//                    environment {
//                        PATH = "${tool 'cmake3.13'};$PATH"
//                        CL = "/MP"
//                    }
//                    stages {
//                        stage("Building DevPi Testing venv for tar.gz"){
//                            steps{
//                                bat "${tool 'CPython-3.6'}\\python.exe -m venv venv\\36"
//                                bat "venv\\36\\Scripts\\pip.exe install tox devpi-client"
//                            }
//                        }
//                        stage("DevPi Testing tar.gz Package "){
//                            steps {
//                                script {
//                                    lock("cppan_${NODE_NAME}"){
//                                        devpiTest(
//                                            devpiExecutable: "venv\\36\\Scripts\\devpi.exe",
//                                            url: "https://devpi.library.illinois.edu",
//                                            index: "${env.BRANCH_NAME}_staging",
//                                            pkgName: "${env.PKG_NAME}",
//                                            pkgVersion: "${env.PKG_VERSION}",
//                                            pkgRegex: "tar.gz"
//                                        )
//                                    }
//                                }
//                            }
//                        }
//                    }
//
//                }
////                stage("Source Distribution: .zip") {
////                     agent {
////                        node {
////                            label "Windows && Python3 && VS2015"
//////                            customWorkspace "c:/Jenkins/temp/${JOB_NAME}/devpi_testing/"
////                        }
////                    }
////                    options {
////                        skipDefaultCheckout(true)
////                    }
////
////                    environment {
////                        PATH = "${tool 'cmake3.12'};$PATH"
////                        CL = "/MP"
////                    }
////                    stages{
////                        stage("Building DevPi Testing venv for Zip"){
////                            steps{
////                                echo "installing DevPi test env"
////                                bat "${tool 'CPython-3.6'} -m venv venv"
////                                bat "venv\\Scripts\\pip.exe install tox devpi-client"
////                            }
////                        }
////                        stage("DevPi Testing zip Package"){
////                            steps {
////                                script {
////                                    lock("cppan_${NODE_NAME}"){
////                                        devpiTest(
////                                            devpiExecutable: "venv\\Scripts\\devpi.exe",
////                                            url: "https://devpi.library.illinois.edu",
////                                            index: "${env.BRANCH_NAME}_staging",
////                                            pkgName: "${env.PKG_NAME}",
////                                            pkgVersion: "${env.PKG_VERSION}",
////                                            pkgRegex: "zip"
////                                        )
////                                    }
////                                }
////                            }
////                        }
////                    }
////                }
//                stage("Built Distribution: .whl") {
//                    agent {
//                        node {
//                            label "Windows && Python3"
//                            customWorkspace "c:/Jenkins/temp/${JOB_NAME}/devpi_testing/"
//                        }
//                    }
//                    options {
//                        skipDefaultCheckout(true)
//                    }
//                    stages{
//                        stage("Building DevPi Testing venv"){
//                            steps{
//                                bat "${tool 'CPython-3.6'}\\python.exe -m venv venv\\36"
//                                bat "venv\\36\\Scripts\\pip.exe install tox devpi-client"
//                            }
//                        }
//                        stage("DevPi Testing Whl"){
//                            steps {
//                                devpiTest(
//                                    devpiExecutable: "venv\\Scripts\\36\\devpi.exe",
//                                    url: "https://devpi.library.illinois.edu",
//                                    index: "${env.BRANCH_NAME}_staging",
//                                    pkgName: "${env.PKG_NAME}",
//                                    pkgVersion: "${env.PKG_VERSION}",
//                                    pkgRegex: "whl"
//                                )
//                                echo "Finished testing Built Distribution: .whl"
//                            }
//                        }
//                    }
//                }
//            }
//            post {
//                success {
//                    echo "it Worked. Pushing file to ${env.BRANCH_NAME} index"
//                    bat "venv\\36\\Scripts\\devpi.exe login ${env.DEVPI_USR} --password ${env.DEVPI_PSW} && venv\\36\\Scripts\\devpi.exe use /${env.DEVPI_USR}/${env.BRANCH_NAME}_staging && venv\\36\\Scripts\\devpi.exe push ${env.PKG_NAME}==${env.PKG_VERSION} ${env.DEVPI_USR}/${env.BRANCH_NAME}"
//                }
//                failure {
//                    echo "At least one package format on DevPi failed."
//                }
//            }
//        }
        stage("Deploy to DevPi") {
            when {
                allOf{
                    anyOf{
                        equals expected: true, actual: params.DEPLOY_DEVPI
                        triggeredBy "TimerTriggerCause"
                    }
                    anyOf {
                        equals expected: "master", actual: env.BRANCH_NAME
                        equals expected: "dev", actual: env.BRANCH_NAME
                    }
                }
            }

            environment{
                PATH = "${WORKSPACE}\\venv\\venv36\\Scripts;$PATH"
            }
            stages{
                stage("Upload to DevPi Staging"){
                    steps {
                        unstash "DOCS_ARCHIVE"
                        unstash "whl 3.6"
                        unstash "whl 3.7"
                        unstash "sdist"
                        bat "pip install devpi-client"
                        bat "devpi use https://devpi.library.illinois.edu && devpi login ${env.DEVPI_USR} --password ${env.DEVPI_PSW} && devpi use /${env.DEVPI_USR}/${env.BRANCH_NAME}_staging && devpi upload --from-dir dist"
                    }
                }
                stage("Test DevPi packages") {
                    options{
                        timestamps()
                    }
                    parallel {
                        stage("Testing DevPi .zip Package with Python 3.6 and 3.7"){
                            environment {
                                PATH = "${tool 'CPython-3.7'};${tool 'CPython-3.6'};$PATH"
                            }
                            agent {
                                node {
                                    label "Windows && Python3 && VS2015"
                                }
                            }
                            options {
                                skipDefaultCheckout(true)

                            }
                            stages{
                                stage("Creating venv to test sdist"){
                                        steps {
                                            lock("system_python_${NODE_NAME}"){
                                                bat "python -m venv venv\\venv36"
                                            }
                                            bat "venv\\venv36\\Scripts\\python.exe -m pip install pip --upgrade && venv\\venv36\\Scripts\\pip.exe install setuptools --upgrade"
                                            bat 'venv\\venv36\\Scripts\\pip.exe install devpi-client "tox<3.7"'
                                        }

                                }
                                stage("Testing DevPi zip Package"){

                                    environment {
                                        PATH = "${WORKSPACE}\\venv\\venv36\\Scripts;${tool 'cmake3.13'};${tool 'CPython-3.6'};${tool 'CPython-3.7'};$PATH"
                                    }
                                    steps {
                                        echo "Testing Source zip package in devpi"

                                        timeout(20){
                                            devpiTest(
                                                devpiExecutable: "${powershell(script: '(Get-Command devpi).path', returnStdout: true).trim()}",
                                                url: "https://devpi.library.illinois.edu",
                                                index: "${env.BRANCH_NAME}_staging",
                                                pkgName: "${env.PKG_NAME}",
                                                pkgVersion: "${env.PKG_VERSION}",
                                                pkgRegex: "zip",
                                                detox: false
                                            )
                                        }
                                    }
                                }
                            }
                            post {
                                cleanup{
                                    cleanWs(
                                        deleteDirs: true,
                                        disableDeferredWipeout: true,
                                        patterns: [
                                            [pattern: '*tmp', type: 'INCLUDE'],
                                            [pattern: 'certs', type: 'INCLUDE']
                                            ]
                                    )
                                }
                                failure{
                                    deleteDir()
                                }
                            }

                        }

                        stage("Testing DevPi .whl Package with Python 3.6"){
                            agent {
                                node {
                                    label "Windows && Python3 && !Docker"
                                }
                            }

                            options {
                                skipDefaultCheckout(true)
                            }
                            stages{
                                stage("Creating venv to Test py36 .whl"){
                                    environment {
                                        PATH = "${tool 'CPython-3.6'};$PATH"
                                    }
                                    steps {
                                        lock("system_python_${NODE_NAME}"){
                                            bat "(if not exist venv\\36 mkdir venv\\36) && python -m venv venv\\36"
                                        }
                                        bat "venv\\36\\Scripts\\python.exe -m pip install pip --upgrade && venv\\36\\Scripts\\pip.exe install setuptools --upgrade && venv\\36\\Scripts\\pip.exe install \"tox<3.7\" devpi-client"
                                    }

                                }
                                stage("Testing DevPi .whl Package with Python 3.6"){
                                    options{
                                        timeout(20)
                                    }
                                    environment {
                                        PATH = "${WORKSPACE}\\venv\\36\\Scripts;$PATH"
                                    }

                                    steps {

                                        devpiTest(
                                                devpiExecutable: "${powershell(script: '(Get-Command devpi).path', returnStdout: true).trim()}",
                                                url: "https://devpi.library.illinois.edu",
                                                index: "${env.BRANCH_NAME}_staging",
                                                pkgName: "${env.PKG_NAME}",
                                                pkgVersion: "${env.PKG_VERSION}",
                                                pkgRegex: "36.*whl",
                                                detox: false,
                                                toxEnvironment: "py36"
                                            )

                                    }
                                }
                            }
                            post {
                                failure {
                                    archiveArtifacts allowEmptyArchive: true, artifacts: "**/MSBuild_*.failure.txt"
                                    deleteDir()
                                }
                                cleanup{
                                    cleanWs(
                                        deleteDirs: true,
                                        disableDeferredWipeout: true,
                                        patterns: [
                                            [pattern: '*tmp', type: 'INCLUDE'],
                                            [pattern: 'certs', type: 'INCLUDE']
                                            ]
                                    )
                                }
                            }
                        }
                        stage("Testing DevPi .whl Package with Python 3.7"){
                            agent {
                                node {
                                    label "Windows && Python3 && !Docker"
                                }
                            }

                            options {
                                skipDefaultCheckout(true)
                            }
                            stages{
                                stage("Creating venv to Test py37 .whl"){
                                    environment {
                                        PATH = "${tool 'CPython-3.7'};$PATH"
                                    }
                                    steps {
                                        lock("system_python_${NODE_NAME}"){
//                                            bat "if not exist venv\\37 mkdir venv\\37"
                                            bat "python -m venv venv\\37"
                                        }
                                        bat "venv\\37\\Scripts\\python.exe -m pip install pip --upgrade && venv\\37\\Scripts\\pip.exe install setuptools --upgrade && venv\\37\\Scripts\\pip.exe install \"tox<3.7\" devpi-client"
                                    }

                                }
                                stage("Testing DevPi .whl Package with Python 3.7"){
                                    options{
                                        timeout(20)
                                    }
                                    environment {
                                        PATH = "${WORKSPACE}\\venv\\37\\Scripts;$PATH"
                                    }

                                    steps {

                                        devpiTest(
                                                devpiExecutable: "${powershell(script: '(Get-Command devpi).path', returnStdout: true).trim()}",
                                                url: "https://devpi.library.illinois.edu",
                                                index: "${env.BRANCH_NAME}_staging",
                                                pkgName: "${env.PKG_NAME}",
                                                pkgVersion: "${env.PKG_VERSION}",
                                                pkgRegex: "37.*whl",
                                                detox: false,
                                                toxEnvironment: "py37"
                                            )

                                    }
                                }
                            }
                            post {
                                failure {
                                    archiveArtifacts allowEmptyArchive: true, artifacts: "**/MSBuild_*.failure.txt"
                                    deleteDir()
                                }
                                cleanup{
                                    cleanWs(
                                        deleteDirs: true,
                                        disableDeferredWipeout: true,
                                        patterns: [
                                            [pattern: '*tmp', type: 'INCLUDE'],
                                            [pattern: 'certs', type: 'INCLUDE']
                                            ]
                                    )
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
                                    bat "venv\\venv36\\Scripts\\devpi.exe login ${env.DEVPI_USR} --password ${env.DEVPI_PSW}"

                                    bat "venv\\venv36\\Scripts\\devpi.exe use /DS_Jenkins/${env.BRANCH_NAME}_staging"
                                    bat "venv\\venv36\\Scripts\\devpi.exe push ${env.PKG_NAME}==${env.PKG_VERSION} production/release"
                                } catch(err){
                                    echo "User response timed out. Packages not deployed to DevPi Production."
                                }
                            }
                        }
                }
            }
            post {
                success {
                    echo "it Worked. Pushing file to ${env.BRANCH_NAME} index"
                    bat "venv\\venv36\\Scripts\\devpi.exe login ${env.DEVPI_USR} --password ${env.DEVPI_PSW} && venv\\venv36\\Scripts\\devpi.exe use /${env.DEVPI_USR}/${env.BRANCH_NAME}_staging && venv\\venv36\\Scripts\\devpi.exe push ${env.PKG_NAME}==${env.PKG_VERSION} ${env.DEVPI_USR}/${env.BRANCH_NAME}"

                }
                cleanup{
                    remove_from_devpi("venv\\venv36\\Scripts\\devpi.exe", "${env.PKG_NAME}", "${env.PKG_VERSION}", "/${env.DEVPI_USR}/${env.BRANCH_NAME}_staging", "${env.DEVPI_USR}", "${env.DEVPI_PSW}")
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

                                bat "venv\\36\\Scripts\\devpi.exe use /DS_Jenkins/${env.BRANCH_NAME}_staging --clientdir ${WORKSPACE}\\certs\\"
                                bat "venv\\36\\Scripts\\devpi.exe push ${env.PKG_NAME}==${env.PKG_VERSION} production/release --clientdir ${WORKSPACE}\\certs\\"
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
//            remove_from_devpi("venv\\36\\Scripts\\devpi.exe", "${env.PKG_NAME}", "${env.PKG_VERSION}", "/${env.DEVPI_USR}/${env.BRANCH_NAME}_staging", "${env.DEVPI_USR}", "${env.DEVPI_PSW}")
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
                    [pattern: 'mypy_stubs', type: 'INCLUDE'],
                    [pattern: "source/**/*.dll", type: 'INCLUDE'],
                    [pattern: "source/**/*.pyd", type: 'INCLUDE'],
                    [pattern: "source/**/*.exe", type: 'INCLUDE'],
                    [pattern: "source/**/*.exe", type: 'INCLUDE']
                    ]
                )
        }
    }
}
