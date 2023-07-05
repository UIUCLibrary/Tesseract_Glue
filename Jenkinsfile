SONARQUBE_CREDENTIAL_ID = 'sonarcloud-uiucprescon.ocr'
SUPPORTED_MAC_VERSIONS = ['3.8', '3.9', '3.10', '3.11']
SUPPORTED_LINUX_VERSIONS = ['3.8', '3.9', '3.10', '3.11']
SUPPORTED_WINDOWS_VERSIONS = ['3.8', '3.9', '3.10', '3.11']

def getPypiConfig() {
    node(){
        configFileProvider([configFile(fileId: 'pypi_config', variable: 'CONFIG_FILE')]) {
            def config = readJSON( file: CONFIG_FILE)
            return config['deployment']['indexes']
        }
    }
}

def getDevpiConfig() {
    node(){
        configFileProvider([configFile(fileId: 'devpi_config', variable: 'CONFIG_FILE')]) {
            def configProperties = readProperties(file: CONFIG_FILE)
            configProperties.stagingIndex = {
                if (env.TAG_NAME?.trim()){
                    return 'tag_staging'
                } else{
                    return "${env.BRANCH_NAME}_staging"
                }
            }()
            return configProperties
        }
    }
}
def DEVPI_CONFIG = getDevpiConfig()
def getToxStages(){
    script{
        def tox = fileLoader.fromGit(
            'tox',
            'https://github.com/UIUCLibrary/jenkins_helper_scripts.git',
            '8',
            null,
            ''
        )
        def windowsJobs = [:]
        def linuxJobs = [:]
        stage('Scanning Tox Environments'){
            parallel(
                'Linux':{
                    linuxJobs = tox.getToxTestsParallel(
                            envNamePrefix: 'Tox Linux',
                            label: 'linux && docker && x86',
                            dockerfile: 'ci/docker/linux/tox/Dockerfile',
                            dockerArgs: '--build-arg TARGETARCH=amd64 --build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL',
                            retry: 2
                        )
                },
                'Windows':{
                    timeout(240){
                        windowsJobs = tox.getToxTestsParallel(
                                envNamePrefix: 'Tox Windows',
                                label: 'windows && docker && x86',
                                dockerfile: 'ci/docker/windows/tox/Dockerfile',
                                dockerArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE',
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

def getMacDevpiTestStages(packageName, packageVersion, pythonVersions, devpiServer, devpiCredentialsId, devpiIndex) {
    node(){
        checkout scm
        devpi = load('ci/jenkins/scripts/devpi.groovy')
    }
    def macPackageStages = [:]
    def architectures = []
    if(params.INCLUDE_MACOS_X86_64 == true){
        architectures.add('x86_64')
    }
    if(params.INCLUDE_MACOS_ARM == true){
        architectures.add("arm64")
    }
    pythonVersions.each{pythonVersion ->
        architectures.each{ processorArchitecture ->
            macPackageStages["MacOS-${processorArchitecture} - Python ${pythonVersion}: wheel"] = {
                withEnv(['PATH+EXTRA=./venv/bin']) {
                    devpi.testDevpiPackage(
                        agent: [
                            label: "mac && python${pythonVersion} && ${processorArchitecture} && devpi-access"
                        ],
                        devpi: [
                            index: devpiIndex,
                            server: devpiServer,
                            credentialsId: devpiCredentialsId,
                            devpiExec: 'venv/bin/devpi'
                        ],
                        package:[
                            name: packageName,
                            version: packageVersion,
                            selector: "(${pythonVersion.replace('.','')}).*(-*macosx_*).*(${processorArchitecture}\\.whl)"
                        ],
                        test:[
                            setup: {
                                checkout scm
                                sh(
                                    label:'Installing Devpi client',
                                    script: '''python3 -m venv venv
                                               . ./venv/bin/activate
                                               python -m pip install pip --upgrade
                                               python -m pip install devpi_client -r requirements/requirements_tox.txt
                                           '''
                                )
                            },
                            toxEnv: "py${pythonVersion}".replace('.',''),
                            teardown: {
                                sh( label: 'Remove Devpi client', script: 'rm -r venv')
                            }
                        ]
                    )
                }
            }
            macPackageStages["MacOS-${processorArchitecture} - Python ${pythonVersion}: sdist"]= {
                withEnv(['PATH+EXTRA=./venv/bin']) {
                    devpi.testDevpiPackage(
                        agent: [
                            label: "mac && python${pythonVersion} && ${processorArchitecture} && devpi-access"
                        ],
                        devpi: [
                            index: devpiIndex,
                            server: devpiServer,
                            credentialsId: devpiCredentialsId,
                            devpiExec: 'venv/bin/devpi'
                        ],
                        package:[
                            name: packageName,
                            version: packageVersion,
                            selector: 'tar.gz'
                        ],
                        test:[
                            setup: {
                                checkout scm
                                sh(
                                    label:'Installing Devpi client',
                                    script: '''python3 -m venv venv
                                               . ./venv/bin/activate
                                               python -m pip install pip --upgrade
                                               python -m pip install devpi_client -r requirements/requirements_tox.txt
                                            '''
                                )
                            },
                            toxEnv: "py${pythonVersion}".replace('.',''),
                            teardown: {
                                sh( label: 'Remove Devpi client', script: 'rm -r venv')
                            }
                        ]
                    )
                }
            }
        }
    }
    return macPackageStages;
}


wheelStashes = []

defaultParameterValues = [
    USE_SONARQUBE: false
]

def build_wheels(){
    script{
        def packages
        node(){
            checkout scm
            packages = load 'ci/jenkins/scripts/packaging.groovy'
        }
        def macBuildStages = [:]

        SUPPORTED_MAC_VERSIONS.each{ pythonVersion ->
            if(params.INCLUDE_MACOS_X86_64 == true){
                macBuildStages["MacOS x86_64 - Python ${pythonVersion}: wheel"] = {
                    packages.buildPkg(
                        agent: [
                            label: "mac && python${pythonVersion} && x86",
                        ],
                        buildCmd: {
                            withEnv([
                                '_PYTHON_HOST_PLATFORM=macosx-10.9-x86_64',
                                'MACOSX_DEPLOYMENT_TARGET=10.9',
                                'ARCHFLAGS=-arch x86_64'
                            ]){
                                 sh(label: 'Building wheel',
                                    script: """python${pythonVersion} -m venv venv
                                               . ./venv/bin/activate
                                               python -m pip install --upgrade pip
                                               pip install wheel==0.37
                                               pip install build delocate
                                               python -m build --wheel
                                               """
                                   )
                                 findFiles(glob: 'dist/*.whl').each{
                                        sh(label: 'Fixing up wheel',
                                           script: """. ./venv/bin/activate
                                                      pip list
                                                      delocate-listdeps --depending ${it.path}
                                                      delocate-wheel -w fixed_wheels --require-archs x86_64 --verbose ${it.path}
                                                   """
                                     )
                                 }
                             }
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
            }
            if(params.INCLUDE_MACOS_ARM == true){
                macBuildStages["MacOS M1 - Python ${pythonVersion}: wheel"] = {
                    packages.buildPkg(
                        agent: [
                            label: "mac && python${pythonVersion} && m1",
                        ],
                        buildCmd: {
                            //                     Taken from cibuildwheel source code
                            //                     https://github.com/pypa/cibuildwheel/blob/main/cibuildwheel/macos.py
                            //
                            //                     # macOS 11 is the first OS with arm64 support, so the wheels
                            //                     # have that as a minimum.
                            withEnv([
                                '_PYTHON_HOST_PLATFORM=macosx-11.0-arm64',
                                'MACOSX_DEPLOYMENT_TARGET=11.0',
                                'ARCHFLAGS=-arch arm64'
                                ]) {
                                 sh(label: 'Building wheel',
                                    script: """python${pythonVersion} -m venv venv
                                               . ./venv/bin/activate
                                               pip install --upgrade pip
                                               pip install wheel==0.37
                                               pip install build delocate
                                               python -m build --wheel
                                               """
                                   )
                                 findFiles(glob: 'dist/*.whl').each{
                                    sh(label: 'Fixing up wheel',
                                       script: """./venv/bin/delocate-listdeps --depending ${it.path}
                                                  ./venv/bin/delocate-wheel -w fixed_wheels --require-archs arm64 --verbose ${it.path}
                                               """
                                 )
                             }
                            }
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
            }

        }
        def windowsBuildStages = [:]
        SUPPORTED_WINDOWS_VERSIONS.each{ pythonVersion ->
            if(params.INCLUDE_WINDOWS_X86_64 == true){
                windowsBuildStages["Windows - Python ${pythonVersion}: wheel"] = {
                    packages.buildPkg(
                        agent: [
                            dockerfile: [
                                label: 'windows && docker && x86',
                                filename: 'ci/docker/windows/tox/Dockerfile',
                                additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE'
                            ]
                        ],
                        buildCmd: {
                            bat """py -${pythonVersion} -m venv venv
                                   venv\\Scripts\\python -m pip install pip --upgrade
                                   venv\\Scripts\\python -m pip install wheel
                                   venv\\Scripts\\python -m pip install build
                                   venv\\Scripts\\python -m build --wheel
                                """
//                            bat "py -${pythonVersion} -m pip wheel -v --no-deps -w ./dist ."
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
            }
        }
        def buildStages =  [
           failFast: true,
            'Source Distribution': {
                node('docker'){
                    docker.image("python").inside(){
                        try{
                            checkout scm
                            if(isUnix()){
                                sh(label: 'Building sdist',
                                   script: '''python -m venv venv --upgrade-deps
                                              venv/bin/pip install build
                                              venv/bin/python -m build --sdist
                                              '''
                                )
                            } else{
                               bat(label: 'Building sdist',
                                   script: '''python -m venv venv --upgrade-deps
                                              venv\\Scripts\\pip install build
                                              venv\\Scripts\\python -m build --sdist
                                              '''
                               )
                            }
                            archiveArtifacts artifacts: 'dist/*.tar.gz,dist/*.zip'
                            stash includes: 'dist/*.tar.gz,dist/*.zip', name: 'python sdist'
                            wheelStashes << 'python sdist'
                        } finally {
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
        ]
        def linuxBuildStages = [:]
        SUPPORTED_LINUX_VERSIONS.each{ pythonVersion ->
            if(params.INCLUDE_LINUX_X86_64 == true){
                linuxBuildStages["Linux x86_64 - Python ${pythonVersion}: wheel"] = {
                    packages.buildPkg(
                        agent: [
                            dockerfile: [
                                label: 'linux && docker && x86',
                                filename: 'ci/docker/linux/package/Dockerfile',
                                additionalBuildArgs: '--build-arg TARGETARCH=amd64  --build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg manylinux_image=quay.io/pypa/manylinux2014_x86_64'
                            ]
                        ],
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
            }
            if(params.INCLUDE_LINUX_ARM == true){
                linuxBuildStages["Linux arm64 - Python ${pythonVersion}: wheel"] = {
                    packages.buildPkg(
                        agent: [
                            dockerfile: [
                                label: 'linux && docker && arm64',
                                filename: 'ci/docker/linux/package/Dockerfile',
                                additionalBuildArgs: '--build-arg TARGETARCH=arm64 --build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg manylinux_image=quay.io/pypa/manylinux2014_aarch64'
                            ]
                        ],
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
            }
        }
        buildStages = buildStages + windowsBuildStages + linuxBuildStages + macBuildStages
        parallel(buildStages)
    }
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
        ]
    )
}
startup()
props = get_props()
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
        booleanParam(name: 'DEPLOY_DEVPI', defaultValue: false, description: "Deploy to devpi on ${DEVPI_CONFIG.server}/${DEVPI_CONFIG.devpiUserName}/${env.BRANCH_NAME}")
        booleanParam(name: 'DEPLOY_DEVPI_PRODUCTION', defaultValue: false, description: "Deploy to ${DEVPI_CONFIG.server}/production/release")
        booleanParam(name: 'DEPLOY_PYPI', defaultValue: false, description: 'Deploy to pypi')
        booleanParam(name: 'DEPLOY_DOCS', defaultValue: false, description: 'Update online documentation')
    }
    stages {
        stage('Building and Testing'){
            when{
                anyOf{
                    equals expected: true, actual: params.RUN_CHECKS
                    equals expected: true, actual: params.TEST_RUN_TOX
                    equals expected: true, actual: params.DEPLOY_DEVPI
                }
            }
            stages{
                stage('Building') {
                    agent {
                        dockerfile {
                            filename 'ci/docker/linux/jenkins/Dockerfile'
                            label 'linux && docker && x86'
                            additionalBuildArgs '--build-arg TARGETARCH=amd64 --build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL '
                        }
                    }
                    when{
                        anyOf{
                            equals expected: true, actual: params.RUN_CHECKS
                            equals expected: true, actual: params.DEPLOY_DEVPI
                        }
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
                                    additionalBuildArgs '--build-arg TARGETARCH=amd64 --build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL'
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
                                            publishCoverage(
                                                adapters: [
                                                    coberturaAdapter(mergeToOneReport: true, path: 'reports/coverage*.xml')
                                                ],
                                                sourceFileResolver: sourceFiles('STORE_ALL_BUILD')
                                            )
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
                                                'sonarcloud-uiucprescon.ocr'
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
                        build_wheels()

                    }
                }
                stage('Testing'){
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
                            def architectures = []
                            if(params.INCLUDE_MACOS_X86_64 == true){
                                architectures.add('x86_64')
                            }
                            if(params.INCLUDE_MACOS_ARM == true){
                                architectures.add("m1")
                            }
                            architectures.each{ processorArchitecture ->
                                SUPPORTED_MAC_VERSIONS.each{ pythonVersion ->
                                    macTestStages["MacOS-${processorArchitecture} - Python ${pythonVersion}: wheel"] = {
                                        packages.testPkg2(
                                            agent: [
                                                label: "mac && python${pythonVersion} && ${processorArchitecture}",
                                            ],
                                            testSetup: {
                                                checkout scm
                                                unstash "python${pythonVersion} ${processorArchitecture} mac wheel"
                                            },
                                            testCommand: {
                                                findFiles(glob: 'dist/*.whl').each{
                                                    sh(label: 'Running Tox',
                                                       script: """python${pythonVersion} -m venv venv
                                                       ./venv/bin/python -m pip install --upgrade pip
                                                       ./venv/bin/pip install -r requirements/requirements_tox.txt
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
                                    macTestStages["MacOS-${processorArchitecture} - Python ${pythonVersion}: sdist"]= {
                                        packages.testPkg2(
                                            agent: [
                                                label: "mac && python${pythonVersion} && ${processorArchitecture}",
                                            ],
                                            testSetup: {
                                                checkout scm
                                                unstash 'python sdist'
                                            },
                                            testCommand: {
                                                findFiles(glob: 'dist/*.tar.gz').each{
                                                    sh(label: 'Running Tox',
                                                       script: """python${pythonVersion} -m venv venv
                                                       ./venv/bin/python -m pip install --upgrade pip
                                                       ./venv/bin/pip install -r requirements/requirements_tox.txt
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
                                            ]
                                        )
                                    }
                                }
                            }
                            def windowsTestStages = [:]
                            SUPPORTED_WINDOWS_VERSIONS.each{ pythonVersion ->
                                if(params.INCLUDE_WINDOWS_X86_64 == true){
                                    windowsTestStages["Windows - Python ${pythonVersion}: wheel"] = {
                                        packages.testPkg2(
                                            agent: [
                                                dockerfile: [
                                                    label: 'windows && docker && x86',
                                                    filename: 'ci/docker/windows/tox_no_vs/Dockerfile',
                                                    additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE'
                                                ]
                                            ],
                                            dockerImageName: "${currentBuild.fullProjectName}_test_no_msvc".replaceAll('-', '_').replaceAll('/', '_').replaceAll(' ', '').toLowerCase(),
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
                                    windowsTestStages["Windows - Python ${pythonVersion}: sdist"] = {
                                        packages.testPkg2(
                                            agent: [
                                                dockerfile: [
                                                    label: 'windows && docker && x86',
                                                    filename: 'ci/docker/windows/tox/Dockerfile',
                                                    additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE'
                                                ]
                                            ],
                                            dockerImageName: "${currentBuild.fullProjectName}_test_with_msvc".replaceAll('-', '_').replaceAll('/', '_').replaceAll(' ', '').toLowerCase(),
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
                            def linuxTestStages = [:]
                            SUPPORTED_LINUX_VERSIONS.each{ pythonVersion ->
                                if(params.INCLUDE_LINUX_X86_64 == true){
                                    linuxTestStages["Linux x86_64 - Python ${pythonVersion}: wheel"] = {
                                        packages.testPkg2(
                                            agent: [
                                                dockerfile: [
                                                    label: 'linux && docker && x86',
                                                    filename: 'ci/docker/linux/tox/Dockerfile',
                                                    additionalBuildArgs: '--build-arg TARGETARCH=amd64 --build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL'
                                                ]
                                            ],
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
                                    linuxTestStages["Linux - Python ${pythonVersion} - x86_64: sdist"] = {
                                        packages.testPkg2(
                                            agent: [
                                                dockerfile: [
                                                    label: 'linux && docker && x86',
                                                    filename: 'ci/docker/linux/tox/Dockerfile',
                                                    additionalBuildArgs: '--build-arg TARGETARCH=amd64 --build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL'
                                                ]
                                            ],
                                            testSetup: {
                                                checkout scm
                                                unstash 'python sdist'
                                            },
                                            testCommand: {
                                                findFiles(glob: 'dist/*.tar.gz').each{
                                                    sh(
                                                        label: 'Running Tox',
                                                        script: "tox --installpkg ${it.path} --workdir /tmp/tox -e py${pythonVersion.replace('.', '')} -vvv"
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
                                if(params.INCLUDE_LINUX_ARM == true){
                                    linuxTestStages["Linux arm64 - Python ${pythonVersion}: wheel"] = {
                                        packages.testPkg2(
                                            agent: [
                                                dockerfile: [
                                                    label: 'linux && docker && arm64',
                                                    filename: 'ci/docker/linux/tox/Dockerfile',
                                                    additionalBuildArgs: '--build-arg TARGETARCH=arm64 --build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL'
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
                                    linuxTestStages["Linux - Python ${pythonVersion} - arm64: sdist"] = {
                                        packages.testPkg2(
                                            agent: [
                                                dockerfile: [
                                                    label: 'linux && docker && arm64',
                                                    filename: 'ci/docker/linux/tox/Dockerfile',
                                                    additionalBuildArgs: '--build-arg TARGETARCH=arm64 --build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL'
                                                ]
                                            ],
                                            testSetup: {
                                                checkout scm
                                                unstash 'python sdist'
                                            },
                                            testCommand: {
                                                findFiles(glob: 'dist/*.tar.gz').each{
                                                    sh(
                                                        label: 'Running Tox',
                                                        script: "tox --installpkg ${it.path} --workdir /tmp/tox -e py${pythonVersion.replace('.', '')} -vvv"
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
                            parallel(windowsTestStages + linuxTestStages + macTestStages)
                        }
                    }
                }
            }
        }
        stage('Deploy to DevPi') {
            agent none
            options{
                lock('uiucprescon.ocr-devpi')
            }
            when {
                allOf{
                    equals expected: true, actual: params.DEPLOY_DEVPI
                    anyOf {
                        equals expected: 'master', actual: env.BRANCH_NAME
                        equals expected: 'dev', actual: env.BRANCH_NAME
                        tag '*'
                    }
                }
                beforeAgent true
                beforeOptions true
            }

            stages{
                stage('Upload to DevPi Staging'){
                    agent {
                        dockerfile {
                            filename 'ci/docker/linux/tox/Dockerfile'
                            label 'linux && docker && x86 && devpi-access'
                            additionalBuildArgs '--build-arg TARGETARCH=amd64 --build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL'
                          }
                    }
                    options{
                        retry(3)
                    }
                    steps {
                        script{
                            unstash 'DOCS_ARCHIVE'
                            wheelStashes.each{
                                unstash it
                            }
                            load('ci/jenkins/scripts/devpi.groovy').upload(
                                server: DEVPI_CONFIG.server,
                                credentialsId: 'DS_devpi',
                                index: DEVPI_CONFIG.stagingIndex,
                                clientDir: './devpi'
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
                stage('Test DevPi packages') {
                    steps{
                        script{
                            def devpi = null
                            node(){
                                checkout scm
                                devpi = load('ci/jenkins/scripts/devpi.groovy')
                            }
                            def macPackages = getMacDevpiTestStages(props.Name, props.Version, SUPPORTED_MAC_VERSIONS, DEVPI_CONFIG.server, DEVPI_CONFIG.credentialsId, DEVPI_CONFIG.stagingIndex)
                            def windowsPackages = [:]
                            SUPPORTED_WINDOWS_VERSIONS.each{pythonVersion ->
                                if(params.INCLUDE_WINDOWS_X86_64 == true){
                                    windowsPackages["Windows - Python ${pythonVersion}: sdist"] = {
                                        retry(3){
                                            devpi.testDevpiPackage(
                                                agent: [
                                                    dockerfile: [
                                                        filename: 'ci/docker/windows/tox/Dockerfile',
                                                        additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE',
                                                        label: 'windows && docker && x86 && devpi-access'
                                                    ]
                                                ],
                                                dockerImageName:  "${currentBuild.fullProjectName}_devpi_with_msvc".replaceAll('-', '_').replaceAll('/', '_').replaceAll(' ', '').toLowerCase(),
                                                devpi: [
                                                    index: DEVPI_CONFIG.stagingIndex,
                                                    server: DEVPI_CONFIG.server,
                                                    credentialsId: DEVPI_CONFIG.credentialsId,
                                                ],
                                                package:[
                                                    name: props.Name,
                                                    version: props.Version,
                                                    selector: 'tar.gz'
                                                ],
                                                test:[
                                                    toxEnv: "py${pythonVersion}".replace('.',''),
                                                ]
                                            )
                                        }
                                    }
                                    windowsPackages["Test Python ${pythonVersion}: wheel Windows"] = {
                                        retry(3){
                                            devpi.testDevpiPackage(
                                                agent: [
                                                    dockerfile: [
                                                        filename: 'ci/docker/windows/tox_no_vs/Dockerfile',
                                                        additionalBuildArgs: '--build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL --build-arg CHOCOLATEY_SOURCE',
                                                        label: 'windows && docker && x86 && devpi-access'
                                                    ]
                                                ],
                                                devpi: [
                                                    index: DEVPI_CONFIG.stagingIndex,
                                                    server: DEVPI_CONFIG.server,
                                                    credentialsId: DEVPI_CONFIG.credentialsId,
                                                ],
                                                dockerImageName:  "${currentBuild.fullProjectName}_devpi_without_msvc".replaceAll('-', '_').replaceAll('/', '_').replaceAll(' ', '').toLowerCase(),
                                                package:[
                                                    name: props.Name,
                                                    version: props.Version,
                                                    selector: "(${pythonVersion.replace('.','')}).*(win_amd64\\.whl)"
                                                ],
                                                test:[
                                                    toxEnv: "py${pythonVersion}".replace('.',''),
                                                ]
                                            )
                                        }
                                    }
                                }
                            }
                            def linuxPackages = [:]
                            SUPPORTED_LINUX_VERSIONS.each{pythonVersion ->
                                if(params.INCLUDE_LINUX_X86_64 == true){
                                    linuxPackages["Linux - Python ${pythonVersion}: sdist"] = {
                                        retry(3){
                                            devpi.testDevpiPackage(
                                                agent: [
                                                    dockerfile: [
                                                        filename: 'ci/docker/linux/tox/Dockerfile',
                                                        additionalBuildArgs: '--build-arg TARGETARCH=amd64 --build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL',
                                                        label: 'linux && docker && x86 && devpi-access'
                                                    ]
                                                ],
                                                devpi: [
                                                    index: DEVPI_CONFIG.stagingIndex,
                                                    server: DEVPI_CONFIG.server,
                                                    credentialsId: DEVPI_CONFIG.credentialsId,
                                                ],
                                                package:[
                                                    name: props.Name,
                                                    version: props.Version,
                                                    selector: 'tar.gz'
                                                ],
                                                test:[
                                                    toxEnv: "py${pythonVersion}".replace('.',''),
                                                ]
                                            )
                                        }
                                    }
                                    linuxPackages["Linux - Python ${pythonVersion}: wheel"] = {
                                        retry(3){
                                            devpi.testDevpiPackage(
                                                agent: [
                                                    dockerfile: [
                                                        filename: 'ci/docker/linux/tox/Dockerfile',
                                                        additionalBuildArgs: '--build-arg TARGETARCH=amd64 --build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL',
                                                        label: 'linux && docker && x86 && devpi-access'
                                                    ]
                                                ],
                                                devpi: [
                                                    index: DEVPI_CONFIG.stagingIndex,
                                                    server: DEVPI_CONFIG.server,
                                                    credentialsId: DEVPI_CONFIG.credentialsId,
                                                ],
                                                package:[
                                                    name: props.Name,
                                                    version: props.Version,
                                                    selector: "(${pythonVersion.replace('.','')}).+(manylinux).+x86"
                                                ],
                                                test:[
                                                    toxEnv: "py${pythonVersion}".replace('.',''),
                                                ]
                                            )
                                        }
                                    }
                                }
                            }
                            parallel(windowsPackages + linuxPackages  + macPackages)
                        }
                    }
                }
                stage('Deploy to DevPi Production') {
                    when {
                        allOf{
                            equals expected: true, actual: params.DEPLOY_DEVPI_PRODUCTION
                            anyOf {
                                branch 'master'
                                tag '*'
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
                            filename 'ci/docker/linux/tox/Dockerfile'
                            label 'linux && docker && devpi-access'
                            additionalBuildArgs '--build-arg TARGETARCH=amd64 --build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL'
                        }
                    }
                    steps {
                        script{
                            echo 'Pushing to production/release index'
                            load('ci/jenkins/scripts/devpi.groovy').pushPackageToIndex(
                                pkgName: props.Name,
                                pkgVersion: props.Version,
                                server: DEVPI_CONFIG.server,
                                indexSource: "${DEVPI_CONFIG.devpiUserName}/${DEVPI_CONFIG.stagingIndex}",
                                indexDestination: 'production/release',
                                credentialsId: DEVPI_CONFIG.credentialsId
                            )
                        }
                    }
                }
            }
            post {
                success{
                    node('linux && docker && devpi-access') {
                        script{
                            if (!env.TAG_NAME?.trim()){
                                checkout scm
                                docker.build('ocr:devpi','-f ./ci/docker/linux/tox/Dockerfile --build-arg TARGETARCH=amd64 --build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL .').inside{
                                    load('ci/jenkins/scripts/devpi.groovy').pushPackageToIndex(
                                        pkgName: props.Name,
                                        pkgVersion: props.Version,
                                        server: DEVPI_CONFIG.server,
                                        indexSource: "${DEVPI_CONFIG.devpiUserName}/${DEVPI_CONFIG.stagingIndex}",
                                        indexDestination: "${DEVPI_CONFIG.devpiUserName}/${env.BRANCH_NAME}",
                                        credentialsId: DEVPI_CONFIG.credentialsId
                                    )
                                }
                            }
                        }
                    }
                }
                cleanup{
                    node('linux && docker && devpi-access') {
                        script{
                            checkout scm
                            docker.build('ocr:devpi','-f ./ci/docker/linux/tox/Dockerfile --build-arg TARGETARCH=amd64 --build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL .').inside{
                                load('ci/jenkins/scripts/devpi.groovy').removePackage(
                                    pkgName: props.Name,
                                    pkgVersion: props.Version,
                                    index: "${DEVPI_CONFIG.devpiUserName}/${DEVPI_CONFIG.stagingIndex}",
                                    server: DEVPI_CONFIG.server,
                                    credentialsId: DEVPI_CONFIG.credentialsId,

                                )
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
                            additionalBuildArgs '--build-arg TARGETARCH=amd64 --build-arg PIP_EXTRA_INDEX_URL --build-arg PIP_INDEX_URL'
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
                            def pypi = fileLoader.fromGit(
                                    'pypi',
                                    'https://github.com/UIUCLibrary/jenkins_helper_scripts.git',
                                    '2',
                                    null,
                                    ''
                                )
                            pypi.pypiUpload(
                                credentialsId: 'jenkins-nexus',
                                repositoryUrl: SERVER_URL,
                                glob: 'dist/*'
                                )
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
