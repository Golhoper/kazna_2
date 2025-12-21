import enum


class EntityAuditLogTypeEnum(enum.Enum):
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE = "CREATE"
