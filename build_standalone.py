"""Standalone Distribution Builder for UAIM Device Adapter Platform.

Builds a self-contained, portable Windows distribution folder and zip package
that can be copied to any desktop and launched/tested without Python installed.
"""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

WORKSPACE_ROOT = Path(__file__).parent.resolve()
DIST_RELEASE_DIR = WORKSPACE_ROOT / "dist_release"
PACKAGE_NAME = "UAIM_Device_Adapter_v1.0.0"
OUTPUT_FOLDER = DIST_RELEASE_DIR / PACKAGE_NAME


def clean_previous_builds():
    """Remove temporary build directories."""
    print("-> Cleaning previous build artifacts...")
    for p in [WORKSPACE_ROOT / "build", WORKSPACE_ROOT / "dist", DIST_RELEASE_DIR]:
        if p.exists():
            shutil.rmtree(p, ignore_errors=True)
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)


def build_pyinstaller_executable():
    """Compile UAIM Device Adapter into a standalone Windows executable."""
    print("-> Compiling standalone executable via PyInstaller...")
    
    hidden_imports = [
        "uvicorn",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.loops.asyncio",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.protocols.http.httptools_impl",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.protocols.websockets.websockets_impl",
        "fastapi",
        "fastapi.staticfiles",
        "fastapi.responses",
        "fastapi.middleware.cors",
        "websockets",
        "websockets.legacy",
        "websockets.legacy.server",
        "pydantic",
        "pydantic_settings",
        "yaml",
        "aiofiles",
        "uaim_device",
        "uaim_device.core",
        "uaim_device.core.adapter",
        "uaim_device.core.events",
        "uaim_device.core.exceptions",
        "uaim_device.core.health",
        "uaim_device.core.lifecycle",
        "uaim_device.core.manager",
        "uaim_device.core.models",
        "uaim_device.core.registry",
        "uaim_device.adapters",
        "uaim_device.adapters.sick_rfu630",
        "uaim_device.adapters.sick_rfu630.adapter",
        "uaim_device.adapters.sick_rfu630.connection",
        "uaim_device.adapters.sick_rfu630.models",
        "uaim_device.adapters.sick_rfu630.parser",
        "uaim_device.adapters.sick_rfu630.cola.commands",
        "uaim_device.adapters.sick_rfu630.cola.framing",
        "uaim_device.adapters.sick_rfu630.cola.parser",
        "uaim_device.adapters.handheld",
        "uaim_device.adapters.handheld.adapter",
        "uaim_device.adapters.handheld.classifier",
        "uaim_device.adapters.handheld.models",
        "uaim_device.adapters.handheld.parser",
        "uaim_device.adapters.handheld.transport",
        "uaim_device.processing",
        "uaim_device.processing.deduplicator",
        "uaim_device.processing.dispatcher",
        "uaim_device.processing.normalizer",
        "uaim_device.processing.read_cycle",
        "uaim_device.api.routes",
        "uaim_device.api.websocket",
        "uaim_device.metrics.metrics",
        "uaim_device.simulator",
        "uaim_device.smoke_test",
    ]

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--name",
        "UAIM_DeviceAdapter",
        "--add-data",
        f"{WORKSPACE_ROOT / 'uaim_device' / 'web'};uaim_device/web",
    ]

    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])

    cmd.append(str(WORKSPACE_ROOT / "uaim_device" / "main.py"))

    print(f"Running PyInstaller...")
    res = subprocess.run(cmd, cwd=WORKSPACE_ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"PyInstaller build failed with exit code {res.returncode}")
    print("-> PyInstaller compilation completed successfully!")


def copy_distribution_files():
    """Assemble the release package with binaries, configs, scripts, and documentation."""
    print("-> Assembling standalone release directory...")

    # 1. Copy compiled onedir output into destination
    dist_built = WORKSPACE_ROOT / "dist" / "UAIM_DeviceAdapter"
    if dist_built.exists():
        for item in dist_built.iterdir():
            dest = OUTPUT_FOLDER / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)

    # 2. Copy config.yaml and technical guides
    shutil.copy2(WORKSPACE_ROOT / "config.yaml", OUTPUT_FOLDER / "config.yaml")
    if (WORKSPACE_ROOT / "SICK_RFID_READER.md").exists():
        shutil.copy2(WORKSPACE_ROOT / "SICK_RFID_READER.md", OUTPUT_FOLDER / "SICK_RFID_READER.md")
    if (WORKSPACE_ROOT / "CIPHERLAB_RS38_WEDGE.md").exists():
        shutil.copy2(WORKSPACE_ROOT / "CIPHERLAB_RS38_WEDGE.md", OUTPUT_FOLDER / "CIPHERLAB_RS38_WEDGE.md")
    if (WORKSPACE_ROOT / "EXPLAINER.md").exists():
        shutil.copy2(WORKSPACE_ROOT / "EXPLAINER.md", OUTPUT_FOLDER / "EXPLAINER.md")

    # 3. Copy web UI assets directory for customization convenience
    web_dest = OUTPUT_FOLDER / "web"
    shutil.copytree(WORKSPACE_ROOT / "uaim_device" / "web", web_dest, dirs_exist_ok=True)

    # 4. Generate Launcher Batch Scripts
    create_batch_scripts()

    # 5. Generate Documentation
    create_documentation()


