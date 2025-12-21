from collections.abc import Callable, Iterable
from typing import Any, TypeVar
from uuid import UUID

from funcy import lmap

T = TypeVar("T")


def map_by_field(objects: Iterable[T], field_name: str) -> dict[Any, T]:
    """Возвращает словарь {<ключ>: object} из objects."""
    return {obj[field_name] if isinstance(obj, dict) else getattr(obj, field_name): obj for obj in objects}


def map_by_id(objects: Iterable[T]) -> dict[str | UUID | int, T]:
    """Возвращает словарь {id: object} из objects."""
    return map_by_field(objects, "id")


def map_by_guid(objects: Iterable[T]) -> dict[str | UUID, T]:
    """Возвращает словарь {guid: object} из objects."""
    return map_by_field(objects, "guid")


def map_by_code(objects: Iterable[T]) -> dict[str | UUID, T]:
    """Возвращает словарь {code: object} из objects."""
    return map_by_field(objects, "code")


def map_by_name(objects: Iterable[T]) -> dict[str | UUID, T]:
    """Возвращает словарь {name: object} из objects."""
    return map_by_field(objects, "name")


def smap(func: Callable[[Iterable[T]], T], objects: Iterable[T]) -> set[T]:
    """Возвращает множество результатов func(objects)."""
    return set(map(func, objects))  # type:ignore[arg-type]


def smap_str(objects: Iterable[T]) -> set[str]:
    """Возвращает множество строк."""
    return smap(str, objects)  # type:ignore[arg-type]


def lmap_str(objects: Iterable[T]) -> list[str]:
    """Возвращает список строк."""
    return lmap(str, objects)  # type:ignore[no-any-return]
