@Library(["devpi", "PythonHelpers"]) _


def remove_files(artifacts){
    script{
        def files = findFiles glob: "${artifacts}"
        files.each { file_name ->
            bat "del ${file_name}"
        }
    }
}


def remove_from_devpi(pkgName, pkgVersion, devpiIndex, devpiUsername, devpiPassword){
        script {
            docker.build("devpi", "-f ci/docker/deploy/devpi/Dockerfile .").inside{
                try {
                    sh "devpi login ${devpiUsername} --password ${devpiPassword} --clientdir ${WORKSPACE}/devpi"
                    sh "devpi use ${devpiIndex} --clientdir ${WORKSPACE}/devpi"
                    sh "devpi remove -y ${pkgName}==${pkgVersion} --clientdir ${WORKSPACE}/devpi"
                } catch (Exception ex) {
                    echo "Failed to remove ${pkgName}==${pkgVersion} from ${devpiIndex}"
                }

            }
        }

    }
def create_venv(python_exe, venv_path){
    script {
        bat "${python_exe} -m venv ${venv_path}"
        try {
            bat "${venv_path}\\Scripts\\python.exe -m pip install -U pip"
        }
        catch (exc) {
            bat "${python_exe} -m venv ${venv_path} && call ${venv_path}\\Scripts\\python.exe -m pip install -U pip --no-cache-dir"
        }
    }
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



def get_package_version(stashName, metadataFile){
    ws {
        unstash "${stashName}"
        script{
            def props = readProperties interpolate: true, file: "${metadataFile}"
            deleteDir()
            return props.Version
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

def CONFIGURATIONS = [
        "3.6" : [
            agents: [
                build: [
                    dockerfile: [
                        filename: 'ci/docker/windows/build/msvc/Dockerfile',
                        label: 'Windows&&Docker',
                        additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.6.8/python-3.6.8-amd64.exe --build-arg CHOCOLATEY_SOURCE'

                    ]
                ],
                test:[
                    dockerfile: [
                        filename: 'ci/docker/windows/test/msvc/Dockerfile',
                        label: 'Windows&&Docker',
                        additionalBuildArgs: '--build-arg PYTHON_DOCKER_IMAGE_BASE=python:3.6-windowsservercore --build-arg CHOCOLATEY_SOURCE'
                    ]
                ]
            ],
            pkgRegex: "*cp36*.whl"
        ],
        "3.7" : [
            agents: [
                build: [
                    dockerfile: [
                        filename: 'ci/docker/windows/build/msvc/Dockerfile',
                        label: 'Windows&&Docker',
                        additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.7.5/python-3.7.5-amd64.exe --build-arg CHOCOLATEY_SOURCE'
                    ]
                ],
                test: [
                    dockerfile: [
                        filename: 'ci/docker/windows/test/msvc/Dockerfile',
                        additionalBuildArgs: '--build-arg PYTHON_DOCKER_IMAGE_BASE=python:3.7',
                        label: 'windows && docker',
                    ]
                ]

            ],
            pkgRegex: "*cp37*.whl"
        ],
    ]

pipeline {
    agent none
    triggers {
       parameterizedCron '@weekly % DEPLOY_DEVPI=true; TEST_RUN_TOX=true'
    }
    options {
        disableConcurrentBuilds()  //each branch has 1 job running at a time
//        timeout(90)  // Timeout after 90 minutes. This shouldn't take this long but it hangs for some reason
        buildDiscarder logRotator(artifactDaysToKeepStr: '30', artifactNumToKeepStr: '30', daysToKeepStr: '100', numToKeepStr: '100')
    }
    environment {
        build_number = VersionNumber(projectStartDate: '2018-7-30', versionNumberString: '${BUILD_DATE_FORMATTED, "yy"}${BUILD_MONTH, XX}${BUILDS_THIS_MONTH, XX}', versionPrefix: '', worstResultForIncrement: 'SUCCESS')
    }
    parameters {
        booleanParam(name: "TEST_RUN_TOX", defaultValue: false, description: "Run Tox Tests")
        booleanParam(name: "DEPLOY_DEVPI", defaultValue: false, description: "Deploy to devpi on http://devpy.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}")
        booleanParam(name: "DEPLOY_DEVPI_PRODUCTION", defaultValue: false, description: "Deploy to https://devpi.library.illinois.edu/production/release")
        string(name: 'DEPLOY_DOCS_URL_SUBFOLDER', defaultValue: "ocr", description: 'The directory that the docs should be saved under')
        booleanParam(name: "DEPLOY_DOCS", defaultValue: false, description: "Update online documentation")
    }
    stages {
        stage("Configure") {
            agent {
                dockerfile {
                    filename 'ci/docker/windows/build/msvc/Dockerfile'
                    label 'Windows&&Docker'
                    additionalBuildArgs "--build-arg CHOCOLATEY_SOURCE"
                  }
            }
            stages{
                stage("Getting Distribution Info"){
                    options{
                        timeout(2)
                    }
                    steps{
                        bat "python setup.py dist_info"
                    }
                    post{
                        success{
                            stash includes: "uiucprescon_ocr.dist-info/**", name: 'DIST-INFO'
                            archiveArtifacts artifacts: "uiucprescon_ocr.dist-info/**"
                        }
                        cleanup{
                             cleanWs(
                                notFailBuild: true
                                )
                        }
                    }
                }
           }

        }
        stage("Building") {
            agent {
                dockerfile {
                    filename 'ci/docker/windows/build/msvc/Dockerfile'
                    label 'Windows&&Docker'
                    additionalBuildArgs "--build-arg CHOCOLATEY_SOURCE"
                  }
            }
            stages{
                stage("Building Python Package"){
                    options{
                        timeout(20)
                    }
                    steps {
                        bat "python setup.py build -b ${WORKSPACE}\\build\\37 -j${env.NUMBER_OF_PROCESSORS} --build-lib .\\build\\37\\lib build_ext --inplace"
                    }
                    post{
                        success{
                            stash includes: 'build/37/lib/**,uiucprescon/**/*.dll,uiucprescon/**/*.pyd', name: 'BUILD_FILES'
                        }
                        cleanup{
                            cleanWs(
                                patterns: [
                                        [pattern: 'logs/build.log', type: 'INCLUDE'],
                                        [pattern: "logs/built_package.log", type: 'INCLUDE'],
                                        [pattern: "logs/env_vars.log", type: 'INCLUDE'],
                                    ],
                                notFailBuild: true
                                )


                        }
                    }
                }
                stage("Building Documentation"){
                    environment {
//                        PATH = "${tool 'CPython-3.6'};${tool 'CPython-3.7'};$PATH"
                        PKG_NAME = get_package_name("DIST-INFO", "uiucprescon_ocr.dist-info/METADATA")
                        PKG_VERSION = get_package_version("DIST-INFO", "uiucprescon_ocr.dist-info/METADATA")
                    }
                    options{
                        timeout(3)
                    }
                    steps{
                        bat "if not exist logs mkdir logs && python -m sphinx docs/source ${WORKSPACE}\\build\\docs\\html -d ${WORKSPACE}\\build\\docs\\.doctrees -w ${WORKSPACE}\\logs\\build_sphinx.log"
                    }
                    post{
                        always {
                            recordIssues(tools: [sphinxBuild(name: 'Sphinx Documentation Build', pattern: 'logs/build_sphinx.log', id: 'sphinx_build')])
                            archiveArtifacts artifacts: 'logs/build_sphinx.log', allowEmptyArchive: true

                        }
                        success{
                            publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'build/docs/html', reportFiles: 'index.html', reportName: 'Documentation', reportTitles: ''])
                            script{
                                def DOC_ZIP_FILENAME = "${env.PKG_NAME}-${env.PKG_VERSION}.doc.zip"
                                zip archive: true, dir: "${WORKSPACE}/build/docs/html", glob: '', zipFile: "dist/${DOC_ZIP_FILENAME}"
                            }
                            stash includes: 'build/docs/html/**', name: 'DOCS_ARCHIVE'
                        }
                    }
                }
            }
            post{
                cleanup{
                    cleanWs(
                        patterns: [
                                [pattern: 'build', type: 'INCLUDE'],
                            ],
                        notFailBuild: true,
                        deleteDirs: true
                        )


                }
            }
        }

        stage("Testing") {
            agent {
                dockerfile {
                    filename 'ci/docker/windows/build/msvc/Dockerfile'
                    label 'Windows&&Docker'
                    additionalBuildArgs "--build-arg CHOCOLATEY_SOURCE"
                  }
            }
            failFast true
            stages{
                stage("Setting up Tests"){
                    options{
                        timeout(3)
                    }
                    steps{
                        unstash "BUILD_FILES"
                        unstash "DOCS_ARCHIVE"

                        bat "if not exist logs mkdir logs"
                        bat "if not exist reports mkdir reports"
                    }
                }
                stage("Running Tests"){
                    parallel {
                        stage("Run Tox test") {
                            when {
                               equals expected: true, actual: params.TEST_RUN_TOX
                            }
                            stages{
                                stage("Run Tox"){
                                    options{
                                        timeout(60)
                                    }

                                    steps {
                                        script{
                                            try{
                                                bat  (
                                                    label: "Run Tox",
                                                    script: "tox -e py -vv "
                                                )

                                            } catch (exc) {
                                                bat (
                                                    label: "Run Tox with new environments",
                                                    script: "tox -e py --recreate -vv "
                                                )
                                            }
                                        }
                                    }
                                    post{
                                        cleanup{
                                            cleanWs(
                                                deleteDirs: true,
                                                patterns: [
                                                    [pattern: '.tox', type: 'INCLUDE'],
                                                ]
                                            )
                                        }
                                    }
                                }

                            }
                            post{
                                always{
                                    archiveArtifacts allowEmptyArchive: true, artifacts: '.tox/py*/log/*.log,.tox/log/*.log,logs/tox_report.json'
                                }
                                cleanup{
                                    cleanWs deleteDirs: true, patterns: [
                                        [pattern: '.tox/py*/log/*.log', type: 'INCLUDE'],
                                        [pattern: '.tox/log/*.log', type: 'INCLUDE'],
                                        [pattern: 'logs/rox_report.json', type: 'INCLUDE']
                                    ]
                                }

                            }
                        }
                        stage("Run Pytest Unit Tests"){
                            environment{
                                junit_filename = "junit-${env.NODE_NAME}-${env.GIT_COMMIT.substring(0,7)}-pytest.xml"
                            }
                            options{
                                timeout(10)
                            }
                            steps{
                                bat "python.exe -m pytest --junitxml=${WORKSPACE}/reports/pytest/${env.junit_filename} --junit-prefix=${env.NODE_NAME}-pytest --cov-report html:${WORKSPACE}/reports/pytestcoverage/  --cov-report xml:${WORKSPACE}/reports/coverage.xml --cov=uiucprescon --integration --cov-config=${WORKSPACE}/setup.cfg"
                            }
                            post {
                                always {
                                    publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: "reports/pytestcoverage", reportFiles: 'index.html', reportName: 'Coverage.py', reportTitles: ''])
                                    junit "reports/pytest/${env.junit_filename}"
                                    publishCoverage(
                                        adapters: [
                                            coberturaAdapter('reports/coverage.xml')
                                        ],
                                        sourceFileResolver: sourceFiles('STORE_ALL_BUILD')
                                    )

                                }
                            }
                        }
                        stage("Run Doctest Tests"){
                            options{
                                timeout(3)
                            }
                            steps {
                                bat "python -m sphinx -b doctest docs\\source ${WORKSPACE}\\build\\docs -d ${WORKSPACE}\\build\\docs\\doctrees -w ${WORKSPACE}/logs/doctest_warnings.log"
                            }
                            post{
                                always {

                                    recordIssues(tools: [sphinxBuild(name: 'Doctest', pattern: 'logs/doctest_warnings.log', id: 'doctest')])
                                }
                            }
                        }
                        stage("Run Flake8 Static Analysis") {
                            options{
                                timeout(2)
                            }
                            steps{
                                bat returnStatus: true, script: "flake8 uiucprescon --tee --output-file ${WORKSPACE}\\logs\\flake8.log"
                            }
                            post {
                                always {
                                    recordIssues(tools: [flake8(name: 'Flake8', pattern: 'logs/flake8.log')])
                                }
                            }
                        }
                        stage("Run MyPy Static Analysis") {
                            stages{
                                stage("Generate Stubs") {
                                    options{
                                        timeout(2)
                                    }
                                    steps{
                                        bat "stubgen uiucprescon -o mypy_stubs"
                                    }

                                }
                                stage("Running MyPy"){
                                    environment{
                                        MYPYPATH = "${WORKSPACE}\\mypy_stubs"
                                    }
                                    options{
                                        timeout(3)
                                    }
                                    steps{
                                        bat "if not exist reports\\mypy\\html mkdir reports\\mypy\\html"
                                        bat returnStatus: true, script: "mypy -p uiucprescon --cache-dir=nul --html-report ${WORKSPACE}\\reports\\mypy\\html > ${WORKSPACE}\\logs\\mypy.log"
                                    }
                                }
                            }
                            post {
                                always {
                                    recordIssues(tools: [myPy(name: 'MyPy', pattern: 'logs/mypy.log')])
                                    publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: "reports/mypy/html/", reportFiles: 'index.html', reportName: 'MyPy HTML Report', reportTitles: ''])
                                }
                                cleanup{
                                    cleanWs(
                                        deleteDirs: true, patterns: [
                                            [pattern: '.eggs', type: 'INCLUDE'],
                                            [pattern: '*egg-info', type: 'INCLUDE'],
                                            [pattern: 'mypy_stubs', type: 'INCLUDE'],
                                            [pattern: 'reports', type: 'INCLUDE'],
                                            [pattern: 'build', type: 'INCLUDE']
                                        ]
                                    )
                                }
                            }
                        }
                    }
                }
            }

        }
        stage("Python sdist"){
            agent {
                dockerfile {
                    filename 'ci/docker/windows/build/msvc/Dockerfile'
                    label 'Windows&&Docker'
                    additionalBuildArgs "--build-arg CHOCOLATEY_SOURCE"
                  }
            }
            steps {
                bat "python setup.py sdist -d ${WORKSPACE}\\dist --format zip"
            }
            post{
                success{
                    stash includes: 'dist/*.zip,dist/*.tar.gz', name: "sdist"
                }
            }
        }
        stage("Packaging Binary Wheels") {
            matrix{
                agent any
                axes {
                    axis {
                        name 'PYTHON_VERSION'
                        values(
                            '3.6',
                            '3.7'
                            )
                    }
                }
                stages {
                    stage("Building whl Package"){
                        agent {
                            dockerfile {
                                filename "${CONFIGURATIONS[PYTHON_VERSION].agents.build.dockerfile.filename}"
                                label "${CONFIGURATIONS[PYTHON_VERSION].agents.build.dockerfile.label}"
                                additionalBuildArgs "${CONFIGURATIONS[PYTHON_VERSION].agents.build.dockerfile.additionalBuildArgs}"
                             }
                        }
                        steps{
                            echo "Building Wheel for Python ${PYTHON_VERSION}"
                            bat "python --version"
                            bat "python setup.py build -b build -j${env.NUMBER_OF_PROCESSORS} build_ext --inplace bdist_wheel -d ${WORKSPACE}\\dist"
                        }
                        post {
                            success{
                                stash includes: "dist/${CONFIGURATIONS[PYTHON_VERSION].pkgRegex}", name: "whl ${PYTHON_VERSION}"

                            }
                            cleanup{
                                cleanWs(
                                        deleteDirs: true,
                                        patterns: [
                                            [pattern: 'dist', type: 'INCLUDE']
                                        ]
                                    )
                            }
                        }
                    }
                    stage("Testing wheel on a Different computer"){
                        agent{
                            dockerfile {
                                filename "${CONFIGURATIONS[PYTHON_VERSION].agents.test.dockerfile.filename}"
                                label "${CONFIGURATIONS[PYTHON_VERSION].agents.test.dockerfile.label}"
                                additionalBuildArgs "${CONFIGURATIONS[PYTHON_VERSION].agents.test.dockerfile.additionalBuildArgs}"
                            }
                        }
                        steps{
                            unstash "whl ${PYTHON_VERSION}"

                            bat(
                                label: "Installing Python virtual environment",
                                script:"python -m venv venv"
                            )

                            bat(
                                label: "Upgrading pip to latest version",
                                script: "venv\\Scripts\\python.exe -m pip install pip --upgrade"
                            )

                            bat(
                                label: "Installing tox to Python virtual environment",
                                script: "venv\\Scripts\\pip.exe install tox --upgrade"
                            )

                            script{
                                def python_wheel = findFiles glob: "**/${CONFIGURATIONS[PYTHON_VERSION].pkgRegex}"

                                python_wheel.each{
                                    try{
                                        bat(label: "Testing ${it}",
                                            script: "venv\\Scripts\\tox.exe --installpkg=${WORKSPACE}\\${it} -e py"
                                            )
                                    } catch (Exception ex) {
                                        bat "pip install wheel"
                                        bat "wheel unpack ${it} -d dist"
                                        bat "cd dist && tree /f /a"
                                    }
                                }
                            }
                        }
                        post{
                            success{
                                archiveArtifacts allowEmptyArchive: true, artifacts: "dist/${CONFIGURATIONS[PYTHON_VERSION].pkgRegex}"
                            }
                            cleanup{
                                cleanWs(
                                    notFailBuild: true
                                )
                            }
                        }
                    }
                }
            }
        }
        stage("Deploy to DevPi") {
            agent{
                label "linux && docker"
            }
            when {
                allOf{
                    equals expected: true, actual: params.DEPLOY_DEVPI
                    anyOf {
                        equals expected: "master", actual: env.BRANCH_NAME
                        equals expected: "dev", actual: env.BRANCH_NAME
                    }
                }
            }
            environment{
                PKG_NAME = get_package_name("DIST-INFO", "uiucprescon_ocr.dist-info/METADATA")
                PKG_VERSION = get_package_version("DIST-INFO", "uiucprescon_ocr.dist-info/METADATA")
                DEVPI = credentials("DS_devpi")
            }
            stages{
                stage("Upload to DevPi Staging"){
                    agent {
                        dockerfile {
                            filename 'ci/docker/deploy/devpi/Dockerfile'
                            label 'linux&&docker'
                            additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                          }
                    }
                    steps {
                            unstash "DOCS_ARCHIVE"
                            unstash "whl 3.6"
                            unstash "whl 3.7"
                            unstash "sdist"
                            sh(
                                label: "Connecting to DevPi Server",
                                script: 'devpi use https://devpi.library.illinois.edu --clientdir ${WORKSPACE}/devpi && devpi login $DEVPI_USR --password $DEVPI_PSW --clientdir ${WORKSPACE}/devpi'
                            )
                            sh(
                                label: "Uploading to DevPi Staging",
                                script: """devpi use /${env.DEVPI_USR}/${env.BRANCH_NAME}_staging --clientdir ${WORKSPACE}/devpi
    devpi upload --from-dir dist --clientdir ${WORKSPACE}/devpi"""
                            )
                    }
                    post{
                        cleanup{
                            cleanWs(
                                notFailBuild: true
                            )
                        }
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
                                                bat "python -m venv venv\\venv36 && venv\\venv36\\Scripts\\python.exe -m pip install pip --upgrade && venv\\venv36\\Scripts\\pip.exe install setuptools --upgrade && venv\\venv36\\Scripts\\pip.exe install devpi-client \"tox<3.7\""
                                            }
                                        }
                                }
                                stage("Testing DevPi zip Package"){
                                    environment {
                                        CMAKE_PATH = "${tool 'cmake3.15'}"
                                        NASM_PATH = "${tool name: 'nasm_2_x64', type: 'com.cloudbees.jenkins.plugins.customtools.CustomTool'}"
                                        PYTHON_SCRIPTS_PATH = "${WORKSPACE}\\venv\\venv36\\Scripts"
                                        PATH = "${env.CMAKE_PATH};${env.NASM_PATH};${env.PYTHON_SCRIPTS_PATH};${tool 'CPython-3.6'};${tool 'CPython-3.7'};$PATH"
                                    }
                                    steps {
                                        timeout(40){
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
                                    label "Windows && Python3"
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
                                        create_venv("python.exe", "venv\\36")
                                        bat "venv\\36\\Scripts\\pip.exe install setuptools --upgrade && venv\\36\\Scripts\\pip.exe install \"tox<3.7\" devpi-client"
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
                                    label "Windows && Python3"
                                }
                            }
//
                            options {
                                skipDefaultCheckout(true)
                            }
                            stages{
                                stage("Creating venv to Test py37 .whl"){
                                    environment {
                                        PATH = "${tool 'CPython-3.7'};$PATH"
                                    }
                                    steps {
                                       create_venv("python.exe", "venv\\37")
                                       bat "venv\\37\\Scripts\\pip.exe install setuptools --upgrade && venv\\37\\Scripts\\pip.exe install \"tox<3.7\" devpi-client"
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
                        beforeAgent true
                    }
                    agent {
                        dockerfile {
                            filename 'ci/docker/deploy/devpi/Dockerfile'
                            label 'linux&&docker'
                            additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                          }
                    }
                    steps {
                        script {
                            try{
                                timeout(30) {
                                    input "Release ${env.PKG_NAME} ${env.PKG_VERSION} (https://devpi.library.illinois.edu/DS_Jenkins/${env.BRANCH_NAME}_staging/${env.PKG_NAME}/${env.PKG_VERSION}) to DevPi Production? "
                                }
//                                    bat "venv\\36\\Scripts\\devpi.exe login ${env.DEVPI_USR} --password ${env.DEVPI_PSW} && venv\\36\\Scripts\\devpi.exe use /DS_Jenkins/${env.BRANCH_NAME}_staging && venv\\36\\Scripts\\devpi.exe push --index ${env.DEVPI_USR}/${env.BRANCH_NAME}_staging ${env.PKG_NAME}==${env.PKG_VERSION} production/release"
                                sh "devpi login ${env.DEVPI_USR} --password ${env.DEVPI_PSW} --clientdir ${WORKSPACE}/devpi && devpi use /DS_Jenkins/${env.BRANCH_NAME}_staging --clientdir ${WORKSPACE}/devpi && devpi push --index ${env.DEVPI_USR}/${env.BRANCH_NAME}_staging ${env.PKG_NAME}==${env.PKG_VERSION} production/release --clientdir ${WORKSPACE}/devpi"
                            } catch(err){
                                echo "User response timed out. Packages not deployed to DevPi Production."
                            }
                        }
                    }
                }
            }
            post {
                success {
                    script {
                        def devpi_docker = docker.build("devpi", "-f ci/docker/deploy/devpi/Dockerfile .")
                        devpi_docker.inside{
                            sh(
                                script: "devpi use https://devpi.library.illinois.edu --clientdir ${WORKSPACE}/devpi  && devpi login ${env.DEVPI_USR} --password ${env.DEVPI_PSW} --clientdir ${WORKSPACE}/devpi && devpi use /${env.DEVPI_USR}/${env.BRANCH_NAME}_staging --clientdir ${WORKSPACE}/devpi",
                                label: "Pushing file to ${env.BRANCH_NAME} index"
                            )
                            sh "devpi push --index ${env.DEVPI_USR}/${env.BRANCH_NAME}_staging ${env.PKG_NAME}==${env.PKG_VERSION} ${env.DEVPI_USR}/${env.BRANCH_NAME} --clientdir ${WORKSPACE}/devpi"
                        }
                    }
                }
                cleanup{
                    remove_from_devpi("${env.PKG_NAME}", "${env.PKG_VERSION}", "/${env.DEVPI_USR}/${env.BRANCH_NAME}_staging", "${env.DEVPI_USR}", "${env.DEVPI_PSW}")
                }
            }
        }
        stage("Deploy Online Documentation") {
            when{
                equals expected: true, actual: params.DEPLOY_DOCS
            }
            environment{
                PKG_NAME = get_package_name("DIST-INFO", "uiucprescon_ocr.dist-info/METADATA")
            }
            steps{
                unstash "DOCS_ARCHIVE"
                deploy_docs(env.PKG_NAME, "build/docs/html")
            }
        }
    }
}
