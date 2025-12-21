from typing import Self


class NonDomainExceptionError(Exception):
    """Ошибка при использовании не-доменного исключения в UoW."""

    @classmethod
    def raise_only_domain_error(cls) -> Self:
        """..."""
        return cls("Нужно вызывать только Domain Exception")
