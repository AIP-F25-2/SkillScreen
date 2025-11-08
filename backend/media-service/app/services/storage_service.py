"""Storage service implementation that routes to either Azure or local storage."""

import os
from typing import List, Optional, Tuple
from flask import current_app
from app.services.azure_storage_service import AzureStorageService as _Cloud
from app.services.local_storage_service import LocalStorageService

def _use_azure() -> bool:
    """Determine backend from Flask config."""
    return current_app.config.get("USE_AZURE_STORAGE", True)


class StorageService:
    """
    Unified interface for storage operations.
    Routes all calls to either Azure or Local implementation.
    Now chunk-aware and interview_id-based.
    """

    # -------------------------------------------------------------------
    # 📁 Folder utilities
    # -------------------------------------------------------------------
    @staticmethod
    def interview_folder(interview_id: str) -> str:
        """Return or create interview-specific folder path/prefix."""
        return _Cloud.interview_folder(interview_id) if _use_azure() else LocalStorageService.interview_folder(interview_id)

    # -------------------------------------------------------------------
    # 🧩 Chunked upload helpers
    # -------------------------------------------------------------------
    @staticmethod
    def save_chunk(interview_id: str, blob_name: str, chunk_index: int, data: bytes) -> str:
        """Save a single chunk to backend under videos/<interview_id>/chunks/."""
        if _use_azure():
            return _Cloud.save_chunk(interview_id, blob_name, chunk_index, data)
        return LocalStorageService.save_chunk(interview_id, blob_name, chunk_index, data)

    @staticmethod
    def merge_chunks(interview_id: str, blob_name: str, total_chunks: int) -> Tuple[str, str]:
        """
        Merge all chunks and return (final_path, final_uri).
        The final merged file is stored under videos/<interview_id>/<final_filename>.
        """
        if _use_azure():
            return _Cloud.merge_chunks(interview_id, blob_name, total_chunks)
        return LocalStorageService.merge_chunks(interview_id, blob_name, total_chunks)

    # -------------------------------------------------------------------
    # 🧹 Cleanup helpers
    # -------------------------------------------------------------------
    @staticmethod
    def delete_folder(prefix: str) -> None:
        """Delete all blobs or files under a given prefix/path."""
        if _use_azure():
            _Cloud.delete_folder(prefix)
        else:
            LocalStorageService.delete_folder(prefix)

    @staticmethod
    def delete_file(interview_id: str, filename: str) -> bool:
        if _use_azure():
            return _Cloud.delete_file(interview_id, filename)
        return LocalStorageService.delete_file(interview_id, filename)

    # -------------------------------------------------------------------
    # 📥 Download utilities
    # -------------------------------------------------------------------
    @staticmethod
    def download_to_temp(interview_id: str, filename: str) -> str:
        """Download a blob/file temporarily to local disk."""
        if _use_azure():
            return _Cloud.download_to_temp(interview_id, filename)
        return LocalStorageService.download_to_temp(interview_id, filename)

    # -------------------------------------------------------------------
    # 📋 Listing helpers
    # -------------------------------------------------------------------
    @staticmethod
    def list_files(interview_id: Optional[str] = None) -> List[str]:
        """
        Lists files for a specific interview if interview_id is provided.
        If interview_id is None, returns all video files (admin mode).
        """
        if _use_azure():
            if interview_id:
                return _Cloud.list_files(interview_id)
            return _Cloud.list_all_files()
        else:
            if interview_id:
                return LocalStorageService.list_files(interview_id)
            return LocalStorageService.list_all_files()


    # -------------------------------------------------------------------
    # 🔄 Generic file upload (non-chunked)
    # -------------------------------------------------------------------
    @staticmethod
    def upload_from_path(interview_id: str, local_path: str, dest_filename: str, content_type: str) -> str:
        """Upload a full file (e.g. merged video) from local disk to backend."""
        if _use_azure():
            return _Cloud.upload_from_path(interview_id, local_path, dest_filename, content_type)
        return LocalStorageService.upload_from_path(interview_id, local_path, dest_filename, content_type)
