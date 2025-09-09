@echo off
set "TASK_NAME=WinTelemetryServiceStartup"
set "EXE_PATH=%~dp0dist\WinTelemetryService.exe"

echo ===================================================
echo  WinTelemetryService Startup Installer
echo ===================================================
echo.
echo This script will create a scheduled task to run the application at logon.
echo It needs to be run as an Administrator.
echo.
echo Task Name: %TASK_NAME%
echo Executable Path: %EXE_PATH%
echo.

if not exist "%EXE_PATH%" (
    echo ERROR: WinTelemetryService.exe not found in 'dist' folder.
    echo Please run build.bat first.
    pause
    exit /b
)

echo Deleting any existing task with the same name...
schtasks /delete /tn "%TASK_NAME%" /f > nul 2>&1

echo Creating new scheduled task...
schtasks /create /tn "%TASK_NAME%" /tr "\"%EXE_PATH%\"" /sc onlogon /rl highest /f

echo.
echo Task created successfully. WinTelemetryService will now run automatically when you log in.
pause