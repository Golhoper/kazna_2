import abc
from dataclasses import dataclass
from typing import Any, Self
from uuid import UUID

from humps import camelize

from generic.domain.values import UNEVALUATED
from generic.utils.log_levels import LogLevel


@dataclass
class FieldErrorDetail:
    """Детали ошибки с полем и сообщением."""

    message: str
    field: str

    def as_dict(self) -> dict[str, Any]:
        """Преобразует детали ошибки в словарь."""
        return {
            "field": camelize(self.field),
            "message": self.message,
        }


class DomainError(Exception):
    """Исключение бизнес логики."""

    def __init__(
        self,
        message: str,
        *,
        id: Any | None = None,
        entity: str | None = None,
        tech_details: dict[str, Any] | None = None,
        log_level: LogLevel = LogLevel.INFO,
        field_errors: list[FieldErrorDetail] | None = None,
    ) -> None:
        """Инициализация.

        Args:
            message: Сообщение об ошибке.
            id: Идентификатор сущности.
            entity: Системное имя сущности.
            tech_details: Детали ошибки для разработчиков.
            log_level: уровень логирования исключения.
            field_errors: Список ошибок, связанных с полями.
        """
        self._message = message
        self.field_errors = field_errors or []
        self.id = str(id) if id else None
        self._entity = entity
        self.tech_details = tech_details or {}
        self.log_level = log_level
        super().__init__(self.message)

    def as_dict(self, include_tech_details: bool = False) -> dict[str, Any]:
        """Ошибка в виде словаря для ответа фронту."""
        base = {
            "error": self.__class__.__name__,
            "entity": self.entity,
            "id": self.id,
            "message": self.message,
            "field_errors": [error.as_dict() for error in self.field_errors],
        }

        return base | {"tech_details": self.tech_details} if include_tech_details else base

    @property
    def message(self) -> str:
        """Сообщение об ошибке."""
        return self._message

    @property
    def entity(self) -> str | None:
        """Класс сущности / Человеческое название сущности, если нужно для ошибки."""
        return self._entity


class EntityFieldError(DomainError):
    """Исключение бизнес логики сущности."""

    @property
    @abc.abstractmethod
    def entity(self) -> str:
        """Название класса сущности."""
        raise NotImplementedError

    @classmethod
    def is_required_field(cls, field: str, id_: str | UUID | None = None) -> Self:
        """Исключение, если имя пустое."""
        return cls("Поле обязательно для заполнения", field=field, id=id_)


class EntityFieldErrorMixin(abc.ABC):
    """Миксин Исключение бизнес логики для сущности."""

    @property
    @abc.abstractmethod
    def exception_class(self) -> type[EntityFieldError]:
        """Класс исключения."""
        raise NotImplementedError

    def raise_error(self, message: str, field: str | None = None, id: Any = UNEVALUATED) -> None:
        """Вызывает исключение бизнес логики."""
        _id = id
        if _id is UNEVALUATED:
            _id = self.id  # type:ignore[attr-defined]
        raise self.exception_class(message=message, id=_id, field=field)


class NotFoundError(abc.ABC, DomainError):
    """Исключение в случае, если сущность не найдена.

    Пример:
        raise IssueNotFoundError(id=self._issue_id)
    """

    def __init__(
        self,
        id: Any,
        message: str = "",
        field_errors: list[FieldErrorDetail] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, id=id, field_errors=field_errors, **kwargs)

    @property
    @abc.abstractmethod
    def entity(self) -> str:
        """Наименование сущности (название на русском - для пользователя)."""
        raise NotImplementedError

    @property
    def message(self) -> str:
        """Сообщение об ошибке."""
        return self._message or f'Объект "{self.entity}" с id "{self.id}" не найден'


class PermissionAccessError(DomainError):
    """Ошибка, связанная с разрешениями."""

    def __init__(self, message: str = "Нет доступа", **kwargs: Any) -> None:
        super().__init__(message, **kwargs)


class ExternalServiceError(DomainError):
    """Исключение для ошибок внешних сервисов.

    Используется для передачи ошибок от внешних API на фронт
    с сохранением исходной структуры ошибки.
    """

    def __init__(
        self,
        message: str,
        *,
        service_name: str,
        external_code: int | str | None = None,
        external_response: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Инициализация ошибки внешнего сервиса.

        Args:
            message: Сообщение об ошибке от внешнего сервиса.
            service_name: Название внешнего сервиса.
            external_code: Код ошибки от внешнего сервиса.
            external_response: Полный ответ от внешнего сервиса.
            **kwargs: Дополнительные параметры для базового класса.
        """
        self.service_name = service_name
        self.external_code = external_code
        self.external_response = external_response or {}

        tech_details = kwargs.pop("tech_details", {})
        tech_details.update(
            {
                "service_name": service_name,
                "external_code": external_code,
                "external_response": external_response,
            }
        )

        super().__init__(
            message=message,
            entity=f"ExternalService.{service_name}",
            tech_details=tech_details,
            log_level=LogLevel.WARNING,
            **kwargs,
        )

    def as_dict(self, include_tech_details: bool = False) -> dict[str, Any]:
        """Ошибка в виде словаря для ответа фронту.

        Включает информацию о внешнем сервисе и коде ошибки.
        """
        base = super().as_dict(include_tech_details=include_tech_details)

        # Добавляем информацию о внешнем сервисе в ответ
        return {
            **base,
            "service_name": self.service_name,
            "external_code": self.external_code,
        }


class SigningServiceError(ExternalServiceError):
    """Исключение для ошибок сервиса подписания документов."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        """Инициализация ошибки сервиса подписания."""
        super().__init__(message=message, service_name="signing", **kwargs)
