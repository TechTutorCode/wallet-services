"""RabbitMQ domain event publisher."""

import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import pika
from pika.adapters.blocking_connection import BlockingChannel

from app.config import get_settings

logger = logging.getLogger(__name__)

EVENT_KEYS = (
    "company.created",
    "company.updated",
    "company.deleted",
    "wallet.created",
)


def _serialize_payload(payload: Any) -> str:
    """Serialize payload to JSON; ensure datetime and UUID are ISO/string."""
    def _default(o: Any) -> Any:
        if isinstance(o, datetime):
            return o.isoformat()
        if hasattr(o, "hex"):  # UUID
            return str(o)
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")
    return json.dumps(payload, default=_default)


class EventPublisher:
    """
    Publishes domain events to RabbitMQ topic exchange 'wallet.events'.
    Message format:
    {
      "event_id": "uuid",
      "event_type": "company.created",
      "occurred_at": "ISO",
      "payload": { ... }
    }
    """

    def __init__(
        self,
        rabbitmq_url: str | None = None,
        exchange: str | None = None,
    ):
        settings = get_settings()
        self._url = rabbitmq_url or settings.rabbitmq_url
        self._exchange = exchange or settings.rabbitmq_exchange
        self._connection: pika.BlockingConnection | None = None
        self._channel: BlockingChannel | None = None

    def _ensure_connection(self) -> BlockingChannel:
        if self._channel is None or self._channel.is_closed:
            try:
                params = pika.URLParameters(self._url)
                # Keep connection from being closed by server when idle (heartbeat every 10 min)
                params.heartbeat = 600
                params.blocked_connection_timeout = 30
                self._connection = pika.BlockingConnection(params)
                self._channel = self._connection.channel()
                self._channel.exchange_declare(
                    exchange=self._exchange,
                    exchange_type="topic",
                    durable=True,
                )
                logger.info("Connected to RabbitMQ, exchange %s declared", self._exchange)
            except Exception as e:
                logger.exception("RabbitMQ connection failed: %s", e)
                raise
        return self._channel

    def declare_exchange(self) -> None:
        """Declare the exchange (and connect). Call at startup so the exchange exists and connectivity is verified."""
        self._ensure_connection()

    def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        if event_type not in EVENT_KEYS:
            logger.warning("Unknown event_type %s, publishing anyway", event_type)
        try:
            channel = self._ensure_connection()
            body = {
                "event_id": str(uuid4()),
                "event_type": event_type,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "payload": payload,
            }
            body_str = _serialize_payload(body)
            channel.basic_publish(
                exchange=self._exchange,
                routing_key=event_type,
                body=body_str,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type="application/json",
                ),
            )
            logger.info("Published event %s", event_type)
        except Exception as e:
            logger.exception("Failed to publish event %s: %s", event_type, e)

    def close(self) -> None:
        try:
            if self._channel and self._channel.is_open:
                self._channel.close()
            if self._connection and self._connection.is_open:
                self._connection.close()
        except Exception as e:
            logger.warning("Error closing RabbitMQ connection: %s", e)
        finally:
            self._channel = None
            self._connection = None


# Singleton for dependency injection (sync publisher; use from sync context or run in executor)
_publisher: EventPublisher | None = None


def get_event_publisher() -> EventPublisher:
    """Return shared event publisher instance."""
    global _publisher
    if _publisher is None:
        _publisher = EventPublisher()
    return _publisher
