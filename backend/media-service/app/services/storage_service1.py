# app/services/storage_service.py
import os
import stat
import json
import shutil
from typing import List
from flask import current_app
from ..utils.filename import secure_part

MANIFEST = "chunks_manifest.json"

class StorageService:
    @staticmethod
    def user_folder(user_id: str) -> str:
        base = current_app.config.get("UPLOAD_FOLDER", "uploads")
        uid = secure_part(user_id)
        folder = os.path.join(base, uid)
        os.makedirs(folder, exist_ok=True)
        return folder

    @staticmethod
    def list_users() -> list[str]:
        base = current_app.config.get("UPLOAD_FOLDER", "uploads")
        if not os.path.isdir(base):
            return []
        return [d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))]

    @staticmethod
    def list_files(user_id: str, include_exts: List[str] | None = None, exclude_exts: List[str] | None = None) -> list[str]:
        folder = StorageService.user_folder(user_id)
        items = []
        for f in os.listdir(folder):
            p = os.path.join(folder, f)
            if not os.path.isfile(p):
                continue
            lower = f.lower()
            if include_exts and not any(lower.endswith(e) for e in include_exts):
                continue
            if exclude_exts and any(lower.endswith(e) for e in exclude_exts):
                continue
            items.append(f)
        return items

    @staticmethod
    def delete_file(user_id: str, filename: str) -> bool:
        folder = StorageService.user_folder(user_id)
        from ..utils.filename import secure_part as sp
        path = os.path.join(folder, sp(filename))
        if os.path.isfile(path):
            os.remove(path)
            return True
        return False

    @staticmethod
    def delete_all(user_id: str, include_exts: List[str] | None = None, exclude_exts: List[str] | None = None) -> list[str]:
        deleted = []
        folder = StorageService.user_folder(user_id)
        for f in os.listdir(folder):
            low = f.lower()
            if include_exts and not any(low.endswith(e) for e in include_exts):
                continue
            if exclude_exts and any(low.endswith(e) for e in exclude_exts):
                continue
            try:
                os.remove(os.path.join(folder, f))
                deleted.append(f)
            except Exception:
                pass
        # if we cleaned webm chunks, also remove manifest(s) and merged.webm
        try:
            if include_exts and ".webm" in include_exts:
                for mf in ("merged.webm", "chunks_manifest.json", "manifest.json"):
                    mp = os.path.join(folder, mf)
                    if os.path.exists(mp):
                        try: os.remove(mp)
                        except Exception: pass
        except Exception:
            pass
        return deleted

    @staticmethod
    def delete_user(user_id: str) -> bool:
        folder = StorageService.user_folder(user_id)
        if not os.path.isdir(folder):
            return False

        def _on_rm_error(func, path, exc_info):
            try:
                os.chmod(path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
                func(path)
            except Exception:
                pass

        try:
            shutil.rmtree(folder, onerror=_on_rm_error)
            return True
        except Exception:
            return False

    @staticmethod
    def delete_all_users() -> list[str]:
        base = current_app.config.get("UPLOAD_FOLDER", "uploads")
        deleted = []
        if not os.path.isdir(base):
            return deleted
        for user in os.listdir(base):
            uf = os.path.join(base, user)
            if os.path.isdir(uf):
                try:
                    shutil.rmtree(uf)
                    deleted.append(user)
                except Exception:
                    pass
        return deleted

    @staticmethod
    def manifest_path(user_id: str) -> str:
        return os.path.join(StorageService.user_folder(user_id), MANIFEST)

    @staticmethod
    def load_manifest(user_id: str) -> dict:
        p = StorageService.manifest_path(user_id)
        if os.path.isfile(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"received": [], "expected_total": None}

    @staticmethod
    def save_manifest(user_id: str, data: dict) -> None:
        p = StorageService.manifest_path(user_id)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
