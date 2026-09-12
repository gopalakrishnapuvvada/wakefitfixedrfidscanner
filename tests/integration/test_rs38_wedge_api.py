"""Integration tests for CipherLab RS38 (AS38N8RF4NSG1) Keyboard Wedge API and Multi-Modal Scans."""

import pytest
from httpx import ASGITransport, AsyncClient
from uaim_device.adapters.handheld.classifier import (
    ETX_CHAR,
    GS_CHAR,
    RS_CHAR,
    STX_CHAR,
)
from uaim_device.core.manager import GLOBAL_DEVICE_MANAGER
from uaim_device.core.models import (
    ClassificationConfig,
    ConnectionType,
    DeduplicationConfig,
    DeviceInfo,
    DeviceType,
    EntityType,
    IdentifierType,
    ReaderMode,
    ReconnectConfig,
    ScannerWedgeConfig,
)
from uaim_device.main import app


@pytest.fixture(autouse=True)
def setup_rs38_device():
    """Ensure HH-001 (CipherLab RS38) is registered in device manager."""
    info = DeviceInfo(
        device_id="HH-001",
        name="CipherLab RS38 Handheld Computer",
        device_type=DeviceType.RFID_HANDHELD,
        vendor="CipherLab",
        model="RS38 (AS38N8RF4NSG1)",
        connection_type=ConnectionType.HID_KEYBOARD,
        host="192.168.88.6",
        station_id="PACKING-01",
        enabled=True,
        reconnect=ReconnectConfig(enabled=False),
        deduplication=DeduplicationConfig(enabled=True, window_ms=1000),
        scanner=ScannerWedgeConfig(rfid_prefix="\x03", qr_prefix="\x02"),
        classification=ClassificationConfig(),
        configuration={"transport": "HID", "default_type": "RFID_EPC"},
    )
    GLOBAL_DEVICE_MANAGER.register_device("handheld", info)


@pytest.mark.asyncio
async def test_rs38_wedge_scan_rfid_etx_valid():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "raw_scan": f"{ETX_CHAR}E2801190A504006FA2BF55AB\x0D",
            "reader_mode": "RFID",
            "input_method": "KEYBOARD_WEDGE",
        }
        res = await client.post("/api/v1/devices/HH-001/scan", json=payload)
        assert res.status_code == 200
        data = res.json()

        assert data["status"] == "accepted"
        assert data["is_duplicate"] is False
        assert data["classification"]["is_valid"] is True
        assert data["classification"]["identifier_type"] == "RFID_EPC"
        assert data["classification"]["source"] == "RFID"
        assert data["classification"]["entity_type"] == "MATERIAL"
        assert data["classification"]["clean_value"] == "E2801190A504006FA2BF55AB"
        assert data["event"]["identifier"] == "E2801190A504006FA2BF55AB"


@pytest.mark.asyncio
async def test_rs38_wedge_scan_qr_stx_valid():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "raw_scan": f"{STX_CHAR}1001234567890\x0D",
            "reader_mode": "BARCODE",
            "input_method": "KEYBOARD_WEDGE",
        }
        res = await client.post("/api/v1/devices/HH-001/scan", json=payload)
        assert res.status_code == 200
        data = res.json()

        assert data["status"] == "accepted"
        assert data["classification"]["identifier_type"] == "MATERIAL_QR"
        assert data["classification"]["entity_type"] == "MATERIAL"
        assert data["classification"]["clean_value"] == "1001234567890"


@pytest.mark.asyncio
async def test_rs38_wedge_scan_rfid_valid():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "raw_scan": f"{RS_CHAR}E2801190A504006FA2BF55AB\x0D",
            "reader_mode": "RFID",
            "input_method": "KEYBOARD_WEDGE",
        }
        res = await client.post("/api/v1/devices/HH-001/scan", json=payload)
        assert res.status_code == 200
        data = res.json()

        assert data["status"] == "accepted"
        assert data["is_duplicate"] is False
        assert data["classification"]["is_valid"] is True
        assert data["classification"]["identifier_type"] == "RFID_EPC"
        assert data["classification"]["source"] == "RFID"
        assert data["classification"]["entity_type"] == "MATERIAL"
        assert data["classification"]["clean_value"] == "E2801190A504006FA2BF55AB"
        assert data["event"]["identifier"] == "E2801190A504006FA2BF55AB"


@pytest.mark.asyncio
async def test_rs38_wedge_scan_material_qr():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "raw_scan": f"{GS_CHAR}1001234567890\x0D",
            "reader_mode": "BARCODE",
            "input_method": "KEYBOARD_WEDGE",
        }
        res = await client.post("/api/v1/devices/HH-001/scan", json=payload)
        assert res.status_code == 200
        data = res.json()

        assert data["status"] == "accepted"
        assert data["classification"]["identifier_type"] == "MATERIAL_QR"
        assert data["classification"]["entity_type"] == "MATERIAL"
        assert data["classification"]["clean_value"] == "1001234567890"


