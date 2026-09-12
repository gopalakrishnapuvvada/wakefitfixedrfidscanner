@echo off
title UAIM Industrial Hardware Simulator
echo ====================================================================
echo   Launching SICK RFU630, Handheld, and Barcode TCP Simulator...
echo   - SICK RFU630 TCP Port: 2111
echo   - Handheld RFID TCP Port: 9001
echo   - Barcode Scanner TCP Port: 9002
echo ====================================================================
"%~dp0UAIM_DeviceAdapter.exe" --simulator
pause
