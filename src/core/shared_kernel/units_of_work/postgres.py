from generic.domain.bounded_events import BoundedEventsProcessor
from generic.units_of_work.base import BaseUnitOfWork
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

class UnitOfWork(BaseUnitOfWork):
    """Класс для оборачивания всех запросов к репозиториям в одну транзакцию.

    Реализует паттерн Unit Of Work (https://www.cosmicpython.com/book/chapter_06_uow.html).
    """

    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession] | None, session: AsyncSession | None = None
    ) -> None:
        """Инициализация класса UnitOfWork."""
        super().__init__(session_factory, session=session)

    def _init_repositories(self) -> None:
        """Инициализирует репозитории."""

    def _init_bounded_events_processor(self) -> None:
        """Инициализирует объект обработки событий ограниченного контекста.

        Переопределяем, чтобы передать карту обработчиков конкретного приложения.

        Пример:
            self._bounded_events_processor = BoundedEventsProcessor(uow=self, handlers_map={
                ProjectUpdated: [RecordProjectUpdatingInHistory, NotifyResponsibleAboutUpdatingProject],
            })
        """
        self._bounded_events_processor = BoundedEventsProcessor(
            uow=self,
            handlers_map={},
        )
