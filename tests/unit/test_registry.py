"""Unit tests for AdapterRegistry and dynamic discovery."""

import pytest
import uaim_device.adapters  # noqa: F401
from uaim_device.adapters.handheld.adapter import HandheldAdapter
from uaim_device.adapters.sick_rfu630.adapter import SickRFU630Adapter
from uaim_device.core.exceptions import DeviceNotSupportedError
from uaim_device.core.registry import AdapterRegistry


def test_registry_contains_initial_adapters():
    registered = AdapterRegistry.list_registered()
    assert "sick_rfu630" in registered
    assert "handheld" in registered
    assert "barcode" not in registered


def test_create_sick_adapter(sample_rfu630_info):
    adapter = AdapterRegistry.create("sick_rfu630", sample_rfu630_info)
    assert isinstance(adapter, SickRFU630Adapter)
    assert adapter.device_id == "TEST-RFID-01"


def test_create_handheld_adapter(sample_handheld_info):
    adapter = AdapterRegistry.create("handheld", sample_handheld_info)
    assert isinstance(adapter, HandheldAdapter)
    assert adapter.device_id == "TEST-HH-01"


def test_create_unknown_adapter_raises_error(sample_rfu630_info):
    with pytest.raises(DeviceNotSupportedError):
        AdapterRegistry.create("non_existent_vendor_adapter", sample_rfu630_info)
