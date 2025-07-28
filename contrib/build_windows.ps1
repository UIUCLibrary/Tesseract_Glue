[CmdletBinding()]
param (
    [ValidateNotNullOrEmpty()]
    [string]$DockerImageName = "uiucprescon_ocr_builder",
    [ValidateNotNullOrEmpty()]
    [string]$PythonVersion = "3.11",
    [string]$PIPDowndloadCachePathInContainer,
    [string]$UVCacheDirPathInContainer,
    [string]$UVPythonInstallDirPathInContainer,
    [string]$UVToolDirPathInContainer,
    [ValidateNotNullOrEmpty()][switch]$Verify
)

function Build-DockerImage {
    [CmdletBinding()]
    param (
        [ValidateScript({
            if (-not (Test-Path -Path $_ -PathType Leaf)) {
                throw "The specified file '$_' does not exist."
            }
            return $true
        })]
        [string]$DockerfilePath = "ci/docker/windows/tox/Dockerfile",
        [string]$ImageName = "uiucprescon_ocr_builder",
        [string]$DockerExec = "docker.exe",
        [string]$DockerIsolation = "process"
    )
    $projectRootDirectory = (Get-Item $PSScriptRoot).Parent.FullName
    $local:dockerArgsList = @(
        "build",
        "--isolation", $DockerIsolation,
        "--platform windows/amd64",
        "-f", $DockerfilePath,
        "--build-arg PIP_EXTRA_INDEX_URL",
        "--build-arg PIP_INDEX_URL",
        "--build-arg CHOCOLATEY_SOURCE",
        "--build-arg CONAN_CENTER_PROXY_V2_URL",
        "--build-arg UV_INDEX_URL",
        "--build-arg UV_EXTRA_INDEX_URL"
    )

    if (Test-Path Env:DEFAULT_DOCKER_DOTNET_SDK_BASE_IMAGE) {
        $local:dockerArgsList += @(
            "--build-arg", "FROM_IMAGE=${env:DEFAULT_DOCKER_DOTNET_SDK_BASE_IMAGE}"
        )
    }
    $local:dockerArgsList += @(
        "-t", $ImageName,
        "."
    )

    $local:dockerBuildProcess = Start-Process -FilePath $DockerExec -WorkingDirectory $projectRootDirectory -ArgumentList $local:dockerArgsList -NoNewWindow -PassThru -Wait
    if ($local:dockerBuildProcess.ExitCode -ne 0)
    {
        throw "An error creating docker image occurred. Exit code: $($local:dockerBuildProcess.ExitCode)"
    }
}

function Test-Wheel {
    [CmdletBinding()]
    param (
        [string]$WheelFile,
        [string]$SourcePath,
        [string]$PythonVersion,
        [string]$DockerExec = "docker.exe",
        [string]$DockerIsolation = "process",
        [string]$ContainerName = "uiucprescon_ocr_tester"
    )
    Write-Host "Testing wheel file: $WheelFile"
    if (!(Test-Path -Path $WheelFile)) {
        throw "Wheel file not found at path: $WheelFile"
    }
    $wheelInfo = Get-Item $WheelFile
    if ($wheelInfo.Extension -ne ".whl") {
        throw "The specified file is not a valid wheel file: $WheelFile"
    }
    $containerWorkingPath = 'c:\src'
    $containerDistPath = "c:\wheels"
    $containerCacheDir = "C:\Users\ContainerUser\Documents\cache"
    $local:PIP_CACHE_DIR = "${containerCacheDir}\pip_cache"
    $local:UV_PYTHON_INSTALL_DIR = "${containerCacheDir}\uvpython"
    $local:UV_CACHE_DIR = "${containerCacheDir}\uv_cache"
    $local:UV_TOOL_DIR = "${containerCacheDir}\uvtools"
    $hostWheelPath = Split-Path -Path $WheelFile -Parent
    $wheelFileName = Split-Path -Path $WheelFile -Leaf
    $wheelInContainer = Join-Path -Path $containerDistPath -ChildPath $wheelFileName

    $local:dockerArgsList = @(
        "run",
        "--isolation", $DockerIsolation,
        "--platform windows/amd64",
        "--rm",
        "--workdir=${containerWorkingPath}",
        "--mount type=volume,source=${ContainerName}Cache,target=${containerCacheDir}",
        "--mount type=bind,source=$(Resolve-Path $projectRootDirectory),target=${containerWorkingPath}",
        "--mount type=bind,source=$(Resolve-Path $hostWheelPath),target=${containerDistPath}",
        "-e UV_TOOL_DIR=${local:UV_TOOL_DIR}",
        "-e UV_PYTHON_INSTALL_DIR=${local:UV_PYTHON_INSTALL_DIR}",
        "-e UV_CACHE_DIR=${local:UV_CACHE_DIR}",
        "-e PIP_CACHE_DIR=${local:PIP_CACHE_DIR}"
    )

    $local:installCertsScript = "if (-not (Test-Path -Path ${containerCacheDir}\roots.sst)) { `
        Write-Host 'Generating root certificates...'; `
        certutil -generateSSTFromWU ${containerCacheDir}\roots.sst `
        Write-Host 'Generating root certificates... Done'; `
    };`
    certutil -addstore -f root ${containerCacheDir}\roots.sst | Out-Null;`
    Write-Host 'Certificate store updated successfully.'; `
    "
    $local:installRuntime = "if (-not (Test-Path -Path ${containerCacheDir}\vc_redist.x64.exe)) {
        Write-Host 'Downloading Visual C++ Redistributable...'; `
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12;Invoke-WebRequest https://aka.ms/vs/17/release/vc_redist.x64.exe -OutFile ${containerCacheDir}\vc_redist.x64.exe; `
        Write-Host 'Downloading Visual C++ Redistributable... Done'; `
    };`
    Write-Host 'Installing Visual C++ Redistributable.';
    Start-Process -filepath ${containerCacheDir}\vc_redist.x64.exe -ArgumentList '/install', '/passive', '/norestart' -Passthru | Wait-Process;`
    Write-Host 'Visual C++ Redistributable installed successfully.';
    "

    $local:dockerArgsList += @(
        '--entrypoint', 'powershell',
        'python:latest',
        "-c",
        "${local:installCertsScript};`
        ${local:installRuntime};`
        python -m pip install --disable-pip-version-check uv; uvx --constraint ${containerWorkingPath}\requirements-dev.txt --with tox-uv tox run -e py${PythonVersion} --installpkg $wheelInContainer --workdir `$env:TEMP"
    )
    $local:dockerVerifyProcess = Start-Process -FilePath $DockerExec -ArgumentList $local:dockerArgsList -NoNewWindow -PassThru -Wait
    if ($local:dockerVerifyProcess.ExitCode -ne 0) {
        throw "Verification failed with exit code: $($local:dockerVerifyProcess.ExitCode)"
    }
    Write-Host "Wheel file validation successful: $WheelFilePath"
}

