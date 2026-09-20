# 系统软件清理工具 - PowerShell 启动脚本
# 用法: 右键 "以管理员身份运行" 此脚本
# 或直接双击运行（会自动请求管理员权限）

$ErrorActionPreference = "Stop"

# 获取脚本所在目录
$ScriptDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($ScriptDir)) {
    $ScriptDir = Get-Location
}

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  系统软件清理工具 v1.0" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# 请求管理员权限（如果尚未以管理员运行）
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "请求管理员权限..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit -ExecutionPolicy Bypass -File `"$ScriptDir\run_cleaner.ps1`"" -Verb RunAs
    exit
}

# 检查虚拟环境
$venvPython = Join-Path $ScriptDir ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "错误: 未找到虚拟环境 (.venv)，请先运行: uv venv" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "Python: $venvPython" -ForegroundColor Green
Write-Host "目录: $ScriptDir" -ForegroundColor Green
Write-Host ""

# 运行主程序
& $venvPython "$ScriptDir\main.py" --cli --admin @args

pause