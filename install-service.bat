@echo off
cd /d "%~dp0"

echo ==========================================
echo   Install Domain Monitor Service (NSSM)
echo ==========================================
echo.

REM Check NSSM
set NSSM_PATH=nssm.exe
if not exist "%NSSM_PATH%" (
    echo [ERROR] nssm.exe not found
    echo.
    echo Please download NSSM and place it in current directory:
    echo Download: https://nssm.cc/download
    echo Or from: https://github.com/bmatzelle/nssm/releases
    echo.
    echo After download, extract and copy nssm.exe to: %CD%
    echo.
    pause
    exit /b 1
)

REM Check Python
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    echo Please ensure Python is installed and added to PATH
    echo.
    pause
    exit /b 1
)

REM Get Python path
for /f "delims=" %%i in ('where python') do set PYTHON_PATH=%%i

REM Get script directory
set SCRIPT_DIR=%~dp0
set SCRIPT_PATH=%SCRIPT_DIR%ipScan.py

REM Check script exists
if not exist "%SCRIPT_PATH%" (
    echo [ERROR] ipScan.py not found: %SCRIPT_PATH%
    pause
    exit /b 1
)

REM Service name
set SERVICE_NAME=DomainMonitor

echo Service Name: %SERVICE_NAME%
echo Python Path: %PYTHON_PATH%
echo Script Path: %SCRIPT_PATH%
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

REM Install service (single line command)
"%NSSM_PATH%" install %SERVICE_NAME% "%PYTHON_PATH%" "%SCRIPT_PATH% --monitor"

if errorlevel 1 (
    echo [ERROR] Service installation failed
    pause
    exit /b 1
)

REM Set service description
"%NSSM_PATH%" set %SERVICE_NAME% Description "Domain Monitor Service - Monitor domain availability and send SMS alerts"

REM Set working directory
"%NSSM_PATH%" set %SERVICE_NAME% AppDirectory "%SCRIPT_DIR%"

REM Set output logs
"%NSSM_PATH%" set %SERVICE_NAME% AppStdout "%SCRIPT_DIR%logs\service_stdout.log"
"%NSSM_PATH%" set %SERVICE_NAME% AppStderr "%SCRIPT_DIR%logs\service_stderr.log"

REM Create logs directory
if not exist "%SCRIPT_DIR%logs" mkdir "%SCRIPT_DIR%logs"

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
echo   Stdout: %SCRIPT_DIR%logs\service_stdout.log
echo   Stderr: %SCRIPT_DIR%logs\service_stderr.log
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
