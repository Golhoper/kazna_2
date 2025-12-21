from generic.domain.exceptions import DomainError


class MultipleObjectsReturnedError(DomainError):
    """Исключение в случае, если запрос вернул несколько записи."""
