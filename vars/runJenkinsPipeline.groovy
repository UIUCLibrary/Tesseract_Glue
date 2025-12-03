import org.jenkinsci.plugins.pipeline.modeldefinition.Utils
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


def linux_wheels(pythonVersions, testPackages, params, wheelStashes){
    def selectedArches = []
    def allValidArches = ['arm64', 'x86_64']
    if(params.INCLUDE_LINUX_ARM == true){
        selectedArches << 'arm64'
    }
    if(params.INCLUDE_LINUX_X86_64 == true){
        selectedArches << 'x86_64'
    }
    parallel([failFast: true] << pythonVersions.collectEntries{ pythonVersion ->
        def newVersionStage = "Python ${pythonVersion} - Linux"
        def retryTimes = 3
        return [
            "${newVersionStage}": {
                stage(newVersionStage){
                    parallel([failFast: true] << allValidArches.collectEntries{ arch ->
                        def newStage = "Python ${pythonVersion} Linux ${arch} Wheel"
                        return [
                            "${newStage}": {
                                stage(newStage){
                                    if(selectedArches.contains(arch)){
                                        withEnv([
                                            'PIP_CACHE_DIR=/tmp/pipcache',
                                            'UV_TOOL_DIR=/tmp/uvtools',
                                            'UV_PYTHON_INSTALL_DIR=/tmp/uvpython',
                                            'UV_CACHE_DIR=/tmp/uvcache',
                                        ]){
                                            stage("Build Wheel (${pythonVersion} Linux ${arch})"){
                                                node("linux && docker && ${arch}"){
                                                    def dockerImageName = "${currentBuild.fullProjectName}_${UUID.randomUUID().toString()}".replaceAll("-", "_").replaceAll('/', "_").replaceAll(' ', "").toLowerCase()
                                                    try{
                                                        retry(retryTimes){
                                                            try{
                                                                checkout scm
                                                                sh(label:'Build Linux Wheel', script: "scripts/build_linux_wheels.sh --python-version ${pythonVersion} --docker-image-name ${dockerImageName}")
                                                                stash includes: 'dist/*manylinux*.*whl', name: "python${pythonVersion} linux - ${arch} - wheel"
                                                                wheelStashes << "python${pythonVersion} linux - ${arch} - wheel"
                                                                archiveArtifacts artifacts: 'dist/*manylinux*.*whl'
                                                            } finally{
                                                                sh "${tool(name: 'Default', type: 'git')} clean -dfx"
                                                            }
                                                        }
                                                    } finally {
                                                        sh "docker rmi --force --no-prune ${dockerImageName}"
                                                    }
                                                }
                                            }
                                            def testWheelStageName = "Test Wheel (${pythonVersion} Linux ${arch})"
                                            stage(testWheelStageName){
                                                if(testPackages == true){
                                                    retry(retryTimes){
                                                        node("docker && linux && ${arch}"){
                                                            checkout scm
                                                            unstash "python${pythonVersion} linux - ${arch} - wheel"
                                                            try{
                                                                withEnv([
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
                                                                                       uv run --only-group tox --with tox-uv tox
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
                                                } else {
                                                    Utils.markStageSkippedForConditional(testWheelStageName)
                                                }
                                            }
                                        }
                                    } else {
                                        Utils.markStageSkippedForConditional(newStage)
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

def windows_wheels(pythonVersions, testPackages, params, wheelStashes){
    parallel([failFast: true] << pythonVersions.collectEntries{ pythonVersion ->
        [
            "Windows - Python ${pythonVersion}": {
                withEnv([
                    'PIP_CACHE_DIR=C:\\Users\\ContainerUser\\Documents\\cache\\pipcache',
                    'UV_TOOL_DIR=C:\\Users\\ContainerUser\\Documents\\cache\\uvtools',
                    'UV_PYTHON_INSTALL_DIR=C:\\Users\\ContainerUser\\Documents\\cache\\uvpython',
                    'UV_CACHE_DIR=C:\\Users\\ContainerUser\\Documents\\cache\\uvcache',
                ]){
                    stage("Windows - Python ${pythonVersion}"){
                        if(params.INCLUDE_WINDOWS_X86_64 == true){
                            stage("Windows - Python ${pythonVersion} x86_64: wheel"){
                                stage("Build Wheel (${pythonVersion} Windows)"){
                                    node('windows && docker && x86_64'){
                                        def retryTimes = 3
                                        def dockerImageName = "${currentBuild.fullProjectName}_${UUID.randomUUID().toString()}".replaceAll("-", '_').replaceAll('/', '_').replaceAll(' ', "").toLowerCase()
                                        try{
                                            retry(retryTimes){
                                                checkout scm
                                                try{
                                                    powershell(label: 'Building Wheel for Windows', script: "scripts/build_windows.ps1 -PythonVersion ${pythonVersion} -DockerImageName ${dockerImageName} -UVCacheDirPathInContainer \$ENV:UV_CACHE_DIR -PIPDowndloadCachePathInContainer \$ENV:PIP_CACHE_DIR -UVPythonInstallDirPathInContainer \$Env:UV_PYTHON_INSTALL_DIR -UVToolDirPathInContainer \$Env:UV_TOOL_DIR")
                                                    stash includes: 'dist/*.whl', name: "python${pythonVersion} windows wheel"
                                                    wheelStashes << "python${pythonVersion} windows wheel"
                                                } catch (e){
                                                    powershell('Get-ChildItem Env:')
                                                    raise e
                                                } finally {
                                                    bat "${tool(name: 'Default', type: 'git')} clean -dfx"
                                                }
                                            }
                                        } finally {
                                            powershell(
                                                label: 'Untagging Docker Image used',
                                                script: "docker image rm --no-prune ${dockerImageName}",
                                                returnStatus: true
                                            )
                                        }
                                    }
                                }
                                if(testPackages == true){
                                    stage("Test Wheel (${pythonVersion} Windows x86_64)"){
                                        node('windows && docker'){
                                            try{
                                                checkout scm
                                                docker.image(env.DEFAULT_PYTHON_DOCKER_IMAGE ? env.DEFAULT_PYTHON_DOCKER_IMAGE: 'python')
                                                    .inside(
                                                        '--mount source=uv_python_install_dir,target=C:\\Users\\ContainerUser\\Documents\\cache\\uvpython ' +
                                                        '--mount source=pipcache,target=C:\\Users\\ContainerUser\\Documents\\cache\\pipcache ' +
                                                        '--mount source=uv_cache_dir,target=C:\\Users\\ContainerUser\\Documents\\cache\\uvcache ' +
                                                        '--mount source=msvc-runtime,target=c:\\msvc_runtime --mount source=windows-certs,target=c:\\certs'
                                                    )
                                                {
                                                    installMSVCRuntime('c:\\msvc_runtime\\')
                                                    installCerts('c:\\certs\\')
                                                    unstash "python${pythonVersion} windows wheel"
                                                    findFiles(glob: 'dist/*.whl').each{
                                                        bat """python -m pip install  --disable-pip-version-check uv
                                                               uv run --only-group tox -p ${pythonVersion} --with tox-uv tox run -e py${pythonVersion.replace('.', '')}  --installpkg ${it.path}
                                                            """
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
            }
        ]
    })
}

def mac_wheels(pythonVersions, testPackages, params, wheelStashes){
    def selectedArches = []
    def allValidArches = ['arm64', 'x86_64']
    if(params.INCLUDE_MACOS_X86_64 == true){
        selectedArches << 'x86_64'
    }
    if(params.INCLUDE_MACOS_ARM == true){
        selectedArches << 'arm64'
    }
    parallel([failFast: true] << pythonVersions.collectEntries{ pythonVersion ->
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
                                                           script: "scripts/build_mac_wheel.sh . --python-version=${pythonVersion}"
                                                        )
                                                    },
                                                    post:[
                                                        cleanup: {
                                                            sh "${tool(name: 'Default', type: 'git')} clean -dfx"
                                                        },
                                                        success: {
                                                            stash includes: 'dist/*.whl', name: "python${pythonVersion} ${arch} mac wheel"
                                                            wheelStashes << "python${pythonVersion} ${arch} mac wheel"
                                                        }
                                                    ]
                                                )
                                            }
                                            if(testPackages == true){
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
                                                            findFiles(glob: 'dist/*.whl').each{
                                                                sh(label: 'Running Tox',
                                                                   script: """python${pythonVersion} -m venv venv
                                                                              trap "rm -rf venv" EXIT
                                                                              ./venv/bin/pip install --disable-pip-version-check uv
                                                                              trap "rm -rf venv && rm -rf .tox" EXIT
                                                                              ./venv/bin/uv run --only-group tox --python ${pythonVersion} --with tox-uv tox run --installpkg ${it.path} -e py${pythonVersion.replace('.', '')}
                                                                           """
                                                                )
                                                            }
                                                        },
                                                        post:[
                                                            cleanup: {
                                                                sh "${tool(name: 'Default', type: 'git')} clean -dfx"
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
                                                      ./venv/bin/uv run --only-group package --python ${pythonVersion} delocate-merge  ${wheelNames.join(' ')} --verbose -w ./out/
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
                                                            findFiles(glob: 'dist/*.whl').each{
                                                                sh(label: 'Running Tox',
                                                                   script: """python${pythonVersion} -m venv venv
                                                                              trap "rm -rf venv" EXIT
                                                                              ./venv/bin/python -m pip install --disable-pip-version-check uv
                                                                              trap "rm -rf venv && rm -rf .tox" EXIT
                                                                              CONAN_REVISIONS_ENABLED=1 ./venv/bin/uv run --only-group tox --with tox-uv tox --installpkg ${it.path} -e py${pythonVersion.replace('.', '')}
                                                                           """
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
        if(! fileExists(report_task_file)){
            error "Could not find ${report_task_file}"
        }
        def props = readProperties  file: report_task_file
        if(! props['serverUrl'] || ! props['projectKey']){
            error "Could not find serverUrl or projectKey in ${report_task_file}"
        }
        def response = httpRequest url : props['serverUrl'] + '/api/issues/search?componentKeys=' + props['projectKey'] + '&resolved=no'
        def outstandingIssues = readJSON text: response.content
        return outstandingIssues
    }
}


def startup(sonarCredentialId, defaultParameterValues){
    parallel(
        [
            failFast: true,
            'Checking sonarqube Settings': {
                stage('Checking sonarqube Settings'){
                    node(){
                        try{
                            withCredentials([string(credentialsId: sonarCredentialId, variable: 'dddd')]) {
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
    startup(SONARQUBE_CREDENTIAL_ID, DEFAULT_PARAMETER_VALUES)
}
def call(){
    library identifier: 'JenkinsPythonHelperLibrary@2024.7.0', retriever: modernSCM(
      [$class: 'GitSCMSource',
       remote: 'https://github.com/UIUCLibrary/JenkinsPythonHelperLibrary.git',
       ])
    def wheelStashes = []
    def SONARQUBE_CREDENTIAL_ID = 'sonarcloud_token'
    def SUPPORTED_MAC_VERSIONS = ['3.10', '3.11', '3.12', '3.13', '3.14', '3.14t']
    def SUPPORTED_LINUX_VERSIONS = ['3.10', '3.11', '3.12', '3.13', '3.14', '3.14t']
    def SUPPORTED_WINDOWS_VERSIONS = ['3.10', '3.11', '3.12', '3.13', '3.14', '3.14t']

    def DEFAULT_PARAMETER_VALUES = [
        USE_SONARQUBE: true
    ]
    pipeline {
        agent none
        options {
            timeout(time: 1, unit: 'DAYS')
        }
        parameters {
            booleanParam(name: 'RUN_CHECKS', defaultValue: true, description: 'Run checks on code')
            booleanParam(name: 'TEST_RUN_TOX', defaultValue: false, description: 'Run Tox Tests')
            booleanParam(name: 'USE_SONARQUBE', defaultValue: true, description: 'Send data test data to SonarQube')
            credentials(name: 'SONARCLOUD_TOKEN', credentialType: 'org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl', defaultValue: 'sonarcloud_token', required: false)
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
                        environment{
                            PIP_CACHE_DIR='/tmp/pipcache'
                            UV_TOOL_DIR='/tmp/uvtools'
                            UV_PYTHON_INSTALL_DIR='/tmp/uvpython'
                            UV_CACHE_DIR='/tmp/uvcache'
                        }
                        agent {
                            dockerfile {
                                filename 'ci/docker/linux/jenkins/Dockerfile'
                                label 'linux && docker && x86'
                                additionalBuildArgs '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg PIP_CACHE_DIR=/.cache/pip --build-arg UV_CACHE_DIR=/.cache/uv --build-arg CONAN_CENTER_PROXY_V2_URL'
                                args '--mount source=sonar-cache-ocr,target=/opt/sonar/.sonar/cache --mount source=python-tmp-uiucpreson-ocr,target=/tmp'
                            }
                        }
                        stages{
                            stage('Setup'){
                                stages{
                                    stage('Setup Testing Environment'){
                                        environment{
                                            CFLAGS='--coverage -fprofile-arcs -ftest-coverage'
                                            LFLAGS='-lgcov --coverage'
                                        }
                                        steps{
                                            retry(3){
                                                script{
                                                    try{
                                                        sh(
                                                            label: 'Create virtual environment',
                                                            script: '''mkdir -p build/python
                                                                       build-wrapper-linux --out-dir build/build_wrapper_output_directory uv sync --group ci --refresh-package=uiucprescon-ocr
                                                                       mkdir -p logs
                                                                       mkdir -p reports
                                                                    '''
                                                       )
                                                    } catch(e){
                                                        cleanWs(
                                                            patterns: [
                                                                    [pattern: 'bootstrap_uv/', type: 'INCLUDE'],
                                                                    [pattern: '.venv/', type: 'INCLUDE'],
                                                                    [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                                ],
                                                            notFailBuild: true,
                                                            deleteDirs: true
                                                            )
                                                        raise e
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            stage('Building Documentation'){
                                steps{
                                    timeout(3){
                                        sh '''mkdir -p logs
                                              uv run -m sphinx docs/source build/docs/html -d build/docs/.doctrees -w logs/build_sphinx.log
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
                                                script: '''uv run conan install conanfile.py -of build/cpp --build=missing -pr:b=default
                                                           uv run cmake --preset conan-release -B build/cpp \
                                                            -S ./ \
                                                            -DCMAKE_EXPORT_COMPILE_COMMANDS:BOOL=ON \
                                                            -DCMAKE_C_FLAGS="-Wall -Wextra -fprofile-arcs -ftest-coverage" \
                                                            -DCMAKE_CXX_FLAGS="-Wall -Wextra -fprofile-arcs -ftest-coverage" \
                                                            -DCMAKE_CXX_OUTPUT_EXTENSION_REPLACE:BOOL=ON \
                                                            -DCMAKE_MODULE_PATH=./build/cpp
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
                                                                       uv run coverage run --parallel-mode --source=src -m pytest --junitxml=./reports/pytest/junit-pytest.xml --basetemp=/tmp/pytest
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
                                                        sh 'uv run -m sphinx -b doctest docs/source build/docs -d build/docs/doctrees -w logs/doctest_warnings.log'
                                                    }
                                                }
                                                post{
                                                    always {
                                                        recordIssues(tools: [sphinxBuild(name: 'Doctest', pattern: 'logs/doctest_warnings.log', id: 'doctest')])
                                                    }
                                                }
                                            }
                                            stage('Audit Lockfile Dependencies'){
                                                steps{
                                                    catchError(buildResult: 'SUCCESS', message: 'uv-secure found issues', stageResult: 'UNSTABLE') {
                                                        sh 'uvx uv-secure --cache-path=/tmp/cache/uv-secure uv.lock'
                                                    }
                                                }
                                            }
                                            stage('Clang Tidy Analysis') {
                                                steps{
                                                    tee('logs/clang-tidy.log') {
                                                        catchError(buildResult: 'SUCCESS', message: 'clang tidy found issues', stageResult: 'UNSTABLE') {
                                                            sh(label: 'Run Clang Tidy', script: 'run-clang-tidy -clang-tidy-binary clang-tidy -p ./build/cpp/ ./src/uiucprescon/ocr')
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
                                                        script: 'cd build/cpp && uv run ctest --output-on-failure --no-compress-output -T Test',
                                                        returnStatus: true
                                                    )

                                                    sh(
                                                        label: 'Running cpp tests',
                                                        script: 'build/cpp/tests/tester -r sonarqube -o reports/test-cpp.xml'
                                                    )
                                                    sh 'mkdir -p reports/coverage && uv run gcovr --root . --filter src/uiucprescon/ocr --exclude-directories build/cpp/_deps/libcatch2-build --print-summary  --xml -o reports/coverage/coverage_cpp.xml'
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
                                                                script: 'uv run flake8 src --tee --output-file logs/flake8.log'
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
                                                        script: '''uv run stubgen src -o mypy_stubs
                                                                   mkdir -p reports/mypy/html
                                                                   MYPYPATH="$WORKSPACE/mypy_stubs" uv run mypy src --cache-dir=nul --html-report reports/mypy/html > logs/mypy.log
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
                                                                       uv run pylint src -r n --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}" --persistent=no > reports/pylint.txt
                                                                    '''

                                                        )
                                                    }
                                                    sh(
                                                        label: 'Running pylint for sonarqube',
                                                        script: 'uv run pylint  -r n --msg-template="{path}:{module}:{line}: [{msg_id}({symbol}), {obj}] {msg}" --persistent=no > reports/pylint_issues.txt',
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
                                                              uv run coverage combine
                                                              mkdir -p reports/coverage
                                                              uv run coverage xml -o ./reports/coverage/coverage-python.xml
                                                              uv run gcovr --root . --filter src/uiucprescon/ocr --exclude-directories build/cpp/_deps/libcatch2-build --exclude-directories build/python/temp/conan_cache --print-summary --keep --json -o reports/coverage/coverage-c-extension.json
                                                              uv run gcovr --root . --filter src/uiucprescon/ocr --exclude-directories build/cpp/_deps/libcatch2-build --print-summary --keep  --json -o reports/coverage/coverage_cpp.json
                                                              uv run gcovr --add-tracefile reports/coverage/coverage-c-extension.json --add-tracefile reports/coverage/coverage_cpp.json --keep --print-summary --xml -o reports/coverage_cpp.xml --sonarqube -o reports/coverage/coverage_cpp_sonar.xml
                                                              '''
                                                    )
                                                recordCoverage(tools: [[parser: 'COBERTURA', pattern: 'reports/coverage/*.xml']])
                                            }
                                        }
                                    }
                                    stage('Sonarcloud Analysis'){
                                        options{
                                            lock('uiucprescon.ocr-sonarcloud')
                                        }
                                        when{
                                            allOf{
                                                equals expected: true, actual: params.USE_SONARQUBE
                                                expression{
                                                    try{
                                                        withCredentials([string(credentialsId: params.SONARCLOUD_TOKEN, variable: 'dddd')]) {
                                                            echo 'Found credentials for sonarqube'
                                                        }
                                                    } catch(e){
                                                        return false
                                                    }
                                                    return true
                                                }
                                            }
                                            beforeOptions true
                                        }
                                        environment{
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
                                                    withCredentials([string(credentialsId: params.SONARCLOUD_TOKEN, variable: 'token')]) {
                                                        if (env.CHANGE_ID){
                                                            sh(
                                                                label: 'Running Sonar Scanner',
                                                                script: "uv run pysonar -t \$token -Dsonar.projectVersion=${props.version} -Dsonar.buildString=\"${env.BUILD_TAG}\" -Dsonar.pullrequest.key=${env.CHANGE_ID} -Dsonar.pullrequest.base=${env.CHANGE_TARGET} -Dsonar.cfamily.cache.enabled=false -Dsonar.cfamily.threads=\$(grep -c ^processor /proc/cpuinfo) -Dsonar.cfamily.build-wrapper-output=build/build_wrapper_output_directory"
                                                            )
                                                        } else {
                                                            sh(
                                                                label: 'Running Sonar Scanner',
                                                                script: "uv run pysonar -t \$token -Dsonar.projectVersion=${props.version} -Dsonar.buildString=\"${env.BUILD_TAG}\" -Dsonar.branch.name=${env.BRANCH_NAME} -Dsonar.cfamily.cache.enabled=false -Dsonar.cfamily.threads=\$(grep -c ^processor /proc/cpuinfo) -Dsonar.cfamily.build-wrapper-output=build/build_wrapper_output_directory"
                                                           )
                                                        }
                                                    }
                                                }
                                                timeout(time: 1, unit: 'HOURS') {
                                                    def sonarqube_result = waitForQualityGate(abortPipeline: false)
                                                    if (sonarqube_result.status != 'OK') {
                                                        unstable "SonarQube quality gate: ${sonarqube_result.status}"
                                                    }
                                                    if(env.BRANCH_IS_PRIMARY){
                                                        writeJSON(file: 'reports/sonar-report.json', json: get_sonarqube_unresolved_issues('.sonar/report-task.txt'))
                                                    }
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
                                sh "git clean -dfx"
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
                                                        script: './venv/bin/uv run --only-group tox --quiet --with tox-uv tox list -d --no-desc',
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
                                                            try{
                                                                lock("${env.JOB_NAME} - ${env.NODE_NAME}"){
                                                                    image = docker.build(UUID.randomUUID().toString(), '-f ci/docker/linux/tox/Dockerfile --build-arg CONAN_CENTER_PROXY_V2_URL --build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg PIP_CACHE_DIR=/.cache/pip --build-arg UV_CACHE_DIR=/.cache/uv .')
                                                                }
                                                                try{
                                                                    image.inside('--mount source=python-tmp-uiucpreson-ocr,target=/tmp'){
                                                                        retry(3){
                                                                            sh( label: 'Running Tox',
                                                                                script: """python3 -m venv venv && venv/bin/pip install --disable-pip-version-check uv
                                                                                           venv/bin/uv run --only-group tox --python ${version} --python-preference system --with tox-uv tox run --runner uv-venv-lock-runner -e ${toxEnv} -vv
                                                                                        """
                                                                                )
                                                                        }
                                                                    }
                                                                }finally{
                                                                    sh "${tool(name: 'Default', type: 'git')} clean -dfx"
                                                                    cleanWs(
                                                                        patterns: [
                                                                            [pattern: 'venv/', type: 'INCLUDE'],
                                                                            [pattern: '.tox', type: 'INCLUDE'],
                                                                            [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                                        ]
                                                                    )
                                                                }
                                                            } finally {
                                                                if (image){
                                                                    sh "docker rmi --no-prune ${image.id}"
                                                                }
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
                                     PIP_CACHE_DIR='C:\\Users\\ContainerUser\\Documents\\cache\\pipcache'
                                     UV_TOOL_DIR='C:\\Users\\ContainerUser\\Documents\\cache\\uvtools'
                                     UV_PYTHON_INSTALL_DIR='C:\\Users\\ContainerUser\\Documents\\cache\\uvpython'
                                     UV_CACHE_DIR='C:\\Users\\ContainerUser\\Documents\\cache\\uvcache'
                                 }
                                 steps{
                                     script{
                                         def envs = []
                                         node('docker && windows'){
                                             try{
                                                checkout scm
                                                docker.image(env.DEFAULT_PYTHON_DOCKER_IMAGE ? env.DEFAULT_PYTHON_DOCKER_IMAGE: 'python')
                                                    .inside(
                                                        "--mount source=uv_python_install_dir,target=${env.UV_PYTHON_INSTALL_DIR} " +
                                                        "--mount source=pipcache,target=${env.PIP_CACHE_DIR} " +
                                                        "--mount source=uv_cache_dir,target=${env.UV_CACHE_DIR}"
                                                        )
                                                {
                                                    bat(script: 'python -m venv venv && venv\\Scripts\\pip install --disable-pip-version-check uv')
                                                    envs = bat(
                                                        label: 'Get tox environments',
                                                        script: '@.\\venv\\Scripts\\uv run --quiet --only-group tox --with tox-uv tox list -d --no-desc',
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
                                                                retry(2){
                                                                    image = docker.build(UUID.randomUUID().toString(), '-f scripts/resources/windows/Dockerfile --build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE --build-arg CONAN_CENTER_PROXY_V2_URL --build-arg UV_INDEX_URL --build-arg UV_EXTRA_INDEX_URL .')
                                                                }
                                                            }
                                                            try{
                                                                try{
                                                                    image.inside(
                                                                        "--mount source=uv_python_install_dir,target=${env.UV_PYTHON_INSTALL_DIR} " +
                                                                        "--mount source=pipcache,target=${env.PIP_CACHE_DIR} " +
                                                                        "--mount source=uv_cache_dir,target=${env.UV_CACHE_DIR}"
                                                                    ){
                                                                        retry(3){
                                                                            try{
                                                                                bat(label: 'Running Tox',
                                                                                     script: """uv python install cpython-${version}
                                                                                                uv run --only-group tox -p ${version} --with tox-uv tox run --runner uv-venv-lock-runner -e ${toxEnv} -vv
                                                                                             """
                                                                                )
                                                                            } finally{
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
                                                                } finally {
                                                                    if(image){
                                                                        bat "docker rmi --no-prune ${image.id}"
                                                                    }
                                                                }
                                                            } finally {
                                                                bat "${tool(name: 'Default', type: 'git')} clean -dfx"
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
                            mac_wheels(SUPPORTED_MAC_VERSIONS, params.TEST_PACKAGES, params, wheelStashes)
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
                            linux_wheels(SUPPORTED_LINUX_VERSIONS, params.TEST_PACKAGES, params, wheelStashes)
                        }
                    }
                    stage('Platform Wheels: Windows'){
                        when {
                            equals expected: true, actual: params.INCLUDE_WINDOWS_X86_64
                        }
                        steps{
                            windows_wheels(SUPPORTED_WINDOWS_VERSIONS, params.TEST_PACKAGES, params, wheelStashes)
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
                                    UV_CACHE_DIR='/tmp/uvcache'
                                }
                                steps{
                                    script{
                                        try{
                                            sh(label: 'Building sdist',
                                               script: '''python -m venv venv
                                                          trap "rm -rf venv" EXIT
                                                          venv/bin/pip install --disable-pip-version-check uv
                                                          venv/bin/uv build --sdist
                                                          '''
                                            )
                                            archiveArtifacts artifacts: 'dist/*.tar.gz,dist/*.zip'
                                            stash includes: 'dist/*.tar.gz,dist/*.zip', name: 'python sdist'
                                            wheelStashes << 'python sdist'
                                        } finally{
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
                                            def allValidArches = ['x86_64', 'arm64']
                                            if(params.INCLUDE_MACOS_X86_64 == true){
                                                selectedArches << 'x86_64'
                                            }
                                            if(params.INCLUDE_MACOS_ARM == true){
                                                selectedArches << 'arm64'
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
                                                                        findFiles(glob: 'dist/*.tar.gz').each{
                                                                            sh(label: 'Running Tox',
                                                                               script: """python3 -m venv venv
                                                                                          trap "rm -rf venv" EXIT
                                                                                          venv/bin/pip install  --disable-pip-version-check uv
                                                                                          trap "rm -rf venv && rm -rf .tox" EXIT
                                                                                          venv/bin/uv run --only-group tox --python ${pythonVersion} --with tox-uv tox --installpkg ${it.path} -e py${pythonVersion.replace('.', '')}
                                                                                       """
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
                                           def allValidArches = ['x86_64']
                                           if(params.INCLUDE_WINDOWS_X86_64 == true){
                                               selectedArches << 'x86_64'
                                           }
                                           return allValidArches.collectEntries{ arch ->
                                               def newStageName = "Test sdist (Windows x86_64 - Python ${pythonVersion})"
                                               return [
                                                   "${newStageName}": {
                                                       if(selectedArches.contains(arch)){
                                                           withEnv([
                                                              'PIP_CACHE_DIR=C:\\Users\\ContainerUser\\Documents\\cache\\pipcache',
                                                              'UV_TOOL_DIR=C:\\Users\\ContainerUser\\Documents\\cache\\uvtools',
                                                              'UV_PYTHON_INSTALL_DIR=C:\\Users\\ContainerUser\\Documents\\cache\\uvpython',
                                                              'UV_CACHE_DIR=C:\\Users\\ContainerUser\\Documents\\cache\\uvcache',
                                                           ]){
                                                                stage(newStageName){
                                                                    node("windows && docker && ${arch}"){
                                                                       def dockerImage
                                                                       try{
                                                                           def dockerImageName = "${currentBuild.fullProjectName}_${UUID.randomUUID().toString()}".replaceAll("-", '_').replaceAll('/', '_').replaceAll(' ', "").toLowerCase()
                                                                           checkout scm
                                                                           def retryTimes = 3
                                                                           retry(retryTimes){
                                                                               lock("docker build-${env.NODE_NAME}"){
                                                                                   dockerImage = docker.build(dockerImageName, '-f scripts/resources/windows/Dockerfile --build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE --build-arg CONAN_CENTER_PROXY_V2_URL --build-arg UV_INDEX_URL --build-arg UV_EXTRA_INDEX_URL .')
                                                                               }
                                                                           }
                                                                           retry(retryTimes){
                                                                                try{
                                                                                    dockerImage.inside(
                                                                                        '--mount type=volume,source=uv_python_install_dir,target=C:\\Users\\ContainerUser\\Documents\\cache\\uvpython ' +
                                                                                        '--mount type=volume,source=pipcache,target=C:\\Users\\ContainerUser\\Documents\\cache\\pipcache ' +
                                                                                        '--mount type=volume,source=uv_cache_dir,target=C:\\Users\\ContainerUser\\Documents\\cache\\uvcache'
                                                                                    ){
                                                                                       checkout scm
                                                                                       unstash 'python sdist'
                                                                                       findFiles(glob: 'dist/*.tar.gz').each{
                                                                                           bat(
                                                                                               label: 'Running Tox',
                                                                                               script: "uv run --only-group tox --python ${pythonVersion} --with tox-uv tox --workdir %TEMP%\\tox --installpkg ${it.path} -e py${pythonVersion.replace('.', '')} -vv"
                                                                                           )
                                                                                       }
                                                                                    }
                                                                                } finally{
                                                                                   bat "${tool(name: 'Default', type: 'git')} clean -dfx"
                                                                                }
                                                                           }
                                                                       } finally {
                                                                           powershell(
                                                                               label: 'Untagging Docker Image used',
                                                                               script: "docker image rm --no-prune ${dockerImage.imageName()}",
                                                                               returnStatus: true
                                                                           )
                                                                       }
                                                                   }
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
                                           def allValidArches = ['x86_64', 'arm64']
                                           if(params.INCLUDE_LINUX_X86_64 == true){
                                               selectedArches << 'x86_64'
                                           }
                                           if(params.INCLUDE_LINUX_ARM == true){
                                               selectedArches << 'arm64'
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
                                                                           additionalBuildArgs: '--build-arg CONAN_CENTER_PROXY_V2_URL --build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg PIP_CACHE_DIR=/.cache/pip --build-arg UV_CACHE_DIR=/.cache/uv'
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
                                                                                              ./venv/bin/uv run --only-group tox --python ${pythonVersion} --with tox-uv tox --installpkg ${it.path} -e py${pythonVersion.replace('.', '')}
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
                             withEnv(["TWINE_REPOSITORY_URL=${SERVER_URL}"]){
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
                                                       uv run --only-group publish twine upload --disable-progress-bar --non-interactive dist/*
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

}