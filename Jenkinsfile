library identifier: 'JenkinsPythonHelperLibrary@2024.7.0', retriever: modernSCM(
  [$class: 'GitSCMSource',
   remote: 'https://github.com/UIUCLibrary/JenkinsPythonHelperLibrary.git',
   ])

SONARQUBE_CREDENTIAL_ID = 'sonarcloud_token'
SUPPORTED_MAC_VERSIONS = ['3.8', '3.9', '3.10', '3.11', '3.12']
SUPPORTED_LINUX_VERSIONS = ['3.8', '3.9', '3.10', '3.11', '3.12']
SUPPORTED_WINDOWS_VERSIONS = ['3.8', '3.9', '3.10', '3.11', '3.12']

def getPypiConfig() {
    node(){
        configFileProvider([configFile(fileId: 'pypi_config', variable: 'CONFIG_FILE')]) {
            def config = readJSON( file: CONFIG_FILE)
            return config['deployment']['indexes']
        }
    }
}

def getToxStages(){
    script{
        def windowsJobs = [:]
        def linuxJobs = [:]
        stage('Scanning Tox Environments'){
            parallel(
                'Linux':{
                    linuxJobs = getToxTestsParallel(
                            envNamePrefix: 'Tox Linux',
                            label: 'linux && docker && x86',
                            dockerfile: 'ci/docker/linux/tox/Dockerfile',
                            dockerArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg PIP_DOWNLOAD_CACHE=/.cache/pip --build-arg UV_CACHE_DIR=/.cache/uv',
                            dockerRunArgs: '-v pipcache_tesseractglue:/.cache/pip -v uvcache_tesseractglue:/.cache/uv',
                            retry: 2
                        )
                },
                'Windows':{
                    timeout(240){
                        // Don't cache uv path here on windows because it keeps running into Access is denied errors on
                        // windows
                        windowsJobs = getToxTestsParallel(
                                envNamePrefix: 'Tox Windows',
                                label: 'windows && docker && x86',
                                dockerfile: 'ci/docker/windows/tox/Dockerfile',
                                dockerArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE --build-arg chocolateyVersion --build-arg PIP_DOWNLOAD_CACHE=c:/users/containeradministrator/appdata/local/pip --build-arg UV_CACHE_DIR=c:/users/ContainerUser/appdata/local/uv',
                                dockerRunArgs: '-v pipcache_tesseractglue:c:/users/containeradministrator/appdata/local/pip',
                                retry: 2
                         )
                    }
                },
                failFast: true
            )
        }
        return windowsJobs + linuxJobs
    }
}


wheelStashes = []

defaultParameterValues = [
    USE_SONARQUBE: false
]

