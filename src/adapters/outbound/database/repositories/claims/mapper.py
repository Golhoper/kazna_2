from typing import Any

from adapters.outbound.database.models.claims.claims import SaClaim
from adapters.outbound.database.models.claims.payment_items import SaPaymentItem
from core.claims.domain.aggregates.claim.aggregate import Claim
from core.claims.domain.aggregates.claim.entities.payment_item.entity import PaymentItem
from generic.database.repositories.base_mapper import BaseMapper


class ClaimMapper(BaseMapper[Claim, SaClaim]):
    def orm_to_entity(self, orm: SaClaim, **_kwargs: Any) -> Claim:
        payment_items = [
            PaymentItem(
                id=payment_item.id,
                created_at=payment_item.created_at,
                updated_at=payment_item.updated_at,
            )
            for payment_item in orm.payment_items
        ]
        return Claim(
            id=orm.id,
            system_number=orm.system_number,
            payment_items=payment_items,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
            is_deleted=orm.is_deleted,
            deleted_at=orm.deleted_at,
        )

    def entity_to_orm(self, obj: Claim, **_kwargs: Any) -> SaClaim:
        payment_items = [
            SaPaymentItem(
                id=obj.id,
                created_at=payment_item.created_at,
                updated_at=payment_item.updated_at,
            )
            for payment_item in obj.payment_items
        ]
        return SaClaim(
            id=obj.id,
            system_number=obj.system_number,
            payment_items=payment_items,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            is_deleted=obj.is_deleted,
            deleted_at=obj.deleted_at,
        )