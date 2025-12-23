from typing import Annotated

from fastapi import APIRouter, Depends, Body, Path

from adapters.inbound.api.app.dependencies import get_uow_from_request
from adapters.inbound.api.controllers.claim.input.claim import ClaimCreateSchemaIn, ClaimUpdateSchemaIn
from adapters.inbound.api.controllers.claim.output.get_claim import ClaimDetailSchemaOut
from core.claims.domain.aggregates.claim.types import ClaimId
from core.shared_kernel.units_of_work.postgres import UnitOfWork
from core.claims.application.commands.claim import create, update
from query.claims.handlers import get


router = APIRouter(prefix="/claim", tags=["claim"])


@router.get(path="/{claim_id}", summary="Возвращает Заявку")
async def get_act_controller(
    claim_id: Annotated[ClaimId, Path()],
    uow: Annotated[UnitOfWork, Depends(get_uow_from_request)],
) -> ClaimDetailSchemaOut:
    async with uow:
        claim = await get.Handler(uow.session).execute(claim_id=claim_id)
        return ClaimDetailSchemaOut.model_validate(claim)


@router.post(path="", summary="Создает Заявку")
async def create_act_controller(
    body: Annotated[ClaimCreateSchemaIn, Body()],
    uow: Annotated[UnitOfWork, Depends(get_uow_from_request)]
) -> ClaimDetailSchemaOut:
    payload = create.Payload(system_number=body.system_number)
    created_claim = await create.Command(uow=uow).execute(payload)
    async with uow:
        claim = await get.Handler(uow.session).execute(claim_id=created_claim.id)
        return ClaimDetailSchemaOut.model_validate(claim)


@router.patch(path="/{claim_id}", summary="Обновляет Заявку")
async def update_act_controller(
    claim_id: Annotated[ClaimId, Path()],
    body: Annotated[ClaimUpdateSchemaIn, Body()],
    uow: Annotated[UnitOfWork, Depends(get_uow_from_request)],
) -> ClaimDetailSchemaOut:
    update_data = update.UpdateData(system_number=body.system_number)
    payload = update.Payload(claim_id=claim_id, update_data=update_data)
    updated_claim = await update.Command(uow=uow).execute(payload)
    async with uow:
        claim = await get.Handler(uow.session).execute(claim_id=updated_claim.id)
        return ClaimDetailSchemaOut.model_validate(claim)
