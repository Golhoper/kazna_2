import datetime
from typing import Any

import humps
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from pydantic_core.core_schema import FieldSerializationInfo


class CamelCasedAliasesModel(BaseModel):
    """Класс для подключения camelCase псевдонимов в api для фронта.

    Можно использовать как request model и response model во view функциях.
    Пример:
        class FooRequest(CamelCasedAliasesModel):
            full_name: str
            extra_number: int

        >>> FooRequest(full_name='name', extra_number=123)
        FooRequest(full_name='name', extra_number=123)
        >>> FooRequest(fullName='name', extraNumber=123)
        FooRequest(full_name='name', extra_number=123)

        >>> foo = FooRequest(full_name='name', extra_number=123)
        >>> foo.model_dump()
        {'full_name': 'name', 'extra_number': 123}
        >>> foo.model_dump(by_alias=True)
        {'fullName': 'name', 'extraNumber': 123}
    """

    model_config = ConfigDict(populate_by_name=True, alias_generator=humps.camelize, from_attributes=True)

    @field_serializer(
        "created_at",
        "updated_at",
        "deleted_at",
        "archived_at",
        when_used="json-unless-none",
        check_fields=False,
    )
    def default_datetime_fields_serialize(self, value: datetime.datetime, _info: FieldSerializationInfo) -> str:
        """Сериализация datetime.datetime для json."""
        return value.isoformat()


class BaseErrorSchemaOut(CamelCasedAliasesModel):
    """Базовая модель информации об ошибки в Response."""

    error: str = Field(description="Класс возникшего исключения")
    entity: str | None = Field(
        description="Название класса сущности бизнес логики, в которой возникло исключение",
        default="",
    )
    id: Any | None = Field(
        description="ID сущности бизнес логики, в которой возникло исключение",
        default=None,
    )
    field: str | None = Field(description="Название поля сущности, с которым связана ошибка", default="")
    message: str = Field(description="Сообщение об ошибке, предназначенное для конечного пользователя")


class UnexpectedErrorSchemaOut(BaseModel):
    """Модель информации о непредвиденной ошибке в Response."""

    message: str = Field(description="Сообщение об ошибке, предназначенное для конечного пользователя")
