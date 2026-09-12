"""Unit tests for CoLa-A Telegram and SICK RFU630 Parser."""

import pytest
from uaim_device.adapters.sick_rfu630.cola.parser import ColaParser
from uaim_device.adapters.sick_rfu630.parser import SickRFU630Parser
from uaim_device.core.exceptions import DeviceParseError


def test_parse_read_response():
    tel = ColaParser.parse("sRA DeviceIdent SICK RFU630-10000 1.20")
    assert tel.command_type == "sRA"
    assert tel.name == "DeviceIdent"
    assert tel.tokens == ["SICK", "RFU630-10000", "1.20"]
    assert tel.is_read_response is True
    assert tel.is_fault is False


def test_parse_fault_telegram():
    tel = ColaParser.parse("sFA 0001")
    assert tel.is_fault is True
    assert tel.fault_code == "0001"
    assert "not found" in tel.fault_description.lower()


def test_parse_empty_raises_error():
    with pytest.raises(DeviceParseError):
        ColaParser.parse("")


def test_parse_rfu630_single_tag():
    tel = ColaParser.parse("sSN ReadResult 1 E20034120123456789ABCDEF 1 -48 1")
    result = SickRFU630Parser.parse_read_result(tel, "TEST-RFID-01")
    assert len(result.tags) == 1
    tag = result.tags[0]
    assert tag.epc == "E20034120123456789ABCDEF"
    assert tag.antenna_id == 1
    assert tag.rssi == -48.0
    assert tag.read_count == 1


def test_parse_rfu630_multiple_tags():
    raw = "sSN ReadResult 2 E20034120123456789ABCD01 1 -45 2 E20034120123456789ABCD02 2 -52 1"
    tel = ColaParser.parse(raw)
    result = SickRFU630Parser.parse_read_result(tel, "TEST-RFID-01")
    assert len(result.tags) == 2
    assert result.tags[0].epc == "E20034120123456789ABCD01"
    assert result.tags[0].antenna_id == 1
    assert result.tags[0].read_count == 2
    assert result.tags[1].epc == "E20034120123456789ABCD02"
    assert result.tags[1].antenna_id == 2


def test_parse_rfu630_with_cycle_id():
    raw = "sSN ReadResult RC-998877 1 E20034120123456789ABCDEF 1 -50 1"
    tel = ColaParser.parse(raw)
    result = SickRFU630Parser.parse_read_result(tel, "TEST-RFID-01")
    assert result.cycle_id == "RC-998877"
    assert len(result.tags) == 1
    assert result.tags[0].epc == "E20034120123456789ABCDEF"
