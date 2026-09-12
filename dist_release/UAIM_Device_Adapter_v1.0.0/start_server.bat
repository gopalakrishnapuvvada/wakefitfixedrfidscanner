@echo off
title UAIM Device Adapter Platform
echo ====================================================================
echo   Starting UAIM Device Adapter Platform...
echo   Web Dashboard: http://localhost:8000
echo ====================================================================
start "" http://localhost:8000
"%~dp0UAIM_DeviceAdapter.exe"
pause
