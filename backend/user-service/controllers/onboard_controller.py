# from fastapi import APIRouter, HTTPException
# from db import DBFactory
# from repositories.organization_repository import OrganizationRepository
# from repositories.user_repository import UserRepository
# from utils.auth_utils import hash_password
# from pydantic import BaseModel

# router = APIRouter(prefix="/onboard", tags=["Onboarding"])

# # ---------------------------
# # Pydantic Models
# # ---------------------------

# class OrganizationCreate(BaseModel):
#     name: str
#     email: str
#     phone: str | None = None
#     address: str | None = None

# class UserCreate(BaseModel):
#     full_name: str
#     email: str
#     password: str
#     role: str

# class OnboardRequest(BaseModel):
#     organization: OrganizationCreate
#     user: UserCreate

# # ---------------------------
# # Combined Endpoint
# # ---------------------------

# @router.post("/")
# def onboard(payload: OnboardRequest):
#     db = DBFactory.get_db()

#     # Create organization
#     org_repo = OrganizationRepository(db)
#     org = org_repo.create_organization(payload.organization.dict())

#     if not org:
#         raise HTTPException(status_code=400, detail="Failed to create organization")

#     org_id = org["id"]

#     # Create user assigned to org
#     user_repo = UserRepository(db)
#     user_data = payload.user.dict()
#     user_data["organization_id"] = org_id
#     user_data["password_hash"] = hash_password(user_data.pop("password"))

#     user = user_repo.create_user(user_data)

#     if not user:
#         raise HTTPException(status_code=400, detail="Failed to create user")

#     return {
#         "success": True,
#         "data": {
#             "organization": org,
#             "user": user
#         }
#     }

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
    session = DBFactory.get_db()

    org_repo = OrganizationRepository(session)
    user_repo = UserRepository(session)

    try:
        # 1️⃣ Create organization
        org_id = org_repo.create(payload.organization.dict())

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

        return {
            "success": True,
            "organization_id": org_id,
            "user_id": user_id,
            "access_token": token,
            "token_type": "bearer"
        }

    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
