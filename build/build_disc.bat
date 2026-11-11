@echo off
rem Overlay test: alpha 5 + item-page English overlay prototype (pgwork/SLPS_010.60_ovproto)
cd /d "%~dp0"
set MK=C:\PortableApps\mkpsxiso-2.30-win64\mkpsxiso.exe
if not exist "%MK%" set MK=C:\PortableApps\mkpsxiso-2.30-win64\bin\mkpsxiso.exe
"%MK%" -y ovtest85.xml > build_ovtest85_log.txt 2>&1
echo exit code %ERRORLEVEL% >> build_ovtest85_log.txt