function Build-Wheel {
    [CmdletBinding()]
    param (
        [string]$DockerImageName = "uiucprescon_ocr_builder",
        [string]$DockerExec = "docker.exe",
        [string]$DockerIsolation = "process",
        [string]$PythonVersion = "3.11",
        [string]$ContainerName = "uiucprescon_ocr_builder",
        [Parameter(Mandatory=$False)]
        [ValidateScript({ [string]::IsNullOrWhiteSpace($_) })]
        [string]$UVCacheDirPathInContainer,
        [Parameter(Mandatory=$False)]
        [ValidateScript({ [string]::IsNullOrWhiteSpace($_) })]
        [string]$PIPDowndloadCachePathInContainer,
        [Parameter(Mandatory=$False)]
        [ValidateScript({ ![string]::IsNullOrWhiteSpace($_) })]
        [string]$UVToolDirPathInContainer,
        [Parameter(Mandatory=$False)]
        [ValidateScript({ ![string]::IsNullOrWhiteSpace($_) })]
        [string]$UVPythonInstallDirPathInContainer
    )
    $containerDistPath = "c:\dist"
    $projectRootDirectory = (Get-Item $PSScriptRoot).Parent.FullName
    $outputDirectory = Join-Path -Path $projectRootDirectory -ChildPath "dist"
    if (!(Test-Path -Path $outputDirectory)) {
      New-Item -ItemType Directory -Path $outputDirectory | Out-Null
    }
    $containerSourcePath = "c:\src"
    $containerWorkingPath = "c:\build"
    $containerCacheDir = "C:\Users\ContainerUser\Documents\cache"
    $venv = "${containerCacheDir}\venv"

    $local:UV_PYTHON_INSTALL_DIR = "${containerCacheDir}\uvpython"
    $local:UV_TOOL_DIR = "${containerCacheDir}\uvtools"

    # This makes a symlink copy of the files mounted in the source. Any changes to the files will not affect outside the container
    $createShallowCopy = "foreach (`$item in `$(Get-ChildItem -Path $containerSourcePath)) { `
        Write-Host `"Creating symlink for `$item.Name`"; `
        `$LinkPath = Join-Path -Path $containerWorkingPath -ChildPath `$item.Name ; `
        New-Item -ItemType SymbolicLink -Path `$LinkPath -Target `$item.FullName | Out-Null `
    }"

    $local:dockerArgsList = @(
        "run",
        "--isolation", $DockerIsolation,
        "--platform windows/amd64",
        "--rm",
        "--workdir=${containerWorkingPath}",
        "--mount type=volume,source=${ContainerName}Cache,target=${containerCacheDir}",
        "--mount type=bind,source=$(Resolve-Path $projectRootDirectory),target=${containerSourcePath}",
        "--mount type=bind,source=$(Resolve-Path $outputDirectory),target=${containerDistPath}"
    )

    if ($PSBoundParameters.ContainsKey('PIPDowndloadCachePathInContainer')) {
        Write-Host "Using PIP cache directory: $PIPDowndloadCachePathInContainer"
        $local:dockerArgsList += @("-e", "PIP_CACHE_DIR=${PIPDowndloadCachePathInContainer}")
    }

    if ($PSBoundParameters.ContainsKey('UVToolDirPathInContainer')) {
        $local:dockerArgsList += @("-e", "UV_TOOL_DIR=${UVToolDirPathInContainer}")
    }

    if ($PSBoundParameters.ContainsKey('UVPythonInstallDirPathInContainer')) {
        $local:dockerArgsList += @("-e", "UV_PYTHON_INSTALL_DIR=${UVPythonInstallDirPathInContainer}")
    }

    if ($PSBoundParameters.ContainsKey('UVCacheDirPathInContainer')) {
        Write-Host "Using UV cache directory: $UVCacheDirPathInContainer"
        $local:dockerArgsList += @("-e", "UV_CACHE_DIR=${UVCacheDirPathInContainer}")
    }
    $local:dockerArgsList += @(
        '--entrypoint', 'powershell',
        $DockerImageName
        "-c",
        ${createShallowCopy};`
            "uv build --build-constraints=${containerSourcePath}\requirements-dev.txt --python=${PythonVersion} --wheel --out-dir=${containerDistPath} --config-setting=conan_cache=C:/Users/ContainerAdministrator/.conan2"
    )

    $local:dockerBuildProcess = Start-Process -FilePath $DockerExec -WorkingDirectory $(Get-Item $PSScriptRoot).Parent.FullName -ArgumentList $local:dockerArgsList -NoNewWindow -PassThru -Wait
    if ($local:dockerBuildProcess.ExitCode -ne 0)
    {
        throw "An error creating docker image occurred. Exit code: $($local:dockerBuildProcess.ExitCode)"
    }
}


function Get-Wheel {
    [CmdletBinding()]
    param (
        [string]$SearchPath,
        [string]$PythonVersion
    )
    if (!(Test-Path -Path $SearchPath)) {
        throw "Wheel file not found at path: $SearchPath"
    }
    $regex = "uiucprescon_ocr-.*cp$($PythonVersion -replace '\.', '').*\.whl$"
    $wheelFile = Get-ChildItem -Path $SearchPath -File | Where-Object { $_.Name -match $regex } | Select-Object -First 1
    if (-not $wheelFile) {
        throw "No wheel file for Python $PythonVersion in: $SearchPath"
    }
    $wheelInfo = Get-Item $wheelFile.FullName
    if ($wheelInfo.Extension -ne ".whl") {
        throw "The specified file is not a valid wheel file: $SearchPath"
    }
    return $wheelInfo
}

# Build the Docker image for building the wheel
$local:buildDockerImageParams = @{
    ImageName = $DockerImageName
}

Build-DockerImage @local:buildDockerImageParams

# Build the wheel using the Docker image
$local:buildWheelParams = @{
    DockerImageName = $DockerImageName
    PythonVersion = $PythonVersion
}

if($PSBoundParameters.ContainsKey('PIPDowndloadCachePathInContainer')) {
    $local:buildDockerImageParams['PIPDowndloadCachePathInContainer'] = $PIPDowndloadCachePathInContainer
}

if($PSBoundParameters.ContainsKey('UVCacheDirPathInContainer')) {
    $local:buildDockerImageParams['UVCacheDirPathInContainer'] = $UVCacheDirPathInContainer
}

if($PSBoundParameters.ContainsKey('UVPythonInstallDirPathInContainer')) {
    $local:buildWheelParams['UVPythonInstallDirPathInContainer'] = $UVPythonInstallDirPathInContainer
}

if($PSBoundParameters.ContainsKey('UVToolDirPathInContainer')) {
    $local:buildWheelParams['UVToolDirPathInContainer'] = $UVToolDirPathInContainer
}

Build-Wheel @local:buildWheelParams

if ($Verify) {
    $local:distDirectory = Join-Path -Path (Get-Item $PSScriptRoot).Parent.FullName -ChildPath "dist"
    $local:wheelFile = Get-Wheel -SearchPath $local:distDirectory -PythonVersion $PythonVersion
    $local:projectRootDirectory = (Get-Item $PSScriptRoot).Parent.FullName
    $local:TestWheelParams = @{
        WheelFile       = $local:wheelFile
        SourcePath      = $local:projectRootDirectory
        PythonVersion   = $PythonVersion
    }

    Test-Wheel @local:TestWheelParams

#    $local:distDirectory = Join-Path -Path (Get-Item $PSScriptRoot).Parent.FullName -ChildPath "dist"
#    $local:wheelFile = Get-Wheel -SearchPath $local:distDirectory -PythonVersion $PythonVersion
#    $local:projectRootDirectory = (Get-Item $PSScriptRoot).Parent.FullName
#    Test-Wheel -WheelFile $local:wheelFile -SourcePath $local:projectRootDirectory -PythonVersion $PythonVersion

}