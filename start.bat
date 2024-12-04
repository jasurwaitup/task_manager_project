@echo off
pip install -r requirements.txt
cd /d %~dp0bot
py main.py
pause