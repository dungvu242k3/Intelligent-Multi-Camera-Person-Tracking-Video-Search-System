import logging
from typing import Optional
import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User

logger = logging.getLogger("auth_service.auth_service")

class AuthenticationBackendUnavailable(Exception):
    """Raised when credential verification cannot reach its backing datastore."""

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
            stmt = select(User).where(User.email == email, User.is_active)
            result = await db.execute(stmt)
            user = result.scalars().first()
            
            if not user:
                # Perform a dummy bcrypt hash check to mitigate timing side-channel attacks
                dummy_hash = "$2b$12$L9cyqFUpysenWtJrxnlYEuyjAeBFlv1nRYRoxc1s3fXq8o1ZwsPPW"
                bcrypt.checkpw(password.encode("utf-8"), dummy_hash.encode("utf-8"))
                logger.info("Authentication attempt failed: active user not found.")
                return None
                
            # Verify password match
            if not AuthService.verify_password(password, str(user.hashed_password)):
                logger.info("Authentication attempt failed: password mismatch.")
                return None
                
            logger.info("User authenticated successfully.", extra={"user_id": str(user.id)})
            return user
        except Exception as e:
            logger.error(f"Database query error during user authentication: {e}", exc_info=True)
            raise AuthenticationBackendUnavailable from e
