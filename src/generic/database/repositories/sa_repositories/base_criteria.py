from __future__ import annotations

import abc
import copy
import uuid
from collections.abc import Callable, Sequence
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Self, TypeAlias, TypeVar

import sqlalchemy as sa
from sqlalchemy import BinaryExpression, Column, and_, not_, or_
from sqlalchemy.orm import MANYTOONE, ONETOMANY, DeclarativeBase, InstrumentedAttribute
from sqlalchemy.sql.elements import BooleanClauseList, ClauseElement
from sqlalchemy.sql.selectable import Select

from generic.database.utils.sa_utils.join import idempotent_join

TSaModel = TypeVar("TSaModel", bound=DeclarativeBase)

"""
    Что может понадобиться от Criteria:
    - входные параметры объекта Criteria не зависят от названия колонок в БД
    - возможность комбинировать фильтрацию по множеству полей (project=1 AND status="done")
    - сложные комбинации условий ((project=1 AND status="done") OR assignee=3)

    Мысли:
    - Один единый класс, фильтрующий целиком по всем нужным колонкам. Принимает на вход все нужные аргументы.
    Жестко завязан на конкретную логику фильтрации.
    - Списки атомарных классов, которые могут объединяться в комбинации для AND и OR.
    - А как делать сложные фильтры, включающие join, subquery и др.?

    Выводы:
    - отдельные классы для атомарных фильтров, которые часто либо используются отдельно,
     либо в простых комбинациях (типа AND).
    - классы для простого комбинирования атомарных фильтров. Думаю только `AndCombinedCriteria`, `OrCombinedCriteria`.
    - отдельные классы для каждого сложного случая, когда атомарных и combined не достаточно.
"""

TEntityId = uuid.UUID | str
_Number: TypeAlias = int | float | Decimal  # noqa: UP040


class BaseCriteria(abc.ABC):
    """Абстрактный класс для инкапсуляции фильтрации записей, отдаваемых репозиторием.
    Так как объекты наследников будут инициализироваться в слое domain, то нужно, чтобы:
     - все тонкости реализации были скрыты внутри реализации
     - все входные параметры были:
       -- либо простых типов,
       -- либо типов, объявленных в слое domain
       -- со значениями, допустимыми классами вроде Enum, определенных в слое Domain.
    """

    _is_negate = False

    @abc.abstractmethod
    def get_conditions(self) -> list[BooleanClauseList | ClauseElement]:
        """Метод должен возвращать список условий, которые будут применены к запросу."""
        raise NotImplementedError

    def get_result_conditions(self) -> list[BooleanClauseList | ClauseElement]:
        """Метод должен возвращать список условий, которые будут применены к запросу.
        Учитывает neq
        """
        conditions = self.get_conditions()
        if self._is_negate:
            return [not_(and_(*conditions))]
        return [and_(*conditions)]

    def filter(self, query: Select) -> Select:
        """Метод можно переопределять, если стандартного поведения недостаточно."""
        conditions = self.get_result_conditions()
        query = self._get_join_query(query)
        return query.where(*conditions)

    def _get_copy(self) -> Self:
        """Возвращает копию себя.

        Копия нужна для CombinedCriteria при реализации критерия через __call__
        для того, чтобы не перезатирались значения.
        """
        return copy.copy(self)

    def _get_join_query(self, query: Select) -> Select:
        """Запрос на join."""
        return query

    def neq(self) -> Self:
        """Вернет критерий для исключения."""
        cp = self._get_copy()
        cp._is_negate = True  # noqa: SLF001
        return cp