def linux_wheels(){
    def wheelStages = [failFast: true]
    SUPPORTED_LINUX_VERSIONS.each{ pythonVersion ->
        wheelStages["Python ${pythonVersion} - Linux"] = {
            stage("Python ${pythonVersion} - Linux"){
                def archs = [failFast: true]
                if(params.INCLUDE_LINUX_X86_64 == true){
                    archs["Linux x86_64 - Python ${pythonVersion}: wheel"] = {
                        stage("Linux x86_64 - Python ${pythonVersion}: wheel"){
                            stage("Build Wheel (${pythonVersion} Linux x86_64)"){
                                buildPythonPkg(
                                    agent: [
                                        dockerfile: [
                                            label: 'linux && docker && x86',
                                            filename: 'ci/docker/linux/package/Dockerfile',
                                            additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg manylinux_image=quay.io/pypa/manylinux_2_28_x86_64'
                                        ]
                                    ],
                                    retries: 3,
                                    buildCmd: {
                                        try {
                                            sh(label: 'Building python wheel',
                                               script:"""python${pythonVersion} -m build --wheel "--config-setting=conan_cache=/conan/.conan"
                                                         auditwheel -v repair ./dist/*.whl -w ./dist
                                                         auditwheel show ./dist/*manylinux*.whl
                                                         """
                                               )
                                        }
                                        catch(e) {
                                            findFiles(glob: 'dist/*.whl').each{
                                                sh(label: 'Getting info on wheel', script: "auditwheel show ${it.path}")
                                            }
                                            throw e
                                       }
                                    },
                                    post:[
                                        cleanup: {
                                            cleanWs(
                                                patterns: [
                                                        [pattern: 'dist/', type: 'INCLUDE'],
                                                        [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                    ],
                                                notFailBuild: true,
                                                deleteDirs: true
                                            )
                                        },
                                        success: {
                                            stash includes: 'dist/*manylinux*.*whl', name: "python${pythonVersion} linux x86_64 wheel"
                                            wheelStashes << "python${pythonVersion} linux x86_64 wheel"
                                        }
                                    ]
                                )
                            }
                            if(params.TEST_PACKAGES == true){
                                stage("Test Wheel (${pythonVersion} Linux x86_64)"){
                                    testPythonPkg(
                                        agent: [
                                            dockerfile: [
                                                label: 'linux && docker && x86',
                                                filename: 'ci/docker/linux/tox/Dockerfile',
                                                additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg PIP_DOWNLOAD_CACHE=/.cache/pip --build-arg UV_CACHE_DIR=/.cache/uv',
                                                args: '-v pipcache_tesseractglue:/.cache/pip -v uvcache_tesseractglue:/.cache/uv',
                                            ]
                                        ],
                                        retries: 3,
                                        testSetup: {
                                            checkout scm
                                            unstash "python${pythonVersion} linux x86_64 wheel"
                                        },
                                        testCommand: {
                                            findFiles(glob: 'dist/*.whl').each{
                                                timeout(5){
                                                    sh(
                                                        label: 'Running Tox',
                                                        script: "tox --installpkg ${it.path} --workdir /tmp/tox -e py${pythonVersion.replace('.', '')}"
                                                        )
                                                }
                                            }
                                        },
                                        post:[
                                            cleanup: {
                                                cleanWs(
                                                    patterns: [
                                                            [pattern: 'dist/', type: 'INCLUDE'],
                                                            [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                        ],
                                                    notFailBuild: true,
                                                    deleteDirs: true
                                                )
                                            },
                                            success: {
                                                archiveArtifacts artifacts: 'dist/*.whl'
                                            },
                                        ]
                                    )
                                }
                            }
                        }
                    }
                }
                if(params.INCLUDE_LINUX_ARM == true){
                    archs["Linux arm64 - Python ${pythonVersion}: wheel"] = {
                        stage("Linux arm64 - Python ${pythonVersion}: wheel"){
                            stage("Build Wheel (${pythonVersion} Linux arm64)"){
                                buildPythonPkg(
                                    agent: [
                                        dockerfile: [
                                            label: 'linux && docker && arm64',
                                            filename: 'ci/docker/linux/package/Dockerfile',
                                            additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg manylinux_image=quay.io/pypa/manylinux_2_28_aarch64'
                                        ]
                                    ],
                                    retries: 3,
                                    buildCmd: {
                                        try {
                                            sh(label: 'Building python wheel',
                                               script:"""python${pythonVersion} -m build --wheel "--config-setting=conan_cache=/conan/.conan"
                                                         auditwheel -v repair ./dist/*.whl -w ./dist
                                                         auditwheel show ./dist/*manylinux*.whl
                                                         """
                                               )
                                        }
                                        catch(e) {
                                            findFiles(glob: 'dist/*.whl').each{
                                                sh(label: 'Getting info on wheel', script: "auditwheel show ${it.path}")
                                            }
                                            throw e
                                       }
                                    },
                                    post:[
                                        cleanup: {
                                            cleanWs(
                                                patterns: [
                                                        [pattern: 'dist/', type: 'INCLUDE'],
                                                        [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                    ],
                                                notFailBuild: true,
                                                deleteDirs: true
                                            )
                                        },
                                        success: {
                                            stash includes: 'dist/*manylinux*.*whl', name: "python${pythonVersion} linux arm64 wheel"
                                            wheelStashes << "python${pythonVersion} linux arm64 wheel"
                                        }
                                    ]
                                )
                            }
                            stage("Test Wheel (${pythonVersion} Linux arm64)"){
                                testPythonPkg(
                                    agent: [
                                        dockerfile: [
                                            label: 'linux && docker && arm64',
                                            filename: 'ci/docker/linux/tox/Dockerfile',
                                            additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg PIP_DOWNLOAD_CACHE=/.cache/pip --build-arg UV_CACHE_DIR=/.cache/uv',
                                            args: '-v pipcache_tesseractglue:/.cache/pip -v uvcache_tesseractglue:/.cache/uv',
                                        ]
                                    ],
                                    testSetup: {
                                        checkout scm
                                        unstash "python${pythonVersion} linux arm64 wheel"
                                    },
                                    testCommand: {
                                        findFiles(glob: 'dist/*.whl').each{
                                            timeout(5){
                                                sh(
                                                    label: 'Running Tox',
                                                    script: "tox --installpkg ${it.path} --workdir /tmp/tox -e py${pythonVersion.replace('.', '')}"
                                                    )
                                            }
                                        }
                                    },
                                    post:[
                                        cleanup: {
                                            cleanWs(
                                                patterns: [
                                                        [pattern: 'dist/', type: 'INCLUDE'],
                                                        [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                    ],
                                                notFailBuild: true,
                                                deleteDirs: true
                                            )
                                        },
                                        success: {
                                            archiveArtifacts artifacts: 'dist/*.whl'
                                        },
                                    ]
                                )
                            }
                        }
                    }
                }
                parallel(archs)
            }
        }
    }
    parallel(wheelStages)
}

def windows_wheels(){
    def wheelStages = [failFast: true]
    SUPPORTED_WINDOWS_VERSIONS.each{ pythonVersion ->
        if(params.INCLUDE_WINDOWS_X86_64 == true){
            wheelStages["Windows - Python ${pythonVersion}"] = {
                stage("Windows - Python ${pythonVersion}"){
                    stage("Windows - Python ${pythonVersion} x86_64: wheel"){
                        stage("Build Wheel (${pythonVersion} Windows)"){
                            buildPythonPkg(
                                agent: [
                                    dockerfile: [
                                        label: 'windows && docker && x86',
                                        filename: 'ci/docker/windows/tox/Dockerfile',
                                        additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE --build-arg chocolateyVersion --build-arg PIP_DOWNLOAD_CACHE=c:/users/containeradministrator/appdata/local/pip --build-arg UV_CACHE_DIR=c:/users/ContainerUser/appdata/local/uv',
                                        args: '-v uvcache_tesseractglue:c:/users/containeradministrator/appdata/local/uv'
                                    ]
                                ],
                                retries: 3,
                                buildCmd: {
                                    withEnv(['UV_INDEX_STRATEGY=unsafe-best-match']){
                                        bat """py -${pythonVersion} -m venv venv
                                               call venv\\Scripts\\activate.bat
                                               python -m pip install uv
                                               uv pip install build
                                               python -m build --wheel --installer=uv
                                            """
                                    }
                                },
                                post:[
                                    cleanup: {
                                        cleanWs(
                                            patterns: [
                                                    [pattern: 'venv/', type: 'INCLUDE'],
                                                    [pattern: 'build/', type: 'INCLUDE'],
                                                    [pattern: 'dist/', type: 'INCLUDE'],
                                                ],
                                            notFailBuild: true,
                                            deleteDirs: true
                                        )
                                    },
                                    success: {
                                        stash includes: 'dist/*.whl', name: "python${pythonVersion} windows wheel"
                                        wheelStashes << "python${pythonVersion} windows wheel"
                                    }
                                ]
                            )
                        }
                        if(params.TEST_PACKAGES == true){
                            stage("Test Wheel (${pythonVersion} Windows x86_64)"){
                                testPythonPkg(
                                    agent: [
                                        dockerfile: [
                                            label: 'windows && docker && x86',
                                            filename: 'ci/docker/windows/tox_no_vs/Dockerfile',
                                            additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE --build-arg chocolateyVersion --build-arg PIP_DOWNLOAD_CACHE=c:/users/containeradministrator/appdata/local/pip --build-arg UV_CACHE_DIR=c:/users/ContainerUser/appdata/local/uv',
                                            dockerImageName: "${currentBuild.fullProjectName}_test_no_msvc".replaceAll('-', '_').replaceAll('/', '_').replaceAll(' ', '').toLowerCase(),
                                        ]
                                    ],
                                    retries: 3,
                                    testSetup: {
                                         checkout scm
                                         unstash "python${pythonVersion} windows wheel"
                                    },
                                    testCommand: {
                                         findFiles(glob: 'dist/*.whl').each{
                                             powershell(label: 'Running Tox', script: "tox --installpkg ${it.path} --workdir \$env:TEMP\\tox  -e py${pythonVersion.replace('.', '')}")
                                         }

                                    },
                                    post:[
                                        cleanup: {
                                            cleanWs(
                                                patterns: [
                                                        [pattern: 'dist/', type: 'INCLUDE'],
                                                        [pattern: '**/__pycache__/', type: 'INCLUDE'],
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
                    }
                }
            }
        }
    }
    parallel(wheelStages)
}

def mac_wheels(){
    def wheelStages = [failFast: true]
    SUPPORTED_MAC_VERSIONS.each{ pythonVersion ->
        wheelStages["Python ${pythonVersion} - Mac"] = {
            stage("Python ${pythonVersion} - Mac"){
                stage('Single architecture wheel'){
                    def archBuilds = [failFast: true]
                    if(params.INCLUDE_MACOS_X86_64 == true){
                        archBuilds["Python ${pythonVersion} MacOS x86_64"] = {
                            stage("Python ${pythonVersion} MacOS x86_64"){
                                stage("Build Wheel (${pythonVersion} MacOS x86_64)"){
                                    buildPythonPkg(
                                        agent: [
                                            label: "mac && python${pythonVersion} && x86",
                                        ],
                                        retries: 3,
                                        buildCmd: {
                                            sh(label: 'Building wheel',
                                               script: "contrib/build_mac_wheel.sh . --venv-path=./venv --base-python=python${pythonVersion}"
                                            )
                                        },
                                        post:[
                                            cleanup: {
                                                cleanWs(
                                                    patterns: [
                                                            [pattern: 'build/', type: 'INCLUDE'],
                                                            [pattern: 'venv/', type: 'INCLUDE'],
                                                            [pattern: 'dist/', type: 'INCLUDE'],
                                                        ],
                                                    notFailBuild: true,
                                                    deleteDirs: true
                                                )
                                            },
                                            success: {
                                                stash includes: 'dist/*.whl', name: "python${pythonVersion} x86_64 mac wheel"
                                                wheelStashes << "python${pythonVersion} x86_64 mac wheel"
                                            }
                                        ]
                                    )
                                }
                                if(params.TEST_PACKAGES == true){
                                    stage("Test Wheel (${pythonVersion} MacOS x86_64)"){
                                        testPythonPkg(
                                            agent: [
                                                label: "mac && python${pythonVersion} && x86_64",
                                            ],
                                            testSetup: {
                                                checkout scm
                                                unstash "python${pythonVersion} x86_64 mac wheel"
                                            },
                                            testCommand: {
                                                withEnv(['UV_INDEX_STRATEGY=unsafe-best-match']){
                                                    findFiles(glob: 'dist/*.whl').each{
                                                        sh(label: 'Running Tox',
                                                           script: """python${pythonVersion} -m venv venv
                                                           . ./venv/bin/activate
                                                           python -m pip install uv
                                                           uv pip install -r requirements-dev.txt
                                                           tox --installpkg ${it.path} -e py${pythonVersion.replace('.', '')}"""
                                                        )
                                                    }
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
                            }
                        }
                    }
                    if(params.INCLUDE_MACOS_ARM == true){
                        archBuilds["Python ${pythonVersion} MacOS m1 wheel"] = {
                            stage("Python ${pythonVersion} MacOS m1 wheel"){
                                stage("Build Wheel (${pythonVersion} MacOS m1)"){
                                    buildPythonPkg(
                                        agent: [
                                            label: "mac && python${pythonVersion} && m1",
                                        ],
                                        buildCmd: {
                                             sh(label: 'Building wheel',
                                                script: "contrib/build_mac_wheel.sh . --venv-path=./venv --base-python=python${pythonVersion}"
                                               )
                                        },
                                        post:[
                                            cleanup: {
                                                cleanWs(
                                                    patterns: [
                                                            [pattern: 'build/', type: 'INCLUDE'],
                                                            [pattern: 'venv/', type: 'INCLUDE'],
                                                            [pattern: 'dist/', type: 'INCLUDE'],
                                                        ],
                                                    notFailBuild: true,
                                                    deleteDirs: true
                                                )
                                            },
                                            success: {
                                                stash includes: 'dist/*.whl', name: "python${pythonVersion} m1 mac wheel"
                                                wheelStashes << "python${pythonVersion} m1 mac wheel"
                                            }
                                        ]
                                    )
                                }
                                if(params.TEST_PACKAGES == true){
                                    stage("Test Wheel (${pythonVersion} MacOS m1)"){
                                        testPythonPkg(
                                            agent: [
                                                label: "mac && python${pythonVersion} && m1",
                                            ],
                                            testSetup: {
                                                checkout scm
                                                unstash "python${pythonVersion} m1 mac wheel"
                                            },
                                            testCommand: {
                                                withEnv(['UV_INDEX_STRATEGY=unsafe-best-match']){
                                                    findFiles(glob: 'dist/*.whl').each{
                                                        sh(label: 'Running Tox',
                                                           script: """python${pythonVersion} -m venv venv
                                                           . ./venv/bin/activate
                                                           python -m pip install uv
                                                           uv pip install -r requirements-dev.txt
                                                           tox --installpkg ${it.path} -e py${pythonVersion.replace('.', '')}"""
                                                        )
                                                    }
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
                            }
                        }
                    }
                    parallel(archBuilds)
                }
                if(params.INCLUDE_MACOS_X86_64 && params.INCLUDE_MACOS_ARM && pythonVersion != '3.8'){
                    stage("Universal2 Wheel: Python ${pythonVersion}"){
                        stage('Make Universal2 wheel'){
                            node("mac && python${pythonVersion}") {
                                unstash "python${pythonVersion} m1 mac wheel"
                                unstash "python${pythonVersion} x86_64 mac wheel"
                                def wheelNames = []
                                findFiles(excludes: '', glob: 'dist/*.whl').each{wheelFile ->
                                    wheelNames.add(wheelFile.path)
                                }
                                try{
                                    sh(label: 'Make Universal2 wheel',
                                       script: """python${pythonVersion} -m venv venv
                                                  . ./venv/bin/activate
                                                  pip install --upgrade pip
                                                  pip install wheel delocate
                                                  mkdir -p out
                                                  delocate-merge  ${wheelNames.join(' ')} --verbose -w ./out/
                                                  rm dist/*.whl
                                                   """
                                       )
                                   def fusedWheel = findFiles(excludes: '', glob: 'out/*.whl')[0]
                                   def pythonVersionShort = pythonVersion.replace('.','')
                                   def universalWheel = "uiucprescon.ocr-${props.Version}-cp${pythonVersionShort}-cp${pythonVersionShort}-macosx_11_0_universal2.whl"
                                   sh "mv ${fusedWheel.path} ./dist/${universalWheel}"
                                   stash includes: 'dist/*.whl', name: "python${pythonVersion} mac-universal2 wheel"
                                   wheelStashes << "python${pythonVersion} mac-universal2 wheel"
                                   archiveArtifacts artifacts: 'dist/*.whl'
                                } finally {
                                    cleanWs(
                                        patterns: [
                                                [pattern: 'out/', type: 'INCLUDE'],
                                                [pattern: 'dist/', type: 'INCLUDE'],
                                                [pattern: 'venv/', type: 'INCLUDE'],
                                            ],
                                        notFailBuild: true,
                                        deleteDirs: true
                                    )
                               }
                            }
                        }
                        if(params.TEST_PACKAGES == true){
                            stage("Test universal2 Wheel"){
                                parallel(
                                    "Test Python ${pythonVersion} universal2 Wheel on x86_64 mac": {
                                        stage("Test Python ${pythonVersion} universal2 Wheel on x86_64 mac"){
                                            testPythonPkg(
                                                agent: [
                                                    label: "mac && python${pythonVersion} && x86_64",
                                                ],
                                                testSetup: {
                                                    checkout scm
                                                    unstash "python${pythonVersion} mac-universal2 wheel"
                                                },
                                                retries: 3,
                                                testCommand: {
                                                    withEnv(['UV_INDEX_STRATEGY=unsafe-best-match']){
                                                        findFiles(glob: 'dist/*.whl').each{
                                                            sh(label: 'Running Tox',
                                                               script: """python${pythonVersion} -m venv venv
                                                                          . ./venv/bin/activate
                                                                          python -m pip install uv
                                                                          uv pip install -r requirements-dev.txt
                                                                          CONAN_REVISIONS_ENABLED=1 tox --installpkg ${it.path} -e py${pythonVersion.replace('.', '')}
                                                                       """
                                                            )
                                                        }
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
                                    },
                                    "Test Python ${pythonVersion} universal2 Wheel on M1 Mac": {
                                        stage("Test Python ${pythonVersion} universal2 Wheel on M1 Mac"){
                                            testPythonPkg(
                                                agent: [
                                                    label: "mac && python${pythonVersion} && m1",
                                                ],
                                                testSetup: {
                                                    checkout scm
                                                    unstash "python${pythonVersion} mac-universal2 wheel"
                                                },
                                                retries: 3,
                                                testCommand: {
                                                    withEnv(['UV_INDEX_STRATEGY=unsafe-best-match']){
                                                        findFiles(glob: 'dist/*.whl').each{
                                                            sh(label: 'Running Tox',
                                                               script: """python${pythonVersion} -m venv venv
                                                                          . ./venv/bin/activate
                                                                          python -m pip install uv
                                                                          uv pip install -r requirements-dev.txt
                                                                          CONAN_REVISIONS_ENABLED=1 tox --installpkg ${it.path} -e py${pythonVersion.replace('.', '')}
                                                                       """
                                                            )
                                                        }
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
                                )
                            }
                        }
                    }
                }
            }
        }
    }
    parallel(wheelStages)
}

def get_props(){
    stage('Reading Package Metadata'){
        node() {
            try{
                unstash 'DIST-INFO'
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
    parallel(
        [
            failFast: true,
            'Checking sonarqube Settings': {
                stage('Checking sonarqube Settings'){
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
                }
            },
            'Getting Distribution Info': {
                stage('Getting Distribution Info'){
                    node('linux && docker') {
                        timeout(2){
                            ws{
                                checkout scm
                                try{
                                    docker.image('python').inside {
                                        withEnv(['PIP_NO_CACHE_DIR=off']) {
                                            sh(
                                               label: 'Running setup.py with dist_info',
                                               script: '''python --version
                                                          python setup.py dist_info
                                                       '''
                                            )
                                        }
                                        stash includes: '*.dist-info/**', name: 'DIST-INFO'
                                        archiveArtifacts artifacts: '*.dist-info/**'
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
            }
        ]
    )
}
stage('Pipeline Pre-tasks'){
    startup()
    props = get_props()
}
pipeline {
    agent none
    options {
        timeout(time: 1, unit: 'DAYS')
    }
    parameters {
        booleanParam(name: 'RUN_CHECKS', defaultValue: true, description: 'Run checks on code')
        booleanParam(name: 'TEST_RUN_TOX', defaultValue: false, description: 'Run Tox Tests')
        booleanParam(name: 'USE_SONARQUBE', defaultValue: defaultParameterValues.USE_SONARQUBE, description: 'Send data test data to SonarQube')
        booleanParam(name: 'BUILD_PACKAGES', defaultValue: false, description: 'Build Python packages')
        booleanParam(name: 'INCLUDE_MACOS_ARM', defaultValue: false, description: 'Include ARM(m1) architecture for Mac')
        booleanParam(name: 'INCLUDE_MACOS_X86_64', defaultValue: false, description: 'Include x86_64 architecture for Mac')
        booleanParam(name: 'INCLUDE_LINUX_ARM', defaultValue: false, description: 'Include ARM architecture for Linux')
        booleanParam(name: 'INCLUDE_LINUX_X86_64', defaultValue: true, description: 'Include x86_64 architecture for Linux')
        booleanParam(name: 'INCLUDE_WINDOWS_X86_64', defaultValue: true, description: 'Include x86_64 architecture for Windows')
        booleanParam(name: 'TEST_PACKAGES', defaultValue: true, description: 'Test Python packages by installing them and running tests on the installed package')
        booleanParam(name: 'DEPLOY_PYPI', defaultValue: false, description: 'Deploy to pypi')
        booleanParam(name: 'DEPLOY_DOCS', defaultValue: false, description: 'Update online documentation')
    }
    stages {
        stage('Building and Testing'){
            when{
                anyOf{
                    equals expected: true, actual: params.RUN_CHECKS
                    equals expected: true, actual: params.TEST_RUN_TOX
                }
            }
            stages{
                stage('Building') {
                    agent {
                        dockerfile {
                            filename 'ci/docker/linux/jenkins/Dockerfile'
                            label 'linux && docker && x86'
                            additionalBuildArgs '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg PIP_DOWNLOAD_CACHE=/.cache/pip '
                        }
                    }
                    when{
                        equals expected: true, actual: params.RUN_CHECKS
                        beforeAgent true
                    }
                    stages{
                        stage('Building Python Package'){
                            steps {
                                timeout(20){
                                    tee('logs/python_build.log'){
                                        sh(
                                            label: 'Build python package',
                                            script: 'CFLAGS="--coverage -fprofile-arcs -ftest-coverage" LFLAGS="-lgcov --coverage" python setup.py build -b build --build-lib build/lib/ build_ext -j $(grep -c ^processor /proc/cpuinfo) --inplace'
                                        )
                                    }
                                }
                            }
                            post{
                                always{
                                    recordIssues(filters: [excludeFile('build/*'), excludeFile('conan/*'), ], tools: [gcc(pattern: 'logs/python_build.log')])
                                }
                            }
                        }
                        stage('Building Documentation'){
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
                                    zip archive: true, dir: 'build/docs/html', glob: '', zipFile: "dist/${props.Name}-${props.Version}.doc.zip"
                                    stash includes: 'dist/*.doc.zip,build/docs/html/**', name: 'DOCS_ARCHIVE'
                                }
                            }
                        }
                    }
                }
                stage('Testing'){
                    stages{
                        stage('Code Quality') {
                            agent {
                                dockerfile {
                                    filename 'ci/docker/linux/jenkins/Dockerfile'
                                    label 'linux && docker && x86'
                                    additionalBuildArgs '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg PIP_DOWNLOAD_CACHE=/.cache/pip --build-arg UV_CACHE_DIR=/.cache/uv'
                                    args '--mount source=sonar-cache-ocr,target=/opt/sonar/.sonar/cache'
                                }
                            }
                            when{
                                equals expected: true, actual: params.RUN_CHECKS
                                beforeAgent true
                            }
                            stages{
                                stage('Setting up Tests'){
                                    parallel{
                                        stage('Setting Up C++ Tests'){
                                            steps{
                                                sh(
                                                    label: 'Building C++ project for metrics',
                                                    script: '''conan install . -if build/cpp -g cmake_find_package
                                                               cmake -B ./build/cpp -S ./ -DCMAKE_EXPORT_COMPILE_COMMANDS:BOOL=ON -D CMAKE_C_FLAGS="-Wall -Wextra -fprofile-arcs -ftest-coverage" -D CMAKE_CXX_FLAGS="-Wall -Wextra -fprofile-arcs -ftest-coverage" -DBUILD_TESTING:BOOL=ON -D CMAKE_BUILD_TYPE=Debug -DCMAKE_CXX_OUTPUT_EXTENSION_REPLACE:BOOL=ON -DCMAKE_MODULE_PATH=./build/cpp
                                                               make -C build/cpp clean tester
                                                               '''
                                                )
                                            }
                                        }
                                        stage('Setting Up Python Tests'){
                                            steps{
                                                timeout(10){
                                                    sh(
                                                        label: 'Build python package',
                                                        script: '''mkdir -p build/python
                                                                   mkdir -p logs
                                                                   mkdir -p reports
                                                                   CFLAGS="--coverage -fprofile-arcs -ftest-coverage" LFLAGS="-lgcov --coverage" build-wrapper-linux-x86-64 --out-dir build/build_wrapper_output_directory  python setup.py build -b build/python --build-lib build/python/lib/ build_ext -j $(grep -c ^processor /proc/cpuinfo) --inplace --debug
                                                                   '''
                                                    )
                                                    unstash 'DOCS_ARCHIVE'
                                                }
                                            }
                                        }
                                    }
                                }
                                stage('Running Tests'){
                                    parallel {
                                        stage('Run Pytest Unit Tests'){
                                            steps{
                                                timeout(10){
                                                    sh(
                                                        label: 'Running pytest',
                                                        script: '''mkdir -p reports/pytestcoverage
                                                                   coverage run --parallel-mode --source=uiucprescon -m pytest --junitxml=./reports/pytest/junit-pytest.xml --basetemp=/tmp/pytest
                                                                   '''
                                                    )
                                                }
                                            }
                                            post {
                                                always {
                                                    junit 'reports/pytest/junit-pytest.xml'

                                                }
                                            }
                                        }
                                        stage('Run Doctest Tests'){
                                            steps {
                                                timeout(3){
                                                    sh 'python -m sphinx -b doctest docs/source build/docs -d build/docs/doctrees -w logs/doctest_warnings.log'
                                                }
                                            }
                                            post{
                                                always {
                                                    recordIssues(tools: [sphinxBuild(name: 'Doctest', pattern: 'logs/doctest_warnings.log', id: 'doctest')])
                                                }
                                            }
                                        }
                                        stage('Clang Tidy Analysis') {
                                            steps{
                                                tee('logs/clang-tidy.log') {
                                                    catchError(buildResult: 'SUCCESS', message: 'clang tidy found issues', stageResult: 'UNSTABLE') {
                                                        sh(label: 'Run Clang Tidy', script: 'run-clang-tidy -clang-tidy-binary clang-tidy -p ./build/cpp/ ./uiucprescon/ocr')
                                                    }
                                                }
                                            }
                                            post{
                                                always {
                                                    recordIssues(tools: [clangTidy(pattern: 'logs/clang-tidy.log')])
                                                }
                                            }
                                        }
                                        stage('C++ Tests') {
                                            steps{
                                                sh(
                                                    label: 'Running CTest',
                                                    script: 'cd build/cpp && ctest --output-on-failure --no-compress-output -T Test',
                                                    returnStatus: true
                                                )

                                                sh(
                                                    label: 'Running cpp tests',
                                                    script: 'build/cpp/tests/tester -r sonarqube -o reports/test-cpp.xml'
                                                )
                                            }
                                            post{
                                                always{
                                                    xunit(
                                                        testTimeMargin: '3000',
                                                        thresholdMode: 1,
                                                        thresholds: [
                                                            failed(),
                                                            skipped()
                                                        ],
                                                        tools: [
                                                            CTest(
                                                                deleteOutputFiles: true,
                                                                failIfNotNew: true,
                                                                pattern: 'build/cpp/Testing/**/*.xml',
                                                                skipNoTestFiles: true,
                                                                stopProcessingIfError: true
                                                            )
                                                        ]
                                                    )
                                                }
                                            }
                                        }
                                        stage('Run Flake8 Static Analysis') {
                                            steps{
                                                timeout(2){
                                                    catchError(buildResult: 'SUCCESS', message: 'Flake8 found issues', stageResult: 'UNSTABLE') {
                                                        sh(
                                                            label: 'Running Flake8',
                                                            script: 'flake8 uiucprescon --tee --output-file logs/flake8.log'
                                                        )
                                                    }
                                                }
                                            }
                                            post {
                                                always {
                                                    recordIssues(tools: [flake8(name: 'Flake8', pattern: 'logs/flake8.log')])
                                                }
                                            }
                                        }
                                        stage('Run MyPy Static Analysis') {
                                            steps{
                                                sh(
                                                    label: 'Running MyPy',
                                                    script: '''stubgen uiucprescon -o mypy_stubs
                                                               mkdir -p reports/mypy/html
                                                               MYPYPATH="$WORKSPACE/mypy_stubs" mypy -p uiucprescon --cache-dir=nul --html-report reports/mypy/html > logs/mypy.log
                                                               '''
                                                )
                                            }
                                            post {
                                                always {
                                                    recordIssues(tools: [myPy(name: 'MyPy', pattern: 'logs/mypy.log')])
                                                    publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'reports/mypy/html/', reportFiles: 'index.html', reportName: 'MyPy HTML Report', reportTitles: ''])
                                                }
                                            }
                                        }
                                        stage('Run Pylint Static Analysis') {
                                            steps{
                                                catchError(buildResult: 'SUCCESS', message: 'Pylint found issues', stageResult: 'UNSTABLE') {
                                                    sh(label: 'Running pylint',
                                                        script: '''mkdir -p logs
                                                                   mkdir -p reports
                                                                   pylint uiucprescon -r n --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}" --persistent=no > reports/pylint.txt
                                                                   '''

                                                    )
                                                }
                                                sh(
                                                    script: 'pylint  -r n --msg-template="{path}:{module}:{line}: [{msg_id}({symbol}), {obj}] {msg}" --persistent=no > reports/pylint_issues.txt',
                                                    label: 'Running pylint for sonarqube',
                                                    returnStatus: true
                                                )
                                            }
                                            post{
                                                always{
                                                    recordIssues(tools: [pyLint(pattern: 'reports/pylint.txt')])
                                                }
                                            }
                                        }
                                    }
                                    post{
                                        always{
                                            sh(script: '''mkdir -p build/coverage
                                                          find ./build -name '*.gcno' -exec gcov {} -p --source-prefix=$WORKSPACE/ \\;
                                                          mv *.gcov build/coverage/
                                                          coverage combine
                                                          coverage xml -o ./reports/coverage-python.xml
                                                          gcovr --filter uiucprescon/ocr --print-summary --keep --xml -o reports/coverage_cpp.xml
                                                          gcovr --filter uiucprescon/ocr --print-summary --keep
                                                          '''
                                                )
                                            recordCoverage(tools: [[parser: 'COBERTURA', pattern: 'reports/coverage.xml']])
                                        }
                                    }
                                }
                                stage('Sonarcloud Analysis'){
                                    options{
                                        lock('uiucprescon.ocr-sonarcloud')
                                    }
                                    when{
                                        equals expected: true, actual: params.USE_SONARQUBE
                                        beforeOptions true
                                    }
                                    steps{
                                        script{
                                            load('ci/jenkins/scripts/sonarqube.groovy').sonarcloudSubmit(
                                                props,
                                                'reports/sonar-report.json',
                                                SONARQUBE_CREDENTIAL_ID
                                                )
                                        }
                                    }
                                    post {
                                        always{
                                           recordIssues(tools: [sonarQube(pattern: 'reports/sonar-report.json')])
                                        }
                                    }
                                }
                            }
                            post{
                                cleanup{
                                    cleanWs(
                                        patterns: [
                                                [pattern: 'dist/', type: 'INCLUDE'],
                                                [pattern: 'build/', type: 'INCLUDE'],
                                                [pattern: 'logs/', type: 'INCLUDE'],
                                                [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                [pattern: 'uiucprescon/**/*.so', type: 'INCLUDE'],
                                            ],
                                        notFailBuild: true,
                                        deleteDirs: true
                                        )
                                }
                            }
                        }
                        stage('Run Tox test') {
                            when {
                               equals expected: true, actual: params.TEST_RUN_TOX
                            }
                            steps {
                                script{
                                    parallel(getToxStages())
                                }

                            }
                        }
                    }
                }
            }
        }
        stage('Python Packaging'){
            when{
                equals expected: true, actual: params.BUILD_PACKAGES
            }
            failFast true
            parallel{
                stage('Platform Wheels: Mac'){
                    when {
                        anyOf {
                            equals expected: true, actual: params.INCLUDE_MACOS_X86_64
                            equals expected: true, actual: params.INCLUDE_MACOS_ARM
                        }
                    }
                    steps{
                        mac_wheels()
                    }
                }
                stage('Platform Wheels: Linux'){
                    when {
                        anyOf {
                            equals expected: true, actual: params.INCLUDE_LINUX_X86_64
                            equals expected: true, actual: params.INCLUDE_LINUX_ARM
                        }
                    }
                    steps{
                        linux_wheels()
                    }
                }
                stage('Platform Wheels: Windows'){
                    when {
                        equals expected: true, actual: params.INCLUDE_WINDOWS_X86_64
                    }
                    steps{
                        windows_wheels()
                    }
                }
                stage('Source Distribution'){
                    stages{
                        stage('Build sdist'){
                            agent {
                                docker {
                                    image 'python:3.11'
                                    label 'docker && linux'
                                }
                            }
                            options {
                                retry(3)
                            }
                            steps{
                                withEnv(['PIP_NO_CACHE_DIR=off']) {
                                    sh(label: 'Building sdist',
                                       script: '''python -m venv venv --upgrade-deps
                                                  venv/bin/pip install build
                                                  venv/bin/python -m build --sdist
                                                  '''
                                    )
                                }
                            }
                            post{
                                success{
                                    archiveArtifacts artifacts: 'dist/*.tar.gz,dist/*.zip'
                                    stash includes: 'dist/*.tar.gz,dist/*.zip', name: 'python sdist'
                                    script{
                                        wheelStashes << 'python sdist'
                                    }
                                }
                                cleanup{
                                    cleanWs(
                                        patterns: [
                                                [pattern: 'dist/', type: 'INCLUDE'],
                                                [pattern: 'venv/', type: 'INCLUDE'],
                                            ],
                                        notFailBuild: true,
                                        deleteDirs: true
                                    )
                                }
                            }
                        }
                        stage('Test sdist'){
                            when{
                                equals expected: true, actual: params.TEST_PACKAGES
                            }
                            steps{
                                script{
                                    def testSdistStages = [
                                        failFast: true
                                    ]
                                    SUPPORTED_MAC_VERSIONS.each{ pythonVersion ->
                                        def arches = []
                                        if(params.INCLUDE_MACOS_X86_64 == true){
                                            arches << "x86_64"
                                        }
                                        if(params.INCLUDE_MACOS_ARM == true){
                                            arches << "m1"
                                        }
                                        arches.each{arch ->
                                            testSdistStages["Test sdist (MacOS ${arch} - Python ${pythonVersion})"] = {
                                                stage("Test sdist (MacOS ${arch} - Python ${pythonVersion})"){
                                                    testPythonPkg(
                                                        agent: [
                                                            label: "mac && python${pythonVersion} && ${arch}",
                                                        ],
                                                        testSetup: {
                                                            checkout scm
                                                            unstash 'python sdist'
                                                        },
                                                        retries: 3,
                                                        testCommand: {
                                                            withEnv(['UV_INDEX_STRATEGY=unsafe-best-match']){
                                                                findFiles(glob: 'dist/*.tar.gz').each{
                                                                    sh(label: 'Running Tox',
                                                                       script: """python${pythonVersion} -m venv venv
                                                                       . ./venv/bin/activate
                                                                       python -m pip install uv
                                                                       uv pip install -r requirements-dev.txt
                                                                       tox --installpkg ${it.path} -e py${pythonVersion.replace('.', '')}"""
                                                                    )
                                                                }
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
                                                        ]
                                                    )
                                                }
                                            }
                                        }
                                    }
                                    SUPPORTED_WINDOWS_VERSIONS.each{ pythonVersion ->
                                        if(params.INCLUDE_WINDOWS_X86_64 == true){
                                            testSdistStages["Test sdist (Windows x86_64 - Python ${pythonVersion})"] = {
                                                stage("Test sdist (Windows x86_64 - Python ${pythonVersion})"){
                                                    retry(2){
                                                        testPythonPkg(
                                                            agent: [
                                                                dockerfile: [
                                                                    label: 'windows && docker && x86',
                                                                    filename: 'ci/docker/windows/tox/Dockerfile',
                                                                    additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE --build-arg chocolateyVersion --build-arg PIP_DOWNLOAD_CACHE=c:/users/containeradministrator/appdata/local/pip --build-arg UV_CACHE_DIR=c:/users/ContainerUser/appdata/local/uv',
                                                                    args: '-v pipcache_pykdu:c:/users/containeradministrator/appdata/local/pip -v uvcache_tesseractglue:c:/users/containeradministrator/appdata/local/uv',
                                                                    dockerImageName: "${currentBuild.fullProjectName}_test_with_msvc".replaceAll('-', '_').replaceAll('/', '_').replaceAll(' ', "").toLowerCase(),
                                                                ]
                                                            ],
                                                            testSetup: {
                                                                checkout scm
                                                                unstash 'python sdist'
                                                            },
                                                            testCommand: {
                                                                findFiles(glob: 'dist/*.tar.gz').each{
                                                                    bat(label: 'Running Tox', script: "tox --workdir %TEMP%\\tox --installpkg ${it.path} -e py${pythonVersion.replace('.', '')} -v")
                                                                }
                                                            },
                                                            post:[
                                                                cleanup: {
                                                                    cleanWs(
                                                                        patterns: [
                                                                            [pattern: 'dist/', type: 'INCLUDE'],
                                                                            [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                                        ],
                                                                        notFailBuild: true,
                                                                        deleteDirs: true
                                                                    )
                                                                },
                                                            ]
                                                        )
                                                    }
                                                }
                                            }
                                        }
                                    }
                                    SUPPORTED_LINUX_VERSIONS.each{pythonVersion ->
                                        if(params.INCLUDE_LINUX_X86_64 == true){
                                            testSdistStages["Test sdist (Linux x86_64 - Python ${pythonVersion})"] = {
                                                stage("Test sdist (Linux x86_64 - Python ${pythonVersion})"){
                                                    testPythonPkg(
                                                        agent: [
                                                            dockerfile: [
                                                                label: 'linux && docker && x86',
                                                                filename: 'ci/docker/linux/tox/Dockerfile',
                                                                additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg PIP_DOWNLOAD_CACHE=/.cache/pip --build-arg UV_CACHE_DIR=/.cache/uv'
                                                            ]
                                                        ],
                                                        retries: 3,
                                                        testSetup: {
                                                            checkout scm
                                                            unstash 'python sdist'
                                                        },
                                                        testCommand: {
                                                            findFiles(glob: 'dist/*.tar.gz').each{
                                                                sh(
                                                                    label: 'Running Tox',
                                                                    script: "tox --installpkg ${it.path} --workdir /tmp/tox -e py${pythonVersion.replace('.', '')}"
                                                                    )
                                                            }
                                                        },
                                                        post:[
                                                            cleanup: {
                                                                cleanWs(
                                                                    patterns: [
                                                                            [pattern: 'dist/', type: 'INCLUDE'],
                                                                            [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                                        ],
                                                                    notFailBuild: true,
                                                                    deleteDirs: true
                                                                )
                                                            },
                                                        ]
                                                    )
                                                }
                                            }
                                        }
                                        if(params.INCLUDE_LINUX_ARM == true){
                                            testSdistStages["Test sdist (Linux ARM64 - Python ${pythonVersion})"] = {
                                                stage("Test sdist (Linux ARM64 - Python ${pythonVersion})"){
                                                    testPythonPkg(
                                                        agent: [
                                                            dockerfile: [
                                                                label: 'linux && docker && arm64',
                                                                filename: 'ci/docker/linux/tox/Dockerfile',
                                                                additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg PIP_DOWNLOAD_CACHE=/.cache/pip --build-arg UV_CACHE_DIR=/.cache/uv'
                                                            ]
                                                        ],
                                                        retries: 3,
                                                        testSetup: {
                                                            checkout scm
                                                            unstash 'python sdist'
                                                        },
                                                        testCommand: {
                                                            findFiles(glob: 'dist/*.tar.gz').each{
                                                                sh(
                                                                    label: 'Running Tox',
                                                                    script: "tox --installpkg ${it.path} --workdir /tmp/tox -e py${pythonVersion.replace('.', '')}"
                                                                    )
                                                            }
                                                        },
                                                        post:[
                                                            cleanup: {
                                                                cleanWs(
                                                                    patterns: [
                                                                            [pattern: 'dist/', type: 'INCLUDE'],
                                                                            [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                                        ],
                                                                    notFailBuild: true,
                                                                    deleteDirs: true
                                                                )
                                                            },
                                                        ]
                                                    )
                                                }
                                            }
                                        }
                                    }
                                    parallel(testSdistStages)
                                }
                            }
                        }
                    }
                }
            }
        }
        stage('Deploy'){
            parallel{
                stage('Deploy to pypi') {
                    agent {
                        dockerfile {
                            filename 'ci/docker/linux/jenkins/Dockerfile'
                            label 'linux && docker'
                            additionalBuildArgs '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg PIP_DOWNLOAD_CACHE=/.cache/pip --build-arg UV_CACHE_DIR=/.cache/uv'
                        }
                    }
                    when{
                        allOf{
                            equals expected: true, actual: params.BUILD_PACKAGES
                            equals expected: true, actual: params.DEPLOY_PYPI
                        }
                        beforeAgent true
                        beforeInput true
                    }
                    options{
                        retry(3)
                    }
                    input {
                        message 'Upload to pypi server?'
                        parameters {
                            choice(
                                choices: getPypiConfig(),
                                description: 'Url to the pypi index to upload python packages.',
                                name: 'SERVER_URL'
                            )
                        }
                    }
                    steps{
                        unstash 'python sdist'
                        script{
                            wheelStashes.each{
                                unstash it
                            }
                        }
                        pypiUpload(
                            credentialsId: 'jenkins-nexus',
                            repositoryUrl: SERVER_URL,
                            glob: 'dist/*'
                        )
                    }
                    post{
                        cleanup{
                            cleanWs(
                                deleteDirs: true,
                                patterns: [
                                        [pattern: 'dist/', type: 'INCLUDE']
                                    ]
                            )
                        }
                    }
                }
                 stage('Deploy Online Documentation') {
                    when{
                        equals expected: true, actual: params.DEPLOY_DOCS
                        beforeAgent true
                        beforeInput true
                    }
                    agent {
                        dockerfile {
                            filename 'ci/docker/linux/jenkins/Dockerfile'
                            label 'linux && docker'
                        }
                    }
                    options{
                        timeout(time: 1, unit: 'DAYS')
                    }
                    input {
                        message 'Update project documentation?'
                    }
                    steps{
                        unstash 'DOCS_ARCHIVE'
                        withCredentials([usernamePassword(credentialsId: 'dccdocs-server', passwordVariable: 'docsPassword', usernameVariable: 'docsUsername')]) {
                            sh 'python utils/upload_docs.py --username=$docsUsername --password=$docsPassword --subroute=ocr build/docs/html apache-ns.library.illinois.edu'
                        }
                    }
                    post{
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
            }
        }
    }
}
