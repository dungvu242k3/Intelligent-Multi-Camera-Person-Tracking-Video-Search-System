import logging
import os
import sys
import time
import uuid as uuid_lib
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, Tuple
from fastapi import FastAPI, HTTPException, Request, Response, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
import httpx
import jwt
from pydantic import BaseModel

# Setup path to import packages correctly in monorepo
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from config.settings import settings
from websocket.manager import manager
from middleware.rate_limiter import rate_limiter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("gateway")

# Persistent async HTTP client pool
async_client: Optional[httpx.AsyncClient] = None

# Local login brute-force lockout storage fallback
# Structure: client_ip -> (failed_attempts_count, lockout_timestamp)
gateway_lockouts: Dict[str, Tuple[int, float]] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event manager mapping startup/shutdown states."""
    global async_client
    logger.info("Initializing API Gateway routing clients...")
    # P1 #6: Configure httpx connection pool limits to prevent socket exhaustion
    async_client = httpx.AsyncClient(
        timeout=httpx.Timeout(10.0, connect=5.0),
        limits=httpx.Limits(max_connections=200, max_keepalive_connections=50)
    )
    
    yield
    
    logger.info("Shutting down API Gateway clients...")
    if async_client:
        await async_client.aclose()

_is_prod = settings.ENV == "production"

app = FastAPI(
    title="Intelligent MCPT — API Gateway",
    description="Single entry point routing traffic and broadcasting WebSocket alert notifications.",
    version="1.0.0",
    lifespan=lifespan,
    # P0 #5: Disable OpenAPI docs in production to prevent schema leakage
    docs_url=None if _is_prod else "/docs",
    redoc_url=None if _is_prod else "/redoc",
)

# 1. CORS Configuration (Restricted based on Environment settings)
cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. HTTP Security Headers Middleware (Anti-XSS, Anti-Clickjacking, CSP)
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Enforce HSTS (Strict-Transport-Security) in production TLS environments
    if os.getenv("HTTPS_ENFORCE", "false").lower() == "true":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# 2b. P3 #16: Request ID / Correlation ID Middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Injects a unique X-Request-Id header for distributed tracing."""
    request_id = request.headers.get("X-Request-Id", str(uuid_lib.uuid4()))
    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    return response

# 3. Payload Size Limit Middleware (DoS & Buffer Exhaustion prevention)
@app.middleware("http")
async def limit_request_payload_size(request: Request, call_next):
    # Retrieve content length header
    content_length = request.headers.get("Content-Length")
    if content_length:
        try:
            length = int(content_length)
            # Route logic: restrict JSON payloads to 2MB, allow 250MB for video trial uploads
            is_upload_route = "upload-video" in request.url.path or "test-video" in request.url.path
            max_limit = 250 * 1024 * 1024 if is_upload_route else 2 * 1024 * 1024
            
            if length > max_limit:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Request payload size exceeds permitted thresholds (Limit: {max_limit} bytes)."
                )
        except ValueError:
            pass
            
    return await call_next(request)

# Service mapping routing keys
SERVICE_MAPPING = {
    "auth": settings.AUTH_SERVICE_URL,
    "cameras": settings.CAMERA_SERVICE_URL,
    "search": settings.SEARCH_SERVICE_URL,
    "analytics": settings.ANALYTICS_SERVICE_URL,
}

def verify_token(authorization_header: Optional[str]) -> Dict[str, Any]:
    """Decodes and validates a JWT Access Token. Protects against token type confusion."""
    if not authorization_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization credentials"
        )
    parts = authorization_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization schema. Use 'Bearer <token>'"
        )
    token = parts[1]
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        # Token type check (must be access token, not refresh token)
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type: Access token expected"
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization credentials have expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization token"
        )