class BaseCombinedCriteria(BaseCriteria, abc.ABC):
    """Базовый класс для фильтрации, выполняющий фильтрацию только на основе других критериев,
    переданных как входные параметры.
    """

    def __init__(self, criteria: Sequence[BaseCriteria]) -> None:
        self._criteria = criteria

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}([{', '.join([repr(crit) for crit in self._criteria])}])"

    def get_conditions(self) -> list[BooleanClauseList | ClauseElement]:
        """Метод должен возвращать список условий, которые будут применены к запросу."""
        conditions = []
        for crit in self._criteria:
            conditions += crit.get_result_conditions()
        op = self._operator
        return [op(*conditions)]

    def filter(self, query: Select) -> Select:
        """Метод можно переопределять, если стандартного поведения недостаточно."""
        conditions = []
        for crit in self._criteria:
            conditions += crit.get_result_conditions()
            query = crit._get_join_query(query)  # noqa: SLF001
        op = self._operator
        return query.where(op(*conditions))

    @property
    @abc.abstractmethod
    def _operator(self) -> Callable[[Any], Any]:
        raise NotImplementedError

    def _get_join_query(self, query: Select) -> Select:
        """Запрос на join."""
        for crit in self._criteria:
            query = crit._get_join_query(query)  # noqa: SLF001
        return query


class AndCombinedCriteria(BaseCombinedCriteria):
    """Критерий фильтрации, выполняющий фильтрацию только на основе других критериев, переданных как входные параметры.
    Использует условие AND для объединения критериев.

    Пример использования:
    proj_crit = OfProjectCriteria(project_id=pid)
    done_status_crit = OfStatusCriteria(status="done")
    combined_crit = AndCombinedCriteria(criteria=[proj_crit, done_status_crit])
    """

    @property
    def _operator(self) -> Any:
        return and_


class OrCombinedCriteria(BaseCombinedCriteria):
    """Критерий фильтрации, выполняющий фильтрацию только на основе других критериев, переданных как входные параметры.
    Использует условие OR для объединения критериев.

    Пример использования:
    proj_crit = OfProjectCriteria(project_id=pid)
    done_status_crit = OfStatusCriteria(status="done")
    combined_crit = OrCombinedCriteria(criteria=[proj_crit, done_status_crit])
    """

    @property
    def _operator(self) -> Any:
        return or_


class SimpleSearchCriteria(BaseCriteria):
    """Параметризированный критерий для простого поиска"""

    def __init__(self, search_fields: list[str], model: type[TSaModel]) -> None:
        self.search_fields = search_fields
        self._model = model

    def __call__(self, value: str) -> Self:
        """Вызов."""
        self._value = value
        return self._get_copy()

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f'(model="{self._model}", search_fields="{self.search_fields}"), '
            f'value="{self._value}", is_negate="{self._is_negate}"'
        )

    def get_conditions(self) -> list[BooleanClauseList | ClauseElement]:
        """Условия поиска"""
        conditions = [getattr(self._model, field).ilike(f"%{self._value}%") for field in self.search_fields]
        return [or_(*conditions)]


class EntityByIdsCriteria(BaseCriteria):
    """Критерий сущности по id/ids."""

    class Method(Enum):
        """Методы поиска."""

        eq = "eq"
        neq = "neq"

    def __init__(self, model: type[TSaModel]) -> None:
        self._model = model
        self._method_call: EntityByIdsCriteria.Method | None = None
        self._value: TEntityId | list[TEntityId] | None = None

    def __repr__(self) -> str:
        return (
            f'{self.__class__.__name__}(model="{self._model}", value="{self._value}", is_negate="{self._is_negate}")'
        )

    def __call__(self, value: TEntityId | list[TEntityId]) -> Self:
        """Поиск по точному совпадению."""
        self._method_call = self.Method.eq
        self._value = value
        return self._get_copy()

    def neq(self, value: TEntityId | list[TEntityId]) -> Self:
        """Поиск по точному НЕсовпадению."""
        self._method_call = self.Method.neq
        self._value = value
        return self._get_copy()

    def get_conditions(self) -> list[BooleanClauseList | ClauseElement]:
        """Условие критерия."""
        if self._method_call == self.Method.neq:
            if isinstance(self._value, list):
                return [self._model.id.notin_(self._value)]
            return [self._model.id != self._value]

        if isinstance(self._value, list):
            return [self._model.id.in_(self._value)]
        return [self._model.id == self._value]


