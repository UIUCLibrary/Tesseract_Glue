# escape=`
ARG FROM_IMAGE=mcr.microsoft.com/dotnet/framework/sdk:4.8
FROM ${FROM_IMAGE}
SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop';"]

ARG CHOCOLATEY_REPO=https://chocolatey.org/api/v2

ARG ChocolateyEnvironmentDebug=false
ADD ci/docker/windows/build/msvc/chocolatey/install_choco.ps1 choco/install_choco.ps1
RUN Set-ExecutionPolicy Bypass -Scope Process -Force; `
    ./choco/install_choco.ps1 -packageRepo $env:CHOCOLATEY_REPO ; `
    if( -not ([string]::IsNullOrEmpty($Env:CHOCOLATEY_SOURCE ))) `
    { `
        choco source remove -n chocolatey ; choco source add -n=chocolatey_repo -s=\"$env:CHOCOLATEY_REPO\" ; `
    }; `
    Remove-Item C:\ProgramData\chocolatey\bin\cpack.exe

# Install packages that can be installed by chocolatey
ADD ci/docker/windows/build/msvc/chocolatey/packages.config choco/packages.config
RUN $SOURCE = $(if( -not ([string]::IsNullOrEmpty($Env:CHOCOLATEY_SOURCE ))) `
    { \"--source=$Env:CHOCOLATEY_SOURCE\" } `
    else `
    { "" }) ; `
    C:\ProgramData\chocolatey\bin\choco.exe install -y --stoponfirstfailure --no-progress $SOURCE choco/packages.config ;`
    Remove-Item C:\Users\ContainerAdministrator\AppData\Local\Temp\chocolatey -Recurse ; `
    Write-Host "Finished install packages with Chocolatey"

#ARG FROM_IMAGE=mcr.microsoft.com/dotnet/framework/sdk:4.8-windowsservercore-ltsc2019
#FROM ${FROM_IMAGE}
#
## Reset the shell.
#SHELL ["cmd", "/S", "/C"]
#RUN mkdir c:\\TEMP
#ADD https://aka.ms/vscollect.exe C:/TEMP/collect.exe

# Download channel for fixed install.
#ARG CHANNEL_URL=https://aka.ms/vs/16/release/channel
#ADD ${CHANNEL_URL} C:/TEMP/VisualStudio.chman
#
## Download and install Build Tools for Visual Studio 2017 for native desktop workload.
#
#ADD https://aka.ms/vs/16/release/vs_buildtools.exe C:/TEMP/vs_buildtools.exe
#
#RUN (C:\\TEMP\\vs_buildtools.exe `
#    --quiet --wait --norestart --nocache `
#    --channelUri C:\\TEMP\\VisualStudio.chman `
#    --installChannelUri C:\\TEMP\\VisualStudio.chman `
#    --add Microsoft.VisualStudio.Workload.VCTools `
#    --add Microsoft.VisualStudio.Component.Windows10SDK `
#    --add Microsoft.VisualStudio.Component.Windows10SDK.18362 `
#    --add Microsoft.VisualStudio.Component.VC.CMake.Project `
#    --add Microsoft.VisualStudio.Component.VC.Tools.x86.x64	 `
#    --includeRecommended `
#    --add Microsoft.VisualStudio.Component.NuGet `
#    --installPath C:\BuildTools `
#  || IF "%ERRORLEVEL%"=="3010" C:\TEMP\collect.exe -zip:C:\vslogs.zip && EXIT 0 )`
#  && C:\TEMP\collect.exe -zip:C:\vslogs.zip `
#  && @echo Cleaning up temp files`
#  && del /S /F /Q %temp% `
#  && del /S /F /Q %Windir%\Temp `
#  && @echo Done cleaning up files in temp directories
SHELL ["cmd", "/S", "/C"]
RUN REG ADD "HKLM\Software\Microsoft\Command Processor" /v AutoRun /t REG_SZ /d c:\temp\startup.bat
ADD ci/docker/windows/build/msvc/startup.bat c:\temp\startup.bat

SHELL ["powershell", "-command"]

#RUN $ErrorActionPreference = 'Stop'; `
#    Invoke-WebRequest https://github.com/ninja-build/ninja/releases/download/v1.9.0/ninja-win.zip -OutFile c:\ninja-win.zip; `
#    Expand-Archive -LiteralPath c:\ninja-win.zip -DestinationPath C:\ninja ; `
#    Remove-Item c:\ninja-win.zip -Force ; `
#    $env:PATH = $env:PATH + ';C:\ninja\;C:\ninja'; `
#    Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Environment\' -Name Path -Value $env:PATH

#RUN $ErrorActionPreference = 'Stop'; `
#    Invoke-WebRequest 'https://github.com/git-for-windows/git/releases/download/v2.12.2.windows.2/MinGit-2.12.2.2-64-bit.zip' -OutFile MinGit.zip ; `
#    Expand-Archive c:\MinGit.zip -DestinationPath c:\MinGit; `
#    $env:PATH = $env:PATH + ';C:\MinGit\cmd\;C:\MinGit\cmd'; `
#    Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Environment\' -Name Path -Value $env:PATH
#
#RUN $ErrorActionPreference = 'Stop'; `
#    Invoke-WebRequest 'https://www.nasm.us/pub/nasm/releasebuilds/2.14.02/win64/nasm-2.14.02-win64.zip' -OutFile nasm-win64.zip ; `
#    Expand-Archive c:\nasm-win64.zip -DestinationPath c:\nasm; `
#    Remove-Item c:\nasm-win64.zip -Force ;`
#    $env:PATH = $env:PATH + ';C:\nasm\nasm-2.14.02\;C:\nasm\nasm-2.14.02'; `
#    Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Environment\' -Name Path -Value $env:PATH
#
RUN certutil -generateSSTFromWU roots.sst ; `
    certutil -addstore -f root roots.sst ; `
    del roots.sst

ARG PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.7.5/python-3.7.5-amd64.exe

RUN $ErrorActionPreference = 'Stop'; `
    Invoke-WebRequest $Env:PYTHON_INSTALLER_URL -OutFile c:\python-installer.exe ; `
    Start-Process python-installer.exe -ArgumentList '/quiet InstallAllUsers=1 PrependPath=1' -Wait ; `
    Remove-Item c:\python-installer.exe -Force

ENV PIPENV_CACHE_DIR=c:\pipenv_cache `
    WORKON_HOME=c:\venvs `
    PIPENV_NOSPIN=True `
    PIP_DOWNLOAD_CACHE=c:\pip_cache

ADD ci/docker/windows/build/msvc/Profile.ps1 C:\Windows\System32\WindowsPowerShell\v1.0\Profile.ps1

RUN python -m pip install --upgrade pip ; `
    pip install --upgrade setuptools ; `
    pip install wheel pipenv sphinx tox mypy lxml pytest flake8 pytest-cov pytest-bdd
#
ADD Pipfile Pipfile.lock c:/temp/
RUN cd c:\temp ; pipenv install --dev --verbose

ENV TEMP c:\temp
ENV TMP c:\temp
ENV TMPDIR c:\temp
# TODO: set this
# REG ADD "HKEY_LOCAL_MACHINE\Software\Microsoft\Command Processor" /v AutoRun /t REG_SZ /d c:\BuildTools\Common7\Tools\vsdevcmd.bat"
