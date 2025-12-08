

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
import bcrypt
import hashlib
import base64

# ------------------------------------------------------------------------------
# Password Hashing + Normalization Fix
# ------------------------------------------------------------------------------

def normalize_password(password: str) -> str:
    """
    Safely normalize password to:
    - Handle unicode
    - Fix encoding
    """
    if not isinstance(password, str):
        password = str(password)

    return password.encode("utf-8", "ignore").decode("utf-8", "ignore")


def hash_password(password: str) -> str:
    password = normalize_password(password)
    
    # Pre-hash with SHA-256 to bypass bcrypt's 72-byte limit
    sha256_hash = hashlib.sha256(password.encode('utf-8')).digest()
    # Encode in base64 to get a string representation safe for bcrypt
    password_b64 = base64.b64encode(sha256_hash)
    
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_b64, salt)
    
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    plain_password = normalize_password(plain_password)
    
    # Pre-hash with SHA-256 to match the hashing strategy
    sha256_hash = hashlib.sha256(plain_password.encode('utf-8')).digest()
    plain_password_b64 = base64.b64encode(sha256_hash)
    
    # Verify hash
    try:
        return bcrypt.checkpw(plain_password_b64, hashed_password.encode('utf-8'))
    except ValueError:
        return False


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
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, organization_id, email, password_hash, role
                FROM users
                WHERE email = %s AND deleted_at IS NULL
            """, (email,))

            row = cur.fetchone()
            if row:
                print(f"SSO Login: Fetched user {row[2]} with Org ID: {row[1]}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if conn:
            conn.close()

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
