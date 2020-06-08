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
            docker.build("devpi", "-f ci/docker/deploy/devpi/deploy/Dockerfile .").inside{
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
            os: [
                windows:[
                    agents: [
                        build: [
                            dockerfile: [
                                filename: 'ci/docker/windows/build/msvc/Dockerfile',
                                label: 'Windows&&Docker',
                                additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.6.8/python-3.6.8-amd64.exe --build-arg CHOCOLATEY_SOURCE'
                            ]
                        ],
                        test:[
                            wheel: [
                                dockerfile: [
                                    filename: 'ci/docker/windows/test/msvc/Dockerfile',
                                    label: 'Windows&&Docker',
                                    additionalBuildArgs: '--build-arg PYTHON_DOCKER_IMAGE_BASE=python:3.6-windowsservercore --build-arg CHOCOLATEY_SOURCE'
                                ]
                            ],
                            sdist: [
                                dockerfile: [
                                    filename: 'ci/docker/windows/build/msvc/Dockerfile',
                                    label: 'Windows&&Docker',
                                    additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.6.8/python-3.6.8-amd64.exe --build-arg CHOCOLATEY_SOURCE'
                                ]
                            ]
                        ],
                        devpi: [
                            wheel: [
                                dockerfile: [
                                    filename: 'ci/docker/deploy/devpi/test/windows/whl/Dockerfile',
                                    label: 'Windows&&Docker',
                                    additionalBuildArgs: '--build-arg PYTHON_DOCKER_IMAGE_BASE=python:3.6-windowsservercore'
                                ]
                            ],
                            sdist: [
                                dockerfile: [
                                    filename: 'ci/docker/deploy/devpi/test/windows/source/Dockerfile',
                                    label: 'Windows&&Docker',
                                    additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.6.8/python-3.6.8-amd64.exe --build-arg CHOCOLATEY_SOURCE'
                                ]
                            ]
                        ]
                    ],
                    pkgRegex: [
                        wheel: "*cp36*.whl",
                        sdist: "uiucprescon.ocr-*.zip"
                    ]
                ],
                linux: [
                    agents: [
                        build: [
                            dockerfile: [
                                filename: 'ci/docker/linux/build/Dockerfile',
                                label: 'linux&&docker',
                                additionalBuildArgs: '--build-arg PYTHON_VERSION=3.6 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                            ]
                        ],
                        test: [
                            sdist: [
                                dockerfile: [
                                    filename: 'ci/docker/linux/build/Dockerfile',
                                    label: 'linux&&docker',
                                    additionalBuildArgs: '--build-arg PYTHON_VERSION=3.6 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                ]
                            ]
                        ],
                        devpi: [
                            whl: [
                                dockerfile: [
                                    filename: 'ci/docker/deploy/devpi/test/linux/Dockerfile',
                                    label: 'linux&&docker',
                                    additionalBuildArgs: '--build-arg PYTHON_VERSION=3.6 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                ]
                            ],
                            sdist: [
                                dockerfile: [
                                    filename: 'ci/docker/deploy/devpi/test/linux/Dockerfile',
                                    label: 'linux&&docker',
                                    additionalBuildArgs: '--build-arg PYTHON_VERSION=3.6 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                ]
                            ]
                        ]
                    ],
                    pkgRegex: [
                        wheel: "*cp36*.whl",
                        sdist: "uiucprescon.ocr-*.zip"
                    ]
                ]
            ],
            tox_env: "py36",
            devpiSelector: [
                sdist: "zip",
                wheel: "36.*whl",
            ],
            pkgRegex: [
                wheel: "*cp36*.whl",
                sdist: "*.zip"
            ]
        ],
        "3.7" : [
            os: [
                windows: [
                    agents: [
                        build: [
                            dockerfile: [
                                filename: 'ci/docker/windows/build/msvc/Dockerfile',
                                label: 'Windows&&Docker',
                                additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.7.5/python-3.7.5-amd64.exe --build-arg CHOCOLATEY_SOURCE'
                            ]
                        ],
                        test: [
                            sdist: [
                                dockerfile: [
                                    filename: 'ci/docker/windows/build/msvc/Dockerfile',
                                    label: 'Windows&&Docker',
                                    additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.7.5/python-3.7.5-amd64.exe --build-arg CHOCOLATEY_SOURCE'
                                ]
                            ],
                            wheel: [
                                dockerfile: [
                                    filename: 'ci/docker/windows/test/msvc/Dockerfile',
                                    additionalBuildArgs: '--build-arg PYTHON_DOCKER_IMAGE_BASE=python:3.7',
                                    label: 'windows && docker',
                                ]
                            ]
                        ],
                        devpi: [
                            wheel: [
                                dockerfile: [
                                    filename: 'ci/docker/deploy/devpi/test/windows/whl/Dockerfile',
                                    label: 'Windows&&Docker',
                                    additionalBuildArgs: '--build-arg PYTHON_DOCKER_IMAGE_BASE=python:3.7'
                                ]
                            ],
                            sdist: [
                                dockerfile: [
                                    filename: 'ci/docker/deploy/devpi/test/windows/source/Dockerfile',
                                    label: 'Windows&&Docker',
                                    additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.7.5/python-3.7.5-amd64.exe --build-arg CHOCOLATEY_SOURCE'
                                ]
                            ]
                        ]
                    ],
                    pkgRegex: [
                        wheel: "*cp37*.whl",
                        sdist: "*.zip"
                    ]
                ],
                linux: [
                    agents: [
                        build: [
                            dockerfile: [
                                filename: 'ci/docker/linux/build/Dockerfile',
                                label: 'linux&&docker',
                                additionalBuildArgs: '--build-arg PYTHON_VERSION=3.7 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                            ]
                        ],
                        test: [
                            sdist: [
                                dockerfile: [
                                    filename: 'ci/docker/linux/build/Dockerfile',
                                    label: 'linux&&docker',
                                    additionalBuildArgs: '--build-arg PYTHON_VERSION=3.7 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                ]
                            ]
                        ],
                        devpi: [
                            wheel: [
                                dockerfile: [
                                    filename: 'ci/docker/deploy/devpi/test/linux/Dockerfile',
                                    label: 'linux&&docker',
                                    additionalBuildArgs: '--build-arg PYTHON_VERSION=3.7 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                ]
                            ],
                            sdist: [
                                dockerfile: [
                                    filename: 'ci/docker/deploy/devpi/test/linux/Dockerfile',
                                    label: 'linux&&docker',
                                    additionalBuildArgs: '--build-arg PYTHON_VERSION=3.7 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                ]
                            ]
                        ]
                    ],
                    pkgRegex: [
                        wheel: "*cp37*.whl",
                        sdist: "uiucprescon.ocr-*.zip"
                    ]
                ]
            ],
            tox_env: "py37",
            devpiSelector: [
                sdist: "zip",
                wheel: "37.*whl",
            ],
            pkgRegex: [
                wheel: "*cp37*.whl",
                sdist: "*.zip"
            ]
        ],
        "3.8" : [
            os: [
                windows: [
                    agents: [
                        build: [
                            dockerfile: [
                                filename: 'ci/docker/windows/build/msvc/Dockerfile',
                                label: 'Windows&&Docker',
                                additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.8.3/python-3.8.3-amd64.exe --build-arg CHOCOLATEY_SOURCE'
                            ]
                        ],
                        test: [
                            sdist: [
                                dockerfile: [
                                    filename: 'ci/docker/windows/build/msvc/Dockerfile',
                                    label: 'Windows&&Docker',
                                    additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.8.3/python-3.8.3-amd64.exe --build-arg CHOCOLATEY_SOURCE'
                                ]
                            ],
                            wheel: [
                                dockerfile: [
                                    filename: 'ci/docker/windows/test/msvc/Dockerfile',
                                    additionalBuildArgs: '--build-arg PYTHON_DOCKER_IMAGE_BASE=python:3.8',
                                    label: 'windows && docker',
                                ]
                            ]
                        ],
                        devpi: [
                            wheel: [
                                dockerfile: [
                                    filename: 'ci/docker/deploy/devpi/test/windows/whl/Dockerfile',
                                    label: 'Windows&&Docker',
                                    additionalBuildArgs: '--build-arg PYTHON_DOCKER_IMAGE_BASE=python:3.8'
                                ]
                            ],
                            sdist: [
                                dockerfile: [
                                    filename: 'ci/docker/deploy/devpi/test/windows/source/Dockerfile',
                                    label: 'Windows&&Docker',
                                    additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.8.3/python-3.8.3-amd64.exe --build-arg CHOCOLATEY_SOURCE'
                                ]
                            ]
                        ]

                    ],
                    pkgRegex: [
                        wheel: "*cp38*.whl",
                        sdist: "uiucprescon.ocr-*.zip"
                    ]
                ],
                linux: [
                    agents: [
                        build: [
                            dockerfile: [
                                filename: 'ci/docker/linux/build/Dockerfile',
                                label: 'linux&&docker',
                                additionalBuildArgs: '--build-arg PYTHON_VERSION=3.8 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                            ]
                        ],
                        test: [
                            sdist: [
                                dockerfile: [
                                    filename: 'ci/docker/linux/build/Dockerfile',
                                    label: 'linux&&docker',
                                    additionalBuildArgs: '--build-arg PYTHON_VERSION=3.8 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                ]
                            ]
                        ],
                        devpi: [
                            wheel: [
                                dockerfile: [
                                    filename: 'ci/docker/deploy/devpi/test/linux/Dockerfile',
                                    label: 'linux&&docker',
                                    additionalBuildArgs: '--build-arg PYTHON_VERSION=3.8 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                ]
                            ],
                            sdist: [
                                dockerfile: [
                                    filename: 'ci/docker/deploy/devpi/test/linux/Dockerfile',
                                    label: 'linux&&docker',
                                    additionalBuildArgs: '--build-arg PYTHON_VERSION=3.8 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                ]
                            ]
                        ]
                    ],
                    pkgRegex: [
                        wheel: "*cp38*.whl",
                        sdist: "uiucprescon.ocr-*.zip"
                    ]
                ]
            ],
            tox_env: "py38",
            devpiSelector: [
                sdist: "zip",
                wheel: "38.*whl",
            ],
            pkgRegex: [
                wheel: "*cp38*.whl",
                sdist: "*.zip"
            ]
        ],
    ]

pipeline {
    agent none
    triggers {
       parameterizedCron '@weekly % DEPLOY_DEVPI=true; TEST_RUN_TOX=true'
    }
    options {
        timeout(time: 1, unit: 'DAYS')
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
                    filename 'ci/docker/linux/build/Dockerfile'
                    label 'linux && docker'
                    additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) --build-arg PYTHON_VERSION=3.8'
                }
//                 dockerfile {
//                     filename 'ci/docker/windows/build/msvc/Dockerfile'
//                     label 'Windows&&Docker'
//                     additionalBuildArgs "--build-arg CHOCOLATEY_SOURCE"
//                   }
            }
            stages{
                stage("Getting Distribution Info"){
                    steps{
                        timeout(2){
                            sh "python setup.py dist_info"
                        }
                    }
                    post{
                        success{
                            stash includes: "uiucprescon.ocr.dist-info/**", name: 'DIST-INFO'
                            archiveArtifacts artifacts: "uiucprescon.ocr.dist-info/**"
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
                    filename 'ci/docker/linux/build/Dockerfile'
                    label 'linux && docker'
                    additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) --build-arg PYTHON_VERSION=3.8'
                }
            }
//                 dockerfile {
//                     filename 'ci/docker/windows/build/msvc/Dockerfile'
//                     label 'Windows&&Docker'
//                     additionalBuildArgs "--build-arg CHOCOLATEY_SOURCE"
//                   }
//             }
            stages{
                stage("Building Python Package"){
                    steps {
                        timeout(20){
                            sh 'python setup.py build -b build --build-lib build/lib/ --build-temp build/temp build_ext -j $(grep -c ^processor /proc/cpuinfo) --inplace'
//                             bat "python setup.py build -b ${WORKSPACE}\\build\\37 -j${env.NUMBER_OF_PROCESSORS} --build-lib .\\build\\37\\lib build_ext --inplace"
                        }
                    }
                    post{
                        success{
                            stash includes: 'uiucprescon/**/*.dll,uiucprescon/**/*.pyd,uiucprescon/**/*.exe,uiucprescon/**/*.so', name: "COMPILED_BINARIES"
//                             stash includes: 'build/37/lib/**,uiucprescon/**/*.dll,uiucprescon/**/*.pyd', name: 'BUILD_FILES'

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
                        PKG_NAME = get_package_name("DIST-INFO", "uiucprescon.ocr.dist-info/METADATA")
                        PKG_VERSION = get_package_version("DIST-INFO", "uiucprescon.ocr.dist-info/METADATA")
                    }
                    steps{
                        timeout(3){
                                sh """mkdir -p logs
                                      python -m sphinx docs/source build/docs/html -d build/docs/.doctrees -w logs/build_sphinx.log"""
                        }
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
                            stash includes: 'build/docs/html/**,dist/${DOC_ZIP_FILENAME}', name: 'DOCS_ARCHIVE'
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
                    filename 'ci/docker/linux/build/Dockerfile'
                    label 'linux && docker'
                    additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) --build-arg PYTHON_VERSION=3.8'
                }
            }
//             agent {
//                 dockerfile {
//                     filename 'ci/docker/windows/build/msvc/Dockerfile'
//                     label 'Windows&&Docker'
//                     additionalBuildArgs "--build-arg CHOCOLATEY_SOURCE"
//                   }
//             }
            failFast true
            stages{
                stage("Setting up Tests"){
                    steps{
                        timeout(3){
                            unstash "COMPILED_BINARIES"
                            unstash "DOCS_ARCHIVE"
                            sh """mkdir -p logs
                                mkdir -p reports
                                """
                        }
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

                                    steps {
                                        timeout(60){
                                            sh  (
                                                label: "Run Tox",
                                                script: "tox -e py -vv "
                                            )
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
                            steps{
                                timeout(10){
                                    sh(
                                        label: "Running pytest",
                                        script: """mkdir -p reports/pytestcoverage
                                                   python -m pytest --junitxml=reports/pytest/${env.junit_filename} --junit-prefix=${env.NODE_NAME}-pytest --cov-report html:reports/pytestcoverage/  --cov-report xml:reports/coverage.xml --cov=uiucprescon --integration --cov-config=setup.cfg
                                                   """
                                    )
                                }
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
//                                     bat returnStatus: true, script: "flake8 uiucprescon --tee --output-file ${WORKSPACE}\\logs\\flake8.log"
                                }
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
                                    steps{
                                        timeout(2){
                                            sh "stubgen uiucprescon -o mypy_stubs"
                                        }
                                    }

                                }
                                stage("Running MyPy"){
                                    environment{
                                        MYPYPATH = "${WORKSPACE}/mypy_stubs"
                                    }
                                    steps{
                                        timeout(3){
                                            sh(
                                                label: "Running MyPy",
                                                script: """mkdir -p reports/mypy/html
                                                           mypy -p uiucprescon --cache-dir=nul --html-report reports/mypy/html > logs/mypy.log
                                                """
                                            )
                                        }
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
        stage("Python packaging"){
            stages{
                stage("Build sdist"){
                    agent {
                        dockerfile {
                            filename 'ci/docker/linux/build/Dockerfile'
                            label 'linux && docker'
                            additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) --build-arg PYTHON_VERSION=3.8'
                        }
//                         dockerfile {
//                             filename 'ci/docker/windows/build/msvc/Dockerfile'
//                             label 'Windows&&Docker'
//                             additionalBuildArgs "--build-arg CHOCOLATEY_SOURCE"
//                           }
                    }
                    steps {
                        sh "python setup.py sdist -d dist --format zip"
                    }
                    post{
                        success{
                            stash includes: 'dist/*.zip,dist/*.tar.gz', name: "sdist"
                        }
                    }
                }
                stage("Testing Packages"){
                    matrix{
                        axes {
                            axis {
                                name 'PYTHON_VERSION'
                                values(
                                    '3.6',
                                    '3.7',
                                    '3.8'
                                )
                            }
                            axis {
                                name 'PLATFORM'
                                values(
                                    "windows",
                                    "linux"
                                )
                            }
                            axis {
                                name 'FORMAT'
                                values(
                                    "sdist",
                                    "wheel"
                                )
                            }
                        }
                        excludes{
                            exclude {
                                axis {
                                    name 'PLATFORM'
                                    values 'linux'
                                }
                                axis {
                                    name 'FORMAT'
                                    values 'wheel'
                                }
                            }
                        }
                        stages {
                            stage("Building Wheel"){
                                agent {
                                    dockerfile {
                                        filename "${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].agents.build.dockerfile.filename}"
                                        label "${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].agents.build.dockerfile.label}"
                                        additionalBuildArgs "${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].agents.build.dockerfile.additionalBuildArgs}"
                                     }
                                }
                                when {
                                    equals expected: 'wheel', actual: FORMAT
                                    beforeAgent true
                                }
                                steps{
                                    script{
                                        if(isUnix()){
                                            sh(
                                                label: "Building Wheel for Python ${PYTHON_VERSION}",
                                                script: "python setup.py build -b build build_ext bdist_wheel -d ${WORKSPACE}/dist"
                                            )
                                        } else {
                                            bat(
                                                label: "Building Wheel for Python ${PYTHON_VERSION}",
                                                script: "python setup.py build -b build build_ext bdist_wheel -d ${WORKSPACE}\\dist"
                                            )
                                        }
                                    }
                                }
                                post {
                                    success{
                                        stash includes: "dist/${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].pkgRegex[FORMAT]}", name: "${FORMAT} ${PYTHON_VERSION}-${PLATFORM}"
                                        script{
                                            if(!isUnix()){
                                                findFiles(excludes: '', glob: '**/*.pyd').each{
                                                    bat(
                                                        label: "Scanning dll dependencies of ${it.name}",
                                                        script:"dumpbin /DEPENDENTS ${it.path}"
                                                        )
                                                }
                                            }
                                        }
                                    }
                                    cleanup{
                                        cleanWs(
                                                deleteDirs: true,
                                                patterns: [
                                                    [pattern: 'dist', type: 'INCLUDE'],
                                                    [pattern: 'build', type: 'INCLUDE']
                                                ]
                                            )
                                    }
                                }
                            }
                            stage("Testing Package"){
                                agent {
                                    dockerfile {
                                        filename "${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].agents.test[FORMAT].dockerfile.filename}"
                                        label "${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].agents.test[FORMAT].dockerfile.label}"
                                        additionalBuildArgs "${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].agents.test[FORMAT].dockerfile.additionalBuildArgs}"
                                     }
                                }
                                steps{
                                    script{
                                        if (PLATFORM != "windows"){
                                            sh(
                                                label: "Installing Python virtual environment",
                                                script:"python -m venv venv"
                                            )

                                            sh(
                                                label: "Upgrading pip to latest version",
                                                script: "venv/bin/python -m pip install pip --upgrade"
                                            )

                                            sh(
                                                label: "Installing tox to Python virtual environment",
                                                script: "venv/bin/pip install tox --upgrade"
                                            )
                                        }
                                        if (FORMAT == "wheel"){
                                            unstash "${FORMAT} ${PYTHON_VERSION}-${PLATFORM}"
                                        }
                                        else{
                                            unstash "sdist"
                                        }
                                        findFiles( glob: "dist/**/${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].pkgRegex[FORMAT]}").each{
                                            if(isUnix()){
                                                sh(
                                                    label: "Testing ${it}",
                                                    script: "venv/bin/tox --installpkg=${it.path} -e py"
                                                    )
                                            } else {
                                                bat(
                                                    label: "Testing ${it}",
                                                    script: "tox --installpkg=${it.path} -e py"
                                                )
                                            }
                                        }
                                    }
                                }
                                post{
                                    success{
                                        archiveArtifacts allowEmptyArchive: true, artifacts: "dist/${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].pkgRegex[FORMAT]}"
                                    }
                                    cleanup{
                                        cleanWs(
                                            notFailBuild: true,
                                            deleteDirs: true,
                                            patterns: [
                                                    [pattern: 'dist', type: 'INCLUDE'],
                                                    [pattern: 'build', type: 'INCLUDE'],
                                                    [pattern: '.tox', type: 'INCLUDE'],
                                                ]
                                        )
                                    }
                                }
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
            options{
                lock("uiucprescon.ocr-devpi")
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
                PKG_NAME = get_package_name("DIST-INFO", "uiucprescon.ocr.dist-info/METADATA")
                PKG_VERSION = get_package_version("DIST-INFO", "uiucprescon.ocr.dist-info/METADATA")
                DEVPI = credentials("DS_devpi")
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
                            unstash "wheel 3.6-windows"
                            unstash "wheel 3.7-windows"
                            unstash "wheel 3.8-windows"
                            unstash "sdist"
                            unstash "DOCS_ARCHIVE"
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
                    matrix{
                        axes {
                            axis {
                                name 'PYTHON_VERSION'
                                values(
                                    '3.6',
                                    '3.7',
                                    '3.8'
                                )
                            }
                            axis {
                                name 'PLATFORM'
                                values(
                                    "windows",
                                    "linux"
                                )
                            }
                            axis {
                                name 'FORMAT'
                                values(
                                    "sdist",
                                    "wheel"
                                )
                            }
                        }
                        excludes{
                            exclude {
                                axis {
                                    name 'PLATFORM'
                                    values 'linux'
                                }
                                axis {
                                    name 'FORMAT'
                                    values 'wheel'
                                }
                            }
                        }
                        stages {
                            stage("Testing Package on DevPi Server"){
                                agent {
                                    dockerfile {
                                        filename "${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].agents.devpi[FORMAT].dockerfile.filename}"
                                        label "${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].agents.devpi[FORMAT].dockerfile.label}"
                                        additionalBuildArgs "${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].agents.devpi[FORMAT].dockerfile.additionalBuildArgs}"
                                     }
                                }
                                steps{
                                    unstash "DIST-INFO"
                                    script{
                                        def props = readProperties interpolate: true, file: "uiucprescon.ocr.dist-info/METADATA"

                                        if(isUnix()){
                                            sh(
                                                label: "Checking Python version",
                                                script: "python --version"
                                            )
                                            sh(
                                                label: "Connecting to DevPi index",
                                                script: "devpi use https://devpi.library.illinois.edu --clientdir certs && devpi login $DEVPI_USR --password $DEVPI_PSW --clientdir certs && devpi use ${env.BRANCH_NAME}_staging --clientdir certs"
                                            )
                                            sh(
                                                label: "Running tests on Devpi",
                                                script: "devpi test --index ${env.BRANCH_NAME}_staging ${props.Name}==${props.Version} -s ${CONFIGURATIONS[PYTHON_VERSION].devpiSelector[FORMAT]} --clientdir certs -e ${CONFIGURATIONS[PYTHON_VERSION].tox_env} -v"
                                            )
                                        } else {
                                            bat(
                                                label: "Checking Python version",
                                                script: "python --version"
                                            )
                                            bat(
                                                label: "Connecting to DevPi index",
                                                script: "devpi use https://devpi.library.illinois.edu --clientdir certs\\ && devpi login %DEVPI_USR% --password %DEVPI_PSW% --clientdir certs\\ && devpi use ${env.BRANCH_NAME}_staging --clientdir certs\\"
                                            )
                                            bat(
                                                label: "Running tests on Devpi",
                                                script: "devpi test --index ${env.BRANCH_NAME}_staging ${props.Name}==${props.Version} -s ${CONFIGURATIONS[PYTHON_VERSION].devpiSelector[FORMAT]} --clientdir certs\\ -e ${CONFIGURATIONS[PYTHON_VERSION].tox_env} -v"
                                            )
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
                                                [pattern: 'certs', type: 'INCLUDE'],
                                                [pattern: 'uiucprescon.ocr.dist-info', type: 'INCLUDE'],
                                            ]
                                        )
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
                            branch "master"
                        }
                        beforeAgent true
                    }
                    agent {
                        dockerfile {
                            filename 'ci/docker/deploy/devpi/deploy/Dockerfile'
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
                                sh "devpi use https://devpi.library.illinois.edu --clientdir ${WORKSPACE}/devpi  && devpi login $DEVPI_USR --password $DEVPI_PSW --clientdir ${WORKSPACE}/devpi && devpi use /DS_Jenkins/${env.BRANCH_NAME}_staging --clientdir ${WORKSPACE}/devpi && devpi push --index ${env.DEVPI_USR}/${env.BRANCH_NAME}_staging ${env.PKG_NAME}==${env.PKG_VERSION} production/release --clientdir ${WORKSPACE}/devpi"
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
                        def devpi_docker = docker.build("devpi", "-f ci/docker/deploy/devpi/deploy/Dockerfile .")
                        devpi_docker.inside{
                            sh(
                                script: "devpi use https://devpi.library.illinois.edu --clientdir ${WORKSPACE}/devpi  && devpi login $DEVPI_USR --password $DEVPI_PSW --clientdir ${WORKSPACE}/devpi && devpi use /${env.DEVPI_USR}/${env.BRANCH_NAME}_staging --clientdir ${WORKSPACE}/devpi",
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
                PKG_NAME = get_package_name("DIST-INFO", "uiucprescon.ocr.dist-info/METADATA")
            }
            steps{
                unstash "DOCS_ARCHIVE"
                deploy_docs(env.PKG_NAME, "build/docs/html")
            }
        }
    }
}
