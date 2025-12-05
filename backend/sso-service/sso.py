# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from jose import jwt
# from datetime import datetime, timedelta
# import uuid

# SECRET_KEY = "supersecret"
# ALGORITHM = "HS256"

# app = FastAPI(title="SSO Service")

# def create_response(data, success=True):
#     """Create standardized API response"""
#     return {
#         "success": success,
#         "data": data,
#         "meta": {
#             "timestamp": datetime.utcnow().isoformat() + "Z",
#             "request_id": f"req_{uuid.uuid4().hex[:8]}",
#             "version": "v1"
#         }
#     }

# class LoginRequest(BaseModel):
#     username: str
#     password: str

# # User mock data
# users_db = {
#     "admin": {"password": "password", "role": "admin"},
#     "ashish": {"password": "1234", "role": "user"}
# }

# @app.get("/")
# def health_check():
#     """Health check endpoint"""
#     return create_response({
#         "message": "SSO Service is running",
#         "status": "deployed",
#         "service": "sso-service"
#     })

# @app.get("/health")
# def health():
#     """Detailed health check"""
#     return create_response({
#         "service": "sso-service",
#         "status": "healthy",
#         "timestamp": datetime.utcnow().isoformat()
#     })

# @app.post("/login")
# def login(req: LoginRequest):
#     """User login endpoint"""
#     user = users_db.get(req.username)
#     if not user or user["password"] != req.password:
#         raise HTTPException(status_code=401, detail="Invalid credentials")
    
#     expire = datetime.utcnow() + timedelta(hours=1)
#     token = jwt.encode(
#         {"sub": req.username, "role": user["role"], "exp": expire},
#         SECRET_KEY,
#         algorithm=ALGORITHM
#     )

#     return create_response({
#         "access_token": token, 
#         "role": user["role"],
#         "expires_in": 3600
#     })

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from passlib.context import CryptContext
import jwt
import psycopg2
import os

# ------------------------------------------------------------------------------
# FastAPI App
# ------------------------------------------------------------------------------
app = FastAPI(title="SSO Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# Environment Variables
# ------------------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
DATABASE_URL = os.getenv("DATABASE_URL")

# ------------------------------------------------------------------------------
# Password Hashing + Normalization Fix
# ------------------------------------------------------------------------------
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def normalize_password(password: str) -> str:
    """
    Safely normalize password to:
    - Handle unicode
    - Fix encoding
    - Prevent bcrypt 72-byte crash
    """
    if not isinstance(password, str):
        password = str(password)

    clean = password.encode("utf-8", "ignore").decode("utf-8", "ignore")
    return clean[:72]  # Critical fix


def hash_password(password: str) -> str:
    password = normalize_password(password)
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    plain_password = normalize_password(plain_password)
    return pwd_context.verify(plain_password, hashed_password)


# ------------------------------------------------------------------------------
# Database Connection Helper
# ------------------------------------------------------------------------------
def get_connection():
    return psycopg2.connect(DATABASE_URL)


# ------------------------------------------------------------------------------
# Request Models
# ------------------------------------------------------------------------------
class LoginRequest(BaseModel):
    email: str
    password: str


# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------
@app.get("/health")
def health_check():
    return {"status": "sso-service running"}

@app.post("/login")
def login(payload: LoginRequest):
    email = payload.email.lower().strip()
    raw_password = payload.password

    # --------------------- Fetch user from database ---------------------------
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, organization_id, email, password_hash, role
            FROM users
            WHERE email = %s AND deleted_at IS NULL
        """, (email,))

        row = cur.fetchone()
        cur.close()
        conn.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    if not row:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user = {
        "id": row[0],
        "organization_id": row[1],
        "email": row[2],
        "password_hash": row[3],
        "role": row[4],
    }

    # ----------------------- Verify password ---------------------------------
    if not verify_password(raw_password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # ----------------------- Create JWT --------------------------------------
    token_data = {
        "id": user["id"],
        "email": user["email"],
        "role": user["role"],
        "organization_id": user["organization_id"],
    }

    try:
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token generation failed: {str(e)}")

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "role": user["role"],
            "organization_id": user["organization_id"],
        }
    }
