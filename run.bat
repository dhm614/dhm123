@echo off
chcp 65001 >nul
title English Speaking Partner - CLI
cd /d "%~dp0"
python chat_cli.py
pause
