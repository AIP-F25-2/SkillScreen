from pydantic import BaseModel, EmailStr

class OrganizationCreate(BaseModel):
    name: str
    email_domain: str
    address: str | None = None
    country: str | None = None

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    role: str

class OnboardRequest(BaseModel):
    organization: OrganizationCreate
    user: UserCreate
