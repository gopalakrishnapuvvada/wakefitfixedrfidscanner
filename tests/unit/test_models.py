"""Unit tests for core Pydantic models."""

from datetime import datetime, timezone
import pytest
from uaim_device.core.events import IdentificationEvent
from uaim_device.core.models import (
    ConnectionType,
    DeduplicationConfig,
    DeviceHealth,
    DeviceInfo,
    DeviceState,
    DeviceType,
    EventType,
    IdentifierType,
    ReadCycle,
    ReconnectConfig,
    RFIDTag,
)


def test_device_info_validation():
    info = DeviceInfo(
        device_id="RFID-001",
        name="Pallet Reader",
        device_type=DeviceType.RFID_FIXED,
        vendor="SICK",
        model="RFU630",
        connection_type=ConnectionType.ETHERNET,
        host="192.168.10.50",
        port=2111,
        station_id="STATION-01"
    )
    assert info.device_id == "RFID-001"
    assert info.port == 2111
    assert info.reconnect.enabled is True
    assert info.deduplication.window_ms == 500


def test_identification_event_defaults():
    evt = IdentificationEvent(
        device_id="RFID-001",
        device_type=DeviceType.RFID_FIXED,
        vendor="SICK",
        model="RFU630",
        event_type=EventType.IDENTIFICATION,
        identifier_type=IdentifierType.RFID_EPC,
        identifier="E20034120123456789ABCDEF",
        rssi=-48.0,
        antenna_id=2
    )
    assert evt.event_id.startswith("EVT-")
    assert evt.identifier == "E20034120123456789ABCDEF"
    assert evt.rssi == -48.0
    summary = evt.to_summary_dict()
    assert summary["device_id"] == "RFID-001"
    assert summary["ant"] == 2


def test_rfid_tag_model():
    tag = RFIDTag(
        epc="E200ABCD",
        tid="E2801234",
        antenna_id=1,
        rssi=-52.5,
        read_count=3
    )
    assert tag.epc == "E200ABCD"
    assert tag.read_count == 3
    assert tag.metadata == {}


def test_read_cycle_model():
    cycle = ReadCycle(cycle_id="RC-001", device_id="RFID-001")
    assert cycle.status == "OPEN"
    assert len(cycle.tags) == 0
