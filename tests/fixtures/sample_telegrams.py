"""Sample raw CoLa-A telegram payloads for unit testing."""

# Single Tag standard SOPAS Read Result
TELEGRAM_SINGLE_TAG = "\x02sSN ReadResult 1 E20034120123456789ABCDEF 1 -48 1\x03"

# Multiple Tags in single Read Result
TELEGRAM_MULTI_TAG = "\x02sSN ReadResult 3 E20034120123456789ABCD01 1 -42 2 E20034120123456789ABCD02 2 -55 1 E20034120123456789ABCD03 1 -60 1\x03"

# SOPAS DeviceIdent response
TELEGRAM_DEVICE_IDENT_RESP = "\x02sRA DeviceIdent SICK RFU630-10000 V1.20\x03"

# SOPAS SCdevicestate response
TELEGRAM_DEVICE_STATE_RESP = "\x02sRA SCdevicestate 0 OK\x03"

# SOPAS Run Method response
TELEGRAM_RUN_RESP = "\x02sMA Run 1\x03"

# SOPAS Freeze Method response
TELEGRAM_FREEZE_RESP = "\x02sMA Freeze 1\x03"

# Fault / Error response
TELEGRAM_FAULT_RESP = "\x02sFA 0001\x03"
