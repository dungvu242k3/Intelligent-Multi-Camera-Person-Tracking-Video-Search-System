import logging
import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Response, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
import httpx
from pydantic import BaseModel

# Setup path to import packages correctly in monorepo
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from config.settings import settings
from websocket.manager import manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("gateway")

# Persistent async HTTP client pool
async_client: Optional[httpx.AsyncClient] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event manager mapping startup/shutdown states."""
    global async_client
    logger.info("Initializing API Gateway routing clients...")
    async_client = httpx.AsyncClient(timeout=15.0)
    
    yield
    
    logger.info("Shutting down API Gateway clients...")
    if async_client:
        await async_client.aclose()

app = FastAPI(
    title="Intelligent MCPT — API Gateway",
    description="Single entry point routing traffic and broadcasting WebSocket alert notifications.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for React Frontend dashboard integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service mapping routing keys
SERVICE_MAPPING = {
    "auth": settings.AUTH_SERVICE_URL,
    "cameras": settings.CAMERA_SERVICE_URL,
    "search": settings.SEARCH_SERVICE_URL,
    "analytics": settings.ANALYTICS_SERVICE_URL,
}

# 1. Reverse Proxy Routing Logic
@app.api_route("/api/v1/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_request(service: str, path: str, request: Request):
    """Generic reverse proxy forwarding client requests to downstream microservices."""
    if service not in SERVICE_MAPPING:
        logger.warning(f"Routing request failed: Target service '{service}' not recognized.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Downstream service '{service}' not registered in Gateway configurations."
        )

    target_base_url = SERVICE_MAPPING[service]
    
    # Reconstruct target URL retaining paths and query parameters
    url = f"{target_base_url}{request.url.path}"
    query = request.url.query
    if query:
        url = f"{url}?{query}"

    # Filter out client-specific host headers
    headers = dict(request.headers)
    headers.pop("host", None)
    
    body = await request.body()
    logger.debug(f"Proxying request {request.method} -> {url}")

    try:
        response = await async_client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body
        )
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

# 2. WebSocket Real-time Alert Broadcasts
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Accepts and manages client WebSocket connections for real-time dashboard events."""
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

# 3. Pydantic Alert Payload
class AlertPublishRequest(BaseModel):
    alert_type: str
    message: dict

@app.post("/api/v1/alerts/publish", status_code=status.HTTP_200_OK, tags=["alerts"])
async def publish_alert(payload: AlertPublishRequest):
    """Receives internal alerts from processing services and broadcasts them to all WebSocket clients."""
    event_message = {
        "event_type": payload.alert_type,
        "data": payload.message
    }
    await manager.broadcast(event_message)
    return {"status": "broadcast_completed", "active_clients": len(manager.active_connections)}

@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "healthy", "service": "api-gateway"}
