@echo off
cd /d "%~dp0"

echo ==========================================
echo   Build Python Script to EXE
echo ==========================================
echo.

REM Check Python
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    echo Please install Python and add it to PATH
    echo.
    pause
    exit /b 1
)

echo [1/3] Checking PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller
        echo Please check network or install manually: pip install pyinstaller
        echo.
        pause
        exit /b 1
    )
    echo [OK] PyInstaller installed
) else (
    echo [OK] PyInstaller found
)

echo.
echo [2/3] Checking script file...
if not exist "ipScan.py" (
    echo [ERROR] ipScan.py not found
    echo Current directory: %CD%
    echo.
    pause
    exit /b 1
)
echo [OK] ipScan.py found

echo.
echo [3/3] Building EXE...
echo This may take a few minutes, please wait...
echo.

REM Clean old build files
if exist "dist\DomainMonitor.exe" (
    echo Found old EXE file, trying to clean...
    REM Try to stop running process
    taskkill /F /IM DomainMonitor.exe >nul 2>&1
    timeout /t 1 >nul
    REM Delete old file
    del /F /Q "dist\DomainMonitor.exe" >nul 2>&1
    if exist "dist\DomainMonitor.exe" (
        echo [WARNING] Cannot delete old EXE file, it may be running
        echo Please close DomainMonitor.exe process manually and try again
        echo Or run clean-build.bat first
        echo.
        pause
        exit /b 1
    )
    echo [OK] Old file cleaned
    echo.
)

REM Build command (single line to avoid line break issues)
pyinstaller --onefile --name DomainMonitor --hidden-import alibabacloud_dysmsapi20170525 --hidden-import alibabacloud_tea_openapi --hidden-import alibabacloud_tea_util --hidden-import requests --console ipScan.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    echo.
    echo Possible reasons:
    echo   1. Dependencies not installed, run: pip install -r requirements.txt
    echo   2. Script has syntax errors
    echo   3. PyInstaller version issue
    echo.
    echo Please check the error messages above
    echo.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo   Build Success!
echo ==========================================
echo.
if exist "dist\DomainMonitor.exe" (
    echo [OK] EXE file created: dist\DomainMonitor.exe
    echo.
    echo File size:
    dir dist\DomainMonitor.exe | findstr DomainMonitor.exe
    echo.
) else (
    echo [WARNING] EXE file not found
    echo Please check dist directory
    echo.
)

echo Usage:
echo   1. Copy dist\DomainMonitor.exe and config.env to target directory
echo   2. Run install-service-exe.bat to install as Windows service
echo.
pause
