"""Unit tests for CoLa-A streaming frame decoder."""

import pytest
from uaim_device.adapters.sick_rfu630.cola.framing import (
    ColaFrameDecoder,
    encode_cola_a_telegram,
)
from uaim_device.core.exceptions import DeviceProtocolError


def test_complete_telegram():
    decoder = ColaFrameDecoder()
    raw = encode_cola_a_telegram("sRN DeviceIdent")
    results = list(decoder.feed(raw))
    assert results == ["sRN DeviceIdent"]
    assert decoder.buffer_size == 0


def test_fragmented_telegram():
    decoder = ColaFrameDecoder()
    raw = encode_cola_a_telegram("sSN ReadResult 1 E200ABCD 1 -48 1")
    
    # Split into 3 chunks
    chunk1 = raw[:5]
    chunk2 = raw[5:15]
    chunk3 = raw[15:]

    res1 = list(decoder.feed(chunk1))
    assert res1 == []
    assert decoder.buffer_size == len(chunk1)

    res2 = list(decoder.feed(chunk2))
    assert res2 == []

    res3 = list(decoder.feed(chunk3))
    assert res3 == ["sSN ReadResult 1 E200ABCD 1 -48 1"]
    assert decoder.buffer_size == 0


def test_multiple_telegrams_in_single_packet():
    decoder = ColaFrameDecoder()
    t1 = encode_cola_a_telegram("sRA DeviceIdent SICK RFU630")
    t2 = encode_cola_a_telegram("sSN ReadResult 1 E2001111 1 -50 1")
    combined = t1 + t2

    results = list(decoder.feed(combined))
    assert len(results) == 2
    assert results[0] == "sRA DeviceIdent SICK RFU630"
    assert results[1] == "sSN ReadResult 1 E2001111 1 -50 1"
    assert decoder.buffer_size == 0


def test_noise_before_stx():
    decoder = ColaFrameDecoder()
    garbage = b"UNKNOWN_RANDOM_NOISE_BYTES"
    telegram = encode_cola_a_telegram("sMN Run")
    data = garbage + telegram

    results = list(decoder.feed(data))
    assert results == ["sMN Run"]
    assert decoder.buffer_size == 0


def test_buffer_overflow_protection():
    decoder = ColaFrameDecoder(max_buffer_size=50)
    huge_data = b"A" * 60

    with pytest.raises(DeviceProtocolError):
        list(decoder.feed(huge_data))
    assert decoder.buffer_size == 0
