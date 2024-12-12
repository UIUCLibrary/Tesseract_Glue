import org.jenkinsci.plugins.pipeline.modeldefinition.Utils
library identifier: 'JenkinsPythonHelperLibrary@2024.7.0', retriever: modernSCM(
  [$class: 'GitSCMSource',
   remote: 'https://github.com/UIUCLibrary/JenkinsPythonHelperLibrary.git',
   ])

SONARQUBE_CREDENTIAL_ID = 'sonarcloud_token'
SUPPORTED_MAC_VERSIONS = ['3.9', '3.10', '3.11', '3.12', '3.13']
SUPPORTED_LINUX_VERSIONS = ['3.9', '3.10', '3.11', '3.12', '3.13']
SUPPORTED_WINDOWS_VERSIONS = ['3.9', '3.10', '3.11', '3.12', '3.13']

def installCerts(cacheLocation){
    def cachedFile = "${cacheLocation}\\roots.sst".replaceAll(/\\\\+/, '\\\\')
    withEnv(["CACHED_FILE=${cachedFile}"]){
        lock("${cachedFile}-${env.NODE_NAME}"){
            powershell(
                label: 'Ensuring certs from windows update',
                script: '''if ([System.IO.File]::Exists("$Env:CACHED_FILE")){
                                Write-Host 'Found certs file'
                            } else {
                                Write-Host 'No certs file found'
                                Write-Host 'Generating new certs from Windows Update'
                                certutil -generateSSTFromWU $Env:CACHED_FILE
                            }
                   '''
                )
            powershell('certutil -addstore -f root $Env:CACHED_FILE')
        }
    }
}

def installMSVCRuntime(cacheLocation){
    def cachedFile = "${cacheLocation}\\vc_redist.x64.exe".replaceAll(/\\\\+/, '\\\\')
    withEnv(
        [
            "CACHED_FILE=${cachedFile}",
            "RUNTIME_DOWNLOAD_URL=https://aka.ms/vs/17/release/vc_redist.x64.exe"
        ]
    ){
        lock("${cachedFile}-${env.NODE_NAME}"){
            powershell(
                label: 'Ensuring vc_redist runtime installer is available',
                script: '''if ([System.IO.File]::Exists("$Env:CACHED_FILE"))
                           {
                                Write-Host 'Found installer'
                           } else {
                                Write-Host 'No installer found'
                                Write-Host 'Downloading runtime'
                                [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12;Invoke-WebRequest "$Env:RUNTIME_DOWNLOAD_URL" -OutFile "$Env:CACHED_FILE"
                           }
                        '''
            )
        }
        powershell(label: 'Install VC Runtime', script: 'Start-Process -filepath "$Env:CACHED_FILE" -ArgumentList "/install", "/passive", "/norestart" -Passthru | Wait-Process;')
    }
}

def getPypiConfig() {
    node(){
        configFileProvider([configFile(fileId: 'pypi_config', variable: 'CONFIG_FILE')]) {
            def config = readJSON( file: CONFIG_FILE)
            return config['deployment']['indexes']
        }
    }
}

wheelStashes = []

defaultParameterValues = [
    USE_SONARQUBE: false
]