class FKCriteria(BaseCriteria):
    """Фабрика критериев для FK связей.

    Пример:
        cr_col = CriteriaCollection(
            by_organization_ids=FKCriteria(SaUser.organization_id)
        )
        criteria = cr_col.by_organization_ids(user_id)
    """

    class Method(Enum):
        """Методы поиска."""

        eq = "eq"
        neq = "neq"

    def __init__(self, fk_column: Column) -> None:
        """Инициализация фабрики критериев для FK связей."""
        self._fk_column = fk_column
        self._method_call: FKCriteria.Method = None  # type:ignore[assignment]
        self._value: TEntityId | list[TEntityId] = None  # type:ignore[assignment]

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f'(column="{self._fk_column}", method_call="{self._method_call.value}", '
            f'value="{self._value}", is_negate="{self._is_negate}")'
        )

    def __call__(self, value: TEntityId | list[TEntityId]) -> Self:
        """Поиск по точному совпадению."""
        self._method_call = self.Method.eq
        self._value = value
        return self._get_copy()

    def neq(self, value: TEntityId | list[TEntityId]) -> Self:
        """Поиск по точному НЕсовпадению."""
        self._method_call = self.Method.neq
        self._value = value
        return self._get_copy()

    def get_conditions(self) -> list[BooleanClauseList | ClauseElement]:
        """Условие критерия."""
        if self._method_call == self.Method.neq:
            if isinstance(self._value, list):
                return [self._fk_column.notin_(self._value)]
            return [self._fk_column != self._value]

        if isinstance(self._value, list):
            return [self._fk_column.in_(self._value)]
        return [self._fk_column == self._value]


class M2MCriteria(BaseCriteria):
    """Фабрика критериев для M2M связей.

    Пример:
        Необходимо создать критерий для поиска проектов по id пользователя.
        SaUser и SaProject связаны через промежуточную таблицу SaUserProject.

        cr_col = CriteriaCollection(
            by_user_id=M2MCriteria(
                target_model=SaProject,
                m2m_target_column=SaUserProject.project_id,
                m2m_search_column=SaUserProject.user_id,
            )
        )
        criteria = cr_col.by_user_id(user_id)
    """

    def __init__(
        self,
        target_model: type[TSaModel],
        m2m_target_column: Column,
        m2m_search_column: Column,
    ) -> None:
        """Инициализация фабрики критериев для M2M связей."""
        self._target_model = target_model
        self._m2m_target_column = m2m_target_column
        self._m2m_search_column = m2m_search_column
        self._value: TEntityId | list[TEntityId] = None  # type:ignore[assignment]

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f'(model="{self._target_model}", search_column="{self._m2m_search_column}", '
            f'value="{self._value}", is_negate="{self._is_negate}")'
        )

    def __call__(self, value: TEntityId | list[TEntityId]) -> Self:
        """Вызов."""
        self._value = value
        return self._get_copy()

    def get_conditions(self) -> list[BooleanClauseList | ClauseElement]:
        """Условие критерия."""
        if isinstance(self._value, list):
            return [
                sa.and_(
                    self._m2m_search_column.in_(self._value),
                    self._m2m_target_column == self._target_model.id,
                ),
            ]
        return [
            sa.and_(
                self._m2m_search_column == self._value,
                self._m2m_target_column == self._target_model.id,
            )
        ]

    def _get_join_query(self, query: Select) -> Select:
        """Запрос на join.

        Если не сделать, то по умолчанию будет crossjoin - неверное поведение фильтров если нету записей в m2m.
        """
        return query.outerjoin(self._m2m_target_column.class_)


