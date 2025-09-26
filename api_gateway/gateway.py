from fastapi import FastAPI, Request, HTTPException, Response
import httpx
from jose import jwt, JWTError
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

SECRET_KEY = "supersecret"
ALGORITHM = "HS256"

app = FastAPI(title="API Gateway")

# RBAC rules: endpoint prefix → allowed roles
RBAC_RULES = {
    "/user": ["admin"],  # only admins can access user service
    "/assessment": ["admin", "user"],  # both admin and user can access assessment
    "/coding": ["user"]  # only normal users can access coding
}

SERVICE_MAP = {
    "user": "http://user_service:8001",
    "assessment": "http://assessment_service:8002",
    "coding": "http://coding_service:8003"
}

# Middleware for JWT validation and RBAC
async def verify_jwt(request: Request, call_next):
    try:
        if request.url.path.startswith("/auth/"):
            return await call_next(request)  # allow auth routes

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
    async with httpx.AsyncClient() as client:
        body = await request.body()
        headers = dict(request.headers)
        resp = await client.request(
            request.method,
            f"{service_url}{path}",
            content=body,
            headers=headers,
            params=request.query_params
        )
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=dict(resp.headers)
        )
    
# Routes for microservices
@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(service: str, path: str, request: Request):
    if service not in SERVICE_MAP:
        raise HTTPException(status_code=404, detail="Unknown service")
    return await forward_request(SERVICE_MAP[service], f"/{path}", request)