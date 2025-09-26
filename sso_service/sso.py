from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from jose import jwt
from datetime import datetime, timedelta

SECRET_KEY = "supersecret"
ALGORITHM = "HS256"

app = FastAPI(title="SSO Service")

class LoginRequest(BaseModel):
    username: str
    password: str

# User mock data
users_db = {
    "admin": {"password": "password", "role": "admin"},
    "ashish": {"password": "1234", "role": "user"}
}

@app.post("/auth/login")
def login(req: LoginRequest):
    user = users_db.get(req.username)
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    expire = datetime.utcnow() + timedelta(hours=1)
    token = jwt.encode(
        {"sub": req.username, "role": user["role"], "exp": expire},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return {"access_token": token, "role": user["role"]}