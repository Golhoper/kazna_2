import datetime as dt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from adapters.outbound.database.models.claims.claims import SaClaim
from core.claims.domain.aggregates.claim.aggregate import Claim
from core.claims.domain.aggregates.claim.entities.payment_item.types import PaymentItemId
from core.claims.domain.aggregates.claim.exceptions import ClaimNotFoundError
from core.claims.domain.aggregates.claim.types import ClaimId
from generic.api.pydantic_models import CamelCasedAliasesModel


class _PaymentItem(CamelCasedAliasesModel):
    id: PaymentItemId
    created_at: dt.datetime | None
    updated_at: dt.datetime | None


class ClaimDetailDTO(CamelCasedAliasesModel):
    id: ClaimId
    system_number: str
    created_at: dt.datetime | None
    updated_at: dt.datetime | None
    is_deleted: bool
    deleted_at: dt.datetime | None
    payment_items: list[_PaymentItem]


class Handler:
    """Данные об 1 `Заявке`."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def execute(self, claim_id: ClaimId) -> None:
        stmt = select(Claim).where(SaClaim.id == claim_id).options(joinedload(SaClaim.payment_items))
        cursor = await self.session.execute(stmt)
        orm = cursor.unique().scalar_one_or_none()
        if not orm:
            raise ClaimNotFoundError(id=claim_id)
        return ClaimDetailDTO.moel_validate(orm)
