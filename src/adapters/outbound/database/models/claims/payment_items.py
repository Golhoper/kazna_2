import uuid
import typing
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects import postgresql
from adapters.outbound.database.base import SaBase
from core.claims.domain.aggregates.claim.entities.payment_item.types import PaymentItemId
from core.claims.domain.aggregates.claim.types import ClaimId
from generic.database.mixins.created_updated import SaCreatedUpdatedMixin
from generic.database.mixins.soft_delete import SaSoftDeleteMixin


if typing.TYPE_CHECKING:
    from adapters.outbound.database.models.claims.claims import SaClaim


class SaPaymentItem(SaSoftDeleteMixin, SaCreatedUpdatedMixin, SaBase):
    """Таблица `Предмет оплаты`."""

    __tablename__ = "claim_payment_items"

    id: Mapped[PaymentItemId] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Relationships
    claim_id: Mapped[ClaimId] = mapped_column(ForeignKey("claim_claims.id"), index=True)
    claim: Mapped["SaClaim"] = relationship(back_populates="payment_items")
