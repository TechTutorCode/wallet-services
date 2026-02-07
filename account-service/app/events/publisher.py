"""RabbitMQ event publisher for account.created and ledger.credit.requested."""

import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import pika

from app.config import get_settings

logger = logging.getLogger(__name__)

EVENT_KEYS = ("account.created", "ledger.credit.requested")


def _serialize(payload: Any) -> str:
    def _default(o: Any) -> Any:
        if isinstance(o, datetime):
            return o.isoformat()
        if hasattr(o, "hex"):
            return str(o)
        raise TypeError(f"Not serializable: {type(o)}")
    return json.dumps(payload, default=_default)


class EventPublisher:
    def __init__(self, rabbitmq_url: str | None = None, exchange: str | None = None):
        s = get_settings()
        self._url = rabbitmq_url or s.rabbitmq_url
        self._exchange = exchange or s.rabbitmq_exchange
        self._conn = None
        self._ch = None

    def _connect(self):
        if self._ch is None or self._ch.is_closed:
            params = pika.URLParameters(self._url)
            params.heartbeat = 600
            self._conn = pika.BlockingConnection(params)
            self._ch = self._conn.channel()
            self._ch.exchange_declare(exchange=self._exchange, exchange_type="topic", durable=True)
            logger.info("RabbitMQ connected, exchange %s", self._exchange)
        return self._ch

    def declare_exchange(self) -> None:
        self._connect()

    def publish(self, event_type: str, payload: dict[str, Any]) -> None:
        try:
            ch = self._connect()
            body = {
                "event_id": str(uuid4()),
                "event_type": event_type,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "payload": payload,
            }
            ch.basic_publish(
                exchange=self._exchange,
                routing_key=event_type,
                body=_serialize(body),
                properties=pika.BasicProperties(delivery_mode=2, content_type="application/json"),
            )
            logger.info("Published %s", event_type)
        except Exception as e:
            logger.exception("Publish failed %s: %s", event_type, e)

    def close(self) -> None:
        try:
            if self._ch and self._ch.is_open:
                self._ch.close()
            if self._conn and self._conn.is_open:
                self._conn.close()
        except Exception as e:
            logger.warning("Close error: %s", e)
        self._ch = None
        self._conn = None


_publisher: EventPublisher | None = None


def get_event_publisher() -> EventPublisher:
    global _publisher
    if _publisher is None:
        _publisher = EventPublisher()
    return _publisher
