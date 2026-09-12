"""Asynchronous Fake SICK RFU630 TCP Server for automated testing."""

import asyncio
import logging
from typing import Optional
from uaim_device.adapters.sick_rfu630.cola.framing import STX, ETX, encode_cola_a_telegram

logger = logging.getLogger(__name__)


class FakeRFU630Server:
    """
    Simulates a physical SICK RFU630 reader over TCP CoLa-A.
    
    Supports:
    - Standard CoLa-A query responses (DeviceIdent, SCdevicestate, Run, Freeze)
    - Pushing asynchronous RFID tag read results (sSN ReadResult)
    - Fragmented TCP packet delivery
    - Multiple telegrams in a single TCP read
    - Noise/Garbage bytes injection
    - Abrupt socket disconnects / connection resets
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 12111) -> None:
        self.host = host
        self.port = port
        self.server: Optional[asyncio.Server] = None
        self.active_clients: list[asyncio.StreamWriter] = []
        self.is_running: bool = False
        self.received_commands: list[str] = []

    async def start(self) -> None:
        """Start listening on TCP socket."""
        self.server = await asyncio.start_server(self._handle_client, self.host, self.port)
        self.is_running = True
        logger.info(f"Fake RFU630 Server started on {self.host}:{self.port}")

    async def stop(self) -> None:
        """Stop server and disconnect all clients."""
        self.is_running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.server = None
        for writer in list(self.active_clients):
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
        self.active_clients.clear()
        logger.info("Fake RFU630 Server stopped.")

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.active_clients.append(writer)
        buffer = bytearray()
        try:
            while self.is_running:
                data = await reader.read(1024)
                if not data:
                    break
                buffer.extend(data)
                while True:
                    stx_idx = buffer.find(bytes([STX]))
                    if stx_idx == -1:
                        buffer.clear()
                        break
                    etx_idx = buffer.find(bytes([ETX]), stx_idx + 1)
                    if etx_idx == -1:
                        break
                    cmd_bytes = buffer[stx_idx + 1:etx_idx]
                    del buffer[:etx_idx + 1]
                    cmd_str = cmd_bytes.decode("latin-1").strip()
                    self.received_commands.append(cmd_str)
                    await self._process_command(cmd_str, writer)
        except Exception as e:
            logger.debug(f"Fake server client error: {e}")
        finally:
            if writer in self.active_clients:
                self.active_clients.remove(writer)
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def _process_command(self, cmd_str: str, writer: asyncio.StreamWriter) -> None:
        """Process incoming command and respond with appropriate CoLa telegram."""
        parts = cmd_str.split()
        if not parts:
            return

        cmd_type = parts[0]
        cmd_name = parts[1] if len(parts) > 1 else ""

        if cmd_type == "sRN" and cmd_name == "DeviceIdent":
            writer.write(encode_cola_a_telegram("sRA DeviceIdent SICK RFU630-10000 V1.20"))
            await writer.drain()
        elif cmd_type == "sRN" and cmd_name == "SCdevicestate":
            writer.write(encode_cola_a_telegram("sRA SCdevicestate 0 OK"))
            await writer.drain()
        elif cmd_type == "sMN" and cmd_name == "Run":
            writer.write(encode_cola_a_telegram("sMA Run 1"))
            await writer.drain()
        elif cmd_type == "sMN" and cmd_name == "Freeze":
            writer.write(encode_cola_a_telegram("sMA Freeze 1"))
            await writer.drain()
        else:
            # Echo generic response or method answer
            writer.write(encode_cola_a_telegram(f"sMA {cmd_name} 1"))
            await writer.drain()

    async def broadcast_telegram(self, telegram_payload: str) -> None:
        """Send complete framed CoLa telegram to all connected clients."""
        framed = encode_cola_a_telegram(telegram_payload)
        for w in list(self.active_clients):
            try:
                w.write(framed)
                await w.drain()
            except Exception:
                pass

    async def broadcast_fragmented(self, telegram_payload: str, chunk_size: int = 3, delay: float = 0.01) -> None:
        """Send a telegram split into tiny chunks to test streaming frame decoder."""
        framed = encode_cola_a_telegram(telegram_payload)
        for i in range(0, len(framed), chunk_size):
            chunk = framed[i:i + chunk_size]
            for w in list(self.active_clients):
                try:
                    w.write(chunk)
                    await w.drain()
                except Exception:
                    pass
            await asyncio.sleep(delay)

    async def broadcast_multiple_in_one_packet(self, telegram_payloads: list[str]) -> None:
        """Coalesce multiple telegrams into a single TCP packet."""
        combined = b"".join(encode_cola_a_telegram(p) for p in telegram_payloads)
        for w in list(self.active_clients):
            try:
                w.write(combined)
                await w.drain()
            except Exception:
                pass

    async def send_single_tag(self, epc: str, antenna: int = 1, rssi: float = -48.0, count: int = 1) -> None:
        """Helper to send standard SOPAS single tag read result."""
        payload = f"sSN ReadResult 1 {epc} {antenna} {rssi} {count}"
        await self.broadcast_telegram(payload)

    async def send_multi_tags(self, tags: list[tuple[str, int, float, int]]) -> None:
        """Helper to send SOPAS multiple tag read result: [(epc, ant, rssi, count), ...]."""
        tokens = [f"{len(tags)}"]
        for epc, ant, rssi, count in tags:
            tokens.extend([epc, str(ant), str(rssi), str(count)])
        payload = f"sSN ReadResult {' '.join(tokens)}"
        await self.broadcast_telegram(payload)

    async def force_disconnect_all(self) -> None:
        """Simulate physical network cable drop or reader power loss."""
        for w in list(self.active_clients):
            try:
                w.close()
                await w.wait_closed()
            except Exception:
                pass
        self.active_clients.clear()
