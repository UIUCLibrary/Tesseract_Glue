# escape=`
ARG CONAN_USER_HOME=C:/Users/ContainerAdministrator
ARG VS_INSTALL_PATH="C:\BuildTools\"
ARG FROM_IMAGE=mcr.microsoft.com/dotnet/framework/sdk:4.8-windowsservercore-ltsc2019
FROM ${FROM_IMAGE} as certsgen
RUN certutil -generateSSTFromWU roots.sst

FROM ${FROM_IMAGE} as BASE_BUILDER

COPY ci/docker/shared/startup.bat c:/startup/startup.bat
ARG VS_INSTALL_PATH
RUN Invoke-WebRequest https://aka.ms/vs/17/release/vs_buildtools.exe -OutFile vs_buildtools.exe ; `
    Write-Host \"Installing Visual Studio Build Tools to ${Env:VS_INSTALL_PATH}\" ; `
    $ARGS_LIST = @(`
        '--quiet', `
        '--wait', `
        '--norestart', `
        '--nocache', `
        '--installPath', `
         ${Env:VS_INSTALL_PATH},`
        '--add Microsoft.VisualStudio.Workload.VCTools', `
        '--add Microsoft.VisualStudio.Component.VC.CLI.Support', `
        '--add Microsoft.VisualStudio.Component.VC.CoreBuildTools', `
        '--add Microsoft.VisualStudio.Component.VC.Tools.x86.x64', `
        '--add Microsoft.VisualStudio.ComponentGroup.VC.Tools.142.x86.x64', `
        '--add Microsoft.VisualStudio.Component.Windows10SDK.18362', `
        '--remove Microsoft.VisualStudio.Component.Windows10SDK.10240',`
        '--remove Microsoft.VisualStudio.Component.Windows10SDK.10586', `
        '--remove Microsoft.VisualStudio.Component.Windows10SDK.14393', `
        '--remove Microsoft.VisualStudio.Component.Windows81SDK'`
        ) ;`
    $process = Start-Process -NoNewWindow -PassThru -FilePath vs_buildtools.exe  `
    -ArgumentList $ARGS_LIST -Wait  ; `
    if ( $process.ExitCode -eq 0) `
    { `
        Write-Host 'Installing Visual Studio Build Tools - Done' ; `
    } `
    else `
    { `
        Get-ChildItem c:\\ ; `
        Get-ChildItem ${Env:ProgramFiles(x86)} ; `
        Get-ChildItem ${Env:VS_INSTALL_PATH} ; `
        Get-ChildItem ${Env:VS_INSTALL_PATH}\\Common7\\Tools ; `
        $message = \"Installing Visual Studio Build Tools exited with code $($process.ExitCode) \"; `
        Write-Host $message ;  `
        throw 'unable to continue' ; `
    } ; `
    Write-Host 'Testing for VsDevCmd.bat' ; `
    if (! (Test-Path "${Env:VS_INSTALL_PATH}\Common7\Tools\VsDevCmd.bat")) `
    { `
        Write-Host 'Testing for VsDevCmd.bat - Failed' ; `
        Start-Process -NoNewWindow -FilePath $Env:TEMP\\collect.exe -ArgumentList '-nologo -zip:${Env:TEMP}\\vslogs.zip' -Wait; `
        if (! (Test-Path '${Env:TEMP}\\vslogs.zip')) `
        { `
            throw 'VsDevCmd.bat not found and ${Env:TEMP}\\vslogs.zip never generated' ; `
        } ; `
        Expand-Archive -Path vslogs.zip -DestinationPath $Env:TEMP\\logs\\ ; `
        Get-Content -LiteralPath '$Env:TEMP\\logs\\[Content_Types].xml' ; `
        throw 'VsDevCmd.bat not found' ; `
    } ; `
    Write-Host "Testing for VsDevCmd.bat - Found" ; `
    Write-Host "Setting up compiler environment to run every time a command is run from CMD" ; `
    Set-ItemProperty -Path 'HKLM:\Software\Microsoft\Command Processor' -Name 'AutoRun' -Value "c:\startup\startup.bat" ; `
    Write-Host "Testing for CL" ; `
    cmd /S /C where cl ; `
    Write-Host "Testing for CL - Success"; `
    Write-Host "Removing build tools installer" ; `
    Remove-Item vs_buildtools.exe ; `
    Write-Host "Removing build tools installer - Done" ; `
    Write-Host "Finished installing Visual Studio Build Tools"


FROM BASE_BUILDER as CHOCOLATEY_BASE
ARG CHOCOLATEY_SOURCE=https://chocolatey.org/api/v2
ARG ChocolateyEnvironmentDebug=false
ADD ci/docker/shared/chocolatey/install_choco.ps1 choco/install_choco.ps1
RUN Set-ExecutionPolicy Bypass -Scope Process -Force; `
    ./choco/install_choco.ps1 -packageRepo $env:CHOCOLATEY_SOURCE ; `
    if( -not ([string]::IsNullOrEmpty($Env:CHOCOLATEY_SOURCE ))) `
    { `
        Write-Host "Adding $env:CHOCOLATEY_SOURCE to chocolatey sources" ; `
        choco source add -n=CHOCOLATEY_SOURCE --priority=1 -s=\"$env:CHOCOLATEY_SOURCE\"; `
        choco source remove -n=chocolatey ;`
    }; `
    Write-Host "Disabling Showing Download Progress" ; `
    choco feature disable -n=showDownloadProgress ; `
    Remove-Item -Force -Recurse ${Env:TEMP}\*


ADD ci/docker/shared/chocolatey/python.xml choco/python.config
RUN C:\ProgramData\chocolatey\bin\choco.exe install -y --stoponfirstfailure --no-progress --verbose choco/python.config ;`
    Remove-Item C:\Users\ContainerAdministrator\AppData\Local\Temp\chocolatey -Recurse ; `
    refreshenv ; `
    Remove-Item -Force -Recurse ${Env:TEMP}\* ; `
    py --list ;`
    py -3.7 --version ;  `
    py -3.8 --version ; `
    py -3.9 --version ; `
    py -3.10 --version ; `
    py -3.11 --version ; `
    Write-Host "Installing Python with Chocolatey - Done"

ADD ci/docker/shared/chocolatey/packages.config choco/packages.config
RUN C:\ProgramData\chocolatey\bin\choco.exe sources ; `
    C:\ProgramData\chocolatey\bin\choco.exe install -y --stoponfirstfailure --no-progress --verbose choco/packages.config ;`
    Remove-Item C:\Users\ContainerAdministrator\AppData\Local\Temp\chocolatey -Recurse ; `
    refreshenv ; `
    Remove-Item -Force -Recurse ${Env:TEMP}\* ; `
    if (!(Test-Path 'C:\Program Files\Git\cmd\git.exe')) `
    { `
        throw 'git.exe not found' ; `
    }; `
    Write-Host "Finished install packages with Chocolatey"


# ==============================================================================
FROM CHOCOLATEY_BASE as WHEEL_BUILDER_PY37
SHELL ["cmd", "/S", "/C" ]
COPY ci/docker/shared/python/requirements-ci.txt ci/docker/shared/python/requirements-extras.txt c:/requirements/
COPY requirements c:/requirements/requirements

ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL
ENV PY_PYTHON=3.7
ENV PIP_NO_CACHE_DIR=off
RUN py -m pip install --upgrade pip && `
    py -m pip install wheel && `
    py -m pip wheel -w c:\wheels\ --no-cache-dir `
      -r c:/requirements/requirements-ci.txt `
      -r c:/requirements/requirements-extras.txt

# ==============================================================================
FROM CHOCOLATEY_BASE as WHEEL_BUILDER_PY38
SHELL ["cmd", "/S", "/C" ]
COPY ci/docker/shared/python/requirements-ci.txt ci/docker/shared/python/requirements-extras.txt c:/requirements/
COPY requirements c:/requirements/requirements

ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL
ENV PY_PYTHON=3.8
ENV PIP_NO_CACHE_DIR=off
RUN py -m pip install --upgrade pip && `
    py -m pip install wheel && `
    py -m pip wheel -w c:\wheels\ --no-cache-dir `
      -r c:/requirements/requirements-ci.txt `
      -r c:/requirements/requirements-extras.txt

# ==============================================================================
FROM CHOCOLATEY_BASE as WHEEL_BUILDER_PY39
SHELL ["cmd", "/S", "/C" ]
COPY ci/docker/shared/python/requirements-ci.txt ci/docker/shared/python/requirements-extras.txt c:/requirements/
COPY requirements c:/requirements/requirements

ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL
ENV PY_PYTHON=3.9
ENV PIP_NO_CACHE_DIR=off
RUN py -m pip install --upgrade pip && `
    py -m pip install wheel && `
    py -m pip wheel -w c:\wheels\ --no-cache-dir `
      -r c:/requirements/requirements-ci.txt `
      -r c:/requirements/requirements-extras.txt

# ==============================================================================
FROM CHOCOLATEY_BASE as WHEEL_BUILDER_PY310
SHELL ["cmd", "/S", "/C" ]
COPY ci/docker/shared/python/requirements-ci.txt ci/docker/shared/python/requirements-extras.txt c:/requirements/
COPY requirements c:/requirements/requirements

ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL
ENV PY_PYTHON=3.10
ENV PIP_NO_CACHE_DIR=off
RUN py -m pip install --upgrade pip && `
    py -m pip install wheel && `
    py -m pip wheel -w c:\wheels\ --no-cache-dir `
      -r c:/requirements/requirements-ci.txt `
      -r c:/requirements/requirements-extras.txt

# ==============================================================================
FROM CHOCOLATEY_BASE as WHEEL_BUILDER_PY311
SHELL ["cmd", "/S", "/C" ]
COPY ci/docker/shared/python/requirements-ci.txt ci/docker/shared/python/requirements-extras.txt c:/requirements/
COPY requirements c:/requirements/requirements

ARG PIP_EXTRA_INDEX_URL
ARG PIP_INDEX_URL
ENV PY_PYTHON=3.11
ENV PIP_NO_CACHE_DIR=off
RUN py -m pip install --upgrade pip && `
    py -m pip install wheel && `
    py -m pip wheel -w c:\wheels\ --no-cache-dir `
      -r c:/requirements/requirements-ci.txt `
      -r c:/requirements/requirements-extras.txt

# ==============================================================================
FROM CHOCOLATEY_BASE as CONAN_BUILDER
ARG PIP_EXTRA_INDEX_URL
ARG CONAN_USER_HOME
ARG PIP_INDEX_URL
RUN python -m pip install --upgrade pip ; `
    pip install wheel ; `
    pip install conan cmake
COPY conanfile.py c:/temp/conanfile.py
COPY ci/docker/shared/conan/remotes.json  ${CONAN_USER_HOME}/.conan/remotes.json
COPY ci/docker/windows/tox/conan/profile.ini  ${CONAN_USER_HOME}/.conan/profiles/default
RUN conan config init ; `
    conan config set general.revisions_enabled=1

RUN conan install c:/temp/ --build missing --no-import; `
    conan install c:/temp/ --build missing -o "tesseract:shared=True" --no-import  ; `
    conan remove "*" -b --src -f ; `
    conan remove --lock
# ==============================================================================

FROM CHOCOLATEY_BASE

COPY --from=WHEEL_BUILDER_PY37 C:/wheels/ c:/wheels/
COPY --from=WHEEL_BUILDER_PY38 C:/wheels/ c:/wheels/
COPY --from=WHEEL_BUILDER_PY39 C:/wheels/ c:/wheels/
COPY --from=WHEEL_BUILDER_PY310 C:/wheels/ c:/wheels/
COPY --from=WHEEL_BUILDER_PY311 C:/wheels/ c:/wheels/

ENV PIP_FIND_LINKS=c:\wheels
COPY requirements c:/requirements/requirements
RUN python -m pip install pip --upgrade ; pip install -r c:/requirements/requirements/requirements_tox.txt conan cmake devpi_client

COPY --from=certsgen c:/roots.sst roots.sst
RUN certutil -addstore -f root roots.sst ; `
    del roots.sst
ARG CONAN_USER_HOME
COPY --from=CONAN_BUILDER ${CONAN_USER_HOME}/.conan/ ${CONAN_USER_HOME}/.conan/
ENV CONAN_USER_HOME=${CONAN_USER_HOME}
COPY conanfile.py c:/temp/conanfile.py
RUN conan install c:/temp/ --build outdated --no-import  ; `
    conan install c:/temp/ --build outdated -o "tesseract:shared=True" --no-import  ; `
    conan remove "*" -b --src -f ; `
    conan remove --locks

WORKDIR C:/src
CMD tox --workdir %TEMP%\tox\ -vv  --recreate
