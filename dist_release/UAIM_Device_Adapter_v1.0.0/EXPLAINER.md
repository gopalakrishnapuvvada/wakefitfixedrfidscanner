# Technical Explainer: Device Protocols, Configuration, Connection Lifecycles & Reading Mechanics

This document provides a comprehensive technical breakdown of the **UAIM Identification Device Adapter Framework**, detailing how the physical identification hardware is configured, connected, supervised, and read:
1. **SICK RFU630 Fixed UHF RFID Reader** (Ethernet/TCP CoLa-A SOPAS protocol)
2. **CipherLab RS38 Rugged Android Mobile Computer (`AS38N8RF4NSG1`)** (Multi-modal UHF RFID & 1D/2D Barcode scanner)

---

## 1. Architectural Foundation & Unified Lifecycle Contract

The UAIM Adapter framework isolates device-specific communication protocols (such as SICK CoLa-A, CipherLab Android DataWedge TCP streams, and HID keyboard wedges) behind a strict, vendor-agnostic contract defined by the `DeviceAdapter` abstract base class.

```
                      ┌─────────────────────────────────────────────────┐
                      │              UAIM Higher-Level Layer            │
                      │       (Traceability, Lite MES, AI Vision)       │
                      └────────────────────────┬────────────────────────┘
                                               │
                                      IdentificationEvent
                                               │
                      ┌────────────────────────┴────────────────────────┐
                      │                 DeviceManager                   │
                      │   (Normalizer ➔ Deduplicator ➔ Read Cycles)     │
                      └────────────────────────┬────────────────────────┘
                                               │
                      ┌────────────────────────┴────────────────────────┐
                      │                                                 │
      ┌───────────────┴──────────────┐                  ┌───────────────┴──────────────┐
      │      SickRFU630Adapter       │                  │       HandheldAdapter        │
      │   (Ethernet / TCP CoLa-A)    │                  │ (CipherLab RS38 AS38N8RF4NSG1)
      └───────────────┬──────────────┘                  └───────────────┬──────────────┘
                      │                                                 │
             SICK RFU630 Reader                                CipherLab RS38 Handheld
             (Fixed RFID Gate)                                 (UHF RFID & 1D/2D Imager)
```

### 1.1 Unified Connection State Machine

Every adapter transitions through a formal, deterministic state machine defined in `ConnectionStateMachine`:

```
                     ┌───────────────────┐
                     │   DISCONNECTED    │◄────────────────────────┐
                     └─────────┬─────────┘                         │
                               │ connect()                         │
                               ▼                                   │
                     ┌───────────────────┐                         │
                     │    CONNECTING     │                         │
                     └─────────┬─────────┘                         │
                               │ (Handshake Verified)              │ disconnect()
                               ▼                                   │
                     ┌───────────────────┐                         │
                     │     CONNECTED     │─────────────────────────┤
                     └───────┬───▲───────┘                         │
                     start() │   │ stop()                          │
                             ▼   │                                 │
                     ┌───────────┴───────┐                         │
        ┌───────────►│      RUNNING      │                         │
        │            └─────────┬─────────┘                         │
        │                      │ (Socket Drop / Timeout)           │
        │                      ▼                                   │
        │            ┌───────────────────┐                         │
        │            │       ERROR       │                         │
        │            └─────────┬─────────┘                         │
        │                      │ Auto-Supervisor Trigger           │
        │                      ▼                                   │
        │            ┌───────────────────┐                         │
        │            │   RECONNECTING    │─────────────────────────┘
        │            └─────────┬─────────┘   (Max Retries / Manual Cancel)
        │                      │ Exponential Backoff + Jitter
        └──────────────────────┘
```

| State | Description | Physical Link Status | Reading Status |
| :--- | :--- | :--- | :--- |
| `DISCONNECTED` | Device is offline; all transport resources and tasks are destroyed. | Closed | Stopped |
| `CONNECTING` | Low-level socket/port is establishing connection & performing initial handshake. | In Progress | Stopped |
| `CONNECTED` | Low-level link established and device identity verified; idle and ready. | Open | Stopped |
| `RUNNING` | Active operational mode; listening loops, event readers, and heartbeats are active. | Open | **Actively Reading & Emitting** |
| `STOPPING` | Reading loop is terminating; commands to pause hardware sensor sent. | Open | Pausing |
| `ERROR` | Connection drop, parse error, or hardware failure detected. | Faulted / Closed | Stopped |
| `RECONNECTING` | Automatic supervisor attempting reconnection using exponential backoff with randomized jitter. | Retrying | Waiting |

