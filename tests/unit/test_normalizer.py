"""Unit tests for EventNormalizer with commissioning rules."""

import binascii
from datetime import datetime, timezone
import pytest
from uaim_device.core.events import IdentificationEvent
from uaim_device.core.models import (
    DeviceType,
    EventType,
    FormatMode,
    IdentifierType,
    OutputFormattingConfig,
)
from uaim_device.processing.normalizer import EventNormalizer


def test_normalize_rfid_epc():
    evt = IdentificationEvent(
        device_id="  RFID-001  ",
        device_type=DeviceType.RFID_FIXED,
        vendor="SICK",
        model="RFU630",
        event_type=EventType.IDENTIFICATION,
        identifier_type=IdentifierType.RFID_EPC,
        identifier="e200 3412-0123 4567 89ab cdef",
        rssi=-48.7891,
        station_id=" GATE-1 "
    )

    norm = EventNormalizer.normalize(evt)
    assert norm is not None
    assert norm.device_id == "RFID-001"
    assert norm.identifier == "E20034120123456789ABCDEF"
    assert norm.rssi == -48.8
    assert norm.station_id == "GATE-1"
    assert norm.timestamp.tzinfo is not None


def test_normalize_with_prefix_and_suffix():
    evt = IdentificationEvent(
        device_id="RFID-001",
        device_type=DeviceType.RFID_FIXED,
        vendor="SICK",
        model="RFU630",
        event_type=EventType.IDENTIFICATION,
        identifier_type=IdentifierType.RFID_EPC,
        identifier="E20034120123456789ABCDEF",
    )
    cfg = OutputFormattingConfig(
        prefix="WF-MAT-",
        suffix="-OK",
        format_mode=FormatMode.HEX_CLEAN
    )
    norm = EventNormalizer.normalize(evt, formatting=cfg)
    assert norm is not None
    assert norm.identifier == "WF-MAT-E20034120123456789ABCDEF-OK"


def test_normalize_strip_prefix():
    evt = IdentificationEvent(
        device_id="BC-001",
        device_type=DeviceType.BARCODE_HANDHELD,
        vendor="Honeywell",
        model="Granit",
        event_type=EventType.IDENTIFICATION,
        identifier_type=IdentifierType.QR_CODE,
        identifier="QR:ITEM-WAKEFIT-MATTRESS-101",
    )
    cfg = OutputFormattingConfig(strip_prefix="QR:")
    norm = EventNormalizer.normalize(evt, formatting=cfg)
    assert norm is not None
    assert norm.identifier == "ITEM-WAKEFIT-MATTRESS-101"


def test_normalize_epc_mask_filter():
    # Tag starting with E200: Allowed
    evt1 = IdentificationEvent(
        device_id="RFID-001",
        device_type=DeviceType.RFID_FIXED,
        vendor="SICK",
        model="RFU630",
        event_type=EventType.IDENTIFICATION,
        identifier_type=IdentifierType.RFID_EPC,
        identifier="E20034120123456789ABCDEF",
    )
    # Stray tag starting with 3008: Filtered
    evt2 = IdentificationEvent(
        device_id="RFID-001",
        device_type=DeviceType.RFID_FIXED,
        vendor="SICK",
        model="RFU630",
        event_type=EventType.IDENTIFICATION,
        identifier_type=IdentifierType.RFID_EPC,
        identifier="300833B2DDD9014000000000",
    )
    cfg = OutputFormattingConfig(epc_filter_prefix="E200")
    
    assert EventNormalizer.normalize(evt1, formatting=cfg) is not None
    assert EventNormalizer.normalize(evt2, formatting=cfg) is None


def test_normalize_min_rssi_threshold():
    # Strong signal (-45 dBm): Allowed
    evt1 = IdentificationEvent(
        device_id="RFID-001",
        device_type=DeviceType.RFID_FIXED,
        vendor="SICK",
        model="RFU630",
        event_type=EventType.IDENTIFICATION,
        identifier_type=IdentifierType.RFID_EPC,
        identifier="E20034120123456789ABCDEF",
        rssi=-45.0
    )
    # Stray weak signal (-80 dBm): Filtered
    evt2 = IdentificationEvent(
        device_id="RFID-001",
        device_type=DeviceType.RFID_FIXED,
        vendor="SICK",
        model="RFU630",
        event_type=EventType.IDENTIFICATION,
        identifier_type=IdentifierType.RFID_EPC,
        identifier="E20034120123456789ABCDEF",
        rssi=-80.0
    )
    cfg = OutputFormattingConfig(min_rssi_dbm=-70.0)

    assert EventNormalizer.normalize(evt1, formatting=cfg) is not None
    assert EventNormalizer.normalize(evt2, formatting=cfg) is None
