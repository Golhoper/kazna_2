from sqlalchemy.orm import Query
from sqlalchemy.sql import coercions, roles
from sqlalchemy.sql._typing import _JoinTargetArgument, _OnClauseArgument


def idempotent_join(
    query: Query,
    target: _JoinTargetArgument,
    onclause: _OnClauseArgument | None = None,
    *,
    isouter: bool = False,
    full: bool = False,
) -> Query:
    """Идемпотентная версия для Query.join.

    Пример использования:
        # Для чего? Следующий запрос упадет:
        query = select(SaMyCatModel.id)
        query = query.join(SaMyBoxModel)
        query = query.join(SaMyBoxModel)  # второй join той же модели приведет к падению

        with pytest.raises(
            ProgrammingError,
            match="<class 'asyncpg.exceptions.DuplicateAliasError'>: "
            'table name "my_boxes" specified more than once',
        ):
            await dbsession.execute(query)

        # используем кастомизированный join
        query = select(SaMyCatModel.id)
        query = idempotent_join(query, SaMyBoxModel)
        query = idempotent_join(query, SaMyBoxModel)
        await dbsession.execute(query)   # не падает
    """
    join_target = coercions.expect(roles.JoinTargetRole, target, apply_propagate_attrs=query, legacy=True)
    onclause_element = None if onclause is None else coercions.expect(roles.OnClauseRole, onclause, legacy=True)

    setup_entry = (
        join_target,
        onclause_element,
        None,
        {
            "isouter": isouter,
            "full": full,
        },
    )

    if setup_entry not in query._setup_joins:  # noqa: SLF001
        query._setup_joins += (setup_entry,)  # noqa: SLF001

        query.__dict__.pop("_last_joined_entity", None)

    return query
