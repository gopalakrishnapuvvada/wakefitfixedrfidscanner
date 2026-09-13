# UAIM Identification Device Adapter Framework

Production-ready, asynchronous Python adapter platform for industrial identification hardware:
1. **SICK RFU630 Fixed UHF RFID Reader** (Ethernet/TCP CoLa-A SOPAS protocol)
2. **CipherLab RS38 Rugged Android Mobile Computer (`AS38N8RF4NSG1`)** (Multi-modal UHF RFID & 1D/2D Barcode scanner)

---

## Architecture Overview

```
                      UAIM APPLICATIONS
                              │
             ┌────────────────┴────────────────┐
             │                                 │
        Traceability                       Lite MES
             │                                 │
             └────────────────┬────────────────┘
                              │
                      Event Processing
                              │
                   IdentificationEvent
                              │
                    Event Dispatcher
                              │
             ┌────────────────┴────────────────┐
             │                                 │
       SICK RFU630                      CipherLab RS38
      Fixed RFID Adapter               Handheld Adapter
             │                                 │
        Ethernet / TCP                   TCP / HTTP / HID
        (CoLa-A SOPAS)                 (DataWedge / Intent)
             │                                 │
     SICK RFU630 Reader              CipherLab RS38 Terminal
     (Pallet Gate / Box)             (AS38N8RF4NSG1 Handheld)
```

### Core Architecture Principles
1. **Edge Normalization**: Vendor-specific protocols (SICK CoLa-A, CipherLab Android DataWedge, TCP streams, HTTP push, and HID keystroke emulation) are strictly isolated inside concrete adapters.
2. **Unified Event Contract**: All physical observations (RFID EPCs, TIDs, and 1D/2D Barcodes/QRs) are normalized into standard `IdentificationEvent` objects.
3. **Hardware Agnostic**: Downstream applications (MES, Traceability, Warehouse UI) never contain SICK, CipherLab, or socket-specific logic.
4. **24/7 Industrial Reliability**: Automatic exponential backoff reconnects, stream framing protection, memory-leak-safe deduplication caches, and structured async lifecycles.

---

## Key Features

- **SICK RFU630 Fixed RFID Reader**:
  - Native `asyncio.open_connection()` CoLa-A (Command Language ASCII) implementation with `<STX>` / `<ETX>` streaming frame decoder.
  - SOPAS variable and method query support (`DeviceIdent`, `SCdevicestate`, `Run`, `Freeze`).
  - Streaming RFID tag parser for single, burst, and key-value SOPAS payloads.
  - Real-time RFID tag write & encode engine (`sMN TAwriteTagData` / `TAextWriteTagData`) for non-addressed and addressed transponder encoding.
  - Heartbeat monitor for real TCP keepalive and latency calculation.
- **CipherLab RS38 Rugged Android Mobile Computer (AS38N8RF4NSG1)**:
  - Multi-modal scan capture: UHF RFID transponder reads + 1D/2D Barcode/QR imager reads.
  - Multi-transport: TCP network stream, HTTP REST / Webhook push, and USB/Bluetooth HID Keyboard wedge.
  - High-performance payload parser supporting JSON intent payloads, Key-Value pairs, hex EPCs, and raw barcode strings.
- **Processing Pipeline**:
  - **Normalizer**: Cleans hex formatting, standardizes station metadata, applies prefix/suffix rules, and enforces UTC timestamps.
  - **Deduplicator**: Sliding time-window tag deduplication with per-device keying.
  - **Read Cycle Engine**: Tracks discrete reading gate events (Pallet entering -> Tag accumulation -> Summary emission).
  - **Pluggable Event Dispatcher**: Broadcasts concurrently to WebSockets, REST clients, Prometheus, and logs.
- **Unified Control & Commissioning Center**:
  - Modern glassmorphic web dashboard at `http://localhost:8001/`.
  - Live RFID Tag Matrix with antenna & RSSI bars.
  - Transponder Memory Encoder (Tag Writer) for Gen2 EPC rewriting.
  - 2D QR Code & Barcode decoded inspector with one-click copy.
  - Live WebSocket stream ticker.
  - Interactive Scan Simulator and SICK CoLa direct console.

---

## Directory Structure

