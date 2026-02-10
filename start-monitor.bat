@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ==========================================
echo   启动域名监控服务
echo ==========================================
echo.
python ipScan.py --monitor
pause
