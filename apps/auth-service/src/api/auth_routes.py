import logging
import re
from typing import AsyncGenerator, Optional
from fastapi import APIRouter, Body, Cookie, Depends, HTTPException, Response, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from config.settings import settings
from services.auth_service import AuthService, AuthenticationBackendUnavailable
from services.token_service import TokenService
from models.user import User

logger = logging.getLogger("auth_service.api.auth_routes")
router = APIRouter()
MAX_TOKEN_LENGTH = 4096

# 1. Local Database setup for auth-service (async connection)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT_SECONDS,
    pool_recycle=settings.DB_POOL_RECYCLE_SECONDS,
    pool_pre_ping=True,
)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency provider yielding SQLAlchemy async database session handles."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# 2. Pydantic v2 I/O Schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=100)

    @field_validator("full_name")
    @classmethod
    def strip_full_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Full name cannot be blank")
        return stripped

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Enforces minimum password complexity: 1 uppercase, 1 lowercase, 1 digit."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: Optional[str] = Field(default=None, max_length=MAX_TOKEN_LENGTH)

class TokenVerifyRequest(BaseModel):
    token: str = Field(..., min_length=1, max_length=MAX_TOKEN_LENGTH)

def set_refresh_token_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key="mcpt_refresh_token",
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=settings.ENV == "production",
        samesite="lax",
        path="/api/v1/auth",
    )

# 3. Router Endpoints
@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    """Authenticates user credentials and generates access/refresh tokens."""
    try:
        user = await AuthService.authenticate_user(db, request.email, request.password)
    except AuthenticationBackendUnavailable:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication backend is temporarily unavailable"
        )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
        
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role_id": user.role_id,
        "full_name": user.full_name,
    }
    
    access_token = TokenService.create_access_token(payload)
    refresh_token = TokenService.create_refresh_token({"sub": str(user.id)})
    set_refresh_token_cookie(response, refresh_token)
    
    return TokenResponse(access_token=access_token)

@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_token(
    response: Response,
    request: RefreshRequest = Body(default_factory=RefreshRequest),
    mcpt_refresh_token: Optional[str] = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Rotates a valid refresh token and returns a fresh access token."""
    token = mcpt_refresh_token or request.refresh_token
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token"
        )
    if len(token) > MAX_TOKEN_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is too large"
        )

    payload = TokenService.decode_and_verify_token(token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid or has expired"
        )

    stmt = select(User).where(User.id == payload.get("sub"), User.is_active)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token subject is no longer active"
        )

    access_payload = {
        "sub": str(user.id),
        "email": user.email,
        "role_id": user.role_id,
        "full_name": user.full_name,
    }
    access_token = TokenService.create_access_token(access_payload)
    rotated_refresh_token = TokenService.create_refresh_token({"sub": str(user.id)})
    set_refresh_token_cookie(response, rotated_refresh_token)

    return AccessTokenResponse(access_token=access_token)

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Registers a new system user with hashed credentials."""
    # Check if email is already taken
    stmt = select(User).where(User.email == request.email)
    result = await db.execute(stmt)
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email address already registered"
        )
        
    hashed_pwd = AuthService.hash_password(request.password)
    new_user = User(
        email=request.email,
        hashed_password=hashed_pwd,
        full_name=request.full_name,
        role_id=2  # Hardcoded: standard user. Only admins can promote via separate endpoint.
    )
    
    db.add(new_user)
    try:
        await db.commit()
        await db.refresh(new_user)
        logger.info("New user registered.", extra={"user_id": str(new_user.id)})
        return {"status": "success", "user_id": str(new_user.id)}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error occurred during registration database commit: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user due to database error"
        )

@router.post("/verify")
async def verify_token(request: TokenVerifyRequest):
    """Verifies a JWT token's signature, expiry, and returns the payload details."""
    payload = TokenService.decode_and_verify_token(request.token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or has expired"
        )
    # Check for token type confusion (ensure it's not a refresh token)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type: Access token expected"
        )
    return {"status": "valid", "payload": payload}
