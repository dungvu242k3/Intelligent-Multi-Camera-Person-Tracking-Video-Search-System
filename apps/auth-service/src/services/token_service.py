import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import jwt
from config.settings import settings

logger = logging.getLogger("auth_service.token_service")

class TokenService:
    """Manages the generation, signing, and verification of JSON Web Tokens (JWT)."""

    @staticmethod
    def create_access_token(payload: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Generates a signed JWT Access Token.
        
        Args:
            payload: Data fields to include in the token payload.
            expires_delta: Optional duration for token expiry. If omitted, uses default config.
            
        Returns:
            The signed JWT token string.
        """
        to_encode = payload.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            
        to_encode.update({"exp": expire, "type": "access"})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.JWT_SECRET_KEY, 
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def create_refresh_token(payload: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Generates a signed JWT Refresh Token.
        
        Args:
            payload: Data fields to include in the token payload.
            expires_delta: Optional duration for token expiry. If omitted, uses default config.
            
        Returns:
            The signed JWT token string.
        """
        to_encode = payload.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            
        to_encode.update({"exp": expire, "type": "refresh"})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.JWT_SECRET_KEY, 
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def decode_and_verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Decodes and validates a JWT token's signature and expiration status.
        
        Args:
            token: The signed JWT token string.
            
        Returns:
            The decoded token payload dict if valid, or None if expired/invalid.
        """
        try:
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token verification failed: Signature has expired.")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token verification failed: Token is invalid. Error: {e}")
            return None
