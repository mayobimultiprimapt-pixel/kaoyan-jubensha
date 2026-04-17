@echo off
chcp 65001 > nul
title 考研剧本杀 · 手机访问服务

cd /d "%~dp0"

where python >nul 2>&1
if %errorlevel%==0 (
    python 启动手机服务.py
    goto :end
)
where py >nul 2>&1
if %errorlevel%==0 (
    py 启动手机服务.py
    goto :end
)

echo [错误] 未检测到 Python
echo 请先安装 Python 3: https://www.python.org/downloads/
echo 安装时勾选 "Add Python to PATH"
pause
exit /b 1

:end
pause
