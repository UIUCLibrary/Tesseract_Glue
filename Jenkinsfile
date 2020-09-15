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
            script: "python -m pep517.build --binary --out-dir dist\\ ."
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
                        package: [
                            dockerfile: [
                                filename: 'ci/docker/windows/build/msvc/Dockerfile',
                                label: 'Windows&&Docker',
                                additionalBuildArgs: '--build-arg PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.6.8/python-3.6.8-amd64.exe --build-arg CHOCOLATEY_SOURCE'
                            ]
                        ],
                        test:[
                            whl: [
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
                    devpiSelector: [
                        sdist: "zip",
                        wheel: "36m-win*.*whl",
                    ],
                    pkgRegex: [
                        whl: "*cp36*.whl",
                        sdist: "uiucprescon.ocr-*.tar.gz,"
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
                        package: [
                            dockerfile: [
                                filename: 'ci/docker/linux/package/Dockerfile',
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
                            ],
                            whl: [
                                dockerfile: [
                                    filename: 'ci/docker/linux/build/Dockerfile',
                                    label: 'linux&&docker',
                                    additionalBuildArgs: '--build-arg PYTHON_VERSION=3.6 --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g)'
                                ]
                            ]
                        ],
                        devpi: [
                            wheel: [
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
                            ],
                        ],
                    ],
                    devpiSelector: [
                        sdist: "zip",
                        wheel: "36m-manylinux*.*whl",
                    ],
                    pkgRegex: [
                        whl: "*cp36*.whl",
                        sdist: "uiucprescon.ocr-*.tar.gz,"
                    ]
                ]
            ],
            tox_env: "py36",
            devpiSelector: [
                sdist: "zip",
                whl: "36.*whl",
            ],
            pkgRegex: [
                whl: "*cp36*.whl",
                sdist: "*.tar.gz"
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
                        package: [
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
                            whl: [
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
                    devpiSelector: [
                        sdist: "zip",
                        wheel: "37m-win*.*whl",
                    ],
                    pkgRegex: [
                        whl: "*cp37*.whl",
                        sdist: "*.tar.gz"
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
                        package: [
                            dockerfile: [
                                filename: 'ci/docker/linux/package/Dockerfile',
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
                            ],
                            whl: [
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
                    devpiSelector: [
                        sdist: "zip",
                        wheel: "37m-manylinux*.*whl",
                    ],
                    pkgRegex: [
                        whl: "*cp37*.whl",
                        sdist: "uiucprescon.ocr-*.tar.gz,"
                    ]
                ],
            ],
            tox_env: "py37",
            devpiSelector: [
                sdist: "zip",
                whl: "37.*whl",
            ],
            pkgRegex: [
                whl: "*cp37*.whl",
                sdist: "*.tar.gz"
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
                        package: [
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
                            whl: [
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
                    devpiSelector: [
                        sdist: "zip",
                        wheel: "38-win*.*whl",
                    ],
                    pkgRegex: [
                        whl: "*cp38*.whl",
                        sdist: "uiucprescon.ocr-*.tar.gz,"
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
                        package: [
                            dockerfile: [
                                filename: 'ci/docker/linux/package/Dockerfile',
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
                            ],
                            whl: [
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
                    devpiSelector: [
                        sdist: "zip",
                        wheel: "38-manylinux*.*whl",
                    ],
                    pkgRegex: [
                        whl: "*cp38*.whl",
                        sdist: "uiucprescon.ocr-*.tar.gz"
                    ]
                ]
            ],
            tox_env: "py38",
            devpiSelector: [
                sdist: "zip",
                wheel: "38.*whl",
            ],
            pkgRegex: [
                whl: "*cp38*.whl",
                sdist: "*.tar.gz"
            ]
        ],
    ]

def test_pkg(glob, timeout_time){

    findFiles( glob: glob).each{
        cleanWs(
            deleteDirs: true,
            disableDeferredWipeout: true,
            patterns: [
                [pattern: 'dist/', type: 'EXCLUDE'],
                [pattern: 'tests/', type: 'EXCLUDE'],
                [pattern: 'tox.ini', type: 'EXCLUDE'],
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
def startup(){
    node('linux && docker') {
        timeout(2){
            ws{
                checkout scm
                try{
                    docker.image('python:3.8').inside {
                        stage("Getting Distribution Info"){
                            sh(
                               label: "Running setup.py with dist_info",
                               script: """python --version
                                          python setup.py dist_info
                                       """
                            )
                            stash includes: "uiucprescon.ocr.dist-info/**", name: 'DIST-INFO'
                            archiveArtifacts artifacts: "uiucprescon.ocr.dist-info/**"
                        }
                    }
                } finally{
                    deleteDir()
                }
            }
        }
    }
}
startup()

pipeline {
    agent none
    options {
        timeout(time: 1, unit: 'DAYS')
    }
    parameters {
        booleanParam(name: "RUN_CHECKS", defaultValue: true, description: "Run checks on code")
        booleanParam(name: "TEST_RUN_TOX", defaultValue: false, description: "Run Tox Tests")
        booleanParam(name: "USE_SONARQUBE", defaultValue: true, description: "Send data test data to SonarQube")
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
                                    script: 'CFLAGS="--coverage" python setup.py build -b build --build-lib build/lib/ build_ext -j $(grep -c ^processor /proc/cpuinfo) --inplace'
                                )
                            }
                        }
                    }
                    post{
                        always{
                            stash includes: 'uiucprescon/**/*.dll,uiucprescon/**/*.pyd,uiucprescon/**/*.exe,uiucprescon/**/*.so,build/**', name: "COMPILED_BINARIES"
                            recordIssues(filters: [excludeFile('build/*')], tools: [gcc(pattern: 'logs/python_build.log')])
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
                                unstash "DIST-INFO"
                                def props = readProperties(interpolate: true, file: "uiucprescon.ocr.dist-info/METADATA")
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
                stage("Testing") {
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
                                        }
                                    }
                                }
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
                stage("Sonarcloud Analysis"){
                    agent {
                      dockerfile {
                        filename 'ci/docker/linux/build/Dockerfile'
                        label 'linux && docker'
                        additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) --build-arg PYTHON_VERSION=3.8'
                        args '--mount source=sonar-cache-ocr,target=/home/user/.sonar/cache'
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
                stage("Build sdist"){
                    agent {
                        dockerfile {
                            filename 'ci/docker/linux/build/Dockerfile'
                            label 'linux && docker'
                            additionalBuildArgs '--build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) --build-arg PYTHON_VERSION=3.8'
                        }
                    }
                    steps {
                        sh "python -m pep517.build --source --out-dir dist/ ."
                    }
                    post{
                        always{
                            stash includes: 'dist/*.zip,dist/*.tar.gz', name: "sdist"
                        }
                    }
                }
                stage("Mac Versions"){
                    when{
                        equals expected: true, actual: params.BUILD_MAC_PACKAGES
                    }
                    stages{
                        stage('Build wheel for Mac') {
                            agent {
                                label 'mac'
                            }
                            steps{
                                sh(
                                    label: "Building wheel",
                                    script: 'python3 -m pip wheel . -w dist'
                                )
                            }
                            post{
                                always{
                                    stash includes: 'dist/*.whl', name: "MacOS 10.14 py38 wheel"
                                }
                                success{
                                    archiveArtifacts artifacts: "dist/*.whl"
                                }
                                cleanup{
                                    cleanWs(
                                        deleteDirs: true,
                                        patterns: [
                                            [pattern: 'build/', type: 'INCLUDE'],
                                            [pattern: 'dist/', type: 'INCLUDE'],
                                        ]
                                    )
                                }
                            }
                        }
                        stage("Testing"){
                            when{
                                equals expected: true, actual: params.TEST_PACKAGES
                            }
                            parallel{
                                stage('Testing Wheel Package on a Mac') {
                                    agent {
                                        label 'mac'
                                    }
                                    steps{
                                        unstash "MacOS 10.14 py38 wheel"
                                        test_package_on_mac("dist/*.whl")

                                    }
                                    post{
                                        cleanup{
                                            deleteDir()
                                        }
                                    }
                                }
                                stage('Testing sdist Package on a Mac') {
                                    when{
                                        anyOf{
                                            equals expected: true, actual: params.TEST_PACKAGES
                                        }
                                        beforeAgent true
                                    }
                                    agent {
                                        label 'mac'
                                    }
                                    steps{
                                        unstash "sdist"
                                        test_package_on_mac("dist/*.tar.gz,dist/*.zip")
                                    }
                                    post{
                                        cleanup{
                                            deleteDir()
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                stage("Packages on Windows and Linux"){
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
                        }
                        stages {
                            stage("Building Wheel"){
                                agent {
                                    dockerfile {
                                        filename "${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].agents.package.dockerfile.filename}"
                                        label "${PLATFORM} && docker"
                                        additionalBuildArgs "${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].agents.package.dockerfile.additionalBuildArgs}"
                                     }
                                }
                                steps{
                                    build_wheel(PLATFORM)
                                }
                                post {
                                    always{
                                        script{
                                            if( PLATFORM == 'linux'){
                                                stash includes: 'dist/*manylinux*.whl', name: "whl ${PYTHON_VERSION}-manylinux"
                                            } else {
                                                stash includes: "dist/*.whl", name: "whl ${PYTHON_VERSION}-${PLATFORM}"
                                            }
                                        }
                                    }
                                    success{
                                        archiveArtifacts allowEmptyArchive: true, artifacts: "dist/${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].pkgRegex['whl']}"
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
                            stage("Testing Packages"){
                                when{
                                    anyOf{
                                        equals expected: true, actual: params.TEST_PACKAGES
                                    }
                                    beforeAgent true
                                }
                                stages{
                                    stage("Testing Wheel Package"){
                                        agent {
                                            dockerfile {
                                                filename "${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].agents.test['whl'].dockerfile.filename}"
                                                label "${PLATFORM} && docker"
                                                additionalBuildArgs "${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].agents.test['whl'].dockerfile.additionalBuildArgs}"
                                             }
                                        }
                                        steps{
                                            script{
                                                if( PLATFORM == "linux"){
                                                    unstash "whl ${PYTHON_VERSION}-manylinux"
                                                } else{
                                                    unstash "whl ${PYTHON_VERSION}-${PLATFORM}"
                                                }
                                                test_pkg("dist/**/${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].pkgRegex['whl']}", 20)
                                            }
                                        }
                                        post{
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
                                    stage("Testing sdist package"){
                                        agent {
                                            dockerfile {
                                                filename "${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].agents.test['sdist'].dockerfile.filename}"
                                                label "${PLATFORM} && docker"
                                                additionalBuildArgs "${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].agents.test['sdist'].dockerfile.additionalBuildArgs}"
                                             }
                                        }
                                        steps{
                                            catchError(stageResult: 'FAILURE') {
                                                unstash "sdist"
                                                test_pkg("dist/**/${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].pkgRegex['sdist']}", 20)
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
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
                DEVPI = credentials("DS_devpi")
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
                            if(params.BUILD_MAC_PACKAGES){
                                unstash "MacOS 10.14 py38 wheel"
                            }
                        }
                            unstash "whl 3.6-windows"
                            unstash "whl 3.6-manylinux"
                            unstash "whl 3.7-windows"
                            unstash "whl 3.7-manylinux"
                            unstash "whl 3.8-windows"
                            unstash "whl 3.8-manylinux"
                            unstash "sdist"
                            unstash "DOCS_ARCHIVE"
                            sh(
                                label: "Uploading to DevPi Staging",
                                script: """devpi use https://devpi.library.illinois.edu --clientdir ./devpi
                                           devpi login $DEVPI_USR --password $DEVPI_PSW --clientdir ./devpi
                                           devpi use /${env.DEVPI_USR}/${env.devpiStagingIndex} --clientdir ./devpi
                                           devpi upload --from-dir dist --clientdir ./devpi
                                           """
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
                stage("Test DevPi packages mac") {
                    when{
                        equals expected: true, actual: params.BUILD_MAC_PACKAGES
                        beforeAgent true
                    }
                    parallel{
                        stage("Wheel"){
                            agent {
                                label 'mac && 10.14 && python3.8'
                            }
                            steps{
                                timeout(10){
                                    sh(
                                        label: "Installing devpi client",
                                        script: '''python3 -m venv venv
                                                   venv/bin/python -m pip install --upgrade pip
                                                   venv/bin/pip install devpi-client
                                                   venv/bin/devpi --version
                                        '''
                                    )
                                    unstash "DIST-INFO"
                                    devpiRunTest(
                                        "venv/bin/devpi",
                                        "uiucprescon.ocr.dist-info/METADATA",
                                        env.devpiStagingIndex,
                                        "38-macosx_10_14_x86_64*.*whl",
                                        DEVPI_USR,
                                        DEVPI_PSW,
                                        "py38"
                                    )
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
                        stage("sdist"){
                            agent {
                                label 'mac && 10.14 && python3.8'
                            }
                            steps{
                                timeout(10){
                                    sh(
                                        label: "Installing devpi client",
                                        script: '''python3 -m venv venv
                                                   venv/bin/python -m pip install --upgrade pip
                                                   venv/bin/pip install devpi-client
                                                   venv/bin/devpi --version
                                        '''
                                    )
                                    unstash "DIST-INFO"
                                    devpiRunTest(
                                        "venv/bin/devpi",
                                        "uiucprescon.ocr.dist-info/METADATA",
                                        env.devpiStagingIndex,
                                        "tar.gz",
                                        DEVPI_USR,
                                        DEVPI_PSW,
                                        "py38"
                                    )
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
                stage("Test DevPi packages") {
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
                        }
                        stages {
                            stage("Testing DevPi Wheel Package"){
                                agent {
                                    dockerfile {
                                        filename "${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].agents.devpi['wheel'].dockerfile.filename}"
                                        label "${PLATFORM} && docker"
                                        additionalBuildArgs "${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].agents.devpi['wheel'].dockerfile.additionalBuildArgs}"
                                     }
                                }
                                options {
                                    warnError('Package Testing Failed')
                                }
                                steps{
                                    timeout(10){
                                        unstash "DIST-INFO"
                                        devpiRunTest("devpi",
                                            "uiucprescon.ocr.dist-info/METADATA",
                                            env.devpiStagingIndex,
                                            CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].devpiSelector["wheel"],
                                            DEVPI_USR,
                                            DEVPI_PSW,
                                            "py${PYTHON_VERSION.replace('.', '')}"
                                            )
                                    }
                                }
                            }
                            stage("Testing DevPi sdist Package"){
                                agent {
                                    dockerfile {
                                        filename "${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].agents.devpi['sdist'].dockerfile.filename}"
                                        label "${PLATFORM} && docker"
                                        additionalBuildArgs "${CONFIGURATIONS[PYTHON_VERSION].os[PLATFORM].agents.devpi['sdist'].dockerfile.additionalBuildArgs}"
                                     }
                                }
                                options {
                                    warnError('Package Testing Failed')
                                }
                                steps{
                                    timeout(10){
                                        unstash "DIST-INFO"
                                        devpiRunTest("devpi",
                                            "uiucprescon.ocr.dist-info/METADATA",
                                            env.devpiStagingIndex,
                                            "tar.gz",
                                            DEVPI_USR,
                                            DEVPI_PSW,
                                            "py${PYTHON_VERSION.replace('.', '')}"
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
                        script {
                            unstash "DIST-INFO"
                            def props = readProperties interpolate: true, file: "uiucprescon.ocr.dist-info/METADATA"
                            sh(
                                label: "Pushing to DS_Jenkins/${env.BRANCH_NAME} index",
                                script: """devpi use https://devpi.library.illinois.edu --clientdir ./devpi
                                           devpi login $DEVPI_USR --password $DEVPI_PSW --clientdir ./devpi
                                           devpi push --index DS_Jenkins/${env.devpiStagingIndex} ${props.Name}==${props.Version} production/release --clientdir ./devpi
                                           """
                            )
                        }
                    }
                }
            }
            post {
                success{
                    node('linux && docker') {
                        checkout scm
                        script{
                            docker.build("ocr:devpi",'-f ./ci/docker/deploy/devpi/deploy/Dockerfile --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) .').inside{
                                if (!env.TAG_NAME?.trim()){
                                    unstash "DIST-INFO"
                                    def props = readProperties interpolate: true, file: "uiucprescon.ocr.dist-info/METADATA"
                                    sh(
                                        label: "Connecting to DevPi Server",
                                        script: """devpi use https://devpi.library.illinois.edu --clientdir ./devpi
                                                   devpi login $DEVPI_USR --password $DEVPI_PSW --clientdir ./devpi
                                                   devpi use /DS_Jenkins/${env.devpiStagingIndex} --clientdir ./devpi
                                                   devpi push ${props.Name}==${props.Version} DS_Jenkins/${env.BRANCH_NAME} --clientdir ./devpi
                                                   """
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
                                unstash "DIST-INFO"
                                def props = readProperties interpolate: true, file: "uiucprescon.ocr.dist-info/METADATA"
                                sh(
                                label: "Connecting to DevPi Server",
                                script: """devpi use https://devpi.library.illinois.edu --clientdir ./devpi
                                           devpi login $DEVPI_USR --password $DEVPI_PSW --clientdir ./devpi
                                           devpi use /DS_Jenkins/${env.devpiStagingIndex} --clientdir ./devpi
                                           devpi remove -y ${props.Name}==${props.Version} --clientdir ./devpi
                                           """
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
