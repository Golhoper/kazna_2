from core.claims.domain.aggregates.claim.aggregate import Claim
from core.shared_kernel.units_of_work.postgres import UnitOfWork
from generic.api.pydantic_models import CamelCasedAliasesModel


class UpdateData(CamelCasedAliasesModel):
    system_number: str


class Payload(CamelCasedAliasesModel):
    claim_id: str
    update_data: UpdateData


class Command:
    """Команда обновления `Заявки`."""

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def execute(self, payload: Payload) -> Claim:
        async with self.uow:
            claim = await self.uow.claim_repository.get_by_id(payload.claim_id)
            claim.update(payload.update_data)
            await self.uow.claim_repository.upsert(claim)
            await self.uow.commit()
            return claim
