from repositories.organization_repository import OrganizationRepository
from repositories.user_repository import UserRepository
from utils.auth_utils import hash_password   # you already have this

class RegisterService:

    def __init__(self, db_session):
        self.org_repo = OrganizationRepository(db_session)
        self.user_repo = UserRepository(db_session)

    def register(self, payload: dict):
        # ================================
        # 1. CREATE ORGANIZATION
        # ================================
        org_data = {
            "name": payload["organization_name"],
            "domain": payload.get("domain"),
            "settings": payload.get("settings")
        }

        org_id = self.org_repo.create(org_data)

        # ================================
        # 2. CREATE ADMIN USER
        # ================================
        admin_data = {
            "organization_id": org_id,
            "email": payload["admin_email"],
            "password_hash": hash_password(payload["admin_password"]),
            "first_name": payload.get("admin_first_name"),
            "last_name": payload.get("admin_last_name"),
            "role": "hr"   # default admin role
        }

        admin_id = self.user_repo.create_user(admin_data)

        # ================================
        # 3. RETURN RESULT
        # ================================
        return {
            "organization_id": org_id,
            "admin_user_id": admin_id
        }
