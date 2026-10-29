@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
python "%~dp0qr.py" --open %*
if errorlevel 1 pause
