"""Domain events and RabbitMQ publishing."""

from app.events.publisher import EventPublisher, get_event_publisher

__all__ = ["EventPublisher", "get_event_publisher"]
