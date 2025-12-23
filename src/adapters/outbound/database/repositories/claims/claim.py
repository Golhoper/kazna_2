from adapters.outbound.database.models.claims.claims import SaClaim
from adapters.outbound.database.repositories.claims.mapper import ClaimMapper
from core.claims.domain.aggregates.claim.aggregate import Claim
from core.claims.domain.aggregates.claim.exceptions import ClaimNotFoundError
from generic.database.repositories.sa_repositories.base_repository import SaRepository


class ClaimRepository(SaRepository[Claim, SaClaim, ClaimMapper]):

    _model = SaClaim
    mapper = ClaimMapper(entity_cls=Claim, orm_model=SaClaim)
    not_found_exception = ClaimNotFoundError