# 4. Reverse Proxy Routing Logic
@app.api_route("/api/v1/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_request(service: str, path: str, request: Request):
    """Generic reverse proxy forwarding client requests to downstream microservices."""
    if service not in SERVICE_MAPPING:
        logger.warning(f"Routing request failed: Target service '{service}' not recognized.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Downstream service '{service}' not registered in Gateway configurations."
        )

    client_ip = request.client.host if request.client else "unknown"

    # Enforce rate limiting threshold
    if not rate_limiter.check_rate_limit(client_ip):
        # P3 #15: Include Retry-After header on 429 responses
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit threshold exceeded. Too many requests. Please try again later.",
            headers={"Retry-After": "60"}
        )

    # Enforce Auth Brute-Force lockout check on Login requests
    if service == "auth" and path == "login":
        lockout_key = f"lockout:login:{client_ip}"
        if rate_limiter.redis_client:
            try:
                attempts = rate_limiter.redis_client.get(lockout_key)
                if attempts and int(attempts) >= 5:
                    logger.warning(f"Prevented login attempt: Client IP {client_ip} is currently locked out (Redis).")
                    raise HTTPException(
                        status_code=status.HTTP_423_LOCKED,
                        detail="Too many failed login attempts. Your IP has been temporarily locked. Try again in 15 minutes.",
                        headers={"Retry-After": "900"}
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error checking lockout key in Redis: {e}")
        else:
            # InMemory lockout check fallback
            attempts, lock_until = gateway_lockouts.get(client_ip, (0, 0.0))
            if attempts >= 5 and time.time() < lock_until:
                logger.warning(f"Prevented login attempt: Client IP {client_ip} is currently locked out (In-Memory).")
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="Too many failed login attempts. Your IP has been temporarily locked. Try again in 15 minutes.",
                    headers={"Retry-After": "900"}
                )

    # Enforce authentication gate on non-public routes
    is_public = False
    if service == "auth" and path in ["login", "register", "verify", "refresh"]:
        is_public = True

    # Filter out client-specific host headers
    headers = dict(request.headers)
    headers.pop("host", None)

    # P3 #16: Propagate correlation ID to downstream services
    if "x-request-id" not in headers:
        headers["x-request-id"] = str(uuid_lib.uuid4())

    if not is_public:
        auth_header = request.headers.get("Authorization")
        payload = verify_token(auth_header)
        # Propagate verified user identity to downstreams via security headers
        headers["X-User-Id"] = payload.get("sub", "")
        headers["X-User-Role"] = str(payload.get("role_id", ""))

    target_base_url = SERVICE_MAPPING[service]
    
    # Reconstruct target URL retaining paths and query parameters
    url = f"{target_base_url}{request.url.path}"
    query = request.url.query
    if query:
        url = f"{url}?{query}"

    body = await request.body()
    logger.debug(f"Proxying request {request.method} -> {url}")

    try:
        response = await async_client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body
        )
        
        # Audit credentials verification results for brute-force lockouts
        if service == "auth" and path == "login":
            lockout_key = f"lockout:login:{client_ip}"
            if response.status_code == status.HTTP_200_OK:
                # Reset counters on success
                if rate_limiter.redis_client:
                    try:
                        rate_limiter.redis_client.delete(lockout_key)
                    except Exception:
                        pass
                else:
                    gateway_lockouts.pop(client_ip, None)
            elif response.status_code == status.HTTP_401_UNAUTHORIZED:
                # Increment failed counts on bad password/email
                if rate_limiter.redis_client:
                    try:
                        pipe = rate_limiter.redis_client.pipeline()
                        pipe.incr(lockout_key)
                        pipe.expire(lockout_key, 900)  # 15 mins block duration
                        pipe.execute()
                    except Exception as e:
                        logger.error(f"Failed to increment Redis brute-force count: {e}")
                else:
                    attempts, lock_until = gateway_lockouts.get(client_ip, (0, 0.0))
                    attempts += 1
                    # Lock IP for 15 minutes if count >= 5
                    lock_until = time.time() + 900 if attempts >= 5 else 0.0
                    gateway_lockouts[client_ip] = (attempts, lock_until)
                    logger.warning(f"Failed login attempt count for {client_ip}: {attempts}/5")
        
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    except httpx.RequestError as e:
        logger.error(f"Connection timeout/refused forwarding to {url}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Downstream service is currently offline or unreachable."
        )

# 5. WebSocket Real-time Alert Broadcasts
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Accepts and manages client WebSocket connections for real-time dashboard events.
    P0 #4: Requires JWT token via query parameter for authentication.
    """
    # Validate JWT token from query parameter
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing authentication token")
        return
    
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != "access":
            await websocket.close(code=4001, reason="Invalid token type")
            return
    except jwt.ExpiredSignatureError:
        await websocket.close(code=4001, reason="Token expired")
        return
    except jwt.InvalidTokenError:
        await websocket.close(code=4001, reason="Invalid token")
        return

    # Check connection cap
    if not manager.can_accept():
        await websocket.close(code=4002, reason="Maximum connections reached")
        return

    await manager.connect(websocket)
    try:
        while True:
            # Maintain connection alive, listen for potential client closures
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket exception encountered: {e}")
        manager.disconnect(websocket)

# 6. Pydantic Alert Payload
class AlertPublishRequest(BaseModel):
    alert_type: str
    message: dict

@app.post("/api/v1/alerts/publish", status_code=status.HTTP_200_OK, tags=["alerts"])
async def publish_alert(payload: AlertPublishRequest, request: Request):
    """Receives internal alerts from processing services and broadcasts them to all WebSocket clients.
    P0 #3: Protected by internal service API key — not accessible to external clients.
    """
    # Validate internal service-to-service API key
    service_key = request.headers.get("X-Internal-Service-Key")
    if service_key != settings.INTERNAL_SERVICE_KEY:
        logger.warning("Unauthorized alert publish attempt detected.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Internal service authentication failed. Invalid or missing X-Internal-Service-Key."
        )

    event_message = {
        "event_type": payload.alert_type,
        "data": payload.message
    }
    await manager.broadcast(event_message)
    return {"status": "broadcast_completed", "active_clients": len(manager.active_connections)}

@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "healthy", "service": "api-gateway"}
