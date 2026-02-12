@echo off
echo Starting Claude Code Rate Limit Monitor...
cd /d "%~dp0src"
start pythonw main.py
echo Monitor started! Check your system tray.