class StrCriteria(BaseCriteria):
    """Фабрика критериев для str/Enum полей.

    Пример:
        cr_col = CriteriaCollection(
            by_name=StrCriteria(SaUser.first_name)
        )
        criteria = cr_col.by_name("Иван")
    """

    _method_call: StrCriteria.Method
    _value: str | list[str]

    class Method(Enum):
        """Методы поиска."""

        eq = "eq"
        ieq = "ieq"
        neq = "neq"
        ilike = "ilike"
        like = "like"

    def __init__(self, column: Column) -> None:
        """Инициализация фабрики критериев."""
        self._column = column
        # self._method_call: StrCriteria.Method = None  # type:ignore[assignment]
        # self._value: str | list[str] | Enum = None  # type:ignore[assignment]

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f'(column="{self._column}", method_call={self._method_call}, '
            f'value="{self._value}", is_negate="{self._is_negate}")'
        )

    def __call__(self, value: str | list[str]) -> Self:
        """Поиск по точному совпадению с учетом регистра."""
        self._method_call = self.Method.eq
        self._value = value
        return self._get_copy()

    def ieq(self, value: str) -> Self:
        """Поиск по точному совпадению без учета регистра."""
        self._method_call = self.Method.ieq
        self._value = value
        return self._get_copy()

    def neq(self, value: str) -> Self:
        """Поиск по точному НЕсовпадению с учетом регистра."""
        self._method_call = self.Method.neq
        self._value = value
        return self._get_copy()

    def ilike(self, value: str) -> Self:
        """Поиск по частичному совпадению без учета регистра."""
        self._method_call = self.Method.ilike
        self._value = value
        return self._get_copy()

    def like(self, value: str) -> Self:
        """Поиск по частичному совпадению с учетом регистра."""
        self._method_call = self.Method.like
        self._value = value
        return self._get_copy()

    def get_conditions(self) -> list[BooleanClauseList | ClauseElement]:
        """Условие критерия."""
        if self._method_call == self.Method.ieq:
            return [sa.func.lower(self._column) == self._value.lower()]  # type:ignore[union-attr]
        if self._method_call == self.Method.neq:
            return [self._column != self._value]
        if self._method_call == self.Method.ilike:
            return [sa.func.lower(self._column).ilike(f"%{self._value.lower()}%")]  # type:ignore[union-attr]
        if self._method_call == self.Method.like:
            return [self._column.like(f"%{self._value}%")]

        if isinstance(self._value, list):
            return [self._column.in_(self._value)]
        if isinstance(self._value, Enum):
            self._value = str(self._value)
        return [self._column == self._value]


class BoolCriteria(BaseCriteria):
    """Фабрика критериев для str полей.

    Пример:
        cr_col = CriteriaCollection(
            by_active=BoolCriteria(SaUser.active)
        )
        criteria = cr_col.by_active(True)
    """

    def __init__(self, column: Column) -> None:
        """Инициализация фабрики критериев."""
        self._column = column
        self._value: bool = None  # type:ignore[assignment]

    def __repr__(self) -> str:
        return (
            f'{self.__class__.__name__}(column="{self._column}", value="{self._value}", is_negate="{self._is_negate}")'
        )

    def __call__(self, value: bool) -> Self:
        """Вызов."""
        self._value = value
        return self._get_copy()

    def get_conditions(self) -> list[BooleanClauseList | ClauseElement]:
        """Условие критерия."""
        return [self._column.is_(self._value)]


def _equals(field: Column, value: Any) -> BinaryExpression:
    return field == value


def _not_equals(field: Column, value: Any) -> BinaryExpression:
    return field != value


def _gte(field: Column, value: Any) -> BinaryExpression:
    return field >= value


def _gt(field: Column, value: Any) -> BinaryExpression:
    return field > value


def _lte(field: Column, value: Any) -> BinaryExpression:
    return field <= value


def _lt(field: Column, value: Any) -> BinaryExpression:
    return field < value


class DatetimeCriteria(BaseCriteria):
    """Фабрика критериев для datetime полей."""

    def __init__(self, column: Column) -> None:
        """Инициализация фабрики критериев."""
        self._column = column
        self._method: Any | None = None
        self._value: datetime | None = None

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f'(column="{self._column}", method={self._method}, '
            f'value="{self._value}", is_negate="{self._is_negate}")'
        )

    def __call__(self, value: datetime) -> Self:
        """Вызов."""
        self._value = value
        return self._get_copy()

    def gte(self, value: datetime) -> Self:
        """Больше или равно."""
        self._method = _gte
        self._value = value
        return self._get_copy()

    def gt(self, value: datetime) -> Self:
        """Больше."""
        self._method = _gt
        self._value = value
        return self._get_copy()

    def lte(self, value: datetime) -> Self:
        """Меньше или равно."""
        self._method = _lte
        self._value = value
        return self._get_copy()

    def lt(self, value: datetime) -> Self:
        """Меньше."""
        self._method = _lt
        self._value = value
        return self._get_copy()

    def get_conditions(self) -> list[BooleanClauseList | ClauseElement]:
        """Условие критерия."""
        if self._method:
            return [self._method(self._column, self._value)]
        return [self._column == self._value]


