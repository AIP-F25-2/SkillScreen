# app/services/storage_service.py
"""Storage service implementation that routes to either Azure or local storage."""

from typing import List
from flask import current_app
from .azure_storage_service import AzureStorageService as _Cloud
from .local_storage_service import LocalStorageService

def _use_azure() -> bool:
    """Get storage mode from config"""
    return current_app.config.get("USE_AZURE_STORAGE", True)

class StorageService:
    """Storage service that routes to Azure or local storage based on config."""
    
    @staticmethod
    def user_folder(user_id: str) -> str:
        return _Cloud.user_folder(user_id) if _use_azure() else LocalStorageService.user_folder(user_id)

    @staticmethod
    def list_users() -> List[str]:
        return _Cloud.list_users() if _use_azure() else LocalStorageService.list_users()

    @staticmethod
    def list_files(user_id: str, include_exts: List[str] | None = None, exclude_exts: List[str] | None = None) -> List[str]:
        return _Cloud.list_files(user_id, include_exts, exclude_exts) if _use_azure() else LocalStorageService.list_files(user_id, include_exts, exclude_exts)

    @staticmethod
    def delete_file(user_id: str, filename: str) -> bool:
        return _Cloud.delete_file(user_id, filename) if _use_azure() else LocalStorageService.delete_file(user_id, filename)

    @staticmethod
    def delete_all(user_id: str, include_exts: List[str] | None = None, exclude_exts: List[str] | None = None) -> List[str]:
        return _Cloud.delete_all(user_id, include_exts, exclude_exts) if _use_azure() else LocalStorageService.delete_all(user_id, include_exts, exclude_exts)

    @staticmethod
    def delete_user(user_id: str) -> bool:
        return _Cloud.delete_user(user_id) if _use_azure() else LocalStorageService.delete_user(user_id)

    @staticmethod
    def delete_all_users() -> List[str]:
        return _Cloud.delete_all_users() if _use_azure() else LocalStorageService.delete_all_users()

    @staticmethod
    def manifest_path(user_id: str) -> str:
        return _Cloud.manifest_blob_name(user_id) if _use_azure() else LocalStorageService.manifest_path(user_id)

    @staticmethod
    def load_manifest(user_id: str) -> dict:
        return _Cloud.load_manifest(user_id) if _use_azure() else LocalStorageService.load_manifest(user_id)

    @staticmethod
    def save_manifest(user_id: str, data: dict, **kwargs) -> None:
        if _use_azure():
            _Cloud.save_manifest(user_id, data, **kwargs)
        else:
            LocalStorageService.save_manifest(user_id, data)

    # Additional Azure-specific methods (only available when USE_AZURE_STORAGE=true)
    @staticmethod
    def save_chunk_to_cloud(user_id: str, filename: str, fileobj, **kwargs) -> str:
        if not _use_azure():
            raise RuntimeError("Azure storage not configured")
        return _Cloud.save_chunk(user_id, filename, fileobj, **kwargs)

    @staticmethod
    def download_to_temp(user_id: str, filename: str) -> str:
        if not _use_azure():
            raise RuntimeError("Azure storage not configured")
        return _Cloud.download_to_temp(user_id, filename)

    @staticmethod
    def upload_from_path(user_id: str, local_path: str, dest_filename: str, content_type: str, **kwargs) -> str:
        if not _use_azure():
            raise RuntimeError("Azure storage not configured")
        return _Cloud.upload_from_path(user_id, local_path, dest_filename, content_type, **kwargs)

    @staticmethod
    def list_chunk_filenames(user_id: str, ext: str = ".webm") -> List[str]:
        if not _use_azure():
            raise RuntimeError("Azure storage not configured")
        return _Cloud.list_chunk_filenames(user_id, ext)
