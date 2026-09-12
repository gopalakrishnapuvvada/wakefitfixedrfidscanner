# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:\\UAIM\\Projects\\Wakefit\\FGLabelGenerationSystem\\Connectionadapter\\uaim_device\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('D:\\UAIM\\Projects\\Wakefit\\FGLabelGenerationSystem\\Connectionadapter\\uaim_device\\web', 'uaim_device/web')],
    hiddenimports=['uvicorn', 'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto', 'uvicorn.loops.asyncio', 'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto', 'uvicorn.protocols.http.h11_impl', 'uvicorn.protocols.http.httptools_impl', 'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto', 'uvicorn.protocols.websockets.websockets_impl', 'fastapi', 'fastapi.staticfiles', 'fastapi.responses', 'fastapi.middleware.cors', 'websockets', 'websockets.legacy', 'websockets.legacy.server', 'pydantic', 'pydantic_settings', 'yaml', 'aiofiles', 'uaim_device', 'uaim_device.core', 'uaim_device.core.adapter', 'uaim_device.core.events', 'uaim_device.core.exceptions', 'uaim_device.core.health', 'uaim_device.core.lifecycle', 'uaim_device.core.manager', 'uaim_device.core.models', 'uaim_device.core.registry', 'uaim_device.adapters', 'uaim_device.adapters.sick_rfu630', 'uaim_device.adapters.sick_rfu630.adapter', 'uaim_device.adapters.sick_rfu630.connection', 'uaim_device.adapters.sick_rfu630.models', 'uaim_device.adapters.sick_rfu630.parser', 'uaim_device.adapters.sick_rfu630.cola.commands', 'uaim_device.adapters.sick_rfu630.cola.framing', 'uaim_device.adapters.sick_rfu630.cola.parser', 'uaim_device.adapters.handheld', 'uaim_device.adapters.handheld.adapter', 'uaim_device.adapters.handheld.classifier', 'uaim_device.adapters.handheld.models', 'uaim_device.adapters.handheld.parser', 'uaim_device.adapters.handheld.transport', 'uaim_device.processing', 'uaim_device.processing.deduplicator', 'uaim_device.processing.dispatcher', 'uaim_device.processing.normalizer', 'uaim_device.processing.read_cycle', 'uaim_device.api.routes', 'uaim_device.api.websocket', 'uaim_device.metrics.metrics', 'uaim_device.simulator', 'uaim_device.smoke_test'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='UAIM_DeviceAdapter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='UAIM_DeviceAdapter',
)
