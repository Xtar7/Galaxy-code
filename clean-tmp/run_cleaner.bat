@echo off
:: 系统软件清理工具 - Windows 批处理启动脚本
:: 右键 "以管理员身份运行" 此脚本

echo ============================================
echo   系统软件清理工具 v1.0
echo ============================================
echo.

:: 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo 请求管理员权限...
    powershell -Command "Start-Process '%~dp0run_cleaner.bat' -Verb RunAs"
    exit /b
)

:: 检查 uv 虚拟环境
if not exist "%~dp0.venv\Scripts\python.exe" (
    echo 错误: 未找到虚拟环境 (.venv)，请先运行: uv venv
    pause
    exit /b 1
)

echo Python: %~dp0.venv\Scripts\python.exe
echo 目录: %~dp0
echo.

:: 运行主程序
"%~dp0.venv\Scripts\python.exe" "%~dp0main.py" --cli --admin %*

pause
