import dataclasses
import uuid
from collections.abc import Iterable
from contextlib import suppress
from enum import Enum
from typing import Any, Generic, TypeAlias, TypeVar

import funcy
from sqlalchemy import Column, Select, UnaryExpression, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, RelationshipProperty, joinedload, load_only

from generic.database.audit_log import AuditLogCollector
from generic.database.repositories.base_mapper import BaseMapper, OrmFKMapping, TBaseMapper
from generic.database.repositories.sa_repositories.base_criteria import (
    AndCombinedCriteria,
    BaseCriteria,
    BoolCriteria,
    EntityByIdsCriteria,
    OrCombinedCriteria,
    SimpleSearchCriteria,
)
from generic.database.repositories.sa_repositories.exceptions import MultipleObjectsReturnedError
from generic.database.softdelete.queries import deleted_select, not_deleted_select
from generic.domain.bounded_events.context import bounded_events_collector_ctx
from generic.domain.bounded_events.events import EntityChangedDataEvent
from generic.domain.entity import BaseEntity, TEntity
from generic.domain.exceptions import NotFoundError
from generic.domain.mixins.archived import ArchivedMixin
from generic.domain.mixins.soft_delete import SoftDeleteMixin
from generic.domain.pagination import PageSizeIn
from generic.domain.schemas import IdNameSchema

TSaModel = TypeVar("TSaModel", bound=DeclarativeBase)
sentinel = object()


@dataclasses.dataclass(kw_only=True)
class BaseCriteriaCollection:
    """Базовый класс для критериев."""

    by_ids: EntityByIdsCriteria
    is_archived: BoolCriteria | None = dataclasses.field(default=None)
    simple_search: SimpleSearchCriteria | None = dataclasses.field(default=None)
    and_: type[AndCombinedCriteria] = dataclasses.field(default=AndCombinedCriteria)
    or_: type[OrCombinedCriteria] = dataclasses.field(default=OrCombinedCriteria)


# сортировка возможна и по нескольким полям, для этого нужно передать список ключей из SaRepository.sorting_map
TSortBy: TypeAlias = Enum | str | list[Enum | str] | None  # noqa: UP040
TSortByPrivate: TypeAlias = TSortBy | UnaryExpression | list[UnaryExpression]  # noqa: UP040
TSaModelId: TypeAlias = uuid.UUID | str  # noqa: UP040