def create_batch_scripts():
    """Create 1-click Windows batch launcher scripts."""
    print("-> Generating Windows batch launchers...")

    # 1. start_server.bat
    start_server_bat = OUTPUT_FOLDER / "start_server.bat"
    start_server_content = (
        "@echo off\r\n"
        "title UAIM Device Adapter Platform\r\n"
        "echo ====================================================================\r\n"
        "echo   Starting UAIM Device Adapter Platform...\r\n"
        "echo   Web Dashboard: http://localhost:8000\r\n"
        "echo ====================================================================\r\n"
        "start \"\" http://localhost:8000\r\n"
        "\"%~dp0UAIM_DeviceAdapter.exe\"\r\n"
        "pause\r\n"
    )
    start_server_bat.write_text(start_server_content, encoding="utf-8")

    # 2. launch_hardware_simulator.bat
    simulator_bat = OUTPUT_FOLDER / "launch_hardware_simulator.bat"
    simulator_content = (
        "@echo off\r\n"
        "title UAIM Industrial Hardware Simulator\r\n"
        "echo ====================================================================\r\n"
        "echo   Launching SICK RFU630, Handheld, and Barcode TCP Simulator...\r\n"
        "echo   - SICK RFU630 TCP Port: 2111\r\n"
        "echo   - Handheld RFID TCP Port: 9001\r\n"
        "echo   - Barcode Scanner TCP Port: 9002\r\n"
        "echo ====================================================================\r\n"
        "\"%~dp0UAIM_DeviceAdapter.exe\" --simulator\r\n"
        "pause\r\n"
    )
    simulator_bat.write_text(simulator_content, encoding="utf-8")

    # 3. run_smoke_test.bat
    smoke_test_bat = OUTPUT_FOLDER / "run_smoke_test.bat"
    smoke_test_content = (
        "@echo off\r\n"
        "title UAIM Automated Smoke Test\r\n"
        "echo ====================================================================\r\n"
        "echo   Executing Automated Smoke Test against local server...\r\n"
        "echo ====================================================================\r\n"
        "\"%~dp0UAIM_DeviceAdapter.exe\" --smoke-test\r\n"
        "echo.\r\n"
        "pause\r\n"
    )
    smoke_test_bat.write_text(smoke_test_content, encoding="utf-8")


