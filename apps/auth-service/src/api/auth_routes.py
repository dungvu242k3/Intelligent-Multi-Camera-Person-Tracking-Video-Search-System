import logging
import re
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from config.settings import settings
from services.auth_service import AuthService
from services.token_service import TokenService
from models.user import User

logger = logging.getLogger("auth_service.api.auth_routes")
router = APIRouter()

# 1. Local Database setup for auth-service (async connection)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=5,
    pool_pre_ping=True
)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncSession:
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
    full_name: str = Field(..., min_length=1, max_length=100, strip_whitespace=True)

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
    refresh_token: str
    token_type: str = "bearer"

class TokenVerifyRequest(BaseModel):
    token: str

# 3. Router Endpoints
@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticates user credentials and generates access/refresh tokens."""
    user = await AuthService.authenticate_user(db, request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
        
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role_id": user.role_id
    }
    
    access_token = TokenService.create_access_token(payload)
    refresh_token = TokenService.create_refresh_token({"sub": str(user.id)})
    
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Registers a new system user with hashed credentials."""
    # Check if email is already taken
    from sqlalchemy import select
    stmt = select(User).where(User.email == request.email)
    result = await db.execute(stmt)
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
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
        logger.info(f"New user registered: {new_user.email} (ID: {new_user.id})")
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