@pytest.mark.asyncio
async def test_rs38_wedge_scan_work_order_qr():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload_200 = {
            "raw_scan": f"{GS_CHAR}2009876543210\x0D",
            "reader_mode": "BARCODE",
        }
        res_200 = await client.post("/api/v1/devices/HH-001/scan", json=payload_200)
        assert res_200.status_code == 200
        assert res_200.json()["classification"]["identifier_type"] == "WORK_ORDER_QR"
        assert res_200.json()["classification"]["entity_type"] == "WORK_ORDER"

        payload_400 = {
            "raw_scan": f"{GS_CHAR}4005544332211\x0D",
            "reader_mode": "BARCODE",
        }
        res_400 = await client.post("/api/v1/devices/HH-001/scan", json=payload_400)
        assert res_400.status_code == 200
        assert res_400.json()["classification"]["identifier_type"] == "WORK_ORDER_QR"
        assert res_400.json()["classification"]["entity_type"] == "WORK_ORDER"


@pytest.mark.asyncio
async def test_rs38_wedge_scan_unknown_qr():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "raw_scan": f"{GS_CHAR}999000111222\x0D",
            "reader_mode": "BARCODE",
        }
        res = await client.post("/api/v1/devices/HH-001/scan", json=payload)
        assert res.status_code == 200
        data = res.json()

        assert data["status"] == "rejected"
        assert data["error"] == "UNKNOWN_QR_PREFIX"
        assert data["event"]["event_type"] == "UNKNOWN_SCAN"


@pytest.mark.asyncio
async def test_rs38_wedge_scan_missing_prefix():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "raw_scan": "E2801190A504006FA2BF55AB\x0D",
        }
        res = await client.post("/api/v1/devices/HH-001/scan", json=payload)
        assert res.status_code == 200
        data = res.json()

        assert data["status"] == "rejected"
        assert data["error"] == "UNKNOWN_PREFIX"


@pytest.mark.asyncio
async def test_rs38_wedge_deduplication_window():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "raw_scan": f"{RS_CHAR}E2801190A504006FA2BF9999\x0D",
            "reader_mode": "RFID",
        }
        # 1. First scan -> Accepted
        res1 = await client.post("/api/v1/devices/HH-001/scan", json=payload)
        assert res1.status_code == 200
        assert res1.json()["status"] == "accepted"
        assert res1.json()["is_duplicate"] is False

        # 2. Immediate second scan (same identifier) -> Duplicate Suppressed
        res2 = await client.post("/api/v1/devices/HH-001/scan", json=payload)
        assert res2.status_code == 200
        assert res2.json()["status"] == "duplicate_suppressed"
        assert res2.json()["is_duplicate"] is True


@pytest.mark.asyncio
async def test_rs38_wedge_arbitrary_scan_sequence():
    """Verify arbitrary multi-modal scan sequences (RFID -> Material QR -> Work Order QR -> RFID)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sequence = [
            (f"{RS_CHAR}E2801190A504006FA2BF0001\x0D", "RFID_EPC", "MATERIAL"),
            (f"{GS_CHAR}100111222333\x0D", "MATERIAL_QR", "MATERIAL"),
            (f"{GS_CHAR}200444555666\x0D", "WORK_ORDER_QR", "WORK_ORDER"),
            (f"{RS_CHAR}E2801190A504006FA2BF0002\x0D", "RFID_EPC", "MATERIAL"),
            (f"{GS_CHAR}400777888999\x0D", "WORK_ORDER_QR", "WORK_ORDER"),
        ]

        for raw_scan, expected_type, expected_entity in sequence:
            res = await client.post("/api/v1/devices/HH-001/scan", json={"raw_scan": raw_scan})
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "accepted"
            assert data["classification"]["identifier_type"] == expected_type
            assert data["classification"]["entity_type"] == expected_entity


@pytest.mark.asyncio
async def test_rs38_diagnostic_key_event_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        key_payload = {
            "key": "F1",
            "code": "F1",
            "key_code": 112,
            "alt_key": False,
            "ctrl_key": False,
            "shift_key": False,
            "meta_key": False,
            "timestamp": 1726050000.0,
        }
        res = await client.post("/api/v1/devices/HH-001/diagnostic/key-event", json=key_payload)
        assert res.status_code == 200
        assert res.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_rs38_prometheus_metrics_exposition():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Ingest one valid scan and one unknown scan
        await client.post("/api/v1/devices/HH-001/scan", json={"raw_scan": f"{RS_CHAR}E2801190A504006FA2BF1234\x0D"})
        await client.post("/api/v1/devices/HH-001/scan", json={"raw_scan": "NO_PREFIX_SCAN\x0D"})

        res = await client.get("/metrics")
        assert res.status_code == 200
        text = res.text

        assert "uaim_scanner_scans_total" in text
        assert "uaim_scanner_unknown_scans_total" in text
        assert "uaim_scanner_duplicate_scans_total" in text
