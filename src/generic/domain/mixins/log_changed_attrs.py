import dataclasses
from typing import Any

from generic.domain.values import UNEVALUATED


@dataclasses.dataclass
class LogChangedAttrs:
    """Класс с данными измененных атрибутов."""

    field_name: str
    old_value: Any
    new_value: Any


class LogChangedAttrsMixin:
    """Миксин для отслеживания изменений атрибутов класса."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._logs_changed_attrs_by_field: dict[str, LogChangedAttrs] = {}

    def __setattr__(self, name: str, value: Any) -> None:
        """Устанавливает значение атрибута."""
        if not hasattr(self, "_logs_changed_attrs_by_field"):
            super().__setattr__(name, value)
            return

        try:
            old_value = getattr(self, name)
        except Exception:  # noqa: BLE001
            old_value = UNEVALUATED

        super().__setattr__(name, value)
        self._make_log_changed_attrs(name, old_value=old_value, new_value=getattr(self, name))

    @property
    def logs_changed_attrs_by_field(self) -> dict[str, LogChangedAttrs]:
        """Возвращает словарь с логами измененных атрибутов с ключем по их названию."""
        return getattr(self, "_logs_changed_attrs_by_field", {})

    @property
    def changed_values(self) -> dict[str, Any]:
        """Возвращает словарь с измененными полями и их новыми значениями."""
        changed = {}
        for field in self._logs_changed_attrs_by_field:
            field_name = field.removeprefix("_")
            changed[field_name] = getattr(self, field)
        return changed

    def update_attrs(self, validated_data: dict[str, Any]) -> None:
        """Обновляет атрибуты из данных `validated_data`."""
        for attr, value in validated_data.items():
            if hasattr(self, attr):
                setattr(self, attr, value)

    def _make_log_changed_attrs(self, name: str, old_value: Any, new_value: Any) -> None:
        """Фиксирует лог измененных атрибутов."""
        if data := self._logs_changed_attrs_by_field.get(name):
            # удалять плохо, т.к. repository.update может сделать промежуточный апдейт на основе changed_values,
            # а после сущность заново не сформируют из бд, но значение вернут на первоначальное
            # if data.old_value == value:
            #     del self._logs_changed_attrs_by_field[name]
            data.new_value = new_value
            # data.old_value не перезатираем - всегда равно первоначальному значению после формирования сущности
        elif new_value != old_value:
            data = LogChangedAttrs(
                field_name=name,
                old_value=old_value,
                new_value=new_value,
            )
            self._logs_changed_attrs_by_field[name] = data
