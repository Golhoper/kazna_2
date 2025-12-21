"""Коллектор для сбора данных audit log."""

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Protocol, TypedDict

import humps

from generic.database.audit_log.enums import EntityAuditLogTypeEnum
from generic.domain.entity import BaseEntity


# Protocols для типизации
class HasId(Protocol):
    """Протокол для объектов с ID."""

    id: Any


class LoggedEntity(Protocol):
    """Протокол для сущностей с логированием изменений."""

    logs_changed_attrs_by_field: dict[str, Any]


class AuditLogConstants:
    """Константы для audit log."""

    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    DATE_FORMAT = "%Y-%m-%d"
    LOGS_ATTR_PREFIX = "_logs_changed_attrs"
    UNKNOWN_ENTITY_NAME = "unknown"

    # Типы коллекций для проверки
    COLLECTION_TYPES = (list, tuple, set)


# TypedDict для структур данных
class FieldChangeDict(TypedDict):
    """Словарь с информацией об изменении поля."""

    old: Any
    new: Any


class M2MChangeDict(TypedDict):
    """Словарь с информацией об изменениях M2M связи."""

    added: list[str]
    removed: list[str]


class EntityRecordDict(TypedDict):
    """Словарь с информацией о сущности в audit log."""

    id: str | None
    type: str
    changes: dict[str, Any]


class AuditLogRootDict(TypedDict):
    """Корневая структура audit log."""

    root_entity: str
    created_at: str


# Type aliases
AuditLogData = AuditLogRootDict  # Базовый тип + динамические ключи с EntityRecordDict
EntitiesChanges = dict[str, EntityRecordDict]


class AuditLogValueSerializer:
    """Сериализатор значений для audit log."""

    @staticmethod
    def serialize(value: Any) -> Any:  # noqa: C901,PLR0911,PLR0912
        """Сериализует значение для сохранения в JSONB.

        Args:
            value: значение для сериализации

        Returns:
            Сериализованное значение
        """
        if value is None:
            return None

        try:
            # Базовые типы
            if isinstance(value, (str, int, float, bool)):
                return value

            # Enum
            if isinstance(value, Enum):
                return value.value

            # UUID
            if isinstance(value, uuid.UUID):
                return str(value)

            # Datetime и date
            if isinstance(value, datetime):
                return value.strftime(AuditLogConstants.DATETIME_FORMAT)
            if isinstance(value, date):
                return value.strftime(AuditLogConstants.DATE_FORMAT)

            # Decimal
            if isinstance(value, Decimal):
                return float(value)

            # Set - конвертируем в list
            if isinstance(value, set):
                return [AuditLogValueSerializer.serialize(v) for v in value]

            # List и tuple
            if isinstance(value, (list, tuple)):
                return [AuditLogValueSerializer.serialize(v) for v in value]

            # Dict
            if isinstance(value, dict):
                return {k: AuditLogValueSerializer.serialize(v) for k, v in value.items()}

            # Для остальных типов используем строковое представление
            return str(value)

        except Exception:  # noqa: BLE001
            # Fallback на строковое представление при любых ошибках сериализации
            return str(value)


class NestedEntitiesCollector:
    """Помощник для сбора вложенных сущностей."""

    def __init__(self) -> None:
        """Инициализирует коллектор."""
        self.entities_set: set[int] = set()
        self.entities: list[BaseEntity] = []

    def add_entity(self, entity: BaseEntity) -> None:
        """Добавляет сущность если её ещё нет.

        Args:
            entity: сущность для добавления
        """
        if id(entity) not in self.entities_set:
            self.entities.append(entity)
            self.entities_set.add(id(entity))

    def add_from_collection(self, collection: list[Any] | tuple[Any, ...] | set[Any]) -> None:
        """Добавляет сущности из коллекции.

        Args:
            collection: коллекция элементов
        """
        for item in collection:
            if isinstance(item, BaseEntity):
                self.add_entity(item)


