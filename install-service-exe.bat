@echo off
cd /d "%~dp0"

echo ==========================================
echo   Install Domain Monitor Service (EXE)
echo ==========================================
echo.

REM Check NSSM
set NSSM_PATH=nssm.exe
if not exist "%NSSM_PATH%" (
    echo [ERROR] nssm.exe not found
    echo.
    echo Please download NSSM and place it in current directory:
    echo Download: https://nssm.cc/download
    echo.
    pause
    exit /b 1
)

REM Check EXE exists
set EXE_PATH=%~dp0DomainMonitor.exe
if not exist "%EXE_PATH%" (
    REM Try dist directory
    set EXE_PATH=%~dp0dist\DomainMonitor.exe
    if not exist "%EXE_PATH%" (
        echo [ERROR] DomainMonitor.exe not found
        echo Please run build-exe.bat first, or ensure DomainMonitor.exe is in current directory
        echo.
        pause
        exit /b 1
    )
)

REM Check config.env exists
set CONFIG_PATH=%~dp0config.env
if not exist "%CONFIG_PATH%" (
    echo [WARNING] config.env not found, please ensure config file exists
    echo.
)

REM Service name
set SERVICE_NAME=DomainMonitor

echo Service Name: %SERVICE_NAME%
echo EXE Path: %EXE_PATH%
echo.

REM Check if service exists
"%NSSM_PATH%" status %SERVICE_NAME% >nul 2>&1
if not errorlevel 1 (
    echo [WARNING] Service %SERVICE_NAME% already exists
    echo.
    choice /C YN /M "Uninstall existing service and reinstall"
    if errorlevel 2 exit /b 0
    echo.
    echo Stopping and removing existing service...
    "%NSSM_PATH%" stop %SERVICE_NAME%
    timeout /t 2 >nul
    "%NSSM_PATH%" remove %SERVICE_NAME% confirm
    echo.
)

echo Installing service...
echo.

REM Get EXE directory
for %%F in ("%EXE_PATH%") do set EXE_DIR=%%~dpF

REM Install service (single line command)
"%NSSM_PATH%" install %SERVICE_NAME% "%EXE_PATH%" "--monitor"

if errorlevel 1 (
    echo [ERROR] Service installation failed
    pause
    exit /b 1
)

REM Set service description
"%NSSM_PATH%" set %SERVICE_NAME% Description "Domain Monitor Service - Monitor domain availability and send SMS alerts"

REM Set working directory
"%NSSM_PATH%" set %SERVICE_NAME% AppDirectory "%EXE_DIR%"

REM Set output logs
"%NSSM_PATH%" set %SERVICE_NAME% AppStdout "%EXE_DIR%logs\service_stdout.log"
"%NSSM_PATH%" set %SERVICE_NAME% AppStderr "%EXE_DIR%logs\service_stderr.log"

REM Create logs directory
if not exist "%EXE_DIR%logs" mkdir "%EXE_DIR%logs"

REM Set service start type to automatic
"%NSSM_PATH%" set %SERVICE_NAME% Start SERVICE_AUTO_START

REM Set auto restart on failure
"%NSSM_PATH%" set %SERVICE_NAME% AppRestartDelay 10000
"%NSSM_PATH%" set %SERVICE_NAME% AppThrottle 1500

echo.
echo ==========================================
echo   Service Installed Successfully!
echo ==========================================
echo.
echo Service Name: %SERVICE_NAME%
echo Start Type: Automatic
echo.
echo Management Commands:
echo   Start: net start %SERVICE_NAME%
echo   Stop: net stop %SERVICE_NAME%
echo   Status: sc query %SERVICE_NAME%
echo   Uninstall: %CD%\uninstall-service.bat
echo.
echo Log Files:
echo   Stdout: %EXE_DIR%logs\service_stdout.log
echo   Stderr: %EXE_DIR%logs\service_stderr.log
echo.
choice /C YN /M "Start service now"
if errorlevel 2 goto :end

echo.
echo Starting service...
net start %SERVICE_NAME%

if errorlevel 1 (
    echo [WARNING] Service start failed, please check log files
) else (
    echo [OK] Service started
)

:end
echo.
pause
