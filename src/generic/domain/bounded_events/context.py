import typing as t
from contextvars import ContextVar

if t.TYPE_CHECKING:
    from generic.domain.bounded_events.events_processing import BoundedEventsCollector

"""Контекст для хранения объекта сборщика событий.
В любом месте приложения можно получить доступ к объекту сборщика событий, чтобы добавить событие,
которое будет обработано при коммите транзакции UnitOfWork.

Пример:
from shared_kernel.domain.bounded_events.context import bounded_events_collector_ctx

class Entity:
    def _publish_some_event(self):
        events_collector = bounded_events_collector_ctx.get()
        event = SomeEvent()
        events_collector.put_event(event)
"""
bounded_events_collector_ctx: ContextVar["BoundedEventsCollector | None"] = ContextVar(
    "bounded_events_collector",
    default=None,
)
