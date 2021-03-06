# escape=`
ARG FROM_IMAGE=mcr.microsoft.com/dotnet/framework/sdk:4.8-windowsservercore-ltsc2019

FROM ${FROM_IMAGE} as certsgen
RUN certutil -generateSSTFromWU roots.sst

FROM ${FROM_IMAGE} as VS_BASE
SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop';"]

# First install Visual Studio Build Tools
RUN Invoke-WebRequest https://aka.ms/vs/16/release/vs_buildtools.exe -OutFile ${Env:TEMP}\\vs_buildtools.exe ; `
    Invoke-WebRequest https://aka.ms/vs/16/release/channel -OutFile ${Env:TEMP}\\VisualStudio.chman ; `
    Invoke-WebRequest https://aka.ms/vscollect.exe  -OutFile ${Env:TEMP}\\collect.exe ; `
    Write-Host "Installing Visual Studio Build Tools" ; `
    Start-Process -NoNewWindow -FilePath $Env:TEMP\\vs_buildtools.exe -ArgumentList '--quiet  --installPath "C:\\BuildTools"  --wait --norestart --nocache --add Microsoft.VisualStudio.Workload.VCTools --add Microsoft.VisualStudio.Component.VC.CLI.Support --add Microsoft.VisualStudio.Component.VC.Tools.x86.x64 --add Microsoft.VisualStudio.Component.Windows10SDK.18362' -Wait  ; `
    Write-Host "Installing Visual Studio Build Tools - Done" ; `
    Write-Host "Testing for VsDevCmd.bat" ; `
    if (! (Test-Path 'C:\BuildTools\Common7\Tools\VsDevCmd.bat')) `
    { `
        Start-Process -NoNewWindow -FilePath $Env:TEMP\\collect.exe -ArgumentList '-nologo -zip:${Env:TEMP}\\vslogs.zip' -Wait; `
        Expand-Archive -Path vslogs.zip -DestinationPath $Env:TEMP\\logs\\ ; `
        ls c:\\ ; `
        tree /F /A; `
        Get-Content -LiteralPath '$Env:TEMP\\logs\\[Content_Types].xml' ; `
        throw 'VsDevCmd.bat not found' ; `
    } ; `
    Write-Host "Testing for VsDevCmd.bat - Found" ; `
    Write-Host "Cleaning up $Env:TEMP" ; `
    Remove-Item -Force -Recurse $Env:TEMP\* ; `
    Write-Host "Cleaning up $Env:TEMP - Done"

ADD ci/docker/windows/build/msvc/startup.bat c:\temp\startup.bat
RUN Set-ItemProperty -Path 'HKLM:\Software\Microsoft\Command Processor' -Name 'AutoRun' -Value "c:\temp\startup.bat"

# ==============================================================================
FROM VS_BASE as CHOCOLATEY_BASE
ARG CHOCOLATEY_SOURCE=https://chocolatey.org/api/v2

ARG ChocolateyEnvironmentDebug=false
ADD ci/docker/shared/chocolatey/install_choco.ps1 choco/install_choco.ps1
RUN Set-ExecutionPolicy Bypass -Scope Process -Force; `
    ./choco/install_choco.ps1 -packageRepo $env:CHOCOLATEY_SOURCE ; `
    choco feature enable --name="useEnhancedExitCodes" ; `
    choco feature disable --name="showDownloadProgress" ; `
    if( -not ([string]::IsNullOrEmpty($Env:CHOCOLATEY_SOURCE ))) `
    { `
        Write-Host "Adding $env:CHOCOLATEY_SOURCE to chocolatey sources" ; `
        choco source add -n=CHOCOLATEY_SOURCE --priority=1 -s=\"$env:CHOCOLATEY_SOURCE\"; `
        choco source remove -n=chocolatey ;`
    }; `
    Remove-Item C:\ProgramData\chocolatey\bin\cpack.exe ; `
    Remove-Item -Force -Recurse ${Env:TEMP}\*

# Install the rest of the packages that can be installed by chocolatey
ADD ci/docker/shared/chocolatey/packages.config choco/packages.config
RUN C:\ProgramData\chocolatey\bin\choco.exe sources ; `
    C:\ProgramData\chocolatey\bin\choco.exe install -y --stoponfirstfailure --no-progress choco/packages.config ;`
    Remove-Item C:\Users\ContainerAdministrator\AppData\Local\Temp\chocolatey -Recurse ; `
    Remove-Item -Force -Recurse ${Env:TEMP}\* ; `
    if (!(Test-Path 'C:\Program Files\Git\cmd\git.exe')) `
    { `
        throw 'git.exe not found' ; `
    }; `
    Write-Host "Finished install packages with Chocolatey"

FROM CHOCOLATEY_BASE as PYTHON_BASE
ARG PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.7.5/python-3.7.5-amd64.exe

RUN Invoke-WebRequest $Env:PYTHON_INSTALLER_URL -OutFile c:\python-installer.exe ; `
    Start-Process python-installer.exe -NoNewWindow -ArgumentList '/quiet InstallAllUsers=1 PrependPath=1' -Wait ; `
    Remove-Item c:\python-installer.exe -Force


ADD ci/docker/shared/python/requirements-ci.txt ci/docker/shared/python/requirements-extras.txt c:/requirements/

RUN python -m pip install --upgrade pip ; `
    pip install --upgrade setuptools ; `
    pip install wheel ; `
    pip install conan ; `
    pip wheel --no-cache --wheel-dir c:/wheels/ `
        -r c:/requirements/requirements-ci.txt ; `
    pip wheel --no-cache --wheel-dir c:/wheels/ `
         -r c:/requirements/requirements-extras.txt ; `
     pip install --no-index --find-links=c:/wheels/ `
         -r c:/requirements/requirements-ci.txt

FROM PYTHON_BASE
COPY ci/docker/shared/conan/remotes.json  C:/Users/ContainerAdministrator/.conan/remotes.json
ADD conanfile.py C:/TEMP/
RUN conan install C:/TEMP/ --build  missing --no-import ;`
    conan remove * -b --src -f ; `
    conan remove --locks
ENV PIP_FIND_LINKS=c:/wheels
