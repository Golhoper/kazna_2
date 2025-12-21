"""Обработка событий в границах ограниченного контекста."""

from collections.abc import Sequence
from typing import Any

from loguru import logger

from generic.domain.bounded_events.context import bounded_events_collector_ctx
from generic.domain.bounded_events.events import Event
from generic.domain.bounded_events.handlers import BaseHandler
from generic.units_of_work.base import TBaseUnitOfWork


def log_event(event: Event) -> None:
    """Логирование события."""
    logger.info(
        "Event published. {}",
        {
            "type": type(event),
            "event": event.model_dump(),
        },
    )


class BoundedEventsCollector:
    """Сборщик событий. Создается один объект сборщика в UseCase или иной "точке входа"
    и передается далее во все объекты доменного слоя, которые могут генерировать события.
    Дополнительный слой абстракции для дополнительной логики, как, например, логирования возникшего события.
    """

    def __init__(self) -> None:
        self.__events: list[Event] = []

    def put_event(self, event: Event) -> None:
        """Добавляет событие в очередь."""
        log_event(event)
        self.__events.append(event)

    def get_events(self) -> list[Event]:
        """Возвращает накопленные события."""
        return self.__events.copy()

    def pop_event(self) -> Event | None:
        """Возвращает 1-е событие и удаляет его из очереди.
        Если событий нет, возвращает None.
        """
        return self.__events.pop(0) if self.__events else None

    def clear(self) -> None:
        """Очищает накопленные события."""
        self.__events = []


class BoundedEventsProcessor:
    """Класс для публикации и обработки доменных событий в границах ограниченного контекста.
    !!!! Для упрощения пока допускаем обрабатывать события одного контекста, обработчиком другого контекста.

    - События только уровня domain.
    - Обработчики (подписчики) событий находятся в том же ограниченном контексте.
    - Обработчики вызываются синхронно, но после основного кода
    (сначала собираются все события, потом при завершении логической транзакции все обработчики запускаются).
    - Обработчики могут быть запущены как до завершения транзакции, так и сразу после
    (это определяется картой обработчиков).
    - Для отправки доменного события в другой продукт через сетевую шину нужно добавлять обработчик,
    который ретранслирует событие, сериализуя его в структуру, описанную контрактом взаимодействия,
    с помощью mapper-класса. События, идущие в шину за пределы продукта, называются интеграционные события.
    """

    def __init__(
        self,
        uow: TBaseUnitOfWork,
        handlers_map: dict[type[Event], Sequence[type[BaseHandler]]],
    ) -> None:
        """Инициализация.

        Args:
            uow: Unit of work для возможности передавать его в обработчики событий.
            handlers_map: карта сопоставления списков обработчиков для каждого типа событий.
        """
        self._uow = uow
        self._handlers_map = handlers_map or {}
        collector = BoundedEventsCollector()
        bounded_events_collector_ctx.set(collector)

    @property
    def events_collector(self) -> Any:
        """Объект сборщика событий."""
        return bounded_events_collector_ctx.get()

    async def dispatch_all_before_commit(self) -> None:
        """Обработать все события обработчиками ДО завершения транзакции.

        События НЕ удаляются из очереди, чтобы дождаться обработчиков, выполняющихся после транзакции.
        """
        events = self.events_collector.get_events()
        for event in events:
            await self._dispatch_event(event, after_commit=False)

    async def dispatch_all_after_commit(self) -> None:
        """Обработать все события обработчиками, которые желают выполнить свой код
        ПОСЛЕ завершения транзакции.

        Каждое событие удаляется из очереди ПЕРЕД запуском первого обработчика.
        """
        while event := self.events_collector.pop_event():
            await self._dispatch_event(event, after_commit=True)

    async def _dispatch_event(self, event: Event, after_commit: bool) -> None:
        handlers = self._get_handlers(event)
        for hl in handlers:
            if hl.ON_TRANSACTION_COMMIT is after_commit:  # type:ignore[comparison-overlap]
                await hl(self._uow).handle(event)  # type:ignore[arg-type]

    def _get_handlers(self, event: Event) -> Sequence[type[BaseHandler]]:
        """Возвращает список классов обработчиков события по указанному объекту события."""
        return self._handlers_map.get(type(event), [])
