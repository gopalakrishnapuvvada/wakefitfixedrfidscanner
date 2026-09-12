"""Unit tests for CipherLab RS38 (AS38N8RF4NSG1) scan classifier and business rules."""

import pytest
from uaim_device.adapters.handheld.classifier import (
    ETX_CHAR,
    GS_CHAR,
    RS_CHAR,
    STX_CHAR,
    ClassificationResult,
    RS38ScanClassifier,
)
from uaim_device.adapters.handheld.parser import HandheldParser, ParsedHandheldScan
from uaim_device.core.models import (
    ClassificationConfig,
    EntityType,
    IdentifierType,
    ReaderMode,
)


def test_classify_valid_rfid_epc_etx():
    raw_scan = f"{ETX_CHAR}E2801190A504006FA2BF55AB\x0D"
    res = RS38ScanClassifier.classify(raw_scan)

    assert res.is_valid is True
    assert res.identifier_type == IdentifierType.RFID_EPC
    assert res.source == "RFID"
    assert res.entity_type == EntityType.MATERIAL
    assert res.clean_value == "E2801190A504006FA2BF55AB"
    assert res.inferred_mode == ReaderMode.RFID
    assert res.error_code is None
    assert res.diagnostic_warning is None


def test_classify_valid_rfid_epc():
    raw_scan = f"{RS_CHAR}E2801190A504006FA2BF55AB\x0D"
    res = RS38ScanClassifier.classify(raw_scan)

    assert res.is_valid is True
    assert res.identifier_type == IdentifierType.RFID_EPC
    assert res.source == "RFID"
    assert res.entity_type == EntityType.MATERIAL
    assert res.clean_value == "E2801190A504006FA2BF55AB"
    assert res.inferred_mode == ReaderMode.RFID
    assert res.error_code is None
    assert res.diagnostic_warning is None


def test_classify_valid_qr_stx():
    raw_scan = f"{STX_CHAR}1009876543210\x0D"
    res = RS38ScanClassifier.classify(raw_scan)

    assert res.is_valid is True
    assert res.identifier_type == IdentifierType.MATERIAL_QR
    assert res.source == "QR"
    assert res.entity_type == EntityType.MATERIAL
    assert res.clean_value == "1009876543210"
    assert res.inferred_mode == ReaderMode.BARCODE
    assert res.error_code is None


def test_classify_invalid_rfid_epc_non_hex():
    raw_scan = f"{RS_CHAR}NOT-A-HEX-VALUE-1234\x0D"
    res = RS38ScanClassifier.classify(raw_scan)

    assert res.is_valid is False
    assert res.identifier_type == IdentifierType.RFID_EPC
    assert res.error_code == "INVALID_EPC_HEX"
    assert res.diagnostic_warning is not None
    assert "not valid hexadecimal" in res.diagnostic_warning


def test_classify_material_qr_100():
    raw_scan = f"{GS_CHAR}1009876543210\x0D"
    res = RS38ScanClassifier.classify(raw_scan)

    assert res.is_valid is True
    assert res.identifier_type == IdentifierType.MATERIAL_QR
    assert res.source == "QR"
    assert res.entity_type == EntityType.MATERIAL
    assert res.clean_value == "1009876543210"
    assert res.inferred_mode == ReaderMode.BARCODE
    assert res.error_code is None


def test_classify_work_order_qr_200():
    raw_scan = f"{GS_CHAR}2001122334455\x0D"
    res = RS38ScanClassifier.classify(raw_scan)

    assert res.is_valid is True
    assert res.identifier_type == IdentifierType.WORK_ORDER_QR
    assert res.source == "QR"
    assert res.entity_type == EntityType.WORK_ORDER
    assert res.clean_value == "2001122334455"
    assert res.inferred_mode == ReaderMode.BARCODE
    assert res.error_code is None


def test_classify_work_order_qr_400():
    raw_scan = f"{GS_CHAR}4009988776655\x0D"
    res = RS38ScanClassifier.classify(raw_scan)

    assert res.is_valid is True
    assert res.identifier_type == IdentifierType.WORK_ORDER_QR
    assert res.source == "QR"
    assert res.entity_type == EntityType.WORK_ORDER
    assert res.clean_value == "4009988776655"
    assert res.inferred_mode == ReaderMode.BARCODE


def test_classify_unknown_qr_prefix():
    raw_scan = f"{GS_CHAR}3001234567890\x0D"
    res = RS38ScanClassifier.classify(raw_scan)

    assert res.is_valid is False
    assert res.identifier_type == IdentifierType.UNKNOWN_SCAN
    assert res.source == "QR"
    assert res.entity_type == EntityType.UNKNOWN
    assert res.error_code == "UNKNOWN_QR_PREFIX"
    assert res.diagnostic_warning is not None
    assert "Unrecognized QR content prefix" in res.diagnostic_warning


