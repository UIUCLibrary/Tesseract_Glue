# escape=`
ARG PIPX_HOME=c:\pipx
ARG VS_INSTALL_PATH="C:\BuildTools"
ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL
ARG UV_CACHE_DIR=c:/users/ContainerUser/appdata/local/uv
ARG FROM_IMAGE=mcr.microsoft.com/dotnet/framework/sdk:4.8.1
ARG CONAN_USER_HOME=C:/Users/ContainerAdministrator
ARG PIP_DOWNLOAD_CACHE=c:/users/containeradministrator/appdata/local/pip
FROM ${FROM_IMAGE} AS certsgen
RUN certutil -generateSSTFromWU roots.sst

FROM ${FROM_IMAGE} AS BASE_BUILDER

SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop';"]

COPY ci/docker/windows/tox/msvc/startup.bat c:/startup/startup.bat
COPY ci/docker/windows/tox/msvc/visual_studio_config.json c:/setup/config.vsconfig
COPY ci/docker/windows/tox/msvc/install_msvc.ps1 c:/scripts/install_msvc.ps1
ARG VS_INSTALL_PATH

RUN c:/scripts/install_msvc.ps1 ${Env:VS_INSTALL_PATH} c:/setup/config.vsconfig; `
    Get-ChildItem C:\Users\ContainerAdministrator\AppData\Local\Temp | Remove-Item -Recurse -Force -Verbose
ARG CHOCOLATEY_SOURCE=https://chocolatey.org/api/v2
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
RUN C:\ProgramData\chocolatey\bin\choco.exe sources ; `
    C:\ProgramData\chocolatey\bin\choco.exe install -y --stoponfirstfailure --no-progress --verbose choco/packages.config ;`
    Remove-Item C:\Users\ContainerAdministrator\AppData\Local\Temp\chocolatey -Recurse ; `
    refreshenv ; `
    choco cache remove --confirm ; `
    if (!(Test-Path 'C:\Program Files\Git\cmd\git.exe')) `
    { `
        throw 'git.exe not found' ; `
    }; `
    Write-Host "Finished install packages with Chocolatey"


# ==============================================================================
FROM BASE_BUILDER AS CONAN_BUILDER
ARG PIP_EXTRA_INDEX_URL
ARG CONAN_USER_HOME
ARG PIP_INDEX_URL
COPY requirements-dev.txt c:/requirements/requirements-dev.txt
COPY conanfile.py c:/temp/conanfile.py
COPY ci/docker/shared/conan/remotes.json  ${CONAN_USER_HOME}/.conan/remotes.json
COPY ci/docker/windows/tox/conan/profile.ini  ${CONAN_USER_HOME}/.conan/profiles/default

RUN python -m venv venv --upgrade-deps; `
    .\\venv\\Scripts\\activate.ps1 ; `
    pip install --disable-pip-version-check --no-cache-dir  uv ; `
    uv pip install -r c:/requirements/requirements-dev.txt --no-cache-dir; `
    conan config init ; `
    conan config set general.revisions_enabled=1 ; `
    conan install c:/temp/ --build missing --no-import; `
    conan install c:/temp/ --build missing -o "tesseract:shared=True" --no-import  ; `
    conan remove "*" -b --src -f ; `
    conan remove --lock ; `
    Remove-Item venv -Force -Recurse
# ==============================================================================

FROM BASE_BUILDER

COPY --from=certsgen c:/roots.sst roots.sst
RUN certutil -addstore -f root roots.sst ; `
    del roots.sst

ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL

ARG CONAN_USER_HOME
COPY --from=CONAN_BUILDER ${CONAN_USER_HOME}/.conan/ ${CONAN_USER_HOME}/.conan/
ENV CONAN_USER_HOME=${CONAN_USER_HOME}

ENV UV_INDEX_STRATEGY=unsafe-best-match
ARG UV_CACHE_DIR
ARG PIP_DOWNLOAD_CACHE
RUN New-Item -type directory -path ${Env:PIP_DOWNLOAD_CACHE} -Force; `
    New-Item -type directory -path ${Env:UV_CACHE_DIR} -Force


WORKDIR C:/src
CMD tox --workdir %TEMP%\tox\ -vv  --recreate
