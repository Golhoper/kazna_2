from generic.domain.exceptions import (
    DomainError,
    EntityFieldError,
    ExternalServiceError,
    FieldErrorDetail,
    NotFoundError,
    PermissionAccessError,
)
from generic.utils.log_levels import LogLevel
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from loguru import logger
from pydantic import ValidationError
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


def _log_domain_exception(exc: DomainError) -> None:
    """Логирование исключений домена."""
    try:
        method_name = exc.log_level.value.lower()
        log_func = getattr(logger, method_name)
    except AttributeError:
        logger.exception("Wrong log_level in exc")
        log_func = logger.error

    log_func(exc.as_dict(include_tech_details=True))


def _handle_not_found_error(request: Request, exc: NotFoundError) -> Response:  # noqa: ARG001
    _log_domain_exception(exc)
    return JSONResponse(exc.as_dict(), status_code=status.HTTP_404_NOT_FOUND)


def _handle_entity_field_error(request: Request, exc: EntityFieldError) -> Response:  # noqa: ARG001
    _log_domain_exception(exc)
    return JSONResponse(exc.as_dict(), status_code=status.HTTP_400_BAD_REQUEST)


def _handle_domain_error(request: Request, exc: DomainError) -> Response:  # noqa: ARG001
    _log_domain_exception(exc)
    return JSONResponse(exc.as_dict(), status_code=status.HTTP_400_BAD_REQUEST)


def _handle_permission_access_error(request: Request, exc: PermissionAccessError) -> Response:  # noqa: ARG001
    """Обработчик ошибок доступа."""
    _log_domain_exception(exc)
    return JSONResponse(exc.as_dict(), status_code=status.HTTP_403_FORBIDDEN)


def _handle_external_service_error(request: Request, exc: ExternalServiceError) -> Response:  # noqa: ARG001
    """Обработчик ошибок внешних сервисов.

    Возвращает ошибку с сохранением структуры от внешнего сервиса
    и подходящим HTTP-кодом.
    """
    _log_domain_exception(exc)

    # Определяем HTTP код на основе external_code от внешнего сервиса
    if isinstance(exc.external_code, int):
        if status.HTTP_400_BAD_REQUEST <= exc.external_code < status.HTTP_500_INTERNAL_SERVER_ERROR:
            status_code = exc.external_code
        elif exc.external_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
            status_code = status.HTTP_502_BAD_GATEWAY  # Bad Gateway для ошибок внешних сервисов
        else:
            status_code = status.HTTP_400_BAD_REQUEST
    else:
        status_code = status.HTTP_400_BAD_REQUEST

    return JSONResponse(exc.as_dict(), status_code=status_code)


def handle_validation_error(request: Request, exc: RequestValidationError | ValidationError) -> Response:  # noqa: ARG001
    """Обработчик исключений валидации (Pydantic)."""
    logger.info(repr(exc))
    err = exc.errors()[0]

    msg = f"Ошибка валидации: {err['msg']}"
    field = str(err["loc"][-1] or "")
    domain_error = DomainError(msg, field_errors=[FieldErrorDetail(field=field, message=msg)])
    return JSONResponse(domain_error.as_dict(), status_code=status.HTTP_400_BAD_REQUEST)


def handle_unexpected_error(request: Request, exc: Exception) -> Response:  # noqa: ARG001
    """Обработчик всех остальных исключений."""
    logger.error(exc)
    err_content = {"message": "Произошла непредвиденная ошибка. Мы уже работаем над её устранением."}
    return JSONResponse(err_content, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


def register_common_exception_handlers(app: FastAPI) -> None:
    """Инициализация обработчиков исключений.
    Вызвать в shared_kernel.infra.fastapi.app.get_app
    """
    app.add_exception_handler(NotFoundError, _handle_not_found_error)
    app.add_exception_handler(EntityFieldError, _handle_entity_field_error)
    app.add_exception_handler(ExternalServiceError, _handle_external_service_error)
    app.add_exception_handler(DomainError, _handle_domain_error)
    app.add_exception_handler(PermissionAccessError, _handle_permission_access_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(ValidationError, handle_validation_error)
    app.add_exception_handler(Exception, handle_unexpected_error)
