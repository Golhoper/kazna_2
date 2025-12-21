"""Модуль для работы с audit log."""

from generic.database.audit_log.collector import AuditLogCollector
from generic.database.audit_log.enums import EntityAuditLogTypeEnum

__all__ = [
    "AuditLogCollector",
    "EntityAuditLogTypeEnum",
]