---

## 2. Device 1: SICK RFU630 (Fixed UHF RFID Reader)

> [!NOTE]
> For the dedicated, comprehensive guide covering hardware wiring, SOPAS ET configuration, CoLa-A telegram mechanics, PowerShell automation scripts, and troubleshooting, see **[SICK_RFID_READER.md](file:///d:/UAIM/Projects/Wakefit/FGLabelGenerationSystem/Connectionadapter/SICK_RFID_READER.md)**.

The `SickRFU630Adapter` (`uaim_device/adapters/sick_rfu630/adapter.py`) manages SICK industrial fixed RFID portal and gate readers (RFU620, RFU630, RFU650).

### 2.1 Communication Architecture & Network Topologies

- **Physical Medium**: Industrial Ethernet (RJ45 / M12 4-pin D-coded) over IPv4 TCP/IP.
- **Port Assignment**:
  - `2111`: Default SICK SOPAS ASCII CoLa port.
  - `2112`: SICK Ethernet Host Port (CoLa-A Command & Data streaming port).
- **Socket Role**:
  - The UAIM Adapter initiates an asynchronous TCP client connection (`asyncio.open_connection(host, port)`) to the SICK reader's IP (e.g. `192.168.1.246:2112`).
  - Enables bidirectional request-response CoLa commanding, periodic health probes, real-time tag write operations, and continuous asynchronous event ingestion.

### 2.2 SICK CoLa-A Telegram Structure

CoLa-A telegrams are framed by ASCII control bytes:
- `<STX>` (`0x02`): Start of Text delimiter.
- `<ETX>` (`0x03`): End of Text delimiter.

```
+-------+--------------------+-------+
| <STX> | CoLa-A Payload ... | <ETX> |
| 0x02  | ASCII text string  | 0x03  |
+-------+--------------------+-------+
```

### 2.3 SICK Transponder Memory Encoding / Tag Writing

The SICK RFU630 adapter supports writing new EPCs to transponders directly using CoLa-A method invocation:
- Non-Addressed Mode: `sMN TAextWriteTagData 0 0 1 2 6 32 +24 <NEW_EPC> 1`
- Addressed Mode: `sMN TAextWriteTagData 2 +24 <TARGET_EPC> 1 2 6 32 +24 <NEW_EPC> 1`

---

## 3. Device 2: CipherLab RS38 Rugged Android Mobile Computer (`AS38N8RF4NSG1`)

The `HandheldAdapter` (`uaim_device/adapters/handheld/adapter.py`) connects the **CipherLab RS38 Rugged Android Mobile Computer (Model: AS38N8RF4NSG1)**.

### 3.1 Transports Supported

1. **`TCP_STREAM` (Default)**:
   - Adapter starts an asynchronous TCP listener on `0.0.0.0:9001`.
   - CipherLab RS38 Software Reader / DataWedge pushes newline-terminated scan strings over Wi-Fi.
   - Multi-terminal support: multiple CipherLab RS38 devices stream concurrently.
2. **`HTTP_WEBHOOK`**:
   - Custom Android / web applications on the RS38 push scans as HTTP JSON payloads via REST endpoint `POST /api/v1/devices/{device_id}/simulate-scan`.
3. **`KEYSTROKE_EMULATION` (HID)**:
   - Emulates USB/Bluetooth barcode/RFID wedge typing directly into the workstation input buffer.

### 3.2 Reading & Multi-Modal Parsing

The `HandheldParser` parses heterogeneous payloads received from the CipherLab RS38:

1. **Structured JSON Payload** (from CipherLab Reader Utility / Android Intent broadcast):
   ```json
   {
     "identifier": "E2801190A504006FA2BF55AB",
     "type": "RFID_EPC",
     "rssi": -42.5,
     "antenna_id": 1,
     "metadata": {"model": "AS38N8RF4NSG1", "operator": "User1"}
   }
   ```
2. **Key-Value String Format**:
   - `EPC=E2801190A504006FA2BF55AB;RSSI=-44` -> Extracts EPC and RSSI.
   - `BARCODE=8901030992812;SYMBOLOGY=EAN13` -> Extracts 1D Barcode.
3. **2D QR Code Format**:
   - `QR:WF-MATTRESS-PALLET-0042` -> Extracts QR identifier and classifies as `IdentifierType.QR_CODE`.
4. **Raw Hex Pattern Matching**:
   - Matches `^[0-9A-Fa-f]{16,64}$` -> Classifies as `IdentifierType.RFID_EPC`.
   - General text -> Classifies as `IdentifierType.BARCODE`.

---

## 4. End-to-End Normalization, Deduplication & Read Cycles

Regardless of whether a tag or barcode was scanned by the SICK RFU630 gate reader or the CipherLab RS38 handheld computer, all raw observations flow through the unified pipeline:

```
 Raw IdentificationEvent from Adapter
                 │
                 ▼
 ┌──────────────────────────────────────────────────────────┐
 │ 1. EventNormalizer                                       │
 │    • Enforces UTC Timestamps                             │
 │    • RSSI Cutoff Filtering (e.g. drop if < -75 dBm)      │
 │    • Strips prefix (e.g. removes "QR:")                  │
 │    • Format transformation (HEX_CLEAN / ASCII_DECODED)   │
 │    • EPC Prefix Mask filtering (e.g. starts with "E200") │
 │    • Applies configured business prefix/suffix           │
 └─────────────────────────────┬────────────────────────────┘
                               │
                               ▼
 ┌──────────────────────────────────────────────────────────┐
 │ 2. RFIDDeduplicator                                      │
 │    • Sliding time-window cache (e.g. 500ms)              │
 │    • Key: Hash(device_id + identifier + read_cycle_id)   │
 │    • Drops duplicates; records Prometheus duplicate count│
 └─────────────────────────────┬────────────────────────────┘
                               │
                               ▼
 ┌──────────────────────────────────────────────────────────┐
 │ 3. ReadCycleProcessor (Gate / Pallet Aggregation)        │
 │    • If explicit Read Cycle is active:                   │
 │      - Appends unique tag to current cycle list          │
 │      - Emits READ_CYCLE_COMPLETED summary on gate close  │
 └─────────────────────────────┬────────────────────────────┘
                               │
                               ▼
 ┌──────────────────────────────────────────────────────────┐
 │ 4. EventDispatcher (Broadcast Fan-Out)                   │
 │    • WebSocket Clients (/ws/events)                      │
 │    • Recent Event Circular Buffer (last 500 events)      │
 │    • Prometheus Metrics (GLOBAL_METRICS)                 │
 └──────────────────────────────────────────────────────────┘
```

---

## 5. Comparison Matrix

| Feature | SICK RFU630 Fixed RFID | CipherLab RS38 Handheld (AS38N8RF4NSG1) |
| :--- | :--- | :--- |
| **Primary Protocol** | SICK CoLa-A (ASCII Telegrams) | TCP Stream / HTTP Webhook / HID Wedge |
| **Transport Layer** | Client TCP (`asyncio.open_connection`) | Server TCP Listener (`start_server`) / HTTP |
| **Framing Format** | `<STX>payload<ETX>` (`0x02`...`0x03`) | Line-delimited (`\r\n`) or JSON |
| **Device Identification** | `sRN DeviceIdent` query handshake | Client IP / JSON header handshake |
| **Keepalive / Liveness** | Periodic `sRN SCdevicestate` heartbeat (5s) | TCP socket liveness |
| **Auto-Reconnect** | Built-in supervisor (Exponential backoff + jitter) | Handheld client auto-reconnects to server |
| **Hardware Triggering** | `sMN Run` (Start) / `sMN Freeze` (Stop) | Software / Physical Gun Trigger |
| **Tag Write / Encode** | Direct CoLa-A (`TAwriteTagData` / `TAextWriteTagData`) | App / Reader Utility UHF writer |
| **Multi-Antenna Support** | Yes (Antennas 1 to 4 with individual RSSI) | Integrated internal antenna |
| **Read Cycle Integration** | Automated (Pallet gate photoeye start/stop) | Batch / Individual tag trigger |
