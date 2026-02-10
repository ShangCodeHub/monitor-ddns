@echo off
cd /d "%~dp0"

echo ==========================================
echo   Clean Build Files
echo ==========================================
echo.

echo Stopping DomainMonitor processes...
taskkill /F /IM DomainMonitor.exe >nul 2>&1
if errorlevel 1 (
    echo No running DomainMonitor process found
) else (
    echo DomainMonitor process stopped
)

echo.
echo Cleaning build files...

REM 删除构建目录
if exist "build" (
    echo Removing build directory...
    rmdir /S /Q "build" >nul 2>&1
)

REM 删除dist目录中的EXE
if exist "dist\DomainMonitor.exe" (
    echo Removing old EXE...
    del /F /Q "dist\DomainMonitor.exe" >nul 2>&1
)

REM 删除spec文件（可选）
if exist "DomainMonitor.spec" (
    echo Removing spec file...
    del /F /Q "DomainMonitor.spec" >nul 2>&1
)

echo.
echo [OK] Clean complete
echo.
pause
