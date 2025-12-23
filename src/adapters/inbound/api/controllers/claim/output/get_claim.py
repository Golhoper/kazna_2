import datetime as dt

from core.claims.domain.aggregates.claim.entities.payment_item.types import PaymentItemId
from core.claims.domain.aggregates.claim.types import ClaimId
from generic.api.pydantic_models import CamelCasedAliasesModel


class _PaymentItem(CamelCasedAliasesModel):
    id: PaymentItemId
    created_at: dt.datetime | None
    updated_at: dt.datetime | None


class ClaimDetailSchemaOut(CamelCasedAliasesModel):
    id: ClaimId
    system_number: str
    created_at: dt.datetime | None
    updated_at: dt.datetime | None
    is_deleted: bool
    deleted_at: dt.datetime | None
    payment_items: list[_PaymentItem]
