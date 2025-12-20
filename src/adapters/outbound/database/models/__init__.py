__all__ = [
    "MatcherMappingItemModel",
    "MatcherMappingItemReceiverModel",
    "MatcherMappingItemSourceModel",
    "MatcherMappingModel",
    "SaAbsence",
    "SaAct",
    "SaActFile",
    "SaActItem",
    "SaAdditionalSubstitute",
    "SaBPInstance",
    "SaClaim",
    "SaContractExtended",
    "SaContractExtendedItem",
    "SaDividedContractFilterList",
    "SaEntityAuditLog",
    "SaEventLog",
    "SaFileTypeExtended",
    "SaKADRCity",
    "SaKADROrganization",
    "SaKADRPosition",
    "SaKADRSubdivision",
    "SaKADRUser",
    "SaOrganizationExtended",
    "SaOutboxMessage",
    "SaPermission",
    "SaPermissionRestriction",
    "SaProductionCalendar",
    "SaReceiptDocument",
    "SaRole",
    "SaSystemConfig",
    "SaTask",
    "SaTaskContext",
    "SaTaskUserSettings",
    "SaUser",
    "act_system_number_seq",
]

# Импортируем модели из mdm_lib и регистрируем их таблицы в нашей metadata
# Модели Matcher
from matcher_integration.db.models import (
    Base as MatcherSaBase,
)
from matcher_integration.db.models import (
    MatcherMappingItemModel,
    MatcherMappingItemReceiverModel,
    MatcherMappingItemSourceModel,
    MatcherMappingModel,
)
from mdm_lib.adapters.outbound.database.base import SaBase as MdmSaBase
from mdm_lib.adapters.outbound.database.models import *

# Переносим таблицы из mdm_lib в нашу metadata для работы relationship'ов
from adapters.outbound.database.base import SaBase
from adapters.outbound.database.models.ac_contracts.contract import SaContractExtended, SaContractExtendedItem

# Импортируем схемные объекты для автоматической регистрации в метаданных
# Это обеспечивает, что Alembic увидит все последовательности, индексы и другие объекты
from adapters.outbound.database.models.acts.act import SaAct
from adapters.outbound.database.models.acts.act_file import SaActFile
from adapters.outbound.database.models.acts.act_item import SaActItem
from adapters.outbound.database.models.acts.receipt_document import SaReceiptDocument
from adapters.outbound.database.models.business_process.instance import SaBPInstance
from adapters.outbound.database.models.claims.claim import SaClaim
from adapters.outbound.database.models.config.system_config import SaSystemConfig
from adapters.outbound.database.models.entity_log.entity_log import SaEntityAuditLog
from adapters.outbound.database.models.event_log.event_log import SaEventLog

# Импортируем локальные KADR модели
from adapters.outbound.database.models.kadr import (
    SaKADRCity,
    SaKADROrganization,
    SaKADRPosition,
    SaKADRSubdivision,
    SaKADRUser,
)
from adapters.outbound.database.models.mdm.divided_contract import SaDividedContractFilterList
from adapters.outbound.database.models.mdm.organization import SaOrganizationExtended
from adapters.outbound.database.models.mdm.production_calendar import SaProductionCalendar
from adapters.outbound.database.models.mdm.type_file import SaFileTypeExtended
from adapters.outbound.database.models.outbox.outbox_message import SaOutboxMessage
from adapters.outbound.database.models.tasks.task import SaTask
from adapters.outbound.database.models.tasks.task_context import SaTaskContext
from adapters.outbound.database.models.tasks.task_user_settings import SaTaskUserSettings
from adapters.outbound.database.models.users.absences import SaAbsence
from adapters.outbound.database.models.users.additional_substitute import SaAdditionalSubstitute
from adapters.outbound.database.models.users.permission import SaPermission
from adapters.outbound.database.models.users.restriction import SaPermissionRestriction
from adapters.outbound.database.models.users.role import SaRole
from adapters.outbound.database.models.users.user import SaUser
from adapters.outbound.database.schema_objects import act_system_number_seq

# Временно закомментировано из-за проблем с настройками MDM
for table in MdmSaBase.metadata.tables.values():
    table.to_metadata(SaBase.metadata)

for table in MatcherSaBase.metadata.tables.values():
    table.to_metadata(SaBase.metadata)