def test_classify_missing_control_prefix():
    raw_scan = "E2801190A504006FA2BF55AB\x0D"
    res = RS38ScanClassifier.classify(raw_scan)

    assert res.is_valid is False
    assert res.identifier_type == IdentifierType.UNKNOWN_SCAN
    assert res.source == "UNKNOWN"
    assert res.entity_type == EntityType.UNKNOWN
    assert res.error_code == "UNKNOWN_PREFIX"
    assert res.diagnostic_warning is not None
    assert "Missing required control character prefix" in res.diagnostic_warning


def test_classify_empty_scan():
    res = RS38ScanClassifier.classify("")
    assert res.is_valid is False
    assert res.identifier_type == IdentifierType.UNKNOWN_SCAN
    assert res.error_code == "EMPTY_SCAN"


def test_classify_reader_mode_mismatch_warning():
    # Reader is currently in BARCODE mode, but RFID scan arrives
    raw_rfid = f"{RS_CHAR}E2801190A504006FA2BF55AB\x0D"
    res = RS38ScanClassifier.classify(raw_rfid, current_reader_mode=ReaderMode.BARCODE)

    assert res.is_valid is True
    assert res.identifier_type == IdentifierType.RFID_EPC
    assert res.diagnostic_warning is not None
    assert "Reader mode mismatch" in res.diagnostic_warning

    # Reader is in RFID mode, but QR scan arrives
    raw_qr = f"{GS_CHAR}100123456789\x0D"
    res_qr = RS38ScanClassifier.classify(raw_qr, current_reader_mode=ReaderMode.RFID)

    assert res_qr.is_valid is True
    assert res_qr.identifier_type == IdentifierType.MATERIAL_QR
    assert res_qr.diagnostic_warning is not None
    assert "Reader mode mismatch" in res_qr.diagnostic_warning


def test_handheld_parser_wedge_integration():
    # Test HandheldParser routing directly to classifier
    raw_rfid = f"{RS_CHAR}E2801190A504006FA2BF55AB\x0D"
    parsed_rfid = HandheldParser.parse(raw_rfid)
    assert parsed_rfid.is_valid is True
    assert parsed_rfid.identifier == "E2801190A504006FA2BF55AB"
    assert parsed_rfid.identifier_type == IdentifierType.RFID_EPC
    assert parsed_rfid.source == "RFID"
    assert parsed_rfid.entity_type == EntityType.MATERIAL

    raw_qr = f"{GS_CHAR}20099887766\x0D"
    parsed_qr = HandheldParser.parse(raw_qr)
    assert parsed_qr.is_valid is True
    assert parsed_qr.identifier == "20099887766"
    assert parsed_qr.identifier_type == IdentifierType.WORK_ORDER_QR
    assert parsed_qr.source == "QR"
    assert parsed_qr.entity_type == EntityType.WORK_ORDER


def test_classify_aim_symbology_identifier_stripping():
    # AIM QR prefix ]Q3 before 100...
    raw_scan = f"{STX_CHAR}]Q3100889922110\x0D"
    res = RS38ScanClassifier.classify(raw_scan)
    assert res.is_valid is True
    assert res.clean_value == "100889922110"
    assert res.identifier_type == IdentifierType.MATERIAL_QR
    assert res.entity_type == EntityType.MATERIAL

    # AIM QR prefix ]Q3 before 200...
    raw_wo = f"{STX_CHAR}]Q3200776655443\x0D"
    res_wo = RS38ScanClassifier.classify(raw_wo)
    assert res_wo.is_valid is True
    assert res_wo.clean_value == "200776655443"
    assert res_wo.identifier_type == IdentifierType.WORK_ORDER_QR


def test_classify_code_id_and_label_stripping():
    # CipherLab single-letter Code ID 'q'
    raw_code_id = f"{STX_CHAR}q100889922110\x0D"
    res = RS38ScanClassifier.classify(raw_code_id)
    assert res.is_valid is True
    assert res.clean_value == "100889922110"
    assert res.identifier_type == IdentifierType.MATERIAL_QR

    # Explicit label prefix 'MC:'
    raw_label = f"{STX_CHAR}MC:100889922110\x0D"
    res_label = RS38ScanClassifier.classify(raw_label)
    assert res_label.is_valid is True
    assert res_label.clean_value == "100889922110"
    assert res_label.identifier_type == IdentifierType.MATERIAL_QR

    # GS1 Application Identifier '(10)'
    raw_gs1 = f"{STX_CHAR}(10)100889922110\x0D"
    res_gs1 = RS38ScanClassifier.classify(raw_gs1)
    assert res_gs1.is_valid is True
    assert res_gs1.clean_value == "100889922110"
    assert res_gs1.identifier_type == IdentifierType.MATERIAL_QR

