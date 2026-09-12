@echo off
title UAIM Automated Smoke Test
echo ====================================================================
echo   Executing Automated Smoke Test against local server...
echo ====================================================================
"%~dp0UAIM_DeviceAdapter.exe" --smoke-test
echo.
pause
