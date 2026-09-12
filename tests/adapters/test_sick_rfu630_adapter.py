"""Unit and integration tests for SickRFU630Adapter."""

import asyncio
import pytest
from tests.fixtures.fake_rfu630 import FakeRFU630Server
from uaim_device.adapters.sick_rfu630.adapter import SickRFU630Adapter
from uaim_device.core.models import DeviceState, EventType, IdentifierType


@pytest.mark.asyncio
async def test_connect_and_disconnect(sample_rfu630_info):
    server = FakeRFU630Server(host="127.0.0.1", port=12111)
    await server.start()

    adapter = SickRFU630Adapter(sample_rfu630_info)
    try:
        assert adapter.state == DeviceState.DISCONNECTED
        await adapter.connect()
        assert adapter.state == DeviceState.CONNECTED

        health = await adapter.health()
        assert health.connected is True
        assert health.adapter_state == DeviceState.CONNECTED

        await adapter.disconnect()
        assert adapter.state == DeviceState.DISCONNECTED
    finally:
        await server.stop()


@pytest.mark.asyncio
async def test_execute_cola_command(sample_rfu630_info):
    server = FakeRFU630Server(host="127.0.0.1", port=12111)
    await server.start()

    adapter = SickRFU630Adapter(sample_rfu630_info)
    try:
        await adapter.connect()
        resp = await adapter.execute_command("sRN SCdevicestate")
        assert resp["command_type"] == "sRA"
        assert resp["name"] == "SCdevicestate"
        assert "OK" in resp["tokens"]
    finally:
        await adapter.disconnect()
        await server.stop()


@pytest.mark.asyncio
async def test_parse_valid_rfid_event(sample_rfu630_info):
    server = FakeRFU630Server(host="127.0.0.1", port=12111)
    await server.start()

    adapter = SickRFU630Adapter(sample_rfu630_info)
    try:
        await adapter.connect()
        await adapter.start()
        assert adapter.state == DeviceState.RUNNING

        # Send tag from fake server
        await server.send_single_tag("E20034120123456789ABCDEF", antenna=1, rssi=-48.0, count=1)

        # Read event from adapter stream
        event_gen = adapter.events()
        # The first event might be the DEVICE_CONNECTED lifecycle event
        event = await anext(event_gen)
        if event.event_type == EventType.DEVICE_CONNECTED:
            event = await anext(event_gen)

        assert event.event_type == EventType.IDENTIFICATION
        assert event.identifier_type == IdentifierType.RFID_EPC
        assert event.identifier == "E20034120123456789ABCDEF"
        assert event.rssi == -48.0
        assert event.antenna_id == 1
    finally:
        await adapter.disconnect()
        await server.stop()


@pytest.mark.asyncio
async def test_parse_multiple_rfid_tags(sample_rfu630_info):
    server = FakeRFU630Server(host="127.0.0.1", port=12111)
    await server.start()

    adapter = SickRFU630Adapter(sample_rfu630_info)
    try:
        await adapter.connect()
        await adapter.start()

        tags_to_send = [
            ("E20034120123456789ABCD01", 1, -45.0, 1),
            ("E20034120123456789ABCD02", 2, -50.0, 2),
        ]
        await server.send_multi_tags(tags_to_send)

        received_epcs = []
        async for evt in adapter.events():
            if evt.event_type == EventType.IDENTIFICATION:
                received_epcs.append(evt.identifier)
                if len(received_epcs) == 2:
                    break

        assert "E20034120123456789ABCD01" in received_epcs
        assert "E20034120123456789ABCD02" in received_epcs
    finally:
        await adapter.disconnect()
        await server.stop()
