import uuid
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from adapters.outbound.database.base import SaBase
from sqlalchemy.dialects import postgresql
from core.claims.domain.aggregates.claim.types import ClaimId
from generic.database.mixins.created_updated import SaCreatedUpdatedMixin
from generic.database.mixins.soft_delete import SaSoftDeleteMixin
from adapters.outbound.database.models.claims.payment_items import SaPaymentItem


class SaClaim(SaSoftDeleteMixin, SaCreatedUpdatedMixin, SaBase):
    """Таблица `Заявки`."""

    __tablename__ = 'claim_claims'

    id: Mapped[ClaimId] = mapped_column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Data
    system_number: Mapped[str] = mapped_column(String(255))

    # Entities
    payment_items: Mapped[list[SaPaymentItem]] = relationship(
        back_populates="claim", cascade="all, delete-orphan"
    )
