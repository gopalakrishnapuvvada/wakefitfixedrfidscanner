"""Unit tests for CipherLab RS38 (AS38N8RF4NSG1) HandheldAdapter."""

import asyncio
import pytest
from uaim_device.adapters.handheld.adapter import HandheldAdapter
from uaim_device.adapters.handheld.parser import HandheldParser
from uaim_device.core.models import DeviceState, EventType, IdentifierType


@pytest.mark.asyncio
async def test_cipherlab_rs38_adapter_lifecycle_and_scan(sample_handheld_info):
    adapter = HandheldAdapter(sample_handheld_info)
    assert adapter.config.device_model == "RS38 (AS38N8RF4NSG1)"
    assert adapter.config.vendor == "CipherLab"

    await adapter.connect()
    await adapter.start()
    assert adapter.state == DeviceState.RUNNING

    # 1. Inject simulated UHF RFID EPC scan
    await adapter.execute_command("simulate_scan", payload="E20034120123456789ABCDEF")

    async for evt in adapter.events():
        if evt.event_type == EventType.IDENTIFICATION:
            assert evt.identifier == "E20034120123456789ABCDEF"
            assert evt.identifier_type == IdentifierType.RFID_EPC
            break

    # 2. Inject JSON Barcode payload from CipherLab Android Reader Utility
    json_scan = '{"barcode": "8901234567890", "rssi": -30, "metadata": {"symbology": "EAN13"}}'
    await adapter.execute_command("simulate_scan", payload=json_scan)

    async for evt in adapter.events():
        if evt.event_type == EventType.IDENTIFICATION:
            assert evt.identifier == "8901234567890"
            assert evt.identifier_type == IdentifierType.BARCODE
            assert evt.metadata.get("symbology") == "EAN13"
            break

    # 3. Inject 2D QR Code payload
    qr_scan = "QR:WF-MATTRESS-PALLET-0042"
    await adapter.execute_command("simulate_scan", payload=qr_scan)

    async for evt in adapter.events():
        if evt.event_type == EventType.IDENTIFICATION:
            assert evt.identifier == "WF-MATTRESS-PALLET-0042"
            assert evt.identifier_type == IdentifierType.QR_CODE
            break

    await adapter.stop()
    await adapter.disconnect()
    assert adapter.state == DeviceState.DISCONNECTED


def test_cipherlab_rs38_parser_key_value_and_json():
    # Key-Value format
    kv_scan = "EPC=E280116060000204968C090F;ANT=1;RSSI=-44.5"
    parsed_kv = HandheldParser.parse(kv_scan)
    assert parsed_kv.identifier == "E280116060000204968C090F"
    assert parsed_kv.identifier_type == IdentifierType.RFID_EPC
    assert parsed_kv.rssi == -44.5

    # Barcode KV
    bc_kv = "BARCODE=8901030992812;TYPE=EAN13"
    parsed_bc = HandheldParser.parse(bc_kv)
    assert parsed_bc.identifier == "8901030992812"
    assert parsed_bc.identifier_type == IdentifierType.BARCODE

    # JSON 2D QR
    json_qr = '{"qr_code": "WF-MAT-FOAM-5531", "type": "QR"}'
    parsed_qr = HandheldParser.parse(json_qr)
    assert parsed_qr.identifier == "WF-MAT-FOAM-5531"
    assert parsed_qr.identifier_type == IdentifierType.QR_CODE
