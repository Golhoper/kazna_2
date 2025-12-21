from collections.abc import Callable, Iterable
from typing import Any, TypeVar

from funcy import lpluck, lpluck_attr, pluck, pluck_attr

from generic.utils.map_utils import smap_str

T = TypeVar("T")


def ipluck_attr(func: Callable[[Iterable[Any]], T], attr: str, objects: Iterable[Any]) -> T:
    """pluck_attr c произвольной коллекцией."""
    return func(pluck_attr(attr, objects))


def ipluck(func: Callable[[Iterable[Any]], T], key: str, mappings: Iterable[Any]) -> T:
    """Pluck c произвольной коллекцией."""
    return func(pluck(key, mappings))


def spluck_attr(attr: str, objects: Iterable[Any]) -> set[Any]:
    """Возвращает множество attr из objects."""
    return ipluck_attr(set, attr, objects)


def spluck_attr_id(objects: Iterable[Any]) -> set[Any]:
    """Возвращает множество id из objects."""
    return spluck_attr("id", objects)


def spluck_attr_id_str(objects: Iterable[Any]) -> set[Any]:
    """Возвращает множество id из objects."""
    return smap_str(pluck_attr("id", objects))


def spluck_attr_guid(objects: Iterable[Any]) -> set[Any]:
    """Возвращает множество guid из objects."""
    return spluck_attr("guid", objects)


def spluck_attr_code(objects: Iterable[Any]) -> set[Any]:
    """Возвращает множество code из objects."""
    return spluck_attr("code", objects)


def spluck_attr_name(objects: Iterable[Any]) -> set[Any]:
    """Возвращает множество name из objects."""
    return spluck_attr("name", objects)


def spluck(key: str, mappings: Iterable[Any]) -> set[Any]:
    """Возвращает множество key из mappings."""
    return ipluck(set, key, mappings)


def spluck_id(mappings: Iterable[Any]) -> set[Any]:
    """Возвращает множество id из mappings."""
    return spluck("id", mappings)


def spluck_guid(mappings: Iterable[Any]) -> set[Any]:
    """Возвращает множество guid из mappings."""
    return spluck("guid", mappings)


def spluck_code(mappings: Iterable[Any]) -> set[Any]:
    """Возвращает множество code из mappings."""
    return spluck("code", mappings)


def spluck_name(mappings: Iterable[Any]) -> set[Any]:
    """Возвращает множество name из mappings."""
    return spluck("name", mappings)


def tpluck_attr(attr: str, objects: Iterable[Any]) -> tuple[Any]:
    """Возвращает кортеж attr из objects."""
    return ipluck_attr(tuple, attr, objects)


def tpluck_attr_id(objects: Iterable[Any]) -> tuple[Any]:
    """Возвращает кортеж id из objects."""
    return tpluck_attr("id", objects)


def tpluck_attr_name(objects: Iterable[Any]) -> tuple[Any]:
    """Возвращает кортеж name из objects."""
    return tpluck_attr("name", objects)


def tpluck(key: str, mappings: Iterable[Any]) -> tuple[Any]:
    """Возвращает кортеж key из mappings."""
    return ipluck(tuple, key, mappings)


def tpluck_id(mappings: Iterable[Any]) -> tuple[Any]:
    """Возвращает кортеж id из mappings."""
    return tpluck("id", mappings)


def tpluck_name(mappings: Iterable[Any]) -> tuple[Any]:
    """Возвращает кортеж name из mappings."""
    return tpluck("name", mappings)


def lpluck_attr_id(objects: Iterable[Any]) -> list[Any] | Any:
    """Возвращает список id из objects."""
    return lpluck_attr("id", objects)


def lpluck_attr_guid(objects: Iterable[Any]) -> list[Any] | Any:
    """Возвращает список id из objects."""
    return lpluck_attr("guid", objects)


def lpluck_attr_code(objects: Iterable[Any]) -> list[Any] | Any:
    """Возвращает список id из objects."""
    return lpluck_attr("code", objects)


def lpluck_id(mappings: Iterable[Any]) -> list[Any] | Any:
    """Возвращает список id из mappings."""
    return lpluck("id", mappings)


def lpluck_guid(mappings: Iterable[Any]) -> list[Any] | Any:
    """Возвращает список id из mappings."""
    return lpluck("guid", mappings)


def lpluck_code(mappings: Iterable[Any]) -> list[Any] | Any:
    """Возвращает список id из mappings."""
    return lpluck("code", mappings)


def lpluck_attr_name(objects: Iterable[Any]) -> list[Any] | Any:
    """Возвращает список name из objects."""
    return lpluck_attr("name", objects)


def lpluck_name(mappings: Iterable[Any]) -> list[Any] | Any:
    """Возвращает список name из mappings."""
    return lpluck("name", mappings)
