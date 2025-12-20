from typing import Annotated

from fastapi import Depends

from adapters.outbound.http import SigningClient
from adapters.outbound.http.kadr.client import KadrClient
from adapters.outbound.http.kazna.client import KaznaClient
from adapters.outbound.s3.service import S3StorageService
from core.acts.application.ports.outbound.file_storage import IFileStorageService


def get_file_storage() -> IFileStorageService:
    """Dependency для получения файлового хранилища."""
    return S3StorageService()


def get_kazna_client() -> KaznaClient:
    """Dependency для получения клиента сервиса АС Казны."""
    return KaznaClient()


def get_signing_client() -> SigningClient:
    """Dependency для получения клиента сервиса АС Подписания."""
    return SigningClient()


def get_kadr_client() -> KadrClient:
    """Dependency для получения клиента сервиса HR 1C."""
    return KadrClient()


FileStorageDep = Annotated[IFileStorageService, Depends(get_file_storage)]

KaznaClientDep = Annotated[KaznaClient, Depends(get_kazna_client)]

SigningClientDep = Annotated[SigningClient, Depends(get_signing_client)]

KadrClientDep = Annotated[KadrClient, Depends(get_kadr_client)]
