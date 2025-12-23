import uuid

from core.claims.domain.aggregates.claim.aggregate import Claim
from core.shared_kernel.units_of_work.postgres import UnitOfWork
from generic.api.pydantic_models import CamelCasedAliasesModel


class Payload(CamelCasedAliasesModel):
    system_number: str


class Command:
    """Команда создания Заявки."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, payload: Payload) -> Claim:
        async with self.uow:
            claim = Claim(
                id=uuid.uuid4(),
                system_number=payload.system_number,
            )
            await self.uow.claim_repository.upsert(claim)
            await self.uow.commit()
            return claim
