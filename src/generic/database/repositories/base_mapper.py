from __future__ import annotations

import dataclasses
import inspect
from enum import Enum
from functools import cached_property
from typing import Any, Generic, Self, TypeAlias, TypeVar

from pydantic import BaseModel
from sqlalchemy.orm import RelationshipProperty

from generic.database.repositories.types import TOrmModel
from generic.domain.entity import BaseEntity, TEntity

sentinel = object()

TBaseMapper = TypeVar("TBaseMapper", bound="BaseMapper[Any, Any]")
EntityFieldName: TypeAlias = str  # noqa: UP040
OrmFieldName: TypeAlias = str  # noqa: UP040


@dataclasses.dataclass
class OrmFKMapping(Generic[TBaseMapper]):
    """Поле в орм модели, которое является внешним ключом."""

    name: OrmFieldName  # название колонки в sa-модели (user_id)
    mapper: TBaseMapper | None

    @property
    def relation_name(self) -> str:
        """Название атрибута связи для колонки."""
        return self.name.removesuffix("_id")


OrmByEntityFields: TypeAlias = dict[EntityFieldName, OrmFieldName | OrmFKMapping[TBaseMapper] | None]  # noqa: UP040


class BaseMapper(Generic[TEntity, TOrmModel]):
    """Базовый класс маппера сущности в орм модель и обратно."""

    def __init__(
        self,
        *,
        entity_cls: type[TEntity],
        orm_model: type[TOrmModel],
        extra_orm_by_entity_fields: OrmByEntityFields | None = None,  # type:ignore[type-arg]
    ) -> None:
        """Инициализация маппера.

        Args:
            entity_cls: класс сущности.
            orm_model: класс орм модели.
            extra_orm_by_entity_fields: словарь сопоставления атрибутов орм модели (значения)
                по атрибутам полей сущности (ключи).
                Необходимо, если название полей различаются, а также ОБЯЗАТЕЛЕН для FK полей.
                В качестве значения для вложенных сущностей нужно указать OrmFKMapping.

        Пример:
            class MyCat:  # сущность
                id: str
                name: str

            class SaMyCat:  # орм модель
                id: str
                name: str

            class MyBox:  # сущность
                id: str
                name: str

            class SaMyBox:  # орм модель
                id: str
                description: str

            cat_mapper = BaseMapper(entity_cls=MyCat, orm_model=SaMyCat)
            box_mapper = BaseMapper(
                entity_cls=MyBox,
                orm_model=SaMyBox,
                extra_orm_by_entity_fields={"name": "description", "cat": OrmFKMapping("cat_id", cat_mapper)}
            )

            В результате:
                box_mapper.entity_to_orm(
                    MyBox(id="1", name="2", cat=MyCat(id="3", name="4"))
                ) -> SaMyBox(id="1", description="2", cat_id="3", cat=None)

                box_mapper.orm_to_entity(
                    SaMyBox(id="1", description="2", cat=SaMyCat(id="3", name="4"))
                ) -> MyBox(id="1", name="2", cat=MyCat(id="3", name="4"))
        """
        self.entity_cls = entity_cls
        self.orm_model = orm_model
        self.extra_orm_by_entity_fields = extra_orm_by_entity_fields or {}

    def entity_to_orm(self, obj: TEntity, **kwargs: Any) -> TOrmModel:
        """Конвертирует TEntity -> TSaModel.

        Для FK сущностей будет замаплено только поле orm.fk_id (entity.fk.id or entity.fk_id).
        FK объектом считается ключ, у которого в качестве значения OrmFKMapping.
        """
        init_kwargs = self._get_init_orm_kwargs(obj, **kwargs)
        return self.orm_model(**init_kwargs)

    def orm_to_entity(self, orm: TOrmModel, **kwargs: Any) -> TEntity:
        """Конвертирует TOrmModel -> TEntity."""
        init_kwargs = self._get_init_entity_kwargs(orm, **kwargs)
        return self.entity_cls(**init_kwargs)

    def _get_init_orm_kwargs(self, obj: TEntity, **kwargs: Any) -> dict[str, Any]:  # noqa: ARG002
        """Возвращает параметры инициализации орм-модели."""
        init_kwargs: dict[str, Any] = {}
        for entity_attr, orm_attr in self.orm_by_entity_fields.items():
            if orm_attr is None:
                continue
            value = getattr(obj, entity_attr, sentinel)
            if value is sentinel:
                continue
            if isinstance(value, (BaseEntity, BaseModel)) and not isinstance(orm_attr, OrmFKMapping):
                msg = (
                    f"""Для FK полей необходимо определить маппинг OrmFKMapping
                    в extra_orm_by_entity_fields: {obj.__class__.__name__}.{entity_attr}={value}""",
                )
                raise TypeError(msg)
            if isinstance(value, Enum):
                value = value.value

            if isinstance(orm_attr, str):
                if not hasattr(self.orm_model, orm_attr):
                    continue
                init_kwargs[orm_attr] = value

            elif isinstance(orm_attr, OrmFKMapping):
                orm_attr = orm_attr.name  # noqa: PLW2901
                value_id = getattr(obj, f"{entity_attr}_id", sentinel)
                value_id = getattr(value, "id", None) if sentinel else value_id
                init_kwargs[orm_attr] = value_id
        return init_kwargs

    def _get_init_entity_kwargs(self, orm: TOrmModel, **kwargs: Any) -> dict[str, Any]:
        """Возвращает параметры инициализации сущности."""
        init_kwargs: dict[str, Any] = {}
        for entity_attr, orm_attr in self.orm_by_entity_fields.items():
            if orm_attr is None:
                continue
            get_attr = orm_attr.name.removesuffix("_id") if isinstance(orm_attr, OrmFKMapping) else orm_attr
            orm_value = getattr(orm, get_attr, sentinel)
            if orm_value is sentinel:
                continue

            if orm_value is None:
                init_kwargs[entity_attr] = None
            elif isinstance(orm_attr, str):
                init_kwargs[entity_attr] = orm_value
            elif isinstance(orm_attr, OrmFKMapping) and orm_attr.mapper:
                init_kwargs[entity_attr] = orm_attr.mapper.orm_to_entity(orm_value, **kwargs)
        return init_kwargs

    @cached_property
    def orm_by_entity_fields(self) -> OrmByEntityFields:  # type:ignore[type-arg]
        """Возвращает словарь значений полей орм-модели по ключам полей сущности."""
        return {f: self.extra_orm_by_entity_fields.get(f, f) for f in self.init_entity_fields}

    @cached_property
    def init_entity_fields(self) -> set[str]:
        """Возвращает поля, которые нужно инициализировать для сущности."""
        init_sign = inspect.signature(self.entity_cls.__init__)
        return set(init_sign.parameters.keys()) - {"self"}

    @cached_property
    def mappers_by_relations(self) -> dict[Any, Self]:
        """Возвращает словарь, где ключ связь с вложенной orm моделью, значение - маппер для нее."""
        return {
            getattr(self.orm_model, orm_attr.relation_name): orm_attr.mapper  # type:ignore[misc,union-attr]
            for orm_attr in self.orm_by_entity_fields.values()
            if (isinstance(orm_attr, OrmFKMapping) and orm_attr.mapper is not None)
            or (hasattr(orm_attr, "property") and isinstance(orm_attr.property, RelationshipProperty))  # type:ignore[union-attr]
        }
