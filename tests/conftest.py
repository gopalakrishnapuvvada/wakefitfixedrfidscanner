"""Pytest configuration and shared test fixtures."""

import pytest
from uaim_device.core.models import (
    ConnectionType,
    DeduplicationConfig,
    DeviceInfo,
    DeviceType,
    ReconnectConfig,
)


@pytest.fixture
def sample_rfu630_info() -> DeviceInfo:
    return DeviceInfo(
        device_id="TEST-RFID-01",
        name="Test RFU630 Reader",
        device_type=DeviceType.RFID_FIXED,
        vendor="SICK",
        model="RFU630",
        connection_type=ConnectionType.ETHERNET,
        host="127.0.0.1",
        port=12111,
        station_id="STATION-TEST",
        enabled=True,
        reconnect=ReconnectConfig(enabled=True, initial_delay=0.1, max_delay=1.0),
        deduplication=DeduplicationConfig(enabled=True, window_ms=300),
        configuration={"auto_start_on_connect": False, "enable_heartbeat": False}
    )


@pytest.fixture
def sample_handheld_info() -> DeviceInfo:
    return DeviceInfo(
        device_id="TEST-HH-01",
        name="Test CipherLab RS38 Handheld",
        device_type=DeviceType.RFID_HANDHELD,
        vendor="CipherLab",
        model="RS38 (AS38N8RF4NSG1)",
        connection_type=ConnectionType.TCP,
        host="127.0.0.1",
        port=19001,
        station_id="STATION-HH",
        enabled=True,
        configuration={"transport": "TCP", "default_type": "RFID_EPC"}
    )
