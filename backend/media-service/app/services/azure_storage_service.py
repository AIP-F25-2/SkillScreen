import os
import tempfile
from typing import Tuple, Optional
from flask import current_app
from azure.storage.blob import ContainerClient, ContentSettings


def _container_client() -> ContainerClient:
    url = current_app.config.get("AZURE_BLOB_CONTAINER_URL") or os.getenv("AZURE_BLOB_CONTAINER_URL")
    if not url:
        raise RuntimeError("AZURE_BLOB_CONTAINER_URL not configured")
    return ContainerClient.from_container_url(url)


def _prefix_for_interview(interview_id: str) -> str:
    return f"videos/{interview_id}/"


class AzureStorageService:
    """
    Simplified Azure service for new media_files flow.
    Stores chunks under videos/<interview_id>/chunks/
    and the final file under videos/<interview_id>/<filename>.
    """

    @staticmethod
    def interview_folder(interview_id: str) -> str:
        return _prefix_for_interview(interview_id)

    # ------------------------------------------------------------------
    # Save one chunk
    # ------------------------------------------------------------------
    @staticmethod
    def save_chunk(interview_id: str, blob_name: str, chunk_index: int, data: bytes) -> str:
        cc = _container_client()
        prefix = _prefix_for_interview(interview_id)
        chunk_blob = f"{prefix}chunks/chunk_{chunk_index:05d}.webm"
        bc = cc.get_blob_client(chunk_blob)
        bc.upload_blob(data, overwrite=True,
                       content_settings=ContentSettings(content_type="video/webm"))
        return chunk_blob

    # ------------------------------------------------------------------
    # Merge all chunks into one blob
    # ------------------------------------------------------------------
    @staticmethod
    def merge_chunks(interview_id: str, blob_name: str, total_chunks: int) -> Tuple[str, str]:
        """
        Downloads chunks, merges locally, uploads final file to
        videos/<interview_id>/<final_filename>, then deletes chunks.
        """
        cc = _container_client()
        prefix = _prefix_for_interview(interview_id)
        final_name = os.path.basename(blob_name).replace(".webm", "_merged.mp4")
        with tempfile.NamedTemporaryFile(prefix="merge_", suffix=".webm", delete=False) as tmp:
            final_local = tmp.name
            # Merge locally into the safe temporary file
            for i in range(total_chunks):
                chunk_blob = f"{prefix}chunks/chunk_{i:05d}.webm"
                bc = cc.get_blob_client(chunk_blob)
                stream = bc.download_blob()
                tmp.write(stream.readall())

        # Upload final merged blob
        final_blob = f"{prefix}{final_name}"
        bc_final = cc.get_blob_client(final_blob)
        with open(final_local, "rb") as f:
            bc_final.upload_blob(
                f,
                overwrite=True,
                content_settings=ContentSettings(content_type="video/mp4"),
            )
        final_uri = bc_final.url

        # Delete chunk blobs
        for i in range(total_chunks):
            try:
                cc.delete_blob(f"{prefix}chunks/chunk_{i:05d}.webm")
            except Exception:
                pass

        return final_local, final_uri

    # ------------------------------------------------------------------
    # Delete helpers
    # ------------------------------------------------------------------
    @staticmethod
    def delete_folder(prefix: str) -> None:
        cc = _container_client()
        for b in cc.list_blobs(name_starts_with=prefix):
            try:
                cc.delete_blob(b.name)
            except Exception:
                pass

    @staticmethod
    def delete_file(interview_id: str, filename: str) -> bool:
        cc = _container_client()
        try:
            cc.delete_blob(f"{_prefix_for_interview(interview_id)}{filename}")
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Download / upload convenience
    # ------------------------------------------------------------------
    @staticmethod
    def download_to_temp(interview_id: str, filename: str) -> str:
        cc = _container_client()
        blob = f"{_prefix_for_interview(interview_id)}{filename}"
        suffix = os.path.splitext(filename)[1]
        with tempfile.NamedTemporaryFile(prefix="media_", suffix=suffix, delete=False) as tmp:
            cc.get_blob_client(blob).download_blob().readinto(tmp)
            return tmp.name

    @staticmethod
    def upload_from_path(interview_id: str, local_path: str, dest_filename: str, content_type: str) -> str:
        cc = _container_client()
        blob = f"{_prefix_for_interview(interview_id)}{dest_filename}"
        with open(local_path, "rb") as f:
            cc.get_blob_client(blob).upload_blob(
                f, overwrite=True,
                content_settings=ContentSettings(content_type=content_type)
            )
        return cc.get_blob_client(blob).url

    @staticmethod
    def list_files(interview_id: Optional[str] = None) -> list[str]:
        """List blobs from the Azure container. Optionally filter by interview_id prefix."""
        cc = _container_client()
        prefix = f"videos/{interview_id}/" if interview_id else "videos/"
        blobs = cc.list_blobs(name_starts_with=prefix)
        return [b.name for b in blobs]

    @staticmethod
    def list_all_files() -> list[str]:
        """List all video blobs in the Azure container."""
        cc = _container_client()
        blobs = cc.list_blobs(name_starts_with="videos/")
        return [b.name for b in blobs]