import os
import sys
import logging
from fastapi import FastAPI
from fastapi import Request
from contextlib import asynccontextmanager

# Setup path to import packages correctly in monorepo
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from sqlalchemy import text
from api.auth_routes import router as auth_router, engine, AsyncSessionLocal
from config.settings import settings as auth_settings
from packages.shared.api_errors import register_exception_handlers

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("auth_service")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event context manager for handling startup and database shutdown."""
    logger.info("Starting up Auth Service...")
    
    # Wait for database readiness before starting
    from packages.shared.db_startup import wait_for_db
    await wait_for_db(auth_settings.DATABASE_URL)
    
    yield
    logger.info("Shutting down Auth Service...")
    await engine.dispose()
    logger.info("Auth service database engine disposed.")

_is_prod = auth_settings.ENV == "production"

app = FastAPI(
    title="Intelligent MCPT — Auth Service",
    description="Manages user credential registrations, logins, and token validation checks.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if _is_prod else "/docs",
    redoc_url=None if _is_prod else "/redoc",
)
register_exception_handlers(app, auth_settings.SERVICE_NAME)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Register endpoints
app.include_router(auth_router, prefix="/api/v1/auth")

@app.get("/health", tags=["system"])
async def health_check():
    """P3 #17: Verifies database connectivity for readiness probes."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "healthy", "service": "auth-service", "db": "connected"}
    except Exception:
        return {"status": "degraded", "service": "auth-service", "db": "disconnected"}

@app.get("/metrics", tags=["system"])
async def metrics():
    return {"message": "Metrics placeholder for auth-service"}
