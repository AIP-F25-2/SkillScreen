from fastapi import HTTPException, status
from repositories.organization_repository import OrganizationRepository
from repositories.user_repository import UserRepository
from utils.auth_utils import hash_password

class RegisterService:

    def __init__(self, uow):
        self.org_repo = OrganizationRepository(uow)
        self.user_repo = UserRepository(uow)

    def register(self, payload: dict):
        # 0) check if admin email already exists
        existing = self.user_repo.get_user_by_email(payload["admin_email"])
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin email is already in use",
            )

        # 1) create organization
        org_data = {
            "name": payload["organization_name"],
            "domain": payload.get("domain"),
            "settings": payload.get("settings"),
        }
        org_id = self.org_repo.create(org_data)

        # 2) create admin user
        admin_data = {
            "organization_id": org_id,
            "email": payload["admin_email"],
            "password_hash": hash_password(payload["admin_password"]),
            "first_name": payload.get("admin_first_name"),
            "last_name": payload.get("admin_last_name"),
            "role": "hr",  # default admin role
        }
        admin_id = self.user_repo.create_user(admin_data)

        return {
            "organization_id": org_id,
            "admin_user_id": admin_id,
        }
