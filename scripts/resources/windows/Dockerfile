# escape=`

# NOTICE: This Dockerfile needs to be run from the root of the repository. If you run it from the same location as this
#         file, it will not work because it needs access to files not in this directory. If you need to build this
#         Dockerfile directly, use the "docker run" command with the "-f scripts/resources/windows/Dockerfile" argument.


ARG FROM_IMAGE=mcr.microsoft.com/dotnet/framework/sdk:4.8.1

ARG VS_INSTALL_PATH="C:\BuildTools"

ARG CONAN_USER_HOME=C:/Users/ContainerAdministrator
# Path where conan data will be stored

ARG CONAN_HOME=${CONAN_USER_HOME}/.conan2

ARG CONAN_CENTER_PROXY_V2_URL=https://center2.conan.io
# If you want to use a diffrent remote for Conan, such as a proxy. Set the CONAN_CENTER_PROXY_V2_URL
# Not this is only for building the image. The actual conan center proxy URL is set in the remotes.json file.

ARG CHOCOLATEY_SOURCE=https://chocolatey.org/api/v2
ARG chocolateyVersion

FROM ${FROM_IMAGE} AS certsgen
RUN certutil -generateSSTFromWU roots.sst

FROM ${FROM_IMAGE} AS base_builder

SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop';"]

COPY scripts/resources/windows/msvc/visual_studio_config.json c:/setup/config.vsconfig
COPY scripts/resources/windows/msvc/install_msvc.ps1 c:/scripts/install_msvc.ps1
ARG VS_INSTALL_PATH
ARG VS_VERSION="2022"
ARG VS_DevCmdArguments="-arch=amd64"
ARG VS_DevPowershellArguments='-arch=amd64'
RUN c:/scripts/install_msvc.ps1 -InstallPath ${Env:VS_INSTALL_PATH} -VSConfigFile c:/setup/config.vsconfig -DevCmdArguments ${Env:VS_DevCmdArguments} -DevPowershellArguments ${Env:VS_DevPowershellArguments} -VSVersion ${Env:VS_VERSION}; `
    Write-Host "Note: Exporting This layer can take a while."

ARG CHOCOLATEY_SOURCE
ARG ChocolateyEnvironmentDebug=false
ARG chocolateyVersion
COPY scripts/resources/windows/chocolatey/install.ps1 c:/choco/install.ps1
COPY scripts/resources/windows/chocolatey/get_latest_chocolatey_url.ps1 c:/choco/get_latest_chocolatey_url.ps1
RUN Set-ExecutionPolicy Bypass -Scope Process -Force; `
    $chocolateyDownloadUrl = c:/choco/get_latest_chocolatey_url.ps1 -packageRepo $env:CHOCOLATEY_SOURCE; `
    c:/choco/install.ps1 -ChocolateyDownloadUrl $chocolateyDownloadUrl;`
    if( -not ([string]::IsNullOrEmpty($Env:CHOCOLATEY_SOURCE ))) `
    { `
        Write-Host "Adding $env:CHOCOLATEY_SOURCE to chocolatey sources" ; `
        choco source add -n=CHOCOLATEY_SOURCE --priority=1 -s=\"${env:CHOCOLATEY_SOURCE}\"; `
    }; `
    Write-Host "Disabling Showing Download Progress" ; `
    choco feature disable -n=showDownloadProgress ; `
    choco cache remove --confirm

COPY scripts/resources/windows/chocolatey/packages.config choco/packages.config
COPY scripts/resources/windows/chocolatey/verifyenv.ps1 c:/verifyenv.ps1
RUN C:\ProgramData\chocolatey\bin\choco.exe sources ; `
    C:\ProgramData\chocolatey\bin\choco.exe install -y --stoponfirstfailure --no-progress c:/choco/packages.config ;`
    refreshenv ; `
    choco cache remove --confirm;`
    Write-Host "Finished install packages with Chocolatey" ;`
    Write-Host "Verifying installed packages" ;`
    $env:Path = [System.Environment]::GetEnvironmentVariable(\"Path\",\"Machine\") + \";\" + [System.Environment]::GetEnvironmentVariable(\"Path\",\"User\") ; `
    c:/verifyenv.ps1

# ==============================================================================
FROM base_builder AS conan_builder
ARG UV_EXTRA_INDEX_URL
ARG UV_INDEX_URL
ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL
ARG CONAN_HOME
COPY scripts/resources/windows/conan/profile.ini  ${CONAN_HOME}/profiles/default
COPY ci/docker/shared/conan/remotes.json  ${CONAN_HOME}/remotes.json

COPY conanfile.py pyproject.toml uv.lock conan.lock c:/temp/
ARG CONAN_CENTER_PROXY_V2_URL
ENV UV_PROJECT c:\temp
ENV UV_PROJECT_ENVIRONMENT c:\temp\conanbuild
RUN uv run --only-group conan conan profile detect --exist-ok ; `
    if (${env:CONAN_CENTER_PROXY_V2_URL} -ne ($(Get-Content -Raw -Path "${Env:CONAN_HOME}/remotes.json") | ConvertFrom-Json).remotes[0].url) { `
      Write-Host "Using a proxy for conan center: $Env:CONAN_CENTER_PROXY_V2_URL" ; `
      Copy-Item -Path "${Env:CONAN_HOME}\remotes.json" -Destination "c:\remotes.json" ; `
      uv run --only-group conan conan remote update conan-center --url ${env:CONAN_CENTER_PROXY_V2_URL}; `
    }; `
    uv run --only-group conan --with ninja conan install c:/temp/conanfile.py --build missing -pr:b=default --conf=tools.cmake.cmaketoolchain:generator=Ninja ; `
    if ($LASTEXITCODE -ne 0) { `
      throw \"Command 'conan install' failed with exit code: $LASTEXITCODE\"`
    } ;`
    uv run --only-group conan conan cache clean "*" -b --source --build --temp ; `
    uv cache clean --no-progress ; `
    if (${env:CONAN_CENTER_PROXY_V2_URL} -ne ($(Get-Content -Raw -Path "${Env:CONAN_HOME}/remotes.json") | ConvertFrom-Json).remotes[0].url) { `
      Move-Item -Path "c:\remotes.json" -Destination "${Env:CONAN_HOME}\remotes.json" -Force ;`
    }; `
    Remove-Item -Path "${Env:UV_PROJECT_ENVIRONMENT}" -Recurse ; `
    Write-Host "Finished building/caching Conan packages"

# ==============================================================================

FROM base_builder
COPY --from=certsgen c:/roots.sst roots.sst
RUN certutil -addstore -f root roots.sst ; `
    del roots.sst

ARG CONAN_USER_HOME
ARG CONAN_HOME
COPY --from=conan_builder ${CONAN_HOME}/ ${CONAN_HOME}/

ENV CONAN_USER_HOME=${CONAN_USER_HOME}`
    CONAN_HOME=${CONAN_HOME}

LABEL purpose=ci
