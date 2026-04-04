@echo off
setlocal

set TARGET=%1
if "%TARGET%"=="help" goto help

if "%TARGET%"=="configure" goto configure
if "%TARGET%"=="help" goto help

echo Unknown target: %TARGET%
echo.
goto help

:help
echo Usage: make.bat [target]
echo.
echo Targets:
echo   configure            Run the configuration script
echo   help                 Show this help
goto end

:configure
echo.
echo =========================================
echo  Configuring Jacazul AI Environment
echo =========================================
echo.
powershell.exe -ExecutionPolicy Bypass -File "scripts\configure.ps1"
echo.
echo Configuration complete.
goto end

:end
endlocal
