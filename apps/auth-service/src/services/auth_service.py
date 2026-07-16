import logging
from typing import Optional
import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User

logger = logging.getLogger("auth_service.auth_service")

class AuthService:
    """Handles password hashing, password validation, and database credential checks."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hashes a plain-text password using bcrypt with a secure salt.
        
        Args:
            password: The plain-text password to hash.
            
        Returns:
            The hashed password string.
        """
        salt = bcrypt.gensalt(rounds=12) # Production-standard salt strength
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifies a plain-text password against a stored bcrypt hash.
        
        Args:
            plain_password: The user-supplied plain-text password.
            hashed_password: The stored hashed password from the database.
            
        Returns:
            True if the password matches, False otherwise.
        """
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception as e:
            logger.error(f"Error during password verification check: {e}")
            return False

    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
        """Queries the database and validates the user credentials.
        
        Args:
            db: The async SQLAlchemy database session.
            email: The login email address.
            password: The login plain-text password.
            
        Returns:
            The User instance if authenticated successfully, otherwise None.
        """
        try:
            # Query user by email address
            stmt = select(User).where(User.email == email, User.is_active == True)
            result = await db.execute(stmt)
            user = result.scalars().first()
            
            if not user:
                logger.info(f"Authentication attempt failed: User with email '{email}' not found.")
                return None
                
            # Verify password match
            if not AuthService.verify_password(password, user.hashed_password):
                logger.info(f"Authentication attempt failed: Password mismatch for email '{email}'.")
                return None
                
            logger.info(f"User '{email}' authenticated successfully.")
            return user
        except Exception as e:
            logger.error(f"Database query error during user authentication: {e}", exc_info=True)
            return None
