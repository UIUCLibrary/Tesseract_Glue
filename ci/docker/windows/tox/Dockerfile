# escape=`

# NOTICE: This Dockerfile needs to be run from the root of the repository. If you run it from the same location as this
#         file, it will not work because it needs access to files not in this directory. If you need to build this
#         Dockerfile directly, use the "docker run" command with the "-f ci/docker/windows/tox/Dockerfile" argument.


ARG FROM_IMAGE=mcr.microsoft.com/dotnet/framework/sdk:4.8.1

ARG VS_INSTALL_PATH="C:\BuildTools"

ARG CONAN_USER_HOME=C:/Users/ContainerAdministrator
ARG CONAN_CENTER_PROXY_V1_URL

ARG UV_CACHE_DIR=c:/users/containeradministrator/appdata/local/uv
ARG PIP_DOWNLOAD_CACHE=c:/users/containeradministrator/appdata/local/pip

ARG CHOCOLATEY_SOURCE=https://chocolatey.org/api/v2
ARG chocolateyVersion

FROM ${FROM_IMAGE} AS certsgen
RUN certutil -generateSSTFromWU roots.sst

FROM ${FROM_IMAGE} AS BASE_BUILDER

SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop';"]

COPY ci/docker/windows/tox/msvc/visual_studio_config.json c:/setup/config.vsconfig
COPY ci/docker/windows/tox/msvc/install_msvc.ps1 c:/scripts/install_msvc.ps1
ARG VS_INSTALL_PATH
ARG VS_VERSION="2022"
ARG VS_DevCmdArguments="-arch=amd64"
ARG VS_DevPowershellArguments='-arch=amd64'
RUN c:/scripts/install_msvc.ps1 -InstallPath ${Env:VS_INSTALL_PATH} -VSConfigFile c:/setup/config.vsconfig -DevCmdArguments ${Env:VS_DevCmdArguments} -DevPowershellArguments ${Env:VS_DevPowershellArguments} -VSVersion ${Env:VS_VERSION}; `
    Write-Host "Note: Exporting This layer can take a while."

ARG CHOCOLATEY_SOURCE
ARG ChocolateyEnvironmentDebug=false
ARG chocolateyVersion
COPY ci/docker/windows/tox/chocolatey/install.ps1 c:/choco/install.ps1
COPY ci/docker/windows/tox/chocolatey/get_latest_chocolatey_url.ps1 c:/choco/get_latest_chocolatey_url.ps1
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

COPY ci/docker/windows/tox/chocolatey/packages.config choco/packages.config
COPY ci/docker/windows/tox/chocolatey/verifyenv.ps1 c:/verifyenv.ps1
RUN C:\ProgramData\chocolatey\bin\choco.exe sources ; `
    C:\ProgramData\chocolatey\bin\choco.exe install -y --stoponfirstfailure --no-progress c:/choco/packages.config ;`
    refreshenv ; `
    choco cache remove --confirm;`
    Write-Host "Finished install packages with Chocolatey" ;`
    Write-Host "Verifying installed packages" ;`
    $env:Path = [System.Environment]::GetEnvironmentVariable(\"Path\",\"Machine\") + \";\" + [System.Environment]::GetEnvironmentVariable(\"Path\",\"User\") ; `
    c:/verifyenv.ps1

# ==============================================================================
FROM BASE_BUILDER AS CONAN_BUILDER
ARG UV_EXTRA_INDEX_URL
ARG UV_INDEX_URL
ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL
ARG CONAN_USER_HOME
COPY requirements-dev.txt c:/requirements/requirements-dev.txt
COPY conanfile.py c:/temp/conanfile.py
COPY ci/docker/shared/conan/remotes.json  ${CONAN_USER_HOME}/.conan/remotes.json
COPY ci/docker/windows/tox/conan/profile.ini  ${CONAN_USER_HOME}/.conan/profiles/default
ARG CONAN_CENTER_PROXY_V1_URL
ENV CONAN_REVISIONS_ENABLED=1
RUN uvx --constraint c:/requirements/requirements-dev.txt --with cmake conan config init ; `
    uvx --constraint c:/requirements/requirements-dev.txt --with cmake conan config set general.revisions_enabled=1 ; `
    if ( -not ([string]::IsNullOrEmpty($Env:CONAN_CENTER_PROXY_V1_URL ))) `
    { `
      Write-Host "Using a proxy for conan center: $Env:CONAN_CENTER_PROXY_V1_URL" ; `
      Copy-Item -Path "${Env:CONAN_USER_HOME}\.conan\remotes.json" -Destination "c:\remotes.json" ; `
      uvx --constraint=c:/requirements/requirements-dev.txt --with cmake conan remote remove conan-center ; `
      uvx --constraint=c:/requirements/requirements-dev.txt --with cmake conan remote add conan-center ${Env:CONAN_CENTER_PROXY_V1_URL} ; `
    }; `
    uvx --constraint c:/requirements/requirements-dev.txt --with cmake conan install c:/temp/ --build missing -o "tesseract:shared=True" --no-import -pr:b=default ; `
    if ($LASTEXITCODE -eq 1) { throw 'Exit code is 1' };`
    uvx --constraint c:/requirements/requirements-dev.txt --with cmake conan remove "*" -b --src -f ; `
    uvx --constraint c:/requirements/requirements-dev.txt --with cmake conan remove --lock ; `
    uv cache clean --no-progress;`
    if ( -not ([string]::IsNullOrEmpty($Env:CONAN_CENTER_PROXY_V1_URL ))) `
    {`
       Move-Item -Path "c:\remotes.json" -Destination "${Env:CONAN_USER_HOME}\.conan\remotes.json" -Force ;`
    }
# ==============================================================================

FROM BASE_BUILDER
COPY --from=certsgen c:/roots.sst roots.sst
RUN certutil -addstore -f root roots.sst ; `
    del roots.sst

ARG CONAN_USER_HOME
COPY --from=CONAN_BUILDER ${CONAN_USER_HOME}/.conan/ ${CONAN_USER_HOME}/.conan/
ENV CONAN_USER_HOME=${CONAN_USER_HOME}

ARG UV_CACHE_DIR
ARG PIP_DOWNLOAD_CACHE
ENV UV_INDEX_STRATEGY=unsafe-best-match
RUN New-Item -type directory -path ${Env:PIP_DOWNLOAD_CACHE} -Force | Out-Null ; `
    New-Item -type directory -path ${Env:UV_CACHE_DIR} -Force | Out-Null


WORKDIR C:/src
CMD tox --workdir %TEMP%\tox\ -vv  --recreate
