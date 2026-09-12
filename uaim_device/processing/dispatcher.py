"""Pluggable Event Dispatcher and Consumer architecture."""

import asyncio
from abc import ABC, abstractmethod
import logging
from typing import Any, Callable, Coroutine
from uaim_device.core.events import IdentificationEvent

logger = logging.getLogger(__name__)


class EventConsumer(ABC):
    """Abstract interface for event destinations (WebSockets, Kafka, Logs, DB)."""

    @abstractmethod
    async def consume(self, event: IdentificationEvent) -> None:
        """Handle incoming normalized IdentificationEvent."""
        pass


class LoggingConsumer(EventConsumer):
    """Logs structured event summaries to standard logger."""

    async def consume(self, event: IdentificationEvent) -> None:
        logger.info(
            f"device_id={event.device_id} "
            f"event_type={event.event_type.value} "
            f"type={event.identifier_type.value} "
            f"id={event.identifier} "
            f"rssi={event.rssi} "
            f"ant={event.antenna_id} "
            f"cycle={event.read_cycle_id}"
        )


class CallbackConsumer(EventConsumer):
    """Invokes an asynchronous or synchronous callback function on each event."""

    def __init__(self, callback: Callable[[IdentificationEvent], Coroutine[Any, Any, None] | None]) -> None:
        self.callback = callback

    async def consume(self, event: IdentificationEvent) -> None:
        try:
            res = self.callback(event)
            if asyncio.iscoroutine(res):
                await res
        except Exception as e:
            logger.error(f"Error in callback consumer: {e}", exc_info=True)


class MockKafkaConsumer(EventConsumer):
    """
    Pluggable Kafka consumer abstraction.
    
    Operates without hard Kafka driver dependencies at runtime.
    Logs/records published messages for enterprise traceability.
    """

    def __init__(self, topic: str = "uaim.identification.events") -> None:
        self.topic = topic
        self.published_events: list[IdentificationEvent] = []

    async def consume(self, event: IdentificationEvent) -> None:
        self.published_events.append(event)
        if len(self.published_events) > 500:
            self.published_events.pop(0)
        logger.debug(f"[Kafka:{self.topic}] Emitted message key={event.device_id} payload={event.identifier}")


class EventDispatcher:
    """Dispatches identification events concurrently to all registered consumers."""

    def __init__(self) -> None:
        self._consumers: list[EventConsumer] = []

    def add_consumer(self, consumer: EventConsumer) -> None:
        """Register a new downstream consumer."""
        self._consumers.append(consumer)

    def remove_consumer(self, consumer: EventConsumer) -> None:
        if consumer in self._consumers:
            self._consumers.remove(consumer)

    async def dispatch(self, event: IdentificationEvent) -> None:
        """Broadcast event to all consumers concurrently."""
        if not self._consumers:
            return

        tasks = [self._safe_consume(c, event) for c in self._consumers]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _safe_consume(self, consumer: EventConsumer, event: IdentificationEvent) -> None:
        try:
            await consumer.consume(event)
        except Exception as e:
            logger.error(f"Consumer {consumer.__class__.__name__} error: {e}", exc_info=True)
