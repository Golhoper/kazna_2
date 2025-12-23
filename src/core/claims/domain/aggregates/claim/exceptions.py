from generic.domain.exceptions import EntityFieldError, NotFoundError

CLAIM_ENTITY = "Claim"


class ClaimException(EntityFieldError):
    entity = CLAIM_ENTITY



class ClaimNotFoundError(NotFoundError):
    entity = CLAIM_ENTITY