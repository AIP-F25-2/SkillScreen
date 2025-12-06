import os, shutil, tempfile
from typing import Tuple, List
from flask import current_app


class LocalStorageService:
    """Local equivalent for new architecture."""

    @staticmethod
    def base_folder() -> str:
        base = current_app.config.get("UPLOAD_FOLDER", "temp/uploads/videos")
        os.makedirs(base, exist_ok=True)
        return base

    @staticmethod
    def interview_folder(interview_id: str) -> str:
        path = os.path.join(LocalStorageService.base_folder(), interview_id)
        os.makedirs(path, exist_ok=True)
        return path

    # ----------------------------------------------------------
    # Chunk save/merge
    # ----------------------------------------------------------
    @staticmethod
    def save_chunk(interview_id: str, blob_name: str, chunk_index: int, data: bytes) -> str:
        folder = os.path.join(LocalStorageService.interview_folder(interview_id), "chunks")
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f"chunk_{chunk_index:05d}.webm")
        with open(path, "wb") as f:
            f.write(data)
        return path

    @staticmethod
    def merge_chunks(interview_id: str, blob_name: str, total_chunks: int) -> Tuple[str, str]:
        folder = LocalStorageService.interview_folder(interview_id)
        chunks_dir = os.path.join(folder, "chunks")
        final_filename = os.path.basename(blob_name).replace(".webm", "_merged.mp4")
        final_local = os.path.join(folder, final_filename)
        with open(final_local, "wb") as merged:
            for i in range(total_chunks):
                chunk_path = os.path.join(chunks_dir, f"chunk_{i:05d}.webm")
                with open(chunk_path, "rb") as c:
                    merged.write(c.read())
        # cleanup
        shutil.rmtree(chunks_dir, ignore_errors=True)
        # Return (local_path, uri) - uri can be accessed via /video/<interview_id>/<filename>
        return final_local, f"/video/{interview_id}/{final_filename}"

    # ----------------------------------------------------------
    # Deletion / listing
    # ----------------------------------------------------------
    @staticmethod
    def delete_folder(prefix: str) -> None:
        base = LocalStorageService.base_folder()
        full = os.path.join(base, prefix)
        if os.path.isdir(full):
            shutil.rmtree(full, ignore_errors=True)

    @staticmethod
    def delete_file(interview_id: str, filename: str) -> bool:
        path = os.path.join(LocalStorageService.interview_folder(interview_id), filename)
        if os.path.isfile(path):
            os.remove(path)
            return True
        return False

    @staticmethod
    def list_files(interview_id: str) -> List[str]:
        folder = LocalStorageService.interview_folder(interview_id)
        if not os.path.isdir(folder):
            return []
        return [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    
    @staticmethod
    def list_all_files() -> List[str]:
        """List all files across all interviews under 'videos/'."""
        base_folder = "videos"
        if not os.path.isdir(base_folder):
            return []
        all_files = []
        # Walk recursively through all subdirectories under /videos
        for root, _, files in os.walk(base_folder):
            for f in files:
                if os.path.isfile(os.path.join(root, f)):
                    all_files.append(os.path.relpath(os.path.join(root, f), start=base_folder))
        return all_files

    # ----------------------------------------------------------
    # Download/upload helpers
    # ----------------------------------------------------------
    @staticmethod
    def download_to_temp(interview_id: str, filename: str) -> str:
        src = os.path.join(LocalStorageService.interview_folder(interview_id), filename)
        if not os.path.exists(src):
            raise FileNotFoundError(filename)
        tmp = tempfile.NamedTemporaryFile(delete=False)
        shutil.copy2(src, tmp.name)
        return tmp.name

    @staticmethod
    def upload_from_path(interview_id: str, local_path: str, dest_filename: str, content_type: str) -> str:
        dest = os.path.join(LocalStorageService.interview_folder(interview_id), dest_filename)
        shutil.copy2(local_path, dest)
        # Return a URL that can be accessed via /video/<interview_id>/<filename>
        return f"/video/{interview_id}/{dest_filename}"