class SaRepository(Generic[TEntity, TSaModel, TBaseMapper]):
    """Базовый класс репозитория для однотипных справочников"""

    _model: type[TSaModel] = NotImplemented
    mapper: BaseMapper[TEntity, TSaModel] = NotImplemented
    not_found_exception: type[NotFoundError] = NotImplemented
    is_read_only_repository: bool = False
    sorting_map: dict[Enum | str, UnaryExpression] = {}

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._audit_log_collector = AuditLogCollector()

    @classmethod
    def get_criteria(cls) -> BaseCriteriaCollection:
        """Возвращает коллекцию критериев."""
        return BaseCriteriaCollection(
            by_ids=EntityByIdsCriteria(model=cls._model),
            is_archived=BoolCriteria(cls._model.is_archived) if issubclass(cls._model, ArchivedMixin) else None,
            simple_search=SimpleSearchCriteria(
                search_fields=["name"],
                model=cls._model,
            ),
        )

    def _get_orm_model_by_tablename(self, tablename: str) -> type[TSaModel] | None | Any:
        """Находит ORM модель по __tablename__ через registry.

        Args:
            tablename: имя таблицы

        Returns:
            ORM модель или None если не найдена
        """
        # Получаем все классы из registry
        for mapper_instance in self._model.registry.mappers:
            orm_class = mapper_instance.class_
            if hasattr(orm_class, "__tablename__") and orm_class.__tablename__ == tablename:
                return orm_class
        return None

    def _get_tablename_for_entity(self, entity: TEntity) -> str | None:
        """Находит tablename для доменной сущности через registry.

        Args:
            entity: доменная сущность

        Returns:
            tablename или None если не найден
        """
        # Ищем ORM модель, которая может быть связана с этой сущностью
        # через проверку типов в mapper или через имя класса
        entity_class_name = entity.__class__.__name__

        # Проходим по всем зарегистрированным маппрам
        for mapper_instance in self._model.registry.mappers:
            orm_class = mapper_instance.class_

            # Проверяем есть ли у mapper связь с этим типом сущности
            if hasattr(orm_class, "__tablename__"):
                # Пытаемся найти по соглашению об именовании:
                # Pet -> SaPetModel, SaPet
                # Owner -> SaOwnerModel, SaOwner
                # MyEntity -> SaMyEntityModel, SaMyEntity
                possible_orm_names = [
                    f"Sa{entity_class_name}Model",
                    f"Sa{entity_class_name}",
                ]
                if orm_class.__name__ in possible_orm_names:
                    return orm_class.__tablename__  # type:ignore[no-any-return]

        return None

    def _collect_nested_entities(self, obj: TEntity, processed: set[int] | None = None) -> list[tuple[TEntity, str]]:
        """Рекурсивно собирает вложенные BaseEntity из коллекций.

        Args:
            obj: сущность для обработки
            processed: множество уже обработанных id объектов (для предотвращения циклов)

        Returns:
            Список кортежей (entity, tablename)
        """
        if processed is None:
            processed = set()

        # Защита от циклов
        obj_id = id(obj)
        if obj_id in processed:
            return []
        processed.add(obj_id)

        nested_entities: list[tuple[TEntity, str]] = []

        # Обходим все атрибуты сущности
        for attr_value in vars(obj).values():
            # Обрабатываем только коллекции (НЕ единичные FK)
            if isinstance(attr_value, (list, tuple, set)):
                for item in attr_value:
                    if isinstance(item, BaseEntity):
                        # Получаем tablename для этой сущности
                        tablename: str | None = self._get_tablename_for_entity(item)  # type:ignore[arg-type]
                        if not tablename:
                            # Не смогли найти tablename - пропускаем
                            continue

                        nested_entities.append((item, tablename))  # type:ignore[arg-type]

                        # Рекурсивно обрабатываем вложенные сущности
                        nested_entities.extend(self._collect_nested_entities(item, processed))  # type:ignore[arg-type]

        return nested_entities

    async def _check_entities_exist_in_db(
        self, entities: list[tuple[TEntity, str]]
    ) -> dict[tuple[uuid.UUID, str], bool]:
        """Проверяет существование сущностей в БД (batch-проверка).

        Args:
            entities: список кортежей (entity, tablename)

        Returns:
            Словарь {(entity_id, tablename): exists}
        """
        if not entities:
            return {}

        # Группируем сущности по tablename для batch-запросов
        entities_by_table: dict[str, list[uuid.UUID]] = {}
        for entity, tablename in entities:
            if tablename not in entities_by_table:
                entities_by_table[tablename] = []
            entities_by_table[tablename].append(entity.id)

        # Результаты проверки
        exists_map: dict[tuple[uuid.UUID, str], bool] = {}

        # Для каждой таблицы делаем один batch-запрос
        for tablename, entity_ids in entities_by_table.items():
            orm_model = self._get_orm_model_by_tablename(tablename)
            if orm_model is None:
                # Если не нашли модель, считаем что сущности не существуют
                for entity_id in entity_ids:
                    exists_map[(entity_id, tablename)] = False
                continue

            # Batch-запрос: SELECT id FROM table WHERE id IN (...)
            stmt = select(orm_model.id).where(orm_model.id.in_(entity_ids))
            result = await self._session.execute(stmt)
            existing_ids = {row[0] for row in result.all()}

            # Заполняем результаты
            for entity_id in entity_ids:
                exists_map[(entity_id, tablename)] = entity_id in existing_ids

        return exists_map

    async def create(self, obj: TEntity, **kwargs: Any) -> None:
        """Добавляет сущность TEntity в хранилище."""
        self._check_allowed_for_read_only_repository()
        created_data = self._get_data_for_audit_log_when_create(obj)
        event_collector = bounded_events_collector_ctx.get()
        event = EntityChangedDataEvent(entity_id=obj.id, entity_type=self._model.__tablename__, changes=created_data)
        event_collector.put_event(event)  # type:ignore[union-attr]
        sa_obj = self.mapper.entity_to_orm(obj, **kwargs)
        self._session.add(sa_obj)

    async def upsert(self, obj: TEntity, **kwargs: Any) -> None:
        """Добавляет или изменяет сущность TEntity в хранилище.

        Автоматически отслеживает создание вложенных BaseEntity в коллекциях.
        """
        self._check_allowed_for_read_only_repository()
        event_collector = bounded_events_collector_ctx.get()

        # 1. Получаем данные для audit log основной сущности
        updated_data = self._get_data_for_audit_log_when_update(obj)

        # 2. Собираем все вложенные BaseEntity из коллекций
        nested_entities = self._collect_nested_entities(obj)

        # 3. Проверяем существование вложенных сущностей в БД (batch)
        if nested_entities:
            exists_map = await self._check_entities_exist_in_db(nested_entities)

            # 4. Для новых сущностей добавляем их данные в changes
            for nested_entity, tablename in nested_entities:
                entity_key = (nested_entity.id, tablename)
                if not exists_map.get(entity_key, False):
                    # Сущность не существует - это создание
                    # Добавляем данные о созданной сущности в changes основного события
                    created_data = self._audit_log_collector.collect_create_data(nested_entity)
                    # Объединяем данные: берем все поля кроме root_entity и created_at
                    for key, value in created_data.items():
                        if key not in ("root_entity", "created_at"):
                            updated_data[key] = value

        # 5. Создаем одно событие со всеми изменениями
        event = EntityChangedDataEvent(entity_id=obj.id, entity_type=self._model.__tablename__, changes=updated_data)
        event_collector.put_event(event)  # type:ignore[union-attr]
        sa_obj = self.mapper.entity_to_orm(obj, **kwargs)
        await self._session.merge(sa_obj)

    async def bulk_create(self, entities: Iterable[TEntity], **kwargs: Any) -> None:
        """Добавляет сущности в хранилище."""
        self._check_allowed_for_read_only_repository()
        sa_objs = []
        for entity in entities:
            sa_obj = self.mapper.entity_to_orm(entity, **kwargs)
            created_data = self._get_data_for_audit_log_when_create(entity)
            event_collector = bounded_events_collector_ctx.get()
            event = EntityChangedDataEvent(
                entity_id=entity.id,
                entity_type=self._model.__tablename__,
                changes=created_data,
            )
            event_collector.put_event(event)  # type:ignore[union-attr]
            sa_objs.append(sa_obj)
        self._session.add_all(sa_objs)

    async def update(self, obj: TEntity) -> None:
        """Обновляет все атрибуты сущности в хранилище."""
        self._check_allowed_for_read_only_repository()
        updated_data = self._get_data_for_audit_log_when_update(obj)
        event_collector = bounded_events_collector_ctx.get()
        event = EntityChangedDataEvent(entity_id=obj.id, entity_type=self._model.__tablename__, changes=updated_data)
        event_collector.put_event(event)  # type:ignore[union-attr]
        if data := self._get_data_for_update(obj):
            await self._session.execute(
                update(self._model).where(self._model.id == obj.id).values(data),
            )

    def _get_data_for_update(self, obj: TEntity) -> dict[str, Any]:
        """Возвращает данные для обновления сущности."""
        data = {}
        for entity_attr, value in obj.changed_values.items():
            if isinstance(value, Enum):
                value = value.value  # noqa: PLW2901
            if orm_attr := self.mapper.extra_orm_by_entity_fields.get(entity_attr):
                if isinstance(orm_attr, OrmFKMapping):
                    orm_attr = orm_attr.name
                    value = getattr(value, "id", None)  # noqa: PLW2901

                data[orm_attr] = value
            elif hasattr(self._model, entity_attr):
                data[entity_attr] = value
        return data

    def _get_data_for_audit_log_when_update(self, obj: TEntity) -> dict[str, Any]:
        """Возвращает данные об изменениях сущности и всех вложенных сущностей для audit log.

        Args:
            obj: сущность с изменениями

        Returns:
            Словарь с данными об изменениях
        """
        return self._audit_log_collector.collect_update_data(obj)

    def _get_data_for_audit_log_when_delete(self, obj: TEntity) -> dict[str, Any]:
        """Возвращает данные о сущности для audit log при удалении.

        Args:
            obj: сущность для удаления

        Returns:
            Словарь с данными сущности
        """
        return self._audit_log_collector.collect_delete_data(obj)

    def _get_data_for_audit_log_when_create(self, obj: TEntity) -> dict[str, Any]:
        """Возвращает данные о сущности для audit log при создании.

        Args:
            obj: созданная сущность

        Returns:
            Словарь с данными сущности
        """
        return self._audit_log_collector.collect_create_data(obj)

    async def get_by_id(
        self,
        id_: uuid.UUID | str,
        lock: bool = False,
        deleted: bool | None = False,
        **kwargs: Any,
    ) -> TEntity:
        """Возвращает сущность по ее id.

        Args:
            id_: id сущности
            lock: блокировать ли строку в БД для записи
            deleted: фильтр по удаленным - True, без удаленных - False, все - None
            kwargs: прочие аргументы, которые нужно прокинуть в маппер
        """
        query = self._base_query(
            deleted=deleted,
            lock=lock,
        ).where(self._model.id == id_)

        result = await self._session.execute(query)
        obj = result.unique().scalar_one_or_none()
        if not obj:
            raise self.not_found_exception(id_)
        return self.mapper.orm_to_entity(obj, **kwargs)

    async def get_by_id_or_none(
        self,
        id_: uuid.UUID | str,
        lock: bool = False,
        deleted: bool | None = False,
        **kwargs: Any,
    ) -> TEntity | None:
        """Возвращает сущность по ее id.

        Args:
            id_: id сущности
            lock: блокировать ли строку в БД для записи
            deleted: фильтр по удаленным - True, без удаленных - False, все - None
            kwargs: прочие аргументы, которые нужно прокинуть в маппер
        """
        with suppress(self.not_found_exception):
            return await self.get_by_id(id_, lock=lock, deleted=deleted, **kwargs)
        return None

    async def first(
        self,
        criteria: BaseCriteria | list[BaseCriteria] | None = None,
        *,
        sort_by: TSortBy = None,
        deleted: bool | None = False,
        **kwargs: Any,
    ) -> TEntity | None | Any:
        """Возвращает первую сущность отвечающих критериям или None, если таких нет.

        Args:
            criteria: критерий поиска. Если передан список, то будет использован AndCombinedCriteria.
            deleted: фильтр по удаленным - True, без удаленных - False, все - None
            sort_by: параметры сортировки
            kwargs: прочие аргументы, которые нужно прокинуть в маппер

        """
        res = await self.filter(criteria=criteria, deleted=deleted, sort_by=sort_by, **kwargs)
        return funcy.first(res)

    async def get(
        self,
        criteria: BaseCriteria | list[BaseCriteria] | None,
        *,
        deleted: bool | None = False,
        **kwargs: Any,
    ) -> TEntity | Any:
        """Возвращает одну сущность отвечающих критериям, в случае если сущностей несколько вызывается исключение,
         если ни одной то исключение not found.

        Args:
            criteria: критерий поиска. Если передан список, то будет использован AndCombinedCriteria.
            deleted: фильтр по удаленным - True, без удаленных - False, все - None
            kwargs: прочие аргументы, которые нужно прокинуть в маппер
        """
        res = await self.filter(criteria=criteria, deleted=deleted, **kwargs)
        if not res:
            raise self.not_found_exception(None)
        if len(res) > 1:
            msg = "Вернулось больше одного элемента"
            raise MultipleObjectsReturnedError(msg, tech_details={"result": res})
        return funcy.first(res)

    async def filter(
        self,
        criteria: BaseCriteria | list[BaseCriteria] | None,
        *,
        page: PageSizeIn | None = None,
        sort_by: TSortBy = None,
        deleted: bool | None = False,
        **kwargs: Any,
    ) -> list[TEntity]:
        """Возвращает множество сущностей, отвечающих критериям.

        Args:
            criteria: критерий поиска. Если передан список, то будет использован AndCombinedCriteria.
            page: параметры пагинации
            sort_by: параметры сортировки
            deleted: фильтр по удаленным - True, без удаленных - False, все - None
            kwargs: прочие аргументы, которые нужно прокинуть в маппер
        """
        query = self._base_query(
            criteria=criteria,
            page=page,
            deleted=deleted,
            sort_by=sort_by,
        )

        result = await self._session.execute(query)
        return [self.mapper.orm_to_entity(row, **kwargs) for row in result.unique().scalars().all()]

    async def all(
        self,
        *,
        page: PageSizeIn | None = None,
        sort_by: TSortBy = None,
        deleted: bool | None = False,
        **kwargs: Any,
    ) -> list[TEntity]:
        """Возвращает все сущности.

        Args:
            page: параметры пагинации
            sort_by: параметры сортировки
            deleted: фильтр по удаленным - True, без удаленных - False, все - None
            kwargs: прочие аргументы, которые нужно прокинуть в маппер
        """
        return await self.filter(
            criteria=None,
            page=page,
            sort_by=sort_by,
            deleted=deleted,
            **kwargs,
        )

    async def count(
        self,
        *,
        criteria: BaseCriteria | list[BaseCriteria] | None = None,
        deleted: bool | None = False,
    ) -> int:
        """Кол-во записей соответствующих критерию.

        Args:
            criteria: критерий поиска. Если передан список, то будет использован AndCombinedCriteria.
            deleted: фильтр по удаленным - True, без удаленных - False, все - None
        """
        query = self._base_query(
            criteria=criteria,
            deleted=deleted,
        )
        subquery = query.with_only_columns(self._model.id.distinct()).order_by(None)
        query = select(func.count()).select_from(subquery)
        result = await self._session.execute(query)
        count_result = result.scalar()
        return count_result or 0

    async def exists(self, criteria: BaseCriteria | list[BaseCriteria], deleted: bool | None = False) -> bool:
        """Возвращает флаг: есть ли сущность в бд.

        Args:
            criteria: критерий поиска. Если передан список, то будет использован AndCombinedCriteria.
            deleted: фильтр по удаленным - True, без удаленных - False, все - None
        """
        query = self._base_query(
            criteria=criteria,
            deleted=deleted,
            only_columns=(self._model.id,),
        )
        query = select(self._model.id).where(query.exists())
        result = await self._session.execute(query)
        return bool(result.scalar())

    async def get_ids(
        self,
        *,
        criteria: BaseCriteria | list[BaseCriteria] | None = None,
        sort_by: TSortBy = None,
        deleted: bool | None = False,
    ) -> list[uuid.UUID | str]:
        """Возвращает список id сущностей, отвечающих критериям.

        Args:
            criteria: критерий поиска. Если передан список, то будет использован AndCombinedCriteria.
            sort_by: параметры сортировки
            deleted: фильтр по удаленным - True, без удаленных - False, все - None
        """
        query = self._base_query(
            criteria=criteria,
            deleted=deleted,
            sort_by=sort_by,
            only_columns=(self._model.id,),
        )
        result = await self._session.execute(query)
        return list(result.unique().scalars().all())

    async def get_id_names(
        self,
        *,
        criteria: BaseCriteria | list[BaseCriteria] | None = None,
        page: PageSizeIn | None = None,
        sort_by: TSortBy = None,
        deleted: bool | None = False,
    ) -> list[IdNameSchema]:
        """Возвращает список id и name сущностей, отвечающих критериям.

        Args:
            criteria: критерий поиска. Если передан список, то будет использован AndCombinedCriteria.
            page: параметры пагинации
            sort_by: параметры сортировки
            deleted: фильтр по удаленным - True, без удаленных - False, все - None
        """
        query = self._base_query(
            criteria=criteria,
            page=page,
            deleted=deleted,
            sort_by=sort_by,
            only_columns=(
                self._model.id,
                self._model.name,
            ),
        )

        result = await self._session.execute(query)
        return [IdNameSchema(id=row.id, name=row.name) for row in result.unique().all()]

    async def get_suggest(
        self,
        *,
        criteria: BaseCriteria | list[BaseCriteria] | None = None,
        page: PageSizeIn | None = None,
        deleted: bool | None = False,
    ) -> list[IdNameSchema]:
        """Получение списка id и name сущностей для suggest.

        Отличается от self.get_id_names() предустановленной сортировкой по имени.
        """
        return await self.get_id_names(
            criteria=criteria,
            page=page,
            sort_by=self._model.name.asc(),
            deleted=deleted,
        )

    def _get_join_query(self, query: Select) -> Select:
        """Запрос на join может включать в себя все FK связи на требуемую глубину.

        Не содержит M2M связи.
        """
        options = self._get_options_for_load_only(self.mapper)
        return query.options(*options)

    def _get_options_for_load_only(self, mapper: BaseMapper[TEntity, TSaModel]) -> list[Any]:
        """Возвращает список опций для `query.options()`, исходя из маппера, а именно:

        1. достает из бд только те колонки, которые объявлены в Entity.init (не загружая остальные)
        2. автоматически подставляет joinedload для FK полей, при этом также работает п.1

        Пример:
            class MyCompanyLite:
                id: UUID
                name: str

            class MyUserLite:
                id: UUID
                company: MyCompanyLite

            Тогда `result` будет выглядеть следующим образом:
                result = [
                    load_only(SaUser.id),
                    joinedload(SaUser.company).options(
                        load_only(SaCompanyLite.id, SaCompanyLite.name)
                    )
                ]
                query.options(*result)

            Тогда sql:
                SELECT users.id, users.organization_id, companies.id AS id_1, companies.name AS name_1
                FROM users LEFT OUTER JOIN companies ON companies.id = users.organization_id
        """
        columns_load = []
        columns_joinedload = []
        for f in mapper.orm_by_entity_fields.values():
            if isinstance(f, str) and hasattr(mapper.orm_model, f):
                attr = getattr(mapper.orm_model, f)
                # Исключаем relationship поля из load_only
                if hasattr(attr, "property") and isinstance(attr.property, RelationshipProperty):
                    columns_joinedload.append(attr)
                else:
                    columns_load.append(attr)

        options = [load_only(*columns_load, raiseload=True)] if columns_load else []
        options.extend([joinedload(column) for column in columns_joinedload])

        for relation_column, _mapper in mapper.mappers_by_relations.items():
            nested_options = self._get_options_for_load_only(_mapper)
            options.append(joinedload(relation_column).options(*nested_options))
        return options

    def _base_query(
        self,
        *,
        criteria: BaseCriteria | list[BaseCriteria] | None = None,
        page: PageSizeIn | None = None,
        sort_by: TSortByPrivate = None,
        only_columns: Iterable[Column] | None = None,
        deleted: bool | None = False,
        lock: bool = False,
    ) -> Select:
        """Базовый запрос.

        Args:
            criteria: критерий поиска. Если передан список, то будет использован AndCombinedCriteria.
            page: параметры пагинации
            sort_by: параметры сортировки
            only_columns: список колонок, которые нужно вернуть из бд
            deleted: фильтр по удаленным - True, без удаленных - False, все - None
            lock: блокировать ли строку в БД для записи
        """
        if self._is_soft_delete_model and deleted is False:
            query = not_deleted_select(self._model)
        elif self._is_soft_delete_model and deleted is True:
            query = deleted_select(self._model)
        else:
            query = select(self._model)
        query = self._get_join_query(query)

        if criteria:
            if isinstance(criteria, list):
                criteria = self.get_criteria().and_(criteria)
            query = criteria.filter(query)
        if only_columns:
            query = query.with_only_columns(*only_columns)
        if lock:
            query = query.with_for_update(of=self._model)
        if page:
            offset = (page.page - 1) * page.size
            query = query.limit(page.size).offset(offset)

        return self._sort(query=query, sort_by=sort_by)

    def _sort(self, *, query: Select, sort_by: TSortByPrivate) -> Select:
        """Сортировка."""
        if sort_by is None:
            return query

        if not isinstance(sort_by, list):
            sort_by = [sort_by]
        if isinstance(sort_by[0], UnaryExpression):
            order_by = sort_by
        else:
            order_by = []
            for sort in sort_by:
                expr = self.sorting_map[sort]
                if isinstance(expr, (list, tuple)):
                    order_by.extend(expr)
                else:
                    order_by.append(expr)
        return query.order_by(*order_by)

    @property
    def _is_soft_delete_model(self) -> bool:
        """Возвращает True, если модель является SoftDeleteMixin."""
        return issubclass(self._model, SoftDeleteMixin)

    @property
    def _is_archived_model(self) -> bool:
        """Возвращает True, если модель является ArchivedMixin."""
        return issubclass(self._model, ArchivedMixin)

    def _check_allowed_for_read_only_repository(self) -> None:
        """Вызывает исключение, если метод не разрешен для вызова в репозитории предназначенном только для чтения."""
        if self.is_read_only_repository:
            msg = f"{self.__class__} is read only repository"
            raise NotImplementedError(msg)
