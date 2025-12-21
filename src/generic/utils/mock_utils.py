import contextlib
import inspect
from collections.abc import Callable, Generator
from types import ModuleType
from typing import Any
from unittest import mock
from unittest.mock import MagicMock


@contextlib.contextmanager
def mock_patch(
    func: Callable,  # type:ignore[type-arg]
    *args: Any,
    called_from: Any = None,
    **kwargs: Any,
) -> Generator[MagicMock]:
    """Шорткат для облегчения прописывания target.path при моке функции.

    Возвращает mock.patch на `func`.

    Args:
        func: функция, которая патчится.
        args: аргументы
        called_from: откуда брать модуль, в котором патчится функция - модуль либо любой объект из этого модуля.
        kwargs: kw аргументы

    Пример:
        вариант без него:
        with mock.patch("src.context.service.create_func"):
            ...

        вариант с ним:
        with mock_patch(create_func):
            ...

        Можно передавать метод класса MyClass.send_to_nats - для этого будет использован
        with mock.patch.object(MyClass, "send_to_nats"):
    """
    if cls := inspect._findclass(func):  # type:ignore[attr-defined]  # noqa: SLF001
        with mock.patch.object(cls, func.__name__, *args, **kwargs) as m:
            yield m

        return

    if called_from is None:
        module_name = f"{func.__module__}"
    elif isinstance(called_from, str):
        module_name = called_from
    elif isinstance(called_from, ModuleType):
        module_name = f"{called_from.__name__}"
    else:
        module_name = f"{called_from.__module__}"

    path = f"{module_name}.{func.__name__}"
    with mock.patch(path, *args, **kwargs) as m:
        yield m
