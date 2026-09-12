"""Unit tests for RFID tag deduplication."""

import time
import pytest
from uaim_device.core.events import IdentificationEvent
from uaim_device.core.models import DeduplicationConfig, DeviceType, EventType, IdentifierType
from uaim_device.processing.deduplicator import RFIDDeduplicator


def make_event(device_id: str, epc: str, read_cycle_id: str | None = None, ant: int = 1) -> IdentificationEvent:
    return IdentificationEvent(
        device_id=device_id,
        device_type=DeviceType.RFID_FIXED,
        vendor="SICK",
        model="RFU630",
        event_type=EventType.IDENTIFICATION,
        identifier_type=IdentifierType.RFID_EPC,
        identifier=epc,
        antenna_id=ant,
        read_cycle_id=read_cycle_id
    )


def test_deduplication_filters_repeated_tag():
    config = DeduplicationConfig(enabled=True, window_ms=200)
    dedup = RFIDDeduplicator(config)

    evt = make_event("RFID-001", "E20034120123456789ABCDEF")

    # 1st observation: unique
    assert dedup.is_unique(evt) is True
    # 2nd observation immediately: duplicate
    assert dedup.is_unique(evt) is False
    # 3rd observation immediately: duplicate
    assert dedup.is_unique(evt) is False
    assert dedup.total_duplicates_filtered == 2
    assert dedup.total_unique_passed == 1


def test_deduplication_allows_tag_after_window_expires():
    config = DeduplicationConfig(enabled=True, window_ms=100)
    dedup = RFIDDeduplicator(config)

    evt = make_event("RFID-001", "E20034120123456789ABCDEF")
    assert dedup.is_unique(evt) is True
    assert dedup.is_unique(evt) is False

    # Sleep past 100ms window
    time.sleep(0.12)

    # Now it is accepted again
    assert dedup.is_unique(evt) is True


def test_deduplication_does_not_mix_different_devices():
    config = DeduplicationConfig(enabled=True, window_ms=500)
    dedup = RFIDDeduplicator(config)

    evt1 = make_event("READER-A", "E20034120123456789ABCDEF")
    evt2 = make_event("READER-B", "E20034120123456789ABCDEF")

    # Both readers should independently record the EPC
    assert dedup.is_unique(evt1) is True
    assert dedup.is_unique(evt2) is True


def test_deduplication_disabled():
    config = DeduplicationConfig(enabled=False)
    dedup = RFIDDeduplicator(config)

    evt = make_event("RFID-001", "E20034120123456789ABCDEF")
    assert dedup.is_unique(evt) is True
    assert dedup.is_unique(evt) is True
    assert dedup.is_unique(evt) is True
    assert dedup.total_duplicates_filtered == 0
