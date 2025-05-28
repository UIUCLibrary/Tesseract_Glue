[CmdletBinding()]
param (
    [ValidateNotNullOrEmpty()]
    [string]$DockerImageName = "uiucprescon_ocr_builder",
    [ValidateNotNullOrEmpty()]
    [string]$PythonVersion = "3.11",
    [ValidateNotNullOrEmpty()][switch]$Verify
)

function Build-DockerImage {
    [CmdletBinding()]
    param (
        [string]$DockerfilePath = "ci/docker/windows/tox/Dockerfile",
        [string]$ImageName = "uiucprescon_ocr_builder",
        [string]$DockerExec = "docker.exe",
        [string]$DockerIsolation = "process"
    )

    $projectRootDirectory = (Get-Item $PSScriptRoot).Parent.FullName
    $dockerArgsList = @(
        "build",
        "--isolation", $DockerIsolation,
        "--platform windows/amd64",
        "-f", $DockerfilePath,
        "--build-arg PIP_EXTRA_INDEX_URL",
        "--build-arg PIP_INDEX_URL",
        "--build-arg CHOCOLATEY_SOURCE",
        "--build-arg CONAN_CENTER_PROXY_V1_URL",
        "--build-arg UV_INDEX_URL",
        "--build-arg UV_EXTRA_INDEX_URL",
        "--build-arg PIP_DOWNLOAD_CACHE=c:/users/containeradministrator/appdata/local/pip",
        "--build-arg UV_CACHE_DIR=c:/users/containeradministrator/appdata/local/uv"
    )
    if (Test-Path Env:DEFAULT_DOCKER_DOTNET_SDK_BASE_IMAGE) {
        $dockerArgsList += @(
            "--build-arg", "FROM_IMAGE=${env:DEFAULT_DOCKER_DOTNET_SDK_BASE_IMAGE}"
        )
    }
    $dockerArgsList += @(
        "-t", $ImageName,
        "."
    )

    $local:dockerBuildProcess = Start-Process -FilePath $DockerExec -WorkingDirectory $projectRootDirectory -ArgumentList $dockerArgsList -NoNewWindow -PassThru -Wait
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
    $local:UV_PYTHON_INSTALL_DIR = "${containerCacheDir}\uvpython"
    $local:UV_TOOL_DIR = "${containerCacheDir}\uvtools"
    $hostWheelPath = Split-Path -Path $WheelFile -Parent
    $wheelFileName = Split-Path -Path $WheelFile -Leaf
    $wheelInContainer = Join-Path -Path $containerDistPath -ChildPath $wheelFileName
    $dockerArgsList = @(
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
        '--entrypoint', 'powershell',
        'python:latest',
        "-c",
        "if (-not (Test-Path -Path ${containerCacheDir}\roots.sst)) { certutil -generateSSTFromWU ${containerCacheDir}\roots.sst }; certutil -addstore -f root ${containerCacheDir}\roots.sst; python -m pip install --disable-pip-version-check uv; uvx --constraint ${containerWorkingPath}\requirements-dev.txt --with tox-uv tox run -e py${PythonVersion} --installpkg $wheelInContainer --workdir `$env:TEMP"
    )
    $local:dockerVerifyProcess = Start-Process -FilePath $DockerExec -ArgumentList $dockerArgsList -NoNewWindow -PassThru -Wait
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
        [string]$ContainerName = "uiucprescon_ocr_builder"
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

    $dockerArgsList = @(
        "run",
        "--isolation", $DockerIsolation,
        "--platform windows/amd64",
        "--rm",
        "--workdir=${containerWorkingPath}",
        "--mount type=volume,source=${ContainerName}Cache,target=${containerCacheDir}",
        "--mount type=bind,source=$(Resolve-Path $projectRootDirectory),target=${containerSourcePath}",
        "--mount type=bind,source=$(Resolve-Path $outputDirectory),target=${containerDistPath}",
        "-e UV_TOOL_DIR=${local:UV_TOOL_DIR}",
        "-e UV_PYTHON_INSTALL_DIR=${local:UV_PYTHON_INSTALL_DIR}",
        '--entrypoint', 'powershell',
        $DockerImageName
        "-c",
        ${createShallowCopy};`
        "uv build --build-constraints=${containerSourcePath}\requirements-dev.txt --python=${PythonVersion} --wheel --out-dir=${containerDistPath} --config-setting=conan_cache=C:/Users/ContainerAdministrator/.conan --verbose"
    )

    $local:dockerBuildProcess = Start-Process -FilePath $DockerExec -WorkingDirectory $(Get-Item $PSScriptRoot).Parent.FullName -ArgumentList $dockerArgsList -NoNewWindow -PassThru -Wait
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



Build-DockerImage -ImageName $DockerImageName

Build-Wheel -PythonVersion $PythonVersion -DockerImageName $DockerImageName

if ($Verify) {
    $local:distDirectory = Join-Path -Path (Get-Item $PSScriptRoot).Parent.FullName -ChildPath "dist"
    $local:wheelFile = Get-Wheel -SearchPath $local:distDirectory -PythonVersion $PythonVersion
    $local:projectRootDirectory = (Get-Item $PSScriptRoot).Parent.FullName
    Test-Wheel -WheelFile $local:wheelFile -SourcePath $local:projectRootDirectory -PythonVersion $PythonVersion

}