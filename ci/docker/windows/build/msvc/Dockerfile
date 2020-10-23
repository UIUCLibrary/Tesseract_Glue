# escape=`
ARG FROM_IMAGE=mcr.microsoft.com/dotnet/framework/sdk:4.8-windowsservercore-ltsc2019

FROM ${FROM_IMAGE} as certsgen
RUN certutil -generateSSTFromWU roots.sst

FROM ${FROM_IMAGE}
SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop';"]
RUN Get-ChildItem -Path 'C:\Program Files (x86)\Microsoft Visual Studio'
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
# First install visual studio with chocolatey
RUN New-Item -Path "c:\\" -Name "TEMP" -ItemType "directory"
RUN Invoke-WebRequest https://aka.ms/vs/16/release/vs_buildtools.exe -OutFile C:\TEMP\vs_buildtools.exe
RUN Invoke-WebRequest https://aka.ms/vs/16/release/channel -OutFile C:\TEMP\VisualStudio.chman
RUN Invoke-WebRequest https://aka.ms/vscollect.exe  -OutFile C:\TEMP\collect.exe

#RUN Start-Process -FilePath 'C:\TEMP\vs_buildtools.exe' -ArgumentList '--quiet --passive --installPath C:\\BuildTools --layout c:\\TEMP\\vs --add Microsoft.VisualStudio.Workload.VCTools' -Wait  ; ls c:\TEMP\vs
#WORKDIR c:/TEMP
#RUN tree /F
COPY ci/docker/shared/msvc/buildtools.json C:/TEMP/buildtools.json
#RUN Get-Content c:\\TEMP\\vs\\vs_installer.version.json
WORKDIR c:/TEMP
RUN ./vs_buildtools.exe --quiet  --installPath "C:\\BuildTools"  --wait --norestart --nocache --add Microsoft.VisualStudio.Workload.VCTools
#RUN ./vs_buildtools.exe --quiet  --installPath "C:\\BuildTools" --wait --norestart --nocache  -in .\\buildtools.json --add Microsoft.VisualStudio.Workload.VCTools
#RUN Start-Process -FilePath 'C:\TEMP\vs_buildtools.exe' -Wait  -ArgumentList '-in', 'c:\TEMP\buildtools.json' ;`
RUN if (! (Test-Path 'C:\BuildTools\Common7\Tools\VsDevCmd.bat')) `
    { `
#        C:\\TEMP\\Collect -? ; `
        C:\\TEMP\\collect.exe -nologo -zip:C:\\TEMP\\vslogs.zip; `
        Expand-Archive -Path vslogs.zip -DestinationPath C:\\TEMP\\logs\\ ; `
        ls logs ; `
        ls c:\\ ; `
        tree /F /A; `
        Get-Content -LiteralPath 'C:\\TEMP\\logs\\[Content_Types].xml' ; `
#        Get-Content -Path 'C:\\TEMP\\logs\\LocalAppData\\Microsoft\\VisualStudio\\Packages\\_Channels\\A0FE1051\\catalog.json' ; `
        throw 'VsDevCmd.bat not found' ; `
    }
WORKDIR c:/
#    Start-Process -FilePath 'C:\TEMP\vs_buildtools.exe' -Wait -PassThru -ArgumentList '-in', 'c:\TEMP\buildtools.json'
#    $res = Start-Process -FilePath 'C:\TEMP\vs_buildtools.exe' -Wait -PassThru `
#    -ArgumentList "--quiet", "--wait", "--norestart", "--nocache", "--installPath", "C:\BuildTools" ; `
#    Write-Host "Finished installing vs_buildtools with $res.ExitCode"
#     if($res.ExitCode  == "3010")`
#     { `
#        EXIT 0 ; `
#     } ;`
#ADD ci/docker/shared/chocolatey/visual_studio.config choco/visual_studio.config
#RUN choco install chocolatey-visualstudio.extension
#RUN Import-Module $Env:ChocolateyInstall\helpers\chocolateyInstaller.psm1 ;`
#    Import-Module $Env:ChocolateyInstall\extensions\chocolatey-visualstudio\*.psm1 ; `
#    Install-VisualStudio `
#    -PackageName 'visualstudio2019buildtools' `
#    -ApplicationName 'Microsoft Visual Studio Build Tools 2019' `
#    -Url 'https://download.visualstudio.microsoft.com/download/pr/6b655578-de8c-4862-ad77-65044ca714cf/5057f683178dbc0bb782519a0d8efcd13f0088ee9162fa0b183acbd84d507a10/vs_BuildTools.exe' `
#    -Checksum '5057F683178DBC0BB782519A0D8EFCD13F0088EE9162FA0B183ACBD84D507A10' `
#    -ChecksumType 'SHA256' `
#    -InstallerTechnology 'WillowVS2017OrLater' `
#    -Product 'BuildTools' `
#    -VisualStudioYear '2019' `
#    -Preview $false
#

#RUN $CocoPackageInstallConfig = \"c:\\choco\\visual_studio.config\" ; `
#    C:\ProgramData\chocolatey\bin\choco.exe sources ; `
#    C:\ProgramData\chocolatey\bin\choco.exe install -y --stoponfirstfailure --no-progress --verbose $CocoPackageInstallConfig; `
#    Remove-Item C:\Users\ContainerAdministrator\AppData\Local\Temp\chocolatey -Recurse ; `
#    refreshenv ; `
#    Remove-Item -Force -Recurse ${Env:TEMP}\* ; `
#    if (! (Test-Path 'C:\BuildTools\Common7\Tools\VsDevCmd.bat')) `
#    { `
#        [Console]::Error.WriteLine.Invoke('Missing expected file') ; `
#        Get-ChildItem -Path 'C:\Program Files (x86)\' ; `
#        Get-ChildItem -Path C:\\ProgramData\\chocolatey\\logs\\ -Recurse -Filter chocolatey.log | foreach { Get-Content $_.FullName } ; `
#        Get-ChildItem -Path C:\ProgramData\chocolatey\lib-bad\\ -Recurse -Filter ChocolateyInstall.ps1 | foreach { Get-Content $_.FullName } ; `
#        throw 'VsDevCmd.bat not found' ; `
#    } ; `
#    Write-Host "Finished installing Visual Studio Build Tools"
##        ls \"C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\" ; `


ADD ci/docker/windows/build/msvc/startup.bat c:\temp\startup.bat
RUN Set-ItemProperty -Path 'HKLM:\Software\Microsoft\Command Processor' -Name 'AutoRun' -Value "c:\temp\startup.bat"

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


ARG PYTHON_INSTALLER_URL=https://www.python.org/ftp/python/3.7.5/python-3.7.5-amd64.exe

RUN Invoke-WebRequest $Env:PYTHON_INSTALLER_URL -OutFile c:\python-installer.exe ; `
    Start-Process python-installer.exe -ArgumentList '/quiet InstallAllUsers=1 PrependPath=1' -Wait ; `
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


ADD conanfile.py C:/TEMP/
RUN conan install C:/TEMP/ --build  missing --no-import ;`
    conan remove * -b --src -f
ENV PIP_FIND_LINKS=c:/wheels
