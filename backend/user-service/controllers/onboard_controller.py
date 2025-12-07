

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from repositories.organization_repository import OrganizationRepository
from repositories.user_repository import UserRepository
from utils.auth_utils import hash_password
from utils.jwt_utils import create_access_token

from db import DBFactory

# This controller will be included with prefix="/users" from user.py
router = APIRouter(tags=["Onboarding"])


# =====================
# Pydantic Schemas
# =====================
class OrgCreate(BaseModel):
    name: str
    domain: str | None = None
    settings: str | None = None


class UserCreate(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    role: str


class OnboardRequest(BaseModel):
    organization: OrgCreate
    user: UserCreate


# =====================
# Onboard Endpoint
# =====================
@router.post("/onboard", summary="Create organization + admin user")
def onboard(payload: OnboardRequest):
    session = DBFactory.get_session()

    org_repo = OrganizationRepository(session)
    user_repo = UserRepository(session)

    try:
        # 1️⃣ Create organization
        org_id = org_repo.create_organization(payload.organization.dict())

        # 2️⃣ Create user with organization_id
        user_data = payload.user.dict()
        user_data["organization_id"] = org_id
        user_data["password_hash"] = hash_password(user_data.pop("password"))

        user_id = user_repo.create_user(user_data)

        # 3️⃣ Generate JWT token
        token = create_access_token({
            "user_id": str(user_id),
            "org_id": str(org_id)
        })

        session.commit()

        return {
            "success": True,
            "organization_id": org_id,
            "user_id": user_id,
            "access_token": token,
            "token_type": "bearer"
        }

    except SQLAlchemyError as e:
        session.rollback()
        print(f"Onboarding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()
