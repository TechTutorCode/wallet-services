"""Consumes wallet.created from RabbitMQ and populates WalletRegistry."""

import asyncio
import json
import logging
import threading
from uuid import UUID

import pika

from app.config import get_settings
from app.db.session import async_session_factory
from app.models.wallet_registry import WalletRegistry

logger = logging.getLogger(__name__)

_consumer_thread: threading.Thread | None = None
_stop_event = threading.Event()


def _on_wallet_created(ch, method, properties, body):
    try:
        msg = json.loads(body)
        payload = msg.get("payload") or msg
        wallet_id = payload.get("wallet_id")
        company_id = payload.get("company_id")
        company_account_number = payload.get("company_account_number") or ""
        if not wallet_id or not company_id:
            logger.warning("wallet.created missing wallet_id or company_id: %s", payload)
            ch.basic_ack(method.delivery_tag)
            return

        prefix = str(company_account_number or "")[:3].ljust(3, "0") or "000"

        async def insert():
            async with async_session_factory() as session:
                from sqlalchemy import select
                r = await session.execute(
                    select(WalletRegistry).where(WalletRegistry.wallet_id == UUID(wallet_id))
                )
                if r.scalar_one_or_none():
                    logger.info("Wallet %s already in registry, skip", wallet_id)
                    return
                reg = WalletRegistry(
                    wallet_id=UUID(wallet_id),
                    company_id=UUID(company_id),
                    company_account_prefix=prefix,
                    sequence_no=0,
                )
                session.add(reg)
                await session.commit()
                logger.info("WalletRegistry updated for wallet_id=%s prefix=%s", wallet_id, prefix)

        asyncio.run(insert())
        ch.basic_ack(method.delivery_tag)
    except Exception as e:
        logger.exception("wallet.created handler failed: %s", e)
        ch.basic_nack(method.delivery_tag, requeue=True)


def _run_consumer():
    settings = get_settings()
    params = pika.URLParameters(settings.rabbitmq_url)
    params.heartbeat = 600
    while not _stop_event.is_set():
        try:
            conn = pika.BlockingConnection(params)
            ch = conn.channel()
            ch.exchange_declare(exchange=settings.rabbitmq_exchange, exchange_type="topic", durable=True)
            q = ch.queue_declare(queue="account-service-wallet-created", durable=True).method.queue
            ch.queue_bind(queue=q, exchange=settings.rabbitmq_exchange, routing_key="wallet.created")
            ch.basic_consume(queue=q, on_message_callback=_on_wallet_created)
            logger.info("Consuming wallet.created")
            while not _stop_event.is_set():
                conn.process_data_events(time_limit=1)
        except Exception as e:
            if _stop_event.is_set():
                break
            logger.warning("Consumer error, reconnecting: %s", e)
            _stop_event.wait(5)


def start_wallet_consumer() -> None:
    global _consumer_thread
    if _consumer_thread is not None:
        return
    _stop_event.clear()
    _consumer_thread = threading.Thread(target=_run_consumer, daemon=True)
    _consumer_thread.start()


def stop_wallet_consumer() -> None:
    global _consumer_thread
    _stop_event.set()
    if _consumer_thread:
        _consumer_thread.join(timeout=5)
    _consumer_thread = None