```
Connectionadapter/
├── pyproject.toml              # Build & dependency specification
├── README.md                   # Comprehensive system documentation
├── SICK_RFID_READER.md         # Dedicated SICK RFU630 technical & protocol guide
├── EXPLAINER.md                # Multi-device architecture & integration explainer
├── config.yaml                 # SICK RFU630 and CipherLab RS38 device configuration
├── uaim_device/
│   ├── main.py                 # FastAPI app, lifespans, CLI runner
│   ├── simulator.py            # Local hardware TCP mock server
│   ├── smoke_test.py           # Automated smoke test suite
│   ├── core/
│   │   ├── adapter.py          # DeviceAdapter ABC contract
│   │   ├── models.py           # DeviceInfo, DeviceHealth, RFIDTag, ReadCycle
│   │   ├── events.py           # IdentificationEvent model
│   │   ├── lifecycle.py        # Connection state machine & exponential backoff
│   │   ├── health.py           # HealthMonitor & telemetry
│   │   ├── registry.py         # AdapterRegistry dynamic discovery
│   │   ├── manager.py          # DeviceManager pipeline coordinator
│   │   └── exceptions.py       # Custom exception hierarchy
│   ├── adapters/
│   │   ├── sick_rfu630/        # SICK RFU630 CoLa-A adapter
│   │   │   ├── adapter.py
│   │   │   ├── connection.py
│   │   │   ├── parser.py
│   │   │   ├── models.py
│   │   │   └── cola/           # CoLa-A framing, parser, and commands
│   │   └── handheld/           # CipherLab RS38 (AS38N8RF4NSG1) adapter
│   │       ├── adapter.py
│   │       ├── classifier.py   # Authoritative RS38 Keyboard Wedge classifier
│   │       ├── models.py
│   │       ├── parser.py
│   │       └── transport.py
│   ├── processing/
│   │   ├── normalizer.py       # Standardizes identifiers & timestamps
│   │   ├── deduplicator.py     # Sliding time-window deduplication
│   │   ├── read_cycle.py       # Gate/pallet read cycle aggregator
│   │   └── dispatcher.py       # Pluggable event bus & WebSocket distributor
│   ├── api/
│   │   ├── routes.py           # REST endpoints & tag writing API
│   │   └── websocket.py        # WebSocket /ws/events streaming hub
│   ├── metrics/
│   │   └── metrics.py          # Prometheus-compatible metrics tracker
│   └── web/                    # Built-in Interactive Test Screen UI
│       ├── index.html
│       ├── styles.css
│       ├── scanner_wedge.js    # RS38 Keyboard Wedge & Debugger engine
│       └── app.js
└── tests/
    ├── conftest.py
    ├── fixtures/
    │   ├── fake_rfu630.py      # Async SICK RFU630 TCP mock server
    │   └── sample_telegrams.py
    ├── unit/                   # Models, framing, parser, dedup, cycles
    ├── adapters/               # SICK and CipherLab RS38 unit tests
    └── integration/            # TCP framing, reconnect, REST/WS e2e, Wedge API
```

---

## Quick Start

### 1. Run the Device Adapter Server
```bash
python -m uaim_device.main --config config.yaml
```
Access the Control Center in your browser at:
`http://localhost:8001/`

### 2. Dedicated Documentation Guides
- **SICK RFU630 Fixed RFID Reader Guide**: [`SICK_RFID_READER.md`](file:///d:/UAIM/Projects/Wakefit/FGLabelGenerationSystem/Connectionadapter/SICK_RFID_READER.md)
- **CipherLab RS38 Keyboard-Wedge Guide**: [`CIPHERLAB_RS38_WEDGE.md`](file:///d:/UAIM/Projects/Wakefit/FGLabelGenerationSystem/Connectionadapter/CIPHERLAB_RS38_WEDGE.md)
- **Multi-Device Architecture Explainer**: [`EXPLAINER.md`](file:///d:/UAIM/Projects/Wakefit/FGLabelGenerationSystem/Connectionadapter/EXPLAINER.md)

### 3. Run Automated Smoke Tests
```bash
python -m uaim_device.smoke_test
```

### 4. Run Pytest Suite
```bash
pytest -v
```
