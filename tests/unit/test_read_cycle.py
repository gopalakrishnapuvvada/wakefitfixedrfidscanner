"""Unit tests for ReadCycle and reading gate aggregation."""

import pytest
from uaim_device.core.events import IdentificationEvent
from uaim_device.core.models import DeviceType, EventType, IdentifierType
from uaim_device.processing.read_cycle import ReadCycleProcessor


def test_read_cycle_lifecycle():
    processor = ReadCycleProcessor()
    device_id = "RFID-PALLET-01"

    # 1. Start cycle
    cycle = processor.start_cycle(device_id, "RC-1001", station_id="GATE-01")
    assert cycle.status == "OPEN"
    assert cycle.cycle_id == "RC-1001"

    # 2. Add multiple tag observations
    evt1 = IdentificationEvent(
        device_id=device_id,
        device_type=DeviceType.RFID_FIXED,
        vendor="SICK",
        model="RFU630",
        event_type=EventType.IDENTIFICATION,
        identifier_type=IdentifierType.RFID_EPC,
        identifier="E200ABCD0001",
        rssi=-50.0,
        antenna_id=1,
    )
    evt2 = IdentificationEvent(
        device_id=device_id,
        device_type=DeviceType.RFID_FIXED,
        vendor="SICK",
        model="RFU630",
        event_type=EventType.IDENTIFICATION,
        identifier_type=IdentifierType.RFID_EPC,
        identifier="E200ABCD0002",
        rssi=-45.0,
        antenna_id=2,
    )
    # Repeated observation of tag 1 with stronger RSSI
    evt1_repeat = IdentificationEvent(
        device_id=device_id,
        device_type=DeviceType.RFID_FIXED,
        vendor="SICK",
        model="RFU630",
        event_type=EventType.IDENTIFICATION,
        identifier_type=IdentifierType.RFID_EPC,
        identifier="E200ABCD0001",
        rssi=-38.0,
        antenna_id=1,
    )

    processor.process_event(evt1)
    processor.process_event(evt2)
    processor.process_event(evt1_repeat)

    active = processor.get_active_cycle(device_id)
    assert active.total_unique_tags == 2
    assert active.total_observations == 3

    # Check that tag 1 has read_count 2 and peak RSSI -38.0
    tag1 = next(t for t in active.tags if t.epc == "E200ABCD0001")
    assert tag1.read_count == 2
    assert tag1.rssi == -38.0

    # 3. Complete cycle
    summary = processor.complete_cycle(device_id)
    assert summary is not None
    assert summary.event_type == EventType.READ_CYCLE_COMPLETED
    assert summary.read_cycle_id == "RC-1001"
    assert summary.metadata["total_unique_tags"] == 2
    assert summary.metadata["total_observations"] == 3
    assert "E200ABCD0001" in summary.metadata["epc_list"]
    assert "E200ABCD0002" in summary.metadata["epc_list"]
    assert processor.get_active_cycle(device_id) is None
