from datetime import UTC, datetime

from sqlalchemy import Select, Table, Update, select, update


def archive(sa_model: Table) -> Update:
    """Возвращает `sqlalchemy.sql.Update` с данными для пометки на архивирование.

    Пример:
        # пометить на архивирование проект с id=55
        archive(Project).where(Project.id == 55)
    """
    return update(sa_model).values(is_archived=True, archived_at=datetime.now(UTC))


def not_archived_select(sa_model: Table) -> Select:
    """Возвращает `sqlalchemy.sql.Select` для работы только с непомеченными на архивирование записями в БД."""
    return select(sa_model).where(sa_model.is_archived.is_(False))


def archived_select(sa_model: Table) -> Select:
    """Возвращает `sqlalchemy.sql.Select` для работы только с помеченными на архивирование записями в БД."""
    return select(sa_model).where(sa_model.is_archived.is_(True))
