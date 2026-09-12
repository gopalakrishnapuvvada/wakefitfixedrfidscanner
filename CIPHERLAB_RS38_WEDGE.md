# CipherLab RS38 (AS38N8RF4NSG1) Keyboard-Wedge Integration Guide

## 1. Architecture Overview

The **CipherLab RS38 Rugged Android Mobile Computer** is integrated into the **UAIM Identification Device Adapter Platform** using **Hardware Keyboard-Wedge (HID Keyboard Emulation)**.

```
+-----------------------------------------------------------------------------------+
|               CipherLab RS38 (AS38N8RF4NSG1) Android Mobile Computer              |
|                                                                                   |
|  [ UHF RFID Engine ]                           [ 2D Barcode / QR Imager Engine ]  |
|         |                                                      |                  |
|         v (UHF Read Event)                                     v (Imager Read)    |
|  [ CipherLab Reader Config: Prefix = RS (0x1E) ]   [ CipherLab Reader Config: Prefix = GS (0x1D) ]
|         \                                                      /                  |
|          +----------------------------------------------------+                   |
|                                   |                                               |
|                    [ Hardware Keystroke Stream ]                                  |
|            (RS/GS Prefix + Payload Data + 0x0D Terminator)                        |
+-----------------------------------|-----------------------------------------------+
                                    | USB / Bluetooth / Browser Focus
                                    v
+-----------------------------------------------------------------------------------+
|                  Browser Host (UAIM Web Console / Operator App)                   |
|                                                                                   |
|  [ scanner_wedge.js ]                                                             |
|    - Global Window Key Listener (50ms rapid keystroke framing buffer)             |
|    - Control Byte Framing Assertions: RS (0x1E) | GS (0x1D) | CR (0x0D)          |
|    - Client-side Classification for instantaneous operator visual feedback        |
|    - Diagnostic Byte Debugger (inspects invisible 0x1E / 0x1D control characters)  |
|    - Physical Trigger Key Event Monitor                                           |
+-----------------------------------|-----------------------------------------------+
                                    | HTTP POST /api/v1/devices/{device_id}/scan
                                    v
+-----------------------------------------------------------------------------------+
|                     FastAPI Backend (UAIM Device Adapter Core)                    |
|                                                                                   |
|  [ RS38ScanClassifier ] (Authoritative Server Business Rule Engine)               |
|    - Stateless, order-independent classification                                  |
|    - RFID vs Material QR vs Work Order QR vs Unknown Scans                        |
|    - Diagnostic warning generation (e.g. reader mode mismatch)                    |
|                                                                                   |
|  [ Deduplication Engine ] (Sliding-window duplicate suppression)                  |
|                                                                                   |
|  [ Event Pipeline & Dispatcher ]                                                  |
|    - WebSocket Broadcast (/ws/events)                                             |
|    - Prometheus Metrics (/metrics)                                                |
+-----------------------------------------------------------------------------------+
```

---

## 2. Hardware Framing & Control Characters

The CipherLab RS38 Reader Utility must be configured to prepend standard non-printable ASCII control characters to separate UHF RFID reads from 2D barcode reads:

| Function | ASCII Control Character | Decimal | Hex Byte | Escape Notation |
| :--- | :--- | :--- | :--- | :--- |
| **RFID Start Prefix** | **Record Separator (RS)** | `30` | `0x1E` | `\x1E` |
| **QR / Barcode Prefix** | **Group Separator (GS)** | `29` | `0x1D` | `\x1D` |
| **Scan Terminator** | **Carriage Return (CR / ENTER)** | `13` | `0x0D` | `\x0D` / `\r` |

---

## 3. Authoritative Business Classification Rules

Classification is **stateless, deterministic, and order-independent**:

