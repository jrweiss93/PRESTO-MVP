@echo off
title Presto Demo
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\run-demo.ps1"
if errorlevel 1 pause
