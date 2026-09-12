"""Integration tests for FastAPI REST API and WebSocket."""

import pytest
from httpx import ASGITransport, AsyncClient
from uaim_device.core.manager import GLOBAL_DEVICE_MANAGER
from uaim_device.core.models import (
    ConnectionType,
    DeduplicationConfig,
    DeviceInfo,
    DeviceType,
    ReconnectConfig,
)
from uaim_device.main import app, load_config_file


@pytest.fixture(autouse=True)
def ensure_devices_registered():
    """Ensure default test devices are loaded into GLOBAL_DEVICE_MANAGER."""
    if not GLOBAL_DEVICE_MANAGER.list_devices():
        raw_devices = load_config_file()
        for d in raw_devices:
            adapter_key = d.get("adapter", "sick_rfu630")
            info = DeviceInfo(
                device_id=d["device_id"],
                name=d["name"],
                device_type=DeviceType(d.get("type", "RFID_FIXED")),
                vendor=d.get("vendor", "GENERIC"),
                model=d.get("model", "DEVICE"),
                connection_type=ConnectionType(d.get("connection_type", "ETHERNET")),
                host=d.get("host"),
                port=d.get("port"),
                station_id=d.get("station_id"),
                enabled=d.get("enabled", True),
                reconnect=ReconnectConfig(**d.get("reconnect", {})),
                deduplication=DeduplicationConfig(**d.get("deduplication", {})),
                configuration=d.get("configuration", {})
            )
            GLOBAL_DEVICE_MANAGER.register_device(adapter_key, info)


@pytest.mark.asyncio
async def test_system_health_and_ready_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "UP"
        assert "configured_devices_count" in data

        res_ready = await client.get("/ready")
        assert res_ready.status_code == 200
        assert res_ready.json()["status"] == "READY"


@pytest.mark.asyncio
async def test_metrics_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/metrics")
        assert res.status_code == 200
        assert "uaim_identification_events_total" in res.text


@pytest.mark.asyncio
async def test_device_crud_and_simulate_scan():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. List devices
        res = await client.get("/api/v1/devices")
        assert res.status_code == 200
        devices = res.json()
        assert len(devices) >= 1
        dev_id = devices[0]["device_id"]

        # 2. Get specific device
        res_dev = await client.get(f"/api/v1/devices/{dev_id}")
        assert res_dev.status_code == 200
        assert res_dev.json()["device_id"] == dev_id

        # 3. Simulate RFID scan
        scan_payload = {
            "identifier": "E20034120123456789ABCDEF",
            "identifier_type": "RFID_EPC",
            "rssi": -48.0,
            "antenna_id": 1,
        }
        res_scan = await client.post(f"/api/v1/devices/{dev_id}/simulate-scan", json=scan_payload)
        assert res_scan.status_code == 200
        assert res_scan.json()["status"] == "ok"
        assert res_scan.json()["identifier"] == "E20034120123456789ABCDEF"

        # 4. Check device events buffer
        res_events = await client.get(f"/api/v1/devices/{dev_id}/events")
        assert res_events.status_code == 200
        events = res_events.json()
        assert len(events) >= 1
        assert events[-1]["identifier"] == "E20034120123456789ABCDEF"


@pytest.mark.asyncio
async def test_read_cycle_api_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        dev_id = "RFID-001"

        # Start read cycle
        res_start = await client.post(f"/api/v1/devices/{dev_id}/read-cycle/start?cycle_id=TEST-RC-101")
        assert res_start.status_code == 200
        assert res_start.json()["read_cycle"]["cycle_id"] == "TEST-RC-101"

        # Simulate scan in cycle
        await client.post(f"/api/v1/devices/{dev_id}/simulate-scan", json={
            "identifier": "E20034120123456789ABCD88",
            "identifier_type": "RFID_EPC",
            "rssi": -42.0
        })

        # Complete read cycle
        res_end = await client.post(f"/api/v1/devices/{dev_id}/read-cycle/complete")
        assert res_end.status_code == 200
        assert res_end.json()["status"] == "ok"