def create_documentation():
    """Create quickstart and deployment documentation."""
    print("-> Creating deployment documentation...")

    quickstart_txt = OUTPUT_FOLDER / "QUICKSTART.txt"
    quickstart_content = (
        "====================================================================\n"
        "  UAIM IDENTIFICATION DEVICE ADAPTER - PORTABLE DESKTOP PACKAGE\n"
        "====================================================================\n\n"
        "HOW TO RUN ON ANY WINDOWS DESKTOP (NO PYTHON REQUIRED):\n\n"
        "1. LAUNCH APPLICATION:\n"
        "   - Double-click 'start_server.bat'\n"
        "   - The server will start and automatically open the Web UI at:\n"
        "     http://localhost:8000\n\n"
        "2. OFFLINE TESTING WITHOUT PHYSICAL HARDWARE:\n"
        "   - In a separate window, double-click 'launch_hardware_simulator.bat'\n"
        "   - The simulator emulates SICK RFU630 (port 2111), Handheld RFID (port 9001),\n"
        "     and Barcode Scanners (port 9002).\n"
        "   - In the Web UI at http://localhost:8000, click 'Connect' on RFID-001,\n"
        "     or use the Interactive Simulator buttons to inject single tags or pallet bursts.\n\n"
        "3. AUTOMATED VERIFICATION:\n"
        "   - While 'start_server.bat' is running, double-click 'run_smoke_test.bat'.\n"
        "   - It will verify REST APIs, WebSockets, simulated scans, and metrics.\n\n"
        "4. CONFIGURATION FOR REAL INDUSTRIAL HARDWARE:\n"
        "   - Open 'config.yaml' in Notepad to configure your real reader IP & port:\n"
        "     Example: change host '127.0.0.1' to your physical SICK RFU630 IP (e.g. 192.168.10.50).\n\n"
        "====================================================================\n"
    )
    quickstart_txt.write_text(quickstart_content, encoding="utf-8")

    readme_md = OUTPUT_FOLDER / "README_DESKTOP_DEPLOYMENT.md"
    readme_content = (
        "# UAIM Identification Device Adapter - Desktop Deployment Guide\n\n"
        "This folder is a standalone, self-contained distribution of the UAIM Identification Device Adapter Framework.\n"
        "It runs natively on any Windows 10/11 or Windows Server desktop without requiring Python, Git, or administrative installer privileges.\n\n"
        "## Package Contents\n\n"
        "| File / Folder | Description |\n"
        "| :--- | :--- |\n"
        "| `UAIM_DeviceAdapter.exe` | Compiled native executable (FastAPI, Uvicorn, WebSockets, All Adapters) |\n"
        "| `config.yaml` | Device configuration file (SICK RFU630, Handhelds, Barcode Scanners) |\n"
        "| `start_server.bat` | 1-click launcher for the Adapter Server and Web UI |\n"
        "| `launch_hardware_simulator.bat` | 1-click launcher for offline SICK RFU630 & Handheld TCP hardware simulator |\n"
        "| `run_smoke_test.bat` | Automated test suite verifying health, WebSocket streams, and REST API |\n"
        "| `web/` | Web Dashboard user interface assets (`index.html`, `styles.css`, `app.js`) |\n"
        "| `QUICKSTART.txt` | Quick reference text guide |\n\n"
        "## Quick Start Instructions\n\n"
        "### 1. Copying to Target Desktop\n"
        "Copy this entire folder (`UAIM_Device_Adapter_v1.0.0`) or the `UAIM_Device_Adapter_v1.0.0_Portable.zip` file to any location on the target PC (e.g., `C:\\UAIM\\DeviceAdapter` or Desktop).\n\n"
        "### 2. Starting the Adapter Platform\n"
        "Double-click **`start_server.bat`**.\n"
        "- The console window will display the server initialization log.\n"
        "- Your default web browser will automatically open to **`http://localhost:8000`**.\n\n"
        "### 3. Testing with Built-in Hardware Simulator\n"
        "If physical SICK RFU630 or barcode hardware is not yet wired to the network:\n"
        "1. Double-click **`launch_hardware_simulator.bat`**.\n"
        "2. In the Web Dashboard at `http://localhost:8000`, the configured `RFID-001` device will connect to `127.0.0.1:2111`.\n"
        "3. In the Simulator window, press `1` to send a single tag, `2` for a 5-tag pallet burst, or `5` for continuous auto-scan mode.\n"
        "4. Observe live tags appearing immediately on the **RFID Tag Matrix** and **Live Event Stream** in the Web UI.\n\n"
        "### 4. Running Automated Smoke Verification\n"
        "Double-click **`run_smoke_test.bat`** while the server is active.\n"
        "It validates all 8 core platform interfaces:\n"
        "- System Health Probe (`/health`)\n"
        "- System Readiness Probe (`/ready`)\n"
        "- Web Dashboard Root (`/`)\n"
        "- Device Inventory API (`/api/v1/devices`)\n"
        "- SICK RFU630 Scan Injection\n"
        "- Barcode/QR Scan Injection\n"
        "- Real-Time WebSocket Event Stream (`/ws/events`)\n"
        "- Prometheus Metrics Exposition (`/metrics`)\n\n"
        "### 5. Connecting to Physical Industrial Hardware\n"
        "Edit `config.yaml` with any text editor (e.g., Notepad):\n"
        "```yaml\n"
        "devices:\n"
        "  - device_id: RFID-001\n"
        "    name: Pallet Gate SICK RFU630\n"
        "    adapter: sick_rfu630\n"
        "    host: 192.168.10.50   # Physical reader IP\n"
        "    port: 2111            # Physical reader CoLa-A port\n"
        "```\n"
        "Save `config.yaml` and restart `start_server.bat`.\n"
    )
    readme_md.write_text(readme_content, encoding="utf-8")


def create_zip_archive():
    """Create a single portable zip archive for easy copying."""
    print("-> Creating portable ZIP archive...")
    zip_path = DIST_RELEASE_DIR / f"{PACKAGE_NAME}_Portable.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(OUTPUT_FOLDER):
            for file in files:
                abs_file = Path(root) / file
                rel_file = abs_file.relative_to(DIST_RELEASE_DIR)
                zf.write(abs_file, rel_file)
    print(f"-> Portable ZIP created: {zip_path.resolve()} ({zip_path.stat().st_size / (1024*1024):.2f} MB)")


def main():
    print("================================================================")
    print("  BUILDING STANDALONE DESKTOP PACKAGE FOR UAIM DEVICE ADAPTER")
    print("================================================================")
    clean_previous_builds()
    build_pyinstaller_executable()
    copy_distribution_files()
    create_zip_archive()
    print("================================================================")
    print("  STANDALONE BUILD COMPLETED SUCCESSFULLY!")
    print(f"  Distribution Folder: {OUTPUT_FOLDER.resolve()}")
    print(f"  ZIP Archive:         {(DIST_RELEASE_DIR / f'{PACKAGE_NAME}_Portable.zip').resolve()}")
    print("================================================================")


if __name__ == "__main__":
    main()
