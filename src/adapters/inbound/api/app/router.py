from fastapi import APIRouter

from adapters.inbound.api.controllers.claim import router as claim_router


api_router = APIRouter()
api_router.include_router(claim_router.router)
