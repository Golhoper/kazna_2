import datetime as dt


def now() -> dt.datetime:
    """Возвращает текущее время."""
    return dt.datetime.now(dt.UTC)
