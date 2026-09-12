# UAIM Identification Device Adapter - Desktop Deployment Guide

This folder is a standalone, self-contained distribution of the UAIM Identification Device Adapter Framework.
It runs natively on any Windows 10/11 or Windows Server desktop without requiring Python, Git, or administrative installer privileges.

## Package Contents

| File / Folder | Description |
| :--- | :--- |
| `UAIM_DeviceAdapter.exe` | Compiled native executable (FastAPI, Uvicorn, WebSockets, All Adapters) |
| `config.yaml` | Device configuration file (SICK RFU630, Handhelds, Barcode Scanners) |
| `start_server.bat` | 1-click launcher for the Adapter Server and Web UI |
| `launch_hardware_simulator.bat` | 1-click launcher for offline SICK RFU630 & Handheld TCP hardware simulator |
| `run_smoke_test.bat` | Automated test suite verifying health, WebSocket streams, and REST API |
| `web/` | Web Dashboard user interface assets (`index.html`, `styles.css`, `app.js`) |
| `QUICKSTART.txt` | Quick reference text guide |

## Quick Start Instructions

### 1. Copying to Target Desktop
Copy this entire folder (`UAIM_Device_Adapter_v1.0.0`) or the `UAIM_Device_Adapter_v1.0.0_Portable.zip` file to any location on the target PC (e.g., `C:\UAIM\DeviceAdapter` or Desktop).

### 2. Starting the Adapter Platform
Double-click **`start_server.bat`**.
- The console window will display the server initialization log.
- Your default web browser will automatically open to **`http://localhost:8000`**.

### 3. Testing with Built-in Hardware Simulator
If physical SICK RFU630 or barcode hardware is not yet wired to the network:
1. Double-click **`launch_hardware_simulator.bat`**.
2. In the Web Dashboard at `http://localhost:8000`, the configured `RFID-001` device will connect to `127.0.0.1:2111`.
3. In the Simulator window, press `1` to send a single tag, `2` for a 5-tag pallet burst, or `5` for continuous auto-scan mode.
4. Observe live tags appearing immediately on the **RFID Tag Matrix** and **Live Event Stream** in the Web UI.

### 4. Running Automated Smoke Verification
Double-click **`run_smoke_test.bat`** while the server is active.
It validates all 8 core platform interfaces:
- System Health Probe (`/health`)
- System Readiness Probe (`/ready`)
- Web Dashboard Root (`/`)
- Device Inventory API (`/api/v1/devices`)
- SICK RFU630 Scan Injection
- Barcode/QR Scan Injection
- Real-Time WebSocket Event Stream (`/ws/events`)
- Prometheus Metrics Exposition (`/metrics`)

### 5. Connecting to Physical Industrial Hardware
Edit `config.yaml` with any text editor (e.g., Notepad):
```yaml
devices:
  - device_id: RFID-001
    name: Pallet Gate SICK RFU630
    adapter: sick_rfu630
    host: 192.168.10.50   # Physical reader IP
    port: 2111            # Physical reader CoLa-A port
```
Save `config.yaml` and restart `start_server.bat`.
