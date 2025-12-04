from fastapi import HTTPException, status
from repositories.user_repository import UserRepository
from utils.auth_utils import hash_password

class UserService:

    def __init__(self, uow):
        self.repo = UserRepository(uow)

    def create(self, payload: dict):
        # Email uniqueness check
        existing = self.repo.get_user_by_email(payload["email"])
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already in use",
            )

        data = {
            "organization_id": payload["organization_id"],
            "email": payload["email"],
            "password_hash": hash_password(payload["password"]),
            "first_name": payload.get("first_name"),
            "last_name": payload.get("last_name"),
            "role": payload["role"],
        }
        return self.repo.create_user(data)

    def get_all(self):
        return self.repo.get_all_users()

    def get_by_id(self, user_id: str):
        return self.repo.get_user_by_id(user_id)

    def update(self, user_id: str, payload: dict):
        updates = payload.copy()

        if "password" in updates and updates["password"]:
            updates["password_hash"] = hash_password(updates.pop("password"))

        updated = self.repo.update_user(user_id, updates)
        return updated

    def delete(self, user_id: str):
        return self.repo.delete_user(user_id)
