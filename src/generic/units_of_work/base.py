from __future__ import annotations

import abc
from types import TracebackType
from typing import TYPE_CHECKING, Self, TypeVar

from asyncpg import StringDataRightTruncationError, UniqueViolationError
from funcy import re_find
from loguru import logger
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from generic.domain.exceptions import DomainError

if TYPE_CHECKING:
    from generic.domain.bounded_events.events_processing import BoundedEventsProcessor

TBaseUnitOfWork = TypeVar("TBaseUnitOfWork", bound="BaseUnitOfWork")


class BaseUnitOfWork:
    """Базовый класс для создания реализаций UoW для каждого ограниченного контекста со своим набором репозиториев."""

    unique_integrity_error_message_map: dict[str, str] = {
        # <ключ уникальности в бд>: <сообщение об ошибке>
        # "users_pkey": "Профиль для этого пользователя уже создан"
    }

    def __init__(
        self,
        session_factory: async_sessionmaker | None,
        session: AsyncSession | None = None,
    ) -> None:
        """Инициализация класса UnitOfWork.

        Args:
            session_factory: фабрика сессий
            session: сессия - если передана, то сессия не будет создаваться и закрываться внутри UoW.
        """
        self.session_factory = session_factory
        self._session: AsyncSession | None = session
        self._is_outside_session = bool(self._session)
        self._bounded_events_processor: BoundedEventsProcessor | None = None
        self._repositories_attrs: set[str] | None = None

    async def __aenter__(self: Self) -> Self:
        """Вход контекстного менеджера."""
        if not self._is_outside_session:
            self._session = self.session_factory()  # type:ignore[misc]
        self._init_repositories()
        self._init_bounded_events_processor()
        return self

    async def __aexit__(
        self,
        _exception_type: type[BaseException] | None,
        exception: BaseException | None,
        _traceback: TracebackType | None,
    ) -> None:
        """Выход из контекстного менеджера."""
        if not self._is_outside_session:
            await self._session.close()  # type:ignore[union-attr]
            self._session = None
        self._exit_repositories()

        if isinstance(exception, DBAPIError):
            raise self._transform_db_error_to_domain(exception)

    async def commit(self) -> None:
        """Завершение транзакции."""
        await self._session.flush()  # type:ignore[union-attr]
        await self.bounded_events_processor.dispatch_all_before_commit()  # type:ignore[union-attr]
        await self._session.commit()  # type:ignore[union-attr]
        await self.bounded_events_processor.dispatch_all_after_commit()  # type:ignore[union-attr]

    async def rollback(self) -> None:
        """Откатывает изменения в БД."""
        await self._session.rollback()  # type:ignore[union-attr]

    @property
    def session(self) -> AsyncSession | None:
        """Возвращает сессию."""
        return self._session

    def _init_bounded_events_processor(self) -> None:
        """Инициализирует объект обработки событий ограниченного контекста.

        Переопределяем, чтобы передать карту обработчиков конкретного приложения.

        Пример:
            self._bounded_events_processor = BoundedEventsProcessor(uow=self, handlers_map={
                ProjectUpdated: [RecordProjectUpdatingInHistory, NotifyResponsibleAboutUpdatingProject],
            })
        """
        from generic.domain.bounded_events.events_processing import BoundedEventsProcessor

        self._bounded_events_processor = BoundedEventsProcessor(self, handlers_map={})

    @property
    def bounded_events_processor(self) -> BoundedEventsProcessor | None:
        """Объект обработки событий ограниченного контекста."""
        return self._bounded_events_processor

    @abc.abstractmethod
    def _init_repositories(self) -> None:
        """Инициализирует репозитории."""
        raise NotImplementedError

    def _get_repositories_attrs(self) -> set[str]:
        """Возвращает названия атрибутов репозиториев."""
        if self._repositories_attrs is None:
            self._repositories_attrs = set()
            for attr in self.__dict__:
                if attr.endswith("_repository"):
                    self._repositories_attrs.add(attr)
        return self._repositories_attrs

    def _exit_repositories(self) -> None:
        """Выход для репозиториев - Обнуляет атрибуты репозиториев."""
        for repo_attr in self._get_repositories_attrs():
            setattr(self, repo_attr, None)

    def _transform_db_error_to_domain(self, exc: DBAPIError) -> DomainError:
        """Ошибку IntegrityError оборачивает доменной ошибкой.

        Пример сообщений:
            # UniqueViolationError.sqlstate
            async def test_user_duplicate_pk(uow: UnitOfWork, user: User):
                with pytest.raises(DomainError, match="Профиль для этого пользователя уже создан"):
                    await UserFactory.create(uow, id=user.id)


            # StringDataRightTruncationError.sqlstate
            async def test_user_position_value_too_long(uow: UnitOfWork):
                with pytest.raises(DomainError, match=re.escape(
                    "Слишком длинное значение (ограничение: 30 символов)"
                )):
                    await UserFactory.create(uow, position="1" * 500)


            # другие ошибки
            async def test_user_company_unknown_id(uow: UnitOfWork, company_build: Company):
                msg = f'Key (company_id)=({str(company_build.id)}) is not present in table "companies".'
                with pytest.raises(DomainError, match=re.escape(msg)):
                    await UserFactory.create(uow, company=company_build)
        """
        error_msg = str(exc.args[0])
        detail = (re_find(r"DETAIL: (.*\.)", error_msg) or error_msg).strip()
        service_msg = 'Пользователю показана заглушка необработанной ошибки: "{}"'

        if exc.orig.sqlstate == UniqueViolationError.sqlstate:
            duplicate_key = re_find('duplicate key value violates unique constraint "(.*)"', error_msg)
            if description := self.unique_integrity_error_message_map.get(duplicate_key):
                return DomainError(description)

            msg = f"Значение должно быть уникальным: {detail} (key={duplicate_key})"
            logger.warning(service_msg, msg)
            return DomainError(msg)

        if exc.orig.sqlstate == StringDataRightTruncationError.sqlstate:
            value = re_find(r"value too long for type character varying\((.*)\)", error_msg)
            msg = f"Слишком длинное значение (ограничение: {value or '???'} символов)"
            logger.warning(service_msg, msg)
            return DomainError(msg)

        logger.warning(service_msg, detail)
        return DomainError(detail)