class AuditLogCollector:
    """Собирает данные для audit log из сущностей."""

    def _build_audit_log_data(self, obj: BaseEntity, action_type: EntityAuditLogTypeEnum) -> dict[str, Any]:
        """Базовый метод для создания audit log данных.

        Args:
            obj: сущность для обработки
            action_type: тип действия (CREATE/UPDATE/DELETE)

        Returns:
            Словарь с данными audit log
        """
        entities_changes: EntitiesChanges = {}

        # Для CREATE и DELETE сохраняем полный снимок,
        # для UPDATE - только изменения
        if action_type in (EntityAuditLogTypeEnum.CREATE, EntityAuditLogTypeEnum.DELETE):
            self._collect_entity_snapshot_hierarchical(
                obj=obj, action_type=action_type, entities_changes=entities_changes
            )
        else:  # EntityAuditLogTypeEnum.UPDATE
            self._collect_entity_changes_hierarchical(
                obj=obj, action_type=action_type, entities_changes=entities_changes
            )

        return {
            "root_entity": self._get_entity_name(obj),
            "created_at": datetime.now(UTC).strftime(AuditLogConstants.DATETIME_FORMAT),
            **entities_changes,
        }

    def collect_update_data(self, obj: BaseEntity) -> dict[str, Any]:
        """Возвращает данные об изменениях сущности и всех вложенных сущностей для audit log.

        Формат возвращаемых данных:
        {
            "root_entity": "act",
            "created_at": "2025-10-01 15:10:01",
            "act": {
                "id": "...",
                "type": "update",
                "changes": {
                    "field1": {"old": old_value, "new": new_value},
                }
            }
        }

        Args:
            obj: сущность с изменениями

        Returns:
            Словарь с данными об изменениях
        """
        return self._build_audit_log_data(obj, EntityAuditLogTypeEnum.UPDATE)

    def collect_delete_data(self, obj: BaseEntity) -> dict[str, Any]:
        """Возвращает данные о сущности для audit log при удалении.

        Сохраняет полное состояние сущности и всех вложенных сущностей перед удалением.

        Args:
            obj: сущность для удаления

        Returns:
            Словарь с данными сущности в новом формате
        """
        return self._build_audit_log_data(obj, EntityAuditLogTypeEnum.DELETE)

    def collect_create_data(self, obj: BaseEntity) -> dict[str, Any]:
        """Возвращает данные о сущности для audit log при создании.

        Сохраняет полное состояние созданной сущности и всех вложенных сущностей.

        Args:
            obj: созданная сущность

        Returns:
            Словарь с данными сущности в новом формате
        """
        return self._build_audit_log_data(obj, EntityAuditLogTypeEnum.CREATE)

    def _get_entity_name(self, obj: BaseEntity | Any) -> str:
        """Возвращает имя сущности для использования в audit log.

        Args:
            obj: сущность

        Returns:
            Имя сущности (имя класса в snake_case с суффиксом _entity)
        """
        if not isinstance(obj, BaseEntity):
            return AuditLogConstants.UNKNOWN_ENTITY_NAME

        class_name = obj.__class__.__name__
        snake_case_name = humps.decamelize(class_name)
        return f"{snake_case_name}_entity"

    def _get_entity_id(self, obj: BaseEntity) -> str | None:
        """Возвращает ID сущности в виде строки.

        Args:
            obj: сущность

        Returns:
            ID сущности или None если ID отсутствует
        """
        return str(obj.id) if hasattr(obj, "id") else None

    def _should_skip_attribute(self, attr_name: str) -> bool:
        """Проверяет, нужно ли пропустить атрибут при обработке.

        Args:
            attr_name: имя атрибута

        Returns:
            True если атрибут нужно пропустить
        """
        return attr_name.startswith(AuditLogConstants.LOGS_ATTR_PREFIX)

    def _generate_unique_key(
        self,
        entity_name: str,
        entity_id: str | None,
        entities_changes: EntitiesChanges,
    ) -> str:
        """Генерирует уникальный ключ для сущности в словаре изменений.

        Если сущность с таким именем уже есть, добавляет ID для уникальности.

        Args:
            entity_name: имя сущности
            entity_id: ID сущности
            entities_changes: словарь изменений

        Returns:
            Уникальный ключ
        """
        key = entity_name
        if key in entities_changes and entity_id:
            key = f"{entity_name}_{entity_id}"
        return key

    def _add_entity_record(
        self,
        entities_changes: EntitiesChanges,
        entity_name: str,
        entity_id: str | None,
        action_type: EntityAuditLogTypeEnum,
        changes: dict[str, FieldChangeDict | M2MChangeDict | Any],
    ) -> None:
        """Добавляет запись о сущности в словарь изменений.

        Args:
            entities_changes: словарь для накопления изменений
            entity_name: имя сущности
            entity_id: ID сущности
            action_type: тип действия (CREATE/UPDATE/DELETE)
            changes: словарь с изменениями или снимком
        """
        key = self._generate_unique_key(entity_name, entity_id, entities_changes)
        record: EntityRecordDict = {
            "id": entity_id,
            "type": action_type.value,
            "changes": changes,
        }
        entities_changes[key] = record

    def _should_process_entity(self, obj: BaseEntity | Any, processed_ids: set[str] | None) -> bool:
        """Проверяет, нужно ли обрабатывать сущность.

        Args:
            obj: объект для проверки
            processed_ids: множество уже обработанных ID

        Returns:
            True если сущность нужно обработать
        """
        if not isinstance(obj, BaseEntity):
            return False

        if processed_ids is None:
            return True

        entity_id = self._get_entity_id(obj)
        entity_name = self._get_entity_name(obj)
        entity_key = f"{entity_name}_{entity_id}"

        return entity_key not in processed_ids

    def _update_processed_ids(
        self, processed_ids: set[str] | None, entity_name: str, entity_id: str | None
    ) -> set[str]:
        """Обновляет множество обработанных ID.

        Args:
            processed_ids: текущее множество ID
            entity_name: имя сущности
            entity_id: ID сущности

        Returns:
            Обновлённое множество ID
        """
        if processed_ids is None:
            processed_ids = set()

        entity_key = f"{entity_name}_{entity_id}"
        processed_ids.add(entity_key)
        return processed_ids

    def _handle_entity_field_change(
        self,
        entity_changes: dict[str, FieldChangeDict | M2MChangeDict],
        field_name: str,
        old_value: Any,
        new_value: BaseEntity,
        nested_collector: NestedEntitiesCollector,
    ) -> None:
        """Обрабатывает изменение поля-сущности.

        Args:
            entity_changes: словарь изменений для накопления
            field_name: имя поля
            old_value: старое значение
            new_value: новое значение (BaseEntity)
            nested_collector: коллектор вложенных сущностей
        """
        # Добавляем изменение ID если есть реальное изменение
        if self._has_entity_id_changed(old_value, new_value):
            entity_changes[field_name] = self._create_id_change_record(old_value, new_value)

        # Добавляем для рекурсивной обработки
        nested_collector.add_entity(new_value)

    def _has_entity_id_changed(self, old_value: Any, new_value: BaseEntity) -> bool:
        """Проверяет, изменился ли ID сущности.

        Args:
            old_value: старое значение
            new_value: новое значение (BaseEntity)

        Returns:
            True если ID изменился
        """
        if isinstance(old_value, BaseEntity):
            return old_value.id != new_value.id
        return old_value is not None  # Было не-сущность, стало сущность

    def _create_id_change_record(self, old_value: Any, new_value: BaseEntity) -> FieldChangeDict:
        """Создаёт запись об изменении ID.

        Args:
            old_value: старое значение
            new_value: новое значение (BaseEntity)

        Returns:
            Словарь с изменением ID
        """
        old_id = str(old_value.id) if isinstance(old_value, BaseEntity) else (str(old_value) if old_value else None)
        return {"old": old_id, "new": str(new_value.id)}

    def _handle_collection_field_change(
        self,
        entity_changes: dict[str, FieldChangeDict | M2MChangeDict],
        field_name: str,
        old_value: Any,
        new_value: list[Any] | tuple[Any, ...] | set[Any],
        nested_collector: NestedEntitiesCollector,
    ) -> None:
        """Обрабатывает изменение поля-коллекции.

        Args:
            entity_changes: словарь изменений для накопления
            field_name: имя поля
            old_value: старое значение
            new_value: новое значение (коллекция)
            nested_collector: коллектор вложенных сущностей
        """
        m2m_changes = self._get_m2m_changes_summary(old_value, new_value)
        if m2m_changes:
            entity_changes[field_name] = m2m_changes

        # Собираем вложенные сущности из коллекции
        nested_collector.add_from_collection(new_value)

    def _handle_simple_field_change(
        self,
        entity_changes: dict[str, FieldChangeDict | M2MChangeDict],
        field_name: str,
        old_value: Any,
        new_value: Any,
    ) -> None:
        """Обрабатывает изменение простого поля.

        Args:
            entity_changes: словарь изменений для накопления
            field_name: имя поля
            old_value: старое значение
            new_value: новое значение
        """
        change: FieldChangeDict = {
            "old": AuditLogValueSerializer.serialize(old_value),
            "new": AuditLogValueSerializer.serialize(new_value),
        }
        entity_changes[field_name] = change

    def _process_changed_fields(
        self, obj: BaseEntity
    ) -> tuple[dict[str, FieldChangeDict | M2MChangeDict], NestedEntitiesCollector]:
        """Обрабатывает изменённые поля сущности.

        Args:
            obj: сущность для обработки

        Returns:
            Кортеж из словаря изменений и коллектора вложенных сущностей
        """
        entity_changes: dict[str, FieldChangeDict | M2MChangeDict] = {}
        nested_collector = NestedEntitiesCollector()

        for field_name, log_data in obj.logs_changed_attrs_by_field.items():
            clean_field_name = field_name.removeprefix("_")
            old_value = log_data.old_value
            new_value = log_data.new_value

            if isinstance(new_value, BaseEntity):
                self._handle_entity_field_change(
                    entity_changes, clean_field_name, old_value, new_value, nested_collector
                )
            elif isinstance(new_value, (list, tuple, set)):
                self._handle_collection_field_change(
                    entity_changes, clean_field_name, old_value, new_value, nested_collector
                )
            else:
                self._handle_simple_field_change(entity_changes, clean_field_name, old_value, new_value)

        return entity_changes, nested_collector

    def _collect_additional_nested_entities(self, obj: BaseEntity, nested_collector: NestedEntitiesCollector) -> None:
        """Собирает дополнительные вложенные сущности, которые не изменились.

        Args:
            obj: сущность для обработки
            nested_collector: коллектор вложенных сущностей
        """
        for attr_name, attr_value in vars(obj).items():
            if self._should_skip_attribute(attr_name):
                continue

            # Если это вложенная сущность
            if isinstance(attr_value, BaseEntity):
                nested_collector.add_entity(attr_value)
            # Если это коллекция
            elif isinstance(attr_value, (list, tuple, set)):
                nested_collector.add_from_collection(attr_value)

    def _process_nested_entities(
        self,
        nested_entities: list[BaseEntity],
        action_type: EntityAuditLogTypeEnum,
        entities_changes: EntitiesChanges,
        processed_ids: set[str],
    ) -> None:
        """Рекурсивно обрабатывает вложенные сущности.

        Args:
            nested_entities: список вложенных сущностей
            action_type: тип действия
            entities_changes: словарь изменений
            processed_ids: множество обработанных ID
        """
        for nested_entity in nested_entities:
            self._collect_entity_changes_hierarchical(
                obj=nested_entity,
                action_type=action_type,
                entities_changes=entities_changes,
                processed_ids=processed_ids,
            )

    def _collect_entity_changes_hierarchical(
        self,
        obj: BaseEntity | Any,
        action_type: EntityAuditLogTypeEnum,
        entities_changes: EntitiesChanges,
        processed_ids: set[str] | None = None,
    ) -> None:
        """Собирает изменения сущности и вложенных сущностей в иерархической структуре.

        Args:
            obj: сущность для сбора изменений
            action_type: тип действия (CREATE/UPDATE/DELETE)
            entities_changes: словарь для накопления изменений по сущностям
            processed_ids: множество уже обработанных id сущностей (для предотвращения циклов)
        """
        if not self._should_process_entity(obj, processed_ids):
            return

        entity_id = self._get_entity_id(obj)
        entity_name = self._get_entity_name(obj)
        processed_ids = self._update_processed_ids(processed_ids, entity_name, entity_id)

        # Обрабатываем изменённые поля
        entity_changes, nested_collector = self._process_changed_fields(obj)

        # Собираем дополнительные вложенные сущности
        self._collect_additional_nested_entities(obj, nested_collector)

        # Добавляем запись о текущей сущности, если есть изменения
        if entity_changes:
            self._add_entity_record(
                entities_changes=entities_changes,
                entity_name=entity_name,
                entity_id=entity_id,
                action_type=action_type,
                changes=entity_changes,
            )

        # Рекурсивно обрабатываем вложенные сущности
        self._process_nested_entities(nested_collector.entities, action_type, entities_changes, processed_ids)

    def _collect_entity_snapshot_hierarchical(  # noqa:C901,PLR0912
        self,
        obj: BaseEntity | Any,
        action_type: EntityAuditLogTypeEnum,
        entities_changes: EntitiesChanges,
        processed_ids: set[str] | None = None,
    ) -> None:
        """Собирает снимок сущности и вложенных сущностей в иерархической структуре.

        Используется для CREATE и DELETE операций.

        Args:
            obj: сущность для снимка
            action_type: тип действия (CREATE/DELETE)
            entities_changes: словарь для накопления данных по сущностям
            processed_ids: множество уже обработанных id сущностей
        """
        if not isinstance(obj, BaseEntity):
            return

        if processed_ids is None:
            processed_ids = set()

        entity_id = self._get_entity_id(obj)
        entity_name = self._get_entity_name(obj)

        # Защита от циклических ссылок
        entity_key = f"{entity_name}_{entity_id}"
        if entity_key in processed_ids:
            return
        processed_ids.add(entity_key)

        # Собираем снимок полей текущей сущности
        entity_snapshot: dict[str, Any] = {}
        nested_entities: list[BaseEntity] = []

        for attr_name, attr_value in vars(obj).items():
            if self._should_skip_attribute(attr_name):
                continue

            clean_attr_name = attr_name.removeprefix("_")

            # Вложенная сущность (FK)
            if isinstance(attr_value, BaseEntity):
                entity_snapshot[clean_attr_name] = str(attr_value.id)
                nested_entities.append(attr_value)
            # M2M коллекция
            elif isinstance(attr_value, (list, tuple, set)):
                # Проверяем, содержит ли коллекция BaseEntity
                if attr_value:
                    first_item = next(iter(attr_value), None)
                    if isinstance(first_item, BaseEntity):
                        entity_snapshot[clean_attr_name] = [str(item.id) for item in attr_value]
                        nested_entities.extend([item for item in attr_value if isinstance(item, BaseEntity)])
                    else:
                        entity_snapshot[clean_attr_name] = AuditLogValueSerializer.serialize(list(attr_value))
                else:
                    entity_snapshot[clean_attr_name] = AuditLogValueSerializer.serialize(list(attr_value))
            # Обычное поле
            else:
                entity_snapshot[clean_attr_name] = AuditLogValueSerializer.serialize(attr_value)

        # Добавляем запись о текущей сущности
        self._add_entity_record(
            entities_changes=entities_changes,
            entity_name=entity_name,
            entity_id=entity_id,
            action_type=action_type,
            changes=entity_snapshot,
        )

        # Рекурсивно обрабатываем вложенные сущности
        for nested_entity in nested_entities:
            self._collect_entity_snapshot_hierarchical(
                obj=nested_entity,
                action_type=action_type,
                entities_changes=entities_changes,
                processed_ids=processed_ids,
            )

    def _get_m2m_changes_summary(
        self,
        old_value: Any,
        new_value: list[Any] | tuple[Any] | set[Any],
    ) -> M2MChangeDict | FieldChangeDict | None:
        """Возвращает краткую информацию об изменениях в M2M коллекции.

        Args:
            old_value: старое значение
            new_value: новое значение

        Returns:
            Словарь с added/removed или old/new, либо None если изменений нет
        """
        old_items = set(old_value) if isinstance(old_value, (list, tuple, set)) else set()
        new_items = set(new_value)

        # Если элементы - BaseEntity
        if new_items and isinstance(next(iter(new_items), None), BaseEntity):
            old_ids = {item.id for item in old_items if isinstance(item, BaseEntity)}
            new_ids = {item.id for item in new_items if isinstance(item, BaseEntity)}

            added_ids = new_ids - old_ids
            removed_ids = old_ids - new_ids

            if added_ids or removed_ids:
                m2m_change: M2MChangeDict = {
                    "added": [str(id_) for id_ in added_ids],
                    "removed": [str(id_) for id_ in removed_ids],
                }
                return m2m_change
        else:  # noqa: PLR5501
            # Для простых типов
            if old_items != new_items:
                field_change: FieldChangeDict = {
                    "old": AuditLogValueSerializer.serialize(list(old_items)),
                    "new": AuditLogValueSerializer.serialize(list(new_items)),
                }
                return field_change

        return None
