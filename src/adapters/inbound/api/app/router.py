from fastapi import APIRouter, Depends

from adapters.inbound.api.app.middlewares.oauth2 import get_current_user
from adapters.inbound.api.controllers.absences.router import router as absences_router
from adapters.inbound.api.controllers.acts.router import router as act_router
from adapters.inbound.api.controllers.entity_changes.router import router as entity_changes_router
from adapters.inbound.api.controllers.event_log.router import router as event_log_router
from adapters.inbound.api.controllers.healthcheck.router import router as healthcheck_router
from adapters.inbound.api.controllers.integration.v1.router import router as integration_v1
from adapters.inbound.api.controllers.maintenance.router import router as maintenance_router
from adapters.inbound.api.controllers.mdm_handbooks.bdr_articles.router import router as mdm_bdr_article_router
from adapters.inbound.api.controllers.mdm_handbooks.construction_objects.router import (
    router as mdm_construction_object_router,
)
from adapters.inbound.api.controllers.mdm_handbooks.cost_centers.router import router as mdm_cost_center_router
from adapters.inbound.api.controllers.mdm_handbooks.counterparties.router import router as mdm_counterparty_router
from adapters.inbound.api.controllers.mdm_handbooks.divided_contracts.router import (
    router as mdm_divided_contract_router,
)
from adapters.inbound.api.controllers.mdm_handbooks.file_types.router import router as mdm_file_type_router
from adapters.inbound.api.controllers.mdm_handbooks.financial_responsibility_centers.router import (
    router as mdm_financial_responsibility_center_router,
)
from adapters.inbound.api.controllers.mdm_handbooks.internal_document_types.router import (
    router as mdm_internal_document_type_router,
)
from adapters.inbound.api.controllers.mdm_handbooks.nomenclatures.router import router as mdm_nomenclature_router
from adapters.inbound.api.controllers.mdm_handbooks.organizations.router import router as mdm_organization_router
from adapters.inbound.api.controllers.mdm_handbooks.production_calendar.router import (
    router as mdm_production_calendar_router,
)
from adapters.inbound.api.controllers.mdm_handbooks.project.router import router as mdm_construction_project_router
from adapters.inbound.api.controllers.mdm_handbooks.regions.router import router as mdm_region_router
from adapters.inbound.api.controllers.mdm_handbooks.unit_measures.router import router as mdm_unit_measure_router
from adapters.inbound.api.controllers.queue_status.router import router as queue_status_router
from adapters.inbound.api.controllers.suggests.router import router as suggests_router
from adapters.inbound.api.controllers.tasks.router import task_router
from adapters.inbound.api.controllers.users.router import router as user_router

api_router = APIRouter()
api_router.include_router(healthcheck_router, tags=["health"], prefix="/health")
api_router.include_router(act_router, tags=["act"], prefix="/act", dependencies=[Depends(get_current_user)])
api_router.include_router(maintenance_router, tags=["maintenance"], prefix="/maintenance")
api_router.include_router(
    mdm_bdr_article_router,
    tags=["mdm_handbook"],
    prefix="/mdm_handbook/bdr_article",
    dependencies=[Depends(get_current_user)],
)
api_router.include_router(
    mdm_counterparty_router,
    tags=["mdm_handbook"],
    prefix="/mdm_handbook/counterparty",
    dependencies=[Depends(get_current_user)],
)
api_router.include_router(
    mdm_cost_center_router,
    tags=["mdm_handbook"],
    prefix="/mdm_handbook/cost_center",
    dependencies=[Depends(get_current_user)],
)
api_router.include_router(
    mdm_financial_responsibility_center_router,
    tags=["mdm_handbook"],
    prefix="/mdm_handbook/financial_responsibility_center",
    dependencies=[Depends(get_current_user)],
)
api_router.include_router(
    mdm_divided_contract_router,
    tags=["mdm_handbook"],
    prefix="/mdm_handbook/divided_contract",
    dependencies=[Depends(get_current_user)],
)
api_router.include_router(
    mdm_internal_document_type_router,
    tags=["mdm_handbook"],
    prefix="/mdm_handbook/internal_document_type",
    dependencies=[Depends(get_current_user)],
)
api_router.include_router(
    mdm_nomenclature_router,
    tags=["mdm_handbook"],
    prefix="/mdm_handbook/nomenclature",
    dependencies=[Depends(get_current_user)],
)
api_router.include_router(
    mdm_organization_router,
    tags=["mdm_handbook"],
    prefix="/mdm_handbook/organization",
    dependencies=[Depends(get_current_user)],
)
api_router.include_router(
    mdm_construction_project_router,
    tags=["mdm_handbook"],
    prefix="/mdm_handbook/construction_project",
    dependencies=[Depends(get_current_user)],
)
api_router.include_router(
    mdm_region_router, tags=["mdm_handbook"], prefix="/mdm_handbook/region", dependencies=[Depends(get_current_user)]
)
api_router.include_router(
    mdm_construction_object_router,
    tags=["mdm_handbook"],
    prefix="/mdm_handbook/construction_object",
    dependencies=[Depends(get_current_user)],
)
api_router.include_router(
    mdm_unit_measure_router,
    tags=["mdm_handbook"],
    prefix="/mdm_handbook/unit_measure",
    dependencies=[Depends(get_current_user)],
)
api_router.include_router(
    mdm_file_type_router,
    tags=["mdm_handbook"],
    prefix="/mdm_handbook/file_type",
    dependencies=[Depends(get_current_user)],
)
api_router.include_router(
    mdm_production_calendar_router,
    tags=["mdm_handbook"],
    prefix="/mdm_handbook/production_calendar",
    dependencies=[Depends(get_current_user)],
)
api_router.include_router(user_router, tags=["user"], prefix="/user", dependencies=[Depends(get_current_user)])
api_router.include_router(
    absences_router, tags=["absences"], prefix="/absences", dependencies=[Depends(get_current_user)]
)
api_router.include_router(
    queue_status_router, tags=["queue"], prefix="/queue", dependencies=[Depends(get_current_user)]
)
api_router.include_router(
    suggests_router, tags=["suggests"], prefix="/suggests", dependencies=[Depends(get_current_user)]
)
api_router.include_router(task_router, tags=["task"], prefix="/task", dependencies=[Depends(get_current_user)])
api_router.include_router(event_log_router, dependencies=[Depends(get_current_user)])
api_router.include_router(entity_changes_router, dependencies=[Depends(get_current_user)])
api_router.include_router(
    integration_v1, tags=["integration"], prefix="/integration/v1", dependencies=[Depends(get_current_user)]
)
