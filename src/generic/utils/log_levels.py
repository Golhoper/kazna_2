import enum


class LogLevel(str, enum.Enum):
    """Possible log levels."""

    DEBUG = "DEBUG"
    ERROR = "ERROR"
    FATAL = "FATAL"
    INFO = "INFO"
    NOTSET = "NOTSET"
    WARNING = "WARNING"