class NumberCriteria(BaseCriteria):
    """Фабрика критериев для числовых полей."""

    _method: Any
    _value: Any

    def __init__(self, column: Column) -> None:
        """Инициализация фабрики критериев."""
        self._column = column
        # self. | None = None
        # self. | None = None

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f'(column="{self._column}", method={self._method}, value="{self._value}", is_negate="{self._is_negate}")'
        )

    def __call__(self, value: _Number | list[_Number]) -> Self:
        """Вызов."""
        self._method = _equals
        self._value = value
        return self._get_copy()

    def gte(self, value: _Number) -> Self:
        """Больше или равно."""
        self._method = _gte
        self._value = value
        return self._get_copy()

    def gt(self, value: _Number) -> Self:
        """Больше."""
        self._method = _gt
        self._value = value
        return self._get_copy()

    def lte(self, value: _Number) -> Self:
        """Меньше или равно."""
        self._method = _lte
        self._value = value
        return self._get_copy()

    def lt(self, value: _Number) -> Self:
        """Меньше."""
        self._method = _lt
        self._value = value
        return self._get_copy()

    def get_conditions(self) -> list[BooleanClauseList | ClauseElement]:
        """Условие критерия."""
        if isinstance(self._value, list):
            return [self._column.in_(self._value)]
        return [self._method(self._column, self._value)]


