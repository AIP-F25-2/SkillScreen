from fastapi import FastAPI, Request, HTTPException, Response
import httpx
from jose import jwt, JWTError
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
PORT = int(os.getenv("PORT", "5000"))

app = FastAPI(title="API Gateway")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# RBAC rules: endpoint prefix → allowed roles
RBAC_RULES = {
    "/user": ["admin", "user"],  # only admins can access user service
    "/auth": ["admin", "user"],  # both admin and user can access auth service
    "/assessment": ["admin", "user"],  # both admin and user can access assessment
    "/coding": ["admin", "user"],  # only normal users can access coding
    "/text-service": ["admin", "user"],  # both admin and user can access text service
    "/audio-ai": ["admin", "user"],  # both admin and user can access audio AI
    "/video-ai": ["admin", "user"],  # both admin and user can access video AI
    "/text-ai": ["admin", "user"],  # both admin and user can access text AI
    "/interview": ["admin", "user"],  # both admin and user can access interview
    "/media": ["admin", "user"],  # both admin and user can access media
    "/notification": ["admin", "user"],  # both admin and user can access notification
    "/logger": ["admin"],  # only admins can access logger service
    "/sso": ["admin", "user"],  # both admin and user can access SSO
    "/orchestration": ["admin", "user"]  # both admin and user can access orchestration
}

# Internal Docker service URLs - HTTP is acceptable for internal container communication
# In production, these can be configured to use HTTPS if needed
# Security Note: These URLs are internal to Docker network and not exposed externally
SERVICE_MAP = {
    "user": os.getenv("USER_SERVICE_URL", "http://user-service:8080"),
    "auth": os.getenv("AUTH_SERVICE_URL", "http://sso-service:8080"),
    "assessment": os.getenv("ASSESSMENT_SERVICE_URL", "http://assessment-service:8080"),
    "coding": os.getenv("CODING_SERVICE_URL", "http://coding-service:8080"),
    "text-service": os.getenv("TEXT_SERVICE_URL", "http://text-service:8080"),
    "audio-ai": os.getenv("AUDIO_AI_SERVICE_URL", "http://audio-ai-service:8080"),
    "video-ai": os.getenv("VIDEO_AI_SERVICE_URL", "http://video-ai-service:8080"),
    "text-ai": os.getenv("TEXT_AI_SERVICE_URL", "http://text-ai-service:8080"),
    "interview": os.getenv("INTERVIEW_SERVICE_URL", "http://localhost:8003"),
    "media": os.getenv("MEDIA_SERVICE_URL", "http://media-service:8080"),
    "notification": os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8080"),
    "sso": os.getenv("SSO_SERVICE_URL", "http://sso-service:8080"),
    "orchestration": os.getenv("ORCHESTRATION_SERVICE_URL", "http://orchestration-service:8080")
}

# Middleware for JWT validation and RBAC
async def verify_jwt(request: Request, call_next):
    try:
        # Always allow CORS preflight without auth
        if request.method == "OPTIONS":
            return await call_next(request)

        if request.url.path.startswith("/auth/"):
            return await call_next(request)  # allow auth routes

        # TEMP: allow AI logic routes during development/testing without auth
        if request.url.path.startswith("/ai-logic/"):
            return await call_next(request)
        
        # TEMP: allow audio-ai routes during development/testing without auth
        if request.url.path.startswith("/audio-ai/"):
            return await call_next(request)
        
        # TEMP: allow media routes during development/testing without auth
        if request.url.path.startswith("/media/"):
            return await call_next(request)
        
        # TEMP: allow text-service routes during development/testing without auth
        if request.url.path.startswith("/text-service/"):
            return await call_next(request)

        # TEMP: allow orchestration routes during development/testing without auth
        if request.url.path.startswith("/orchestration/"):
            return await call_next(request)

        # TEMP: allow interview routes during development/testing without auth
        if request.url.path.startswith("/interview/"):
            return await call_next(request)

        # TEMP: allow text-ai routes during development/testing without auth
        if request.url.path.startswith("/text-ai/"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid token")

        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            request.state.user = payload
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        #RBAC enforcement
        for prefix, roles in RBAC_RULES.items():
            if request.url.path.startswith(prefix):
                if payload.get("role") not in roles:
                    raise HTTPException(status_code=403, detail="Forbidden: insufficient role")

        return await call_next(request)
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})


app.add_middleware(BaseHTTPMiddleware, dispatch=verify_jwt)

# Proxy function
async def forward_request(service_url: str, path: str, request: Request) -> Response:
    async with httpx.AsyncClient(timeout=600.0) as client:  # 10 minute timeout for audio processing
        body = await request.body()
        headers = dict(request.headers)
        
        # Remove content-length header to let httpx recalculate it
        headers.pop("content-length", None)
        headers.pop("host", None)
        
        resp = await client.request(
            request.method,
            f"{service_url}{path}",
            content=body,
            headers=headers,
            params=request.query_params
        )
        
        # Add CORS headers explicitly to ensure they're present
        response_headers = dict(resp.headers)
        response_headers["Access-Control-Allow-Origin"] = "*"
        response_headers["Access-Control-Allow-Credentials"] = "true"
        response_headers["Access-Control-Allow-Methods"] = "*"
        response_headers["Access-Control-Allow-Headers"] = "*"
        
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=response_headers
        )
    
# Special route for audio-ai to bypass validation for file:// URLs
@app.api_route("/audio-ai/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy_audio_ai(path: str, request: Request):
    """Special proxy for audio-ai service that allows file:// URLs"""
    return await forward_request(SERVICE_MAP["audio-ai"], f"/{path}", request)

# Routes for other microservices
@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy(service: str, path: str, request: Request):
    if service not in SERVICE_MAP:
        raise HTTPException(status_code=404, detail="Unknown service")
    return await forward_request(SERVICE_MAP[service], f"/{path}", request)