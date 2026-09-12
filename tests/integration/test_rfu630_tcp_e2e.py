"""End-to-end integration tests for SICK RFU630 with Fake TCP Server."""

import asyncio
import pytest
from tests.fixtures.fake_rfu630 import FakeRFU630Server
from uaim_device.adapters.sick_rfu630.adapter import SickRFU630Adapter
from uaim_device.core.models import DeviceState, EventType, IdentifierType


@pytest.mark.asyncio
async def test_fragmented_tcp_telegram(sample_rfu630_info):
    server = FakeRFU630Server(host="127.0.0.1", port=12111)
    await server.start()

    adapter = SickRFU630Adapter(sample_rfu630_info)
    try:
        await adapter.connect()
        await adapter.start()

        # Send fragmented tag telegram (1 byte per chunk)
        payload = "sSN ReadResult 1 E20034120123456789ABCDEF 1 -48 1"
        await server.broadcast_fragmented(payload, chunk_size=2, delay=0.01)

        received = None
        async for evt in adapter.events():
            if evt.event_type == EventType.IDENTIFICATION:
                received = evt
                break

        assert received is not None
        assert received.identifier == "E20034120123456789ABCDEF"
        assert received.rssi == -48.0
    finally:
        await adapter.disconnect()
        await server.stop()


@pytest.mark.asyncio
async def test_multiple_telegrams_in_single_tcp_read(sample_rfu630_info):
    server = FakeRFU630Server(host="127.0.0.1", port=12111)
    await server.start()

    adapter = SickRFU630Adapter(sample_rfu630_info)
    try:
        await adapter.connect()
        await adapter.start()

        telegrams = [
            "sSN ReadResult 1 E20034120123456789ABCD01 1 -40 1",
            "sSN ReadResult 1 E20034120123456789ABCD02 2 -42 1",
            "sSN ReadResult 1 E20034120123456789ABCD03 1 -45 1",
        ]
        await server.broadcast_multiple_in_one_packet(telegrams)

        received_epcs = []
        async for evt in adapter.events():
            if evt.event_type == EventType.IDENTIFICATION:
                received_epcs.append(evt.identifier)
                if len(received_epcs) == 3:
                    break

        assert len(received_epcs) == 3
        assert received_epcs == [
            "E20034120123456789ABCD01",
            "E20034120123456789ABCD02",
            "E20034120123456789ABCD03",
        ]
    finally:
        await adapter.disconnect()
        await server.stop()


@pytest.mark.asyncio
async def test_invalid_telegram_handling(sample_rfu630_info):
    server = FakeRFU630Server(host="127.0.0.1", port=12111)
    await server.start()

    adapter = SickRFU630Adapter(sample_rfu630_info)
    try:
        await adapter.connect()
        await adapter.start()

        # Send invalid corrupted telegram followed by a valid telegram
        await server.broadcast_telegram("INVALID_UNKNOWN_TELEGRAM_HEADER")
        await server.send_single_tag("E20034120123456789ABCDEF", 1, -50.0)

        received = None
        async for evt in adapter.events():
            if evt.event_type == EventType.IDENTIFICATION:
                received = evt
                break

        assert received is not None
        assert received.identifier == "E20034120123456789ABCDEF"
    finally:
        await adapter.disconnect()
        await server.stop()


@pytest.mark.asyncio
async def test_reconnect_after_connection_loss(sample_rfu630_info):
    sample_rfu630_info.reconnect.enabled = True
    sample_rfu630_info.reconnect.initial_delay = 0.1
    sample_rfu630_info.reconnect.max_delay = 0.5

    server = FakeRFU630Server(host="127.0.0.1", port=12111)
    await server.start()

    adapter = SickRFU630Adapter(sample_rfu630_info)
    try:
        await adapter.connect()
        await adapter.start()
        assert adapter.state == DeviceState.RUNNING

        # Simulate abrupt disconnect
        await server.force_disconnect_all()
        await asyncio.sleep(0.3)

        # Allow reconnect loop to detect drop and re-establish connection
        await asyncio.sleep(0.5)
        # Server is still running, adapter should reconnect automatically
        health = await adapter.health()
        assert health.reconnect_count >= 1
    finally:
        await adapter.disconnect()
        await server.stop()