def linux_wheels(){
    def selectedArches = []
    def allValidArches = ['arm64', 'x86_64']
    if(params.INCLUDE_LINUX_ARM == true){
        selectedArches << 'arm64'
    }
    if(params.INCLUDE_LINUX_X86_64 == true){
        selectedArches << 'x86_64'
    }
    parallel([failFast: true] << SUPPORTED_LINUX_VERSIONS.collectEntries{ pythonVersion ->
        [
            "Python ${pythonVersion} - Linux": {
                stage("Python ${pythonVersion} - Linux"){
                    parallel([failFast: true] << allValidArches.collectEntries{ arch ->
                        [
                            "Python ${pythonVersion} Linux ${arch} Wheel": {
                                stage("Python ${pythonVersion} Linux ${arch} Wheel"){
                                    if(selectedArches.contains(arch)){
                                        stage("Build Wheel (${pythonVersion} Linux ${arch})"){
                                            retry(3){
                                                buildPythonPkg(
                                                    agent: [
                                                        dockerfile: [
                                                            label: "linux && docker && ${arch}",
                                                            filename: 'ci/docker/linux/package/Dockerfile',
                                                            additionalBuildArgs: "--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg manylinux_image=${arch=='x86_64'? 'quay.io/pypa/manylinux2014_x86_64': 'quay.io/pypa/manylinux2014_aarch64'}"
                                                        ]
                                                    ],
                                                    buildCmd: {
                                                        sh(label: 'Building python wheel',
                                                           script:"""python -m venv venv
                                                                     trap "rm -rf venv" EXIT
                                                                     venv/bin/pip install --disable-pip-version-check uv
                                                                     UV_INDEX_STRATEGY=unsafe-best-match venv/bin/uv build --python ${pythonVersion}  --wheel "--config-setting=conan_cache=/conan/.conan"
                                                                     rm -rf venv
                                                                     auditwheel show ./dist/*.whl
                                                                     auditwheel -v repair ./dist/*.whl -w ./dist
                                                                     auditwheel show ./dist/*manylinux*.whl
                                                                     """
                                                        )
                                                    },
                                                    post:[
                                                        cleanup: {
                                                            cleanWs(
                                                                patterns: [
                                                                    [pattern: 'venv/', type: 'INCLUDE'],
                                                                    [pattern: 'dist/', type: 'INCLUDE'],
                                                                    [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                                ],
                                                                notFailBuild: true,
                                                                deleteDirs: true
                                                            )
                                                        },
                                                        success: {
                                                            stash includes: 'dist/*manylinux*.*whl', name: "python${pythonVersion} linux - ${arch} - wheel"
                                                            wheelStashes << "python${pythonVersion} linux - ${arch} - wheel"
                                                            archiveArtifacts artifacts: 'dist/*manylinux*.*whl'
                                                        }
                                                    ]
                                                )
                                            }
                                        }
                                        if(params.TEST_PACKAGES == true){
                                            stage("Test Wheel (${pythonVersion} Linux ${arch})"){
                                                retry(3){
                                                    node("docker && linux && ${arch}"){
                                                        checkout scm
                                                        unstash "python${pythonVersion} linux - ${arch} - wheel"
                                                        try{
                                                            withEnv([
                                                                'PIP_CACHE_DIR=/tmp/pipcache',
                                                                'UV_INDEX_STRATEGY=unsafe-best-match',
                                                                'UV_TOOL_DIR=/tmp/uvtools',
                                                                'UV_PYTHON_INSTALL_DIR=/tmp/uvpython',
                                                                'UV_CACHE_DIR=/tmp/uvcache',
                                                                "TOX_INSTALL_PKG=${findFiles(glob:'dist/*.whl')[0].path}",
                                                                "TOX_ENV=py${pythonVersion.replace('.', '')}"
                                                            ]){
                                                                docker.image('python').inside('--mount source=python-tmp-uiucpreson-ocr,target=/tmp'){
                                                                    sh(
                                                                        label: 'Testing with tox',
                                                                        script: '''python3 -m venv venv
                                                                                   . ./venv/bin/activate
                                                                                   trap "rm -rf venv" EXIT
                                                                                   pip install --disable-pip-version-check uv
                                                                                   uvx --with tox-uv tox
                                                                                   rm -rf .tox
                                                                                '''
                                                                    )
                                                                }
                                                            }
                                                        } finally {
                                                            sh "${tool(name: 'Default', type: 'git')} clean -dfx"
                                                            cleanWs(
                                                                patterns: [
                                                                    [pattern: '.tox/', type: 'INCLUDE'],
                                                                    [pattern: 'dist/', type: 'INCLUDE'],
                                                                    [pattern: 'venv/', type: 'INCLUDE'],
                                                                    [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                                    ]
                                                            )
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    } else {
                                        Utils.markStageSkippedForConditional("Python ${pythonVersion} Linux ${arch} Wheel")
                                    }
                                }
                            }
                        ]
                    })
                }
            }
        ]
    })
}

def windows_wheels(){
    parallel([failFast: true] << SUPPORTED_WINDOWS_VERSIONS.collectEntries{ pythonVersion ->
        [
            "Windows - Python ${pythonVersion}": {
                stage("Windows - Python ${pythonVersion}"){
                    if(params.INCLUDE_WINDOWS_X86_64 == true){
                        stage("Windows - Python ${pythonVersion} x86_64: wheel"){
                            stage("Build Wheel (${pythonVersion} Windows)"){
                                buildPythonPkg(
                                    agent: [
                                        dockerfile: [
                                            label: 'windows && docker && x86',
                                            filename: 'ci/docker/windows/tox/Dockerfile',
                                            additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE --build-arg chocolateyVersion --build-arg PIP_DOWNLOAD_CACHE=c:/users/containeradministrator/appdata/local/pip --build-arg UV_CACHE_DIR=c:/users/ContainerUser/appdata/local/uv',
                                            args: '--mount source=uv_python_install_dir,target=C:\\Users\\ContainerUser\\Documents\\uvpython'
                                        ]
                                    ],
                                    retries: 3,
                                    buildCmd: {
                                        withEnv([
                                            'UV_INDEX_STRATEGY=unsafe-best-match',
                                            'UV_PYTHON_INSTALL_DIR=C:\\Users\\ContainerUser\\Documents\\uvpython'
                                        ]){
                                            bat """py -m venv venv
                                                   venv\\Scripts\\pip install --disable-pip-version-check uv
                                                   venv\\Scripts\\uv build --python ${pythonVersion} --wheel
                                                   rmdir /S /Q venv
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
                                    node('windows && docker'){
                                        try{
                                            docker.image('python').inside('--mount source=uv_python_install_dir,target=C:\\Users\\ContainerUser\\Documents\\uvpython --mount source=msvc-runtime,target=c:\\msvc_runtime --mount source=windows-certs,target=c:\\certs'){
                                                checkout scm
                                                installMSVCRuntime('c:\\msvc_runtime\\')
                                                installCerts('c:\\certs\\')
                                                unstash "python${pythonVersion} windows wheel"
                                                withEnv([
                                                    'PIP_CACHE_DIR=C:\\Users\\ContainerUser\\Documents\\pipcache',
                                                    'UV_TOOL_DIR=C:\\Users\\ContainerUser\\Documents\\uvtools',
                                                    'UV_PYTHON_INSTALL_DIR=C:\\Users\\ContainerUser\\Documents\\uvpython',
                                                    'UV_CACHE_DIR=C:\\Users\\ContainerUser\\Documents\\uvcache',
                                                    'UV_INDEX_STRATEGY=unsafe-best-match',
                                                ]){
                                                    findFiles(glob: 'dist/*.whl').each{
                                                        bat """python -m pip install  --disable-pip-version-check uv
                                                               uvx -p ${pythonVersion} --with tox-uv tox run -e py${pythonVersion.replace('.', '')}  --installpkg ${it.path}
                                                            """
                                                    }
                                                }
                                            }
                                        } finally{
                                            bat "${tool(name: 'Default', type: 'git')} clean -dfx"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        ]
    })
}

def mac_wheels(){
    def selectedArches = []
    def allValidArches = ['arm64', 'x86_64']
    if(params.INCLUDE_MACOS_X86_64 == true){
        selectedArches << "x86_64"
    }
    if(params.INCLUDE_MACOS_ARM == true){
        selectedArches << "arm64"
    }
    parallel([failFast: true] << SUPPORTED_MAC_VERSIONS.collectEntries{ pythonVersion ->
        [
            "Python ${pythonVersion} - Mac":{
                stage("Python ${pythonVersion} - Mac"){
                    stage('Single architecture wheel'){
                        parallel([failFast: true] << allValidArches.collectEntries{arch ->
                            [
                                "Python ${pythonVersion} MacOS ${arch}": {
                                    stage("Python ${pythonVersion} MacOS ${arch}"){
                                        if(selectedArches.contains(arch)){
                                            stage("Build Wheel (${pythonVersion} ${arch}"){
                                                buildPythonPkg(
                                                    agent: [
                                                        label: "mac && python${pythonVersion} && ${arch}",
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
                                                            stash includes: 'dist/*.whl', name: "python${pythonVersion} ${arch} mac wheel"
                                                            wheelStashes << "python${pythonVersion} ${arch} mac wheel"
                                                        }
                                                    ]
                                                )
                                            }
                                            if(params.TEST_PACKAGES == true){
                                                stage("Test Wheel (${pythonVersion} MacOS ${arch})"){
                                                    testPythonPkg(
                                                        agent: [
                                                            label: "mac && python${pythonVersion} && ${arch}",
                                                        ],
                                                        testSetup: {
                                                            checkout scm
                                                            unstash "python${pythonVersion} ${arch} mac wheel"
                                                        },
                                                        testCommand: {
                                                            withEnv(['UV_INDEX_STRATEGY=unsafe-best-match']){
                                                                findFiles(glob: 'dist/*.whl').each{
                                                                    sh(label: 'Running Tox',
                                                                       script: """python${pythonVersion} -m venv venv
                                                                                  trap "rm -rf venv" EXIT
                                                                                  ./venv/bin/pip install --disable-pip-version-check uv
                                                                                  trap "rm -rf venv && rm -rf .tox" EXIT
                                                                                  ./venv/bin/uvx --python ${pythonVersion} --with-requirements requirements-dev.txt --with tox-uv tox --installpkg ${it.path} -e py${pythonVersion.replace('.', '')}
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
                                        } else {
                                            Utils.markStageSkippedForConditional("Python ${pythonVersion} MacOS ${arch}")
                                        }
                                    }
                                }
                            ]}
                        )
                    }
                    if(params.INCLUDE_MACOS_X86_64 && params.INCLUDE_MACOS_ARM){
                        stage("Universal2 Wheel: Python ${pythonVersion}"){
                            stage('Make Universal2 wheel'){
                                node("mac && python${pythonVersion}") {
                                    checkout scm
                                    unstash "python${pythonVersion} arm64 mac wheel"
                                    unstash "python${pythonVersion} x86_64 mac wheel"
                                    def wheelNames = []
                                    findFiles(excludes: '', glob: 'dist/*.whl').each{wheelFile ->
                                        wheelNames.add(wheelFile.path)
                                    }
                                    try{
                                        sh(label: 'Make Universal2 wheel',
                                           script: """python3 -m venv venv
                                                      trap "rm -rf venv" EXIT
                                                      ./venv/bin/pip install --disable-pip-version-check uv
                                                      mkdir -p out
                                                      ./venv/bin/uvx --python ${pythonVersion} --index-strategy unsafe-best-match --with-requirements requirements-dev.txt --from delocate delocate-merge  ${wheelNames.join(' ')} --verbose -w ./out/
                                                      rm dist/*.whl
                                                   """
                                           )
                                       def fusedWheel = findFiles(excludes: '', glob: 'out/*.whl')[0]
                                       def pythonVersionShort = pythonVersion.replace('.','')
                                       def props = readTOML( file: 'pyproject.toml')['project']
                                       def universalWheel = "uiucprescon.ocr-${props.version}-cp${pythonVersionShort}-cp${pythonVersionShort}-macosx_11_0_universal2.whl"
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
                                    parallel(selectedArches.collectEntries{arch ->
                                        [
                                            "Test Python ${pythonVersion} universal2 Wheel on ${arch} mac": {
                                                stage("Test Python ${pythonVersion} universal2 Wheel on ${arch} mac"){
                                                    testPythonPkg(
                                                        agent: [
                                                            label: "mac && python${pythonVersion} && ${arch}",
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
                                                                                  trap "rm -rf venv" EXIT
                                                                                  ./venv/bin/python -m pip install --disable-pip-version-check uv
                                                                                  trap "rm -rf venv && rm -rf .tox" EXIT
                                                                                  CONAN_REVISIONS_ENABLED=1 ./venv/bin/uvx --with-requirements requirements-dev.txt --with tox-uv tox --installpkg ${it.path} -e py${pythonVersion.replace('.', '')}
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
                                        ]
                                    })
                                }
                            }
                        }
                    }
                }
            }
        ]
    })
}
def get_sonarqube_unresolved_issues(report_task_file){
    script{

        def props = readProperties  file: '.scannerwork/report-task.txt'
        def response = httpRequest url : props['serverUrl'] + "/api/issues/search?componentKeys=" + props['projectKey'] + "&resolved=no"
        def outstandingIssues = readJSON text: response.content
        return outstandingIssues
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
        ]
    )
}
stage('Pipeline Pre-tasks'){
    startup()
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
                stage('Building and Testing') {
                    agent {
                        dockerfile {
                            filename 'ci/docker/linux/jenkins/Dockerfile'
                            label 'linux && docker && x86'
                            additionalBuildArgs '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg PIP_DOWNLOAD_CACHE=/.cache/pip --build-arg UV_CACHE_DIR=/.cache/uv'
                            args '--mount source=sonar-cache-ocr,target=/opt/sonar/.sonar/cache'
                        }
                    }
                    stages{
                        stage('Setup'){
                            stages{
                                stage('Setup Testing Environment'){
                                    steps{
                                        sh(
                                            label: 'Create virtual environment',
                                            script: '''python3 -m venv bootstrap_uv
                                                       bootstrap_uv/bin/pip install uv
                                                       bootstrap_uv/bin/uv venv venv
                                                       . ./venv/bin/activate
                                                       bootstrap_uv/bin/uv pip install --index-strategy unsafe-best-match uv
                                                       rm -rf bootstrap_uv
                                                       uv pip install --index-strategy unsafe-best-match -r requirements-dev.txt
                                                       '''
                                       )
                                    }
                                }
                                stage('Installing project as editable module'){
                                    steps{
                                        timeout(10){
                                            sh(
                                                label: 'Build python package',
                                                script: '''mkdir -p build/python
                                                           mkdir -p logs
                                                           mkdir -p reports
                                                           . ./venv/bin/activate
                                                           CFLAGS="--coverage -fprofile-arcs -ftest-coverage" LFLAGS="-lgcov --coverage" build-wrapper-linux --out-dir build/build_wrapper_output_directory uv pip install --index-strategy unsafe-best-match --verbose -e .
                                                           '''
                                            )
                                        }
                                    }
                                }
                            }
                        }
                        stage('Building Documentation'){
                            steps{
                                timeout(3){
                                    sh '''mkdir -p logs
                                          . ./venv/bin/activate
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
                                        def props = readTOML( file: 'pyproject.toml')['project']
                                        zip archive: true, dir: 'build/docs/html', glob: '', zipFile: "dist/${props.name}-${props.version}.doc.zip"
                                    }
                                    stash includes: 'dist/*.doc.zip,build/docs/html/**', name: 'DOCS_ARCHIVE'
                                }
                            }
                        }
                        stage('Checks'){
                            when{
                                equals expected: true, actual: params.RUN_CHECKS
                                beforeAgent true
                            }
                            stages{
                                stage('Setting Up C++ Tests'){
                                    steps{
                                        sh(
                                            label: 'Building C++ project for metrics',
                                            script: '''. ./venv/bin/activate
                                                       conan install . -if build/cpp -g cmake_find_package
                                                       cmake -B ./build/cpp -S ./ -DCMAKE_EXPORT_COMPILE_COMMANDS:BOOL=ON -D CMAKE_C_FLAGS="-Wall -Wextra -fprofile-arcs -ftest-coverage" -D CMAKE_CXX_FLAGS="-Wall -Wextra -fprofile-arcs -ftest-coverage" -DBUILD_TESTING:BOOL=ON -D CMAKE_BUILD_TYPE=Debug -DCMAKE_CXX_OUTPUT_EXTENSION_REPLACE:BOOL=ON -DCMAKE_MODULE_PATH=./build/cpp
                                                       make -C build/cpp clean tester
                                                       '''
                                        )
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
                                                                   . ./venv/bin/activate
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
                                                    sh '''. ./venv/bin/activate
                                                          python -m sphinx -b doctest docs/source build/docs -d build/docs/doctrees -w logs/doctest_warnings.log
                                                       '''
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
                                                    script: '''. ./venv/bin/activate
                                                               cd build/cpp && ctest --output-on-failure --no-compress-output -T Test
                                                            ''',
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
                                                            script: '''. ./venv/bin/activate
                                                                       flake8 uiucprescon --tee --output-file logs/flake8.log
                                                                    '''
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
                                                    script: '''. ./venv/bin/activate
                                                               stubgen uiucprescon -o mypy_stubs
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
                                                                   . ./venv/bin/activate
                                                                   pylint uiucprescon -r n --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}" --persistent=no > reports/pylint.txt
                                                                '''

                                                    )
                                                }
                                                sh(
                                                    label: 'Running pylint for sonarqube',
                                                    script: '''. ./venv/bin/activate
                                                               pylint  -r n --msg-template="{path}:{module}:{line}: [{msg_id}({symbol}), {obj}] {msg}" --persistent=no > reports/pylint_issues.txt
                                                            ''',
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
                                                          . ./venv/bin/activate
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
                                    environment{
                                        UV_INDEX_STRATEGY='unsafe-best-match'
                                        SONAR_SCANNER_HOME='/tmp/sonar'
                                        UV_TOOL_DIR='/tmp/uvtools'
                                        UV_PYTHON_INSTALL_DIR='/tmp/uvpython'
                                        UV_CACHE_DIR='/tmp/uvcache'
                                    }
                                    steps{
                                        milestone 1
                                        script{
                                            def props = readTOML( file: 'pyproject.toml')['project']
                                            withSonarQubeEnv(installationName:'sonarcloud', credentialsId: SONARQUBE_CREDENTIAL_ID) {
                                                if (env.CHANGE_ID){
                                                    sh(
                                                        label: 'Running Sonar Scanner',
                                                        script: """python3 -m venv uv
                                                                  uv/bin/pip install --disable-pip-version-check uv
                                                                  trap "rm -rf uv" EXIT
                                                                  uv/bin/uv venv venv
                                                                  trap "rm -rf uv && rm -rf venv" EXIT
                                                                  . ./venv/bin/activate
                                                                  uv/bin/uv pip install uv
                                                                  uv tool run pysonar-scanner -Dsonar.projectVersion=${props.version} -Dsonar.buildString=\"${env.BUILD_TAG}\" -Dsonar.pullrequest.key=${env.CHANGE_ID} -Dsonar.pullrequest.base=${env.CHANGE_TARGET} -Dsonar.cfamily.cache.enabled=false -Dsonar.cfamily.threads=\$(grep -c ^processor /proc/cpuinfo) -Dsonar.cfamily.build-wrapper-output=build/build_wrapper_output_directory
                                                                  """
                                                    )
                                                } else {
                                                    sh(
                                                        label: 'Running Sonar Scanner',
                                                        script: """python3 -m venv uv
                                                                   uv/bin/pip install --disable-pip-version-check uv
                                                                   uv/bin/uv venv venv
                                                                   . ./venv/bin/activate
                                                                   uv/bin/uv pip install uv
                                                                   uv tool run pysonar-scanner -Dsonar.projectVersion=${props.version} -Dsonar.buildString=\"${env.BUILD_TAG}\" -Dsonar.branch.name=${env.BRANCH_NAME} -Dsonar.cfamily.cache.enabled=false -Dsonar.cfamily.threads=\$(grep -c ^processor /proc/cpuinfo) -Dsonar.cfamily.build-wrapper-output=build/build_wrapper_output_directory
                                                               """
                                                   )
                                                }
                                            }
                                            timeout(time: 1, unit: 'HOURS') {
                                                 def sonarqube_result = waitForQualityGate(abortPipeline: false)
                                                 if (sonarqube_result.status != 'OK') {
                                                     unstable "SonarQube quality gate: ${sonarqube_result.status}"
                                                 }
                                                 def outstandingIssues = get_sonarqube_unresolved_issues('.scannerwork/report-task.txt')
                                                 writeJSON file: 'reports/sonar-report.json', json: outstandingIssues
                                            }
                                        }
                                    }
                                    post {
                                        always{
                                           recordIssues(tools: [sonarQube(pattern: 'reports/sonar-report.json')])
                                        }
                                    }
                                }
                            }
                        }
                    }
                    post{
                        cleanup{
                            cleanWs(
                                patterns: [
                                        [pattern: 'venv/', type: 'INCLUDE'],
                                        [pattern: 'build/', type: 'INCLUDE'],
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
                    parallel{
                        stage('Linux'){
                            environment{
                                PIP_CACHE_DIR='/tmp/pipcache'
                                UV_INDEX_STRATEGY='unsafe-best-match'
                                UV_TOOL_DIR='/tmp/uvtools'
                                UV_PYTHON_INSTALL_DIR='/tmp/uvpython'
                                UV_CACHE_DIR='/tmp/uvcache'
                            }
                            when{
                                expression {return nodesByLabel('linux && docker').size() > 0}
                            }
                            steps{
                                script{
                                    def envs = []
                                    node('docker && linux'){
                                        try{
                                            docker.image('python').inside('--mount source=python-tmp-uiucpreson-ocr,target=/tmp'){
                                                checkout scm
                                                sh(script: 'python3 -m venv venv && venv/bin/pip install --disable-pip-version-check uv')
                                                envs = sh(
                                                    label: 'Get tox environments',
                                                    script: './venv/bin/uvx --quiet --with tox-uv tox list -d --no-desc',
                                                    returnStdout: true,
                                                ).trim().split('\n')
                                            }
                                        } finally{
                                            sh "${tool(name: 'Default', type: 'git')} clean -dfx"
                                            cleanWs(
                                                patterns: [
                                                    [pattern: 'venv/', type: 'INCLUDE'],
                                                    [pattern: '.tox', type: 'INCLUDE'],
                                                    [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                ]
                                            )
                                        }
                                    }
                                    parallel(
                                        envs.collectEntries{toxEnv ->
                                            def version = toxEnv.replaceAll(/py(\d)(\d+)/, '$1.$2')
                                            [
                                                "Tox Environment: ${toxEnv}",
                                                {
                                                    node('docker && linux'){
                                                        checkout scm
                                                        def image
                                                        lock("${env.JOB_NAME} - ${env.NODE_NAME}"){
                                                            image = docker.build(UUID.randomUUID().toString(), '-f ci/docker/linux/tox/Dockerfile --build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg PIP_DOWNLOAD_CACHE=/.cache/pip --build-arg UV_CACHE_DIR=/.cache/uv .')
                                                        }
                                                        try{
                                                            image.inside('--mount source=python-tmp-uiucpreson-ocr,target=/tmp'){
                                                                retry(3){
                                                                    sh( label: 'Running Tox',
                                                                        script: """python3 -m venv venv && venv/bin/pip install --disable-pip-version-check uv
                                                                                   venv/bin/uvx --python ${version} --python-preference system --with tox-uv tox run -e ${toxEnv} -vvv
                                                                                """
                                                                        )
                                                                }
                                                            }
                                                        } finally {
                                                            sh "docker rmi ${image.id}"
                                                            sh "${tool(name: 'Default', type: 'git')} clean -dfx"
                                                            cleanWs(
                                                                patterns: [
                                                                    [pattern: 'venv/', type: 'INCLUDE'],
                                                                    [pattern: '.tox', type: 'INCLUDE'],
                                                                    [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                                ]
                                                            )
                                                        }
                                                    }
                                                }
                                            ]
                                        }
                                    )
                                }
                            }
                        }
                        stage('Windows'){
                             when{
                                 expression {return nodesByLabel('windows && docker && x86').size() > 0}
                             }
                             environment{
                                 UV_INDEX_STRATEGY='unsafe-best-match'
                                 PIP_CACHE_DIR='C:\\Users\\ContainerUser\\Documents\\pipcache'
                                 UV_TOOL_DIR='C:\\Users\\ContainerUser\\Documents\\uvtools'
                                 UV_PYTHON_INSTALL_DIR='C:\\Users\\ContainerUser\\Documents\\uvpython'
                                 UV_CACHE_DIR='C:\\Users\\ContainerUser\\Documents\\uvcache'
                             }
                             steps{
                                 script{
                                     def envs = []
                                     node('docker && windows'){
                                         try{
                                            docker.image('python').inside("--mount source=uv_python_install_dir,target=${env.UV_PYTHON_INSTALL_DIR}"){
                                                 checkout scm
                                                 bat(script: 'python -m venv venv && venv\\Scripts\\pip install --disable-pip-version-check uv')
                                                 envs = bat(
                                                     label: 'Get tox environments',
                                                     script: '@.\\venv\\Scripts\\uvx --quiet --with-requirements requirements-dev.txt --with tox-uv tox list -d --no-desc',
                                                     returnStdout: true,
                                                 ).trim().split('\r\n')
                                            }
                                         } finally{
                                             bat "${tool(name: 'Default', type: 'git')} clean -dfx"
                                             cleanWs(
                                                 patterns: [
                                                     [pattern: 'venv/', type: 'INCLUDE'],
                                                     [pattern: '.tox', type: 'INCLUDE'],
                                                     [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                 ]
                                             )
                                         }
                                     }
                                     parallel(
                                         envs.collectEntries{toxEnv ->
                                             def version = toxEnv.replaceAll(/py(\d)(\d+)/, '$1.$2')
                                             [
                                                 "Tox Environment: ${toxEnv}",
                                                 {
                                                     node('docker && windows'){
                                                        def image
                                                        checkout scm
                                                        lock("${env.JOB_NAME} - ${env.NODE_NAME}"){
                                                            image = docker.build(UUID.randomUUID().toString(), '-f ci/docker/windows/tox/Dockerfile --build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE --build-arg chocolateyVersion .')
                                                        }
                                                        try{
                                                            image.inside("--mount source=uv_python_install_dir,target=${env.UV_PYTHON_INSTALL_DIR}"){
                                                                retry(3){
                                                                    bat(label: 'Running Tox',
                                                                         script: """python -m venv venv && venv\\Scripts\\pip install --disable-pip-version-check uv
                                                                                call venv\\Scripts\\activate.bat
                                                                                uv python install cpython-${version}
                                                                                uvx -p ${version} --with-requirements requirements-dev.txt --with tox-uv tox run -e ${toxEnv}
                                                                             """
                                                                    )
                                                                }
                                                            }
                                                        } finally {
                                                            bat "docker rmi --no-prune ${image.id}"
                                                            bat "${tool(name: 'Default', type: 'git')} clean -dfx"
                                                            cleanWs(
                                                                patterns: [
                                                                    [pattern: 'venv/', type: 'INCLUDE'],
                                                                    [pattern: '.tox', type: 'INCLUDE'],
                                                                    [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                                ]
                                                            )
                                                        }
                                                     }
                                                 }
                                             ]
                                         }
                                     )
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
                                    image 'python'
                                    label 'docker && linux'
                                    args '--mount source=python-tmp-uiucpreson-ocr,target=/tmp'
                                }
                            }
                            options {
                                retry(3)
                            }
                            environment{
                                PIP_CACHE_DIR='/tmp/pipcache'
                                UV_INDEX_STRATEGY='unsafe-best-match'
                                UV_CACHE_DIR='/tmp/uvcache'
                            }
                            steps{
                                sh(label: 'Building sdist',
                                   script: '''python -m venv venv
                                              trap "rm -rf venv" EXIT
                                              venv/bin/pip install --disable-pip-version-check uv
                                              venv/bin/uv build --sdist
                                              '''
                                )
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
                                    testSdistStages << SUPPORTED_MAC_VERSIONS.collectEntries{ pythonVersion ->
                                        def selectedArches = []
                                        def allValidArches = ["x86_64", "arm64"]
                                        if(params.INCLUDE_MACOS_X86_64 == true){
                                            selectedArches << "x86_64"
                                        }
                                        if(params.INCLUDE_MACOS_ARM == true){
                                            selectedArches << "arm64"
                                        }
                                        return allValidArches.collectEntries{ arch ->
                                            def newStageName = "Test sdist (MacOS ${arch} - Python ${pythonVersion})"
                                            return [
                                                "${newStageName}": {
                                                    if(selectedArches.contains(arch)){
                                                        stage(newStageName){
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
                                                                               script: """python3 -m venv venv
                                                                                          trap "rm -rf venv" EXIT
                                                                                          venv/bin/pip install  --disable-pip-version-check uv
                                                                                          trap "rm -rf venv && rm -rf .tox" EXIT
                                                                                          venv/bin/uvx --python ${pythonVersion} --with-requirements requirements-dev.txt --with tox-uv tox --installpkg ${it.path} -e py${pythonVersion.replace('.', '')}
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
                                                                ]
                                                            )
                                                        }
                                                    } else {
                                                        Utils.markStageSkippedForConditional(newStageName)
                                                    }
                                                }
                                            ]
                                        }
                                    }
                                    testSdistStages << SUPPORTED_WINDOWS_VERSIONS.collectEntries{ pythonVersion ->
                                        def selectedArches = []
                                        def allValidArches = ["x86_64"]
                                        if(params.INCLUDE_WINDOWS_X86_64 == true){
                                            selectedArches << "x86_64"
                                        }
                                        return allValidArches.collectEntries{ arch ->
                                            def newStageName = "Test sdist (Windows x86_64 - Python ${pythonVersion})"
                                            return [
                                                "${newStageName}": {
                                                    if(selectedArches.contains(arch)){
                                                        stage(newStageName){
                                                            retry(2){
                                                                testPythonPkg(
                                                                    agent: [
                                                                        dockerfile: [
                                                                            label: 'windows && docker && x86',
                                                                            filename: 'ci/docker/windows/tox/Dockerfile',
                                                                            additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE --build-arg chocolateyVersion --build-arg PIP_DOWNLOAD_CACHE=c:/users/containeradministrator/appdata/local/pip --build-arg UV_CACHE_DIR=c:/users/ContainerUser/appdata/local/uv',
                                                                            dockerImageName: "${currentBuild.fullProjectName}_test_with_msvc".replaceAll('-', '_').replaceAll('/', '_').replaceAll(' ', "").toLowerCase(),
                                                                        ]
                                                                    ],
                                                                    testSetup: {
                                                                        checkout scm
                                                                        unstash 'python sdist'
                                                                    },
                                                                    testCommand: {
                                                                        findFiles(glob: 'dist/*.tar.gz').each{
                                                                            bat(
                                                                                label: 'Running Tox',
                                                                                script: """py -m venv venv
                                                                                           venv\\Scripts\\pip install --disable-pip-version-check uv
                                                                                           venv\\Scripts\\uvx --python ${pythonVersion} --with-requirements requirements-dev.txt --with tox-uv tox --workdir %TEMP%\\tox --installpkg ${it.path} -e py${pythonVersion.replace('.', '')} -v
                                                                                           rmdir /S /Q venv
                                                                                           """
                                                                            )
                                                                        }
                                                                    },
                                                                    post:[
                                                                        cleanup: {
                                                                            cleanWs(
                                                                                patterns: [
                                                                                    [pattern: 'venv/', type: 'INCLUDE'],
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
                                                    } else {
                                                        Utils.markStageSkippedForConditional(newStageName)
                                                    }
                                                }
                                            ]
                                        }
                                    }
                                    testSdistStages << SUPPORTED_LINUX_VERSIONS.collectEntries{ pythonVersion ->
                                        def selectedArches = []
                                        def allValidArches = ["x86_64", "arm64"]
                                        if(params.INCLUDE_LINUX_X86_64 == true){
                                            selectedArches << "x86_64"
                                        }
                                        if(params.INCLUDE_LINUX_ARM == true){
                                            selectedArches << "arm64"
                                        }
                                        return allValidArches.collectEntries{ arch ->
                                            def newStageName = "Test sdist (Linux ${arch} - Python ${pythonVersion})"
                                            return [
                                                "${newStageName}": {
                                                    if(selectedArches.contains(arch)){
                                                        stage(newStageName){
                                                            testPythonPkg(
                                                                agent: [
                                                                    dockerfile: [
                                                                        label: "linux && docker && ${arch}",
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
                                                                    withEnv([
                                                                        'PIP_CACHE_DIR=/tmp/pipcache',
                                                                        'UV_INDEX_STRATEGY=unsafe-best-match',
                                                                        'UV_TOOL_DIR=/tmp/uvtools',
                                                                        'UV_PYTHON_INSTALL_DIR=/tmp/uvpython',
                                                                        'UV_CACHE_DIR=/tmp/uvcache',
                                                                    ]){
                                                                        findFiles(glob: 'dist/*.tar.gz').each{
                                                                            sh(
                                                                                label: 'Running Tox',
                                                                                script: """python3 -m venv venv
                                                                                           trap "rm -rf venv" EXIT
                                                                                           ./venv/bin/pip install --disable-pip-version-check uv
                                                                                           trap "rm -rf venv && rm -rf .tox" EXIT
                                                                                           ./venv/bin/uvx --python ${pythonVersion} --with-requirements requirements-dev.txt --with tox-uv tox --installpkg ${it.path} -e py${pythonVersion.replace('.', '')}
                                                                                        """
                                                                                )
                                                                        }
                                                                    }
                                                                },
                                                                post:[
                                                                    cleanup: {
                                                                        cleanWs(
                                                                            patterns: [
                                                                                    [pattern: '.tox/', type: 'INCLUDE'],
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
                                                     } else {
                                                         Utils.markStageSkippedForConditional(newStageName)
                                                     }
                                                }
                                            ]
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
                    environment{
                        PIP_CACHE_DIR='/tmp/pipcache'
                        UV_INDEX_STRATEGY='unsafe-best-match'
                        UV_TOOL_DIR='/tmp/uvtools'
                        UV_PYTHON_INSTALL_DIR='/tmp/uvpython'
                        UV_CACHE_DIR='/tmp/uvcache'
                    }
                    agent {
                        docker{
                            image 'python'
                            label 'docker && linux'
                            args '--mount source=python-tmp-uiucpreson-ocr,target=/tmp'
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
                         withEnv(
                            [
                                "TWINE_REPOSITORY_URL=${SERVER_URL}",
                                'UV_INDEX_STRATEGY=unsafe-best-match'
                            ]
                        ){
                            withCredentials(
                                [
                                    usernamePassword(
                                        credentialsId: 'jenkins-nexus',
                                        passwordVariable: 'TWINE_PASSWORD',
                                        usernameVariable: 'TWINE_USERNAME'
                                    )
                                ]){
                                    sh(
                                        label: 'Uploading to pypi',
                                        script: '''python3 -m venv venv
                                                   trap "rm -rf venv" EXIT
                                                   . ./venv/bin/activate
                                                   pip install --disable-pip-version-check uv
                                                   uvx --with-requirements=requirements-dev.txt twine upload --disable-progress-bar --non-interactive dist/*
                                                '''
                                    )
                            }
                        }
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
