from datetime import UTC, datetime

from sqlalchemy import Delete, Select, Table, Update, delete, select, update


def soft_delete(sa_model: Table) -> Update:
    """Возвращает `sqlalchemy.sql.Update` с данными для пометки на удаление.

    Пример:
        # пометить на удаление проект с id=55
        soft_delete(Project).where(Project.id == 55)
    """
    return update(sa_model).values(is_deleted=True, deleted_at=datetime.now(UTC))


def force_delete(sa_model: Table) -> Delete:
    """Возвращает `sqlalchemy.sql.Delete` для удаления записей в БД (минуя пометку на удаление)."""
    return delete(sa_model)


def undelete(sa_model: Table) -> Update:
    """Возвращает `sqlalchemy.sql.Update` с данными для снятия пометки на удаление.

    Пример:
        # снять пометку на удаление проект с id=55
        undelete(Project).where(Project.id == 55)
    """
    return update(sa_model).values(is_deleted=False, deleted_at=None)


def not_deleted_select(sa_model: Table) -> Select:
    """Возвращает `sqlalchemy.sql.Select` для работы только с непомеченными на удаление записями в БД."""
    return select(sa_model).where(sa_model.is_deleted.is_(False))


def deleted_select(sa_model: Table) -> Select:
    """Возвращает `sqlalchemy.sql.Select` для работы только с помеченными на удаление записями в БД."""
    return select(sa_model).where(sa_model.is_deleted.is_(True))
