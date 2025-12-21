import abc

from generic.domain.bounded_events.events import Event
from generic.units_of_work.base import TBaseUnitOfWork


class IHandler(abc.ABC):
    """Интерфейс обработчика событий в границах ограниченного контекста."""

    @abc.abstractmethod
    def __init__(self, uow: TBaseUnitOfWork) -> None:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def ON_TRANSACTION_COMMIT(self) -> bool:  # noqa: N802
        """Флаг требования момента запуска обработчика. Если True, запускать только после завершения транзакции."""
        raise NotImplementedError

    @abc.abstractmethod
    async def handle(self, event: Event) -> None:
        """Обработать событие."""
        raise NotImplementedError


class BaseHandler(IHandler, abc.ABC):
    """Базовый класс, от которого нужно наследовать остальные обработчики.

    !!! ВНИМАНИЕ:
    Если код, выполняемый обработчиками,
    добавляет события в units_of_work.bounded_events_processor.events_collector,
    то события могут НЕ обработаться, если этот обработчик выполняется после коммита,
    а порождаемое им событие должно обработаться хэндлером до коммита.
    В этом случае можно вызвать дополнительный коммит из обработчика.
    """

    def __init__(self, uow: TBaseUnitOfWork) -> None:
        self._uow = uow
        self._uow._is_outside_session = True  # noqa: SLF001
