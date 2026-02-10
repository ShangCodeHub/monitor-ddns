@echo off
cd /d "%~dp0"

echo ==========================================
echo   Uninstall Domain Monitor Service
echo ==========================================
echo.

set SERVICE_NAME=DomainMonitor
set NSSM_PATH=nssm.exe

REM Check NSSM exists
if not exist "%NSSM_PATH%" (
    echo [ERROR] nssm.exe not found
    echo Please ensure nssm.exe is in current directory
    pause
    exit /b 1
)

REM Check service exists
"%NSSM_PATH%" status %SERVICE_NAME% >nul 2>&1
if errorlevel 1 (
    echo [INFO] Service %SERVICE_NAME% does not exist, nothing to uninstall
    pause
    exit /b 0
)

echo Service Name: %SERVICE_NAME%
echo.

REM Stop service
echo Stopping service...
net stop %SERVICE_NAME% >nul 2>&1
timeout /t 2 >nul

REM Uninstall service
echo Uninstalling service...
"%NSSM_PATH%" remove %SERVICE_NAME% confirm

if errorlevel 1 (
    echo [ERROR] Service uninstall failed
    pause
    exit /b 1
)

echo.
echo ==========================================
echo   Service Uninstalled Successfully!
echo ==========================================
echo.
pause