class RelationCriteria(BaseCriteria):
    """Фабрика критериев для связанных полей через relationship.

    Пример:
        # для модели SaUser
        cc = CriteriaCollection(
            by_companies_name=RelationCriteria(SaUser, "company.name")
            by_companies_roles_name=RelationCriteria(SaUser, "company.role.name")
        )
        criteria = cc.by_companies_name("Ромашка")
        criteria = cc.by_companies_roles_name("Контрагент")

        # для модели SaCompanyRole
        cc = CriteriaCollection(
            by_companies_name=RelationCriteria(SaCompanyRole, "companies.name")
            by_users_name=RelationCriteria(SaCompanyRole, "companies.users.name")
        )
        criteria = cc.by_companies_name("Ромашка")
        criteria = cc.by_users_name("Иван")
    """

    _method: BinaryExpression
    _method_call: RelationCriteria.Method

    class Method(Enum):
        """Методы поиска."""

        eq = "eq"
        ieq = "ieq"
        ilike = "ilike"
        like = "like"
        gt = "gt"
        gte = "gte"
        lt = "lt"
        lte = "lte"
        isnull = "isnull"

    def __init__(self, model: type[TSaModel], field_path: str) -> None:
        """Инициализация фабрики критериев.

        Args:
            model: искомая модель.
            field_path: Путь через точку к полю, по которому будет фильтрация.
        """
        column = None
        self._fk_columns: list[Column] = []
        self._models_to_join = []
        for field in field_path.split("."):
            if column:
                if column.prop.direction is ONETOMANY:
                    fk_column = getattr(column.prop.entity.class_, column.prop.back_populates)
                elif column.prop.direction is MANYTOONE:
                    fk_column = column
                else:
                    msg = f"Для MANYTOMANY не сделано: {column=} {field=}"
                    raise NotImplementedError(msg)

                self._fk_columns.append(fk_column)

            if isinstance(column, InstrumentedAttribute):
                _inner_model = column.comparator.entity.class_
                column = getattr(_inner_model, field)
                self._models_to_join.append(_inner_model)
            elif column is None:
                column = getattr(model, field)
                self._first_fk_column = column
            else:
                msg = f"Что-то пошло не так, почини меня: {column=} {field=}"
                raise ValueError(msg)

        self._model = model
        self._column = column
        # self. | None = None
        # self. = None
        self._value: TEntityId | str | Enum | _Number | None | list[TEntityId | str | _Number] = None
        self._with_non_related: bool = False

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f'(column="{self._column}", method_call="{self._method_call.value}", '
            f'value="{self._value}", is_negate="{self._is_negate}")'
        )

    def __call__(self, value: TEntityId | str | Enum | _Number | list[TEntityId | str | _Number]) -> Self:
        """Вызов."""
        self._method_call = self.Method.eq
        self._method = _equals
        self._value = value
        return self._get_copy()

    def ieq(self, value: str) -> Self:
        """Поиск по точному совпадению без учета регистра."""
        self._method_call = self.Method.ieq
        self._value = value
        return self._get_copy()

    def ilike(self, value: str) -> Self:
        """Поиск по частичному совпадению без учета регистра."""
        self._method_call = self.Method.ilike
        self._value = value
        return self._get_copy()

    def like(self, value: str) -> Self:
        """Поиск по частичному совпадению с учетом регистра."""
        self._method_call = self.Method.like
        self._value = value
        return self._get_copy()

    def gte(self, value: _Number) -> Self:
        """Больше или равно."""
        self._method_call = self.Method.gte
        self._method = _gte
        self._value = value
        return self._get_copy()

    def gt(self, value: _Number) -> Self:
        """Больше."""
        self._method_call = self.Method.gt
        self._method = _gt
        self._value = value
        return self._get_copy()

    def lte(self, value: _Number) -> Self:
        """Меньше или равно."""
        self._method_call = self.Method.lte
        self._method = _lte
        self._value = value
        return self._get_copy()

    def lt(self, value: _Number) -> Self:
        """Меньше."""
        self._method_call = self.Method.lt
        self._method = _lt
        self._value = value
        return self._get_copy()

    def isnull(self, value: bool = True) -> Self:
        """Возвращает критерий для проверки null."""
        self._method_call = self.Method.isnull
        self._method = _equals if value else _not_equals
        self._value = None
        return self._get_copy()

    def neq(self) -> Self:
        """Возвращает критерий для исключения."""
        self._with_non_related = True
        return super().neq()

    def _get_join_query(self, query: Select) -> Select:
        """Запрос на join."""
        if self._is_negate and self._first_fk_column.prop.direction is ONETOMANY:
            # джоиниться будет _subquery в get_conditions
            return query

        for model in self._models_to_join:
            query = idempotent_join(query, model, isouter=self._with_non_related)
        return query

    def get_conditions(self) -> list[BooleanClauseList | ClauseElement]:
        """Условие критерия."""
        conditions = self._prepare_conditions()
        if self._is_negate:
            conditions = [c.expression.right.is_not(None) for c in self._fk_columns] + conditions

            if self._first_fk_column.prop.direction is ONETOMANY:
                _subquery = sa.select(self._first_fk_column.expression.right).where(*conditions)
                for model in self._models_to_join[1:]:
                    _subquery = idempotent_join(_subquery, model)

                return [self._model.id.in_(_subquery)]

        return conditions

    def _prepare_conditions(self) -> list[BooleanClauseList | ClauseElement]:
        """Условие критерия."""
        if self._method_call == self.Method.ieq:
            return [sa.func.lower(self._column) == self._value.lower()]  # type:ignore[union-attr]
        if self._method_call == self.Method.ilike:
            return [sa.func.lower(self._column).ilike(f"%{self._value.lower()}%")]  # type:ignore[union-attr]
        if self._method_call == self.Method.like:
            return [self._column.like(f"%{self._value}%")]  # type:ignore[union-attr]

        if isinstance(self._value, list):
            return [self._column.in_(self._value)]  # type:ignore[union-attr]
        if isinstance(self._value, Enum):
            self._value = self._value.value
        return [self._method(self._column, self._value)]