| Prefix | Payload Data Pattern | Inferred Mode | Source | Entity Type | Identifier Type | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `RS (0x1E)` | Hex Alphanumeric (16–64 chars) | `RFID` | `RFID` | `MATERIAL` | `RFID_EPC` | **Valid** |
| `RS (0x1E)` | Non-Hex string | `RFID` | `RFID` | `MATERIAL` | `RFID_EPC` | **Rejected** (`INVALID_EPC_HEX`) |
| `GS (0x1D)` | Starts with `100` (e.g. `100123456`) | `BARCODE` | `QR` | `MATERIAL` | `MATERIAL_QR` | **Valid** |
| `GS (0x1D)` | Starts with `200` (e.g. `200987654`) | `BARCODE` | `QR` | `WORK_ORDER` | `WORK_ORDER_QR` | **Valid** |
| `GS (0x1D)` | Starts with `400` (e.g. `400556677`) | `BARCODE` | `QR` | `WORK_ORDER` | `WORK_ORDER_QR` | **Valid** |
| `GS (0x1D)` | Other prefix (e.g. `300...`, `ABC...`) | `BARCODE` | `QR` | `UNKNOWN` | `UNKNOWN_SCAN` | **Rejected** (`UNKNOWN_QR_PREFIX`) |
| *None* | Un-prefixed / missing control byte | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN_SCAN` | **Rejected** (`UNKNOWN_PREFIX`) |
| *Any* | Empty string / whitespace | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN_SCAN` | **Rejected** (`EMPTY_SCAN`) |

---

## 4. REST API Reference

### 4.1 Ingest Scan (`POST /api/v1/devices/{device_id}/scan`)
Ingests raw keystroke buffer data from the client wedge:

**Request Body:**
```json
{
  "raw_scan": "\u001eE2801190A504006FA2BF55AB\r",
  "reader_mode": "RFID",
  "input_method": "KEYBOARD_WEDGE",
  "station_id": "PACKING-01"
}
```

**Accepted Response (`200 OK`):**
```json
{
  "status": "accepted",
  "is_duplicate": false,
  "event": {
    "event_id": "EVT-7A39B1E02F1C",
    "device_id": "HH-001",
    "device_type": "RFID_HANDHELD",
    "vendor": "CipherLab",
    "model": "RS38 (AS38N8RF4NSG1)",
    "event_type": "IDENTIFICATION",
    "identifier_type": "RFID_EPC",
    "identifier": "E2801190A504006FA2BF55AB",
    "reader_mode": "RFID",
    "source": "RFID",
    "entity_type": "MATERIAL",
    "input_method": "KEYBOARD_WEDGE",
    "diagnostic_warning": null,
    "timestamp": "2026-09-11T11:00:00.000Z"
  },
  "classification": {
    "raw_payload": "\u001eE2801190A504006FA2BF55AB\r",
    "clean_value": "E2801190A504006FA2BF55AB",
    "source": "RFID",
    "entity_type": "MATERIAL",
    "identifier_type": "RFID_EPC",
    "inferred_mode": "RFID",
    "is_valid": true,
    "error_code": null,
    "diagnostic_warning": null
  }
}
```

**Duplicate Suppressed Response (`200 OK`):**
```json
{
  "status": "duplicate_suppressed",
  "is_duplicate": true,
  "event": { ... },
  "classification": { ... }
}
```

### 4.2 Diagnostic Key Event Monitor (`POST /api/v1/devices/{device_id}/diagnostic/key-event`)
Logs browser-captured keydown events to detect physical trigger switch keycodes:

**Request Body:**
```json
{
  "key": "F1",
  "code": "F1",
  "key_code": 112,
  "alt_key": false,
  "ctrl_key": false,
  "shift_key": false,
  "meta_key": false,
  "timestamp": 1726050000.0
}
```

---

## 5. Web UI & Commissioning Debugger

The web UI contains a dedicated **📱 CipherLab RS38 Wedge & Debugger** tab:

1. **Live Mode & Status Header:** Real-time reader mode indicator (`RFID` / `BARCODE` / `UNKNOWN`) and mode origin tracking.
2. **Last Normalized Scan Card:** Displays clean value, identifier type, entity type, source, server dispatch status, and warning alerts.
3. **Commissioning Diagnostic Byte Inspector:** Visualizes non-printable prefix bytes (`[PREFIX: 0x1E (RS)]`, `[PREFIX: 0x1D (GS)]`, `[TERMINATOR: 0x0D (CR)]`) and raw byte counts.
4. **Physical Trigger Key Monitor:** Displays captured trigger key codes and timestamps.
5. **Quick Test Presets:** 1-click test buttons simulating exact hardware framing for RFID valid, Material QR 100, Work Order QR 200/400, Unknown QR 300, and Missing Prefix.
