import os
from dataclasses import dataclass
from enum import IntEnum
from typing import Callable, Iterable

from fastapi import Header, HTTPException, status


class Role(IntEnum):
    ADMIN = 1
    OPERATOR = 2


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str
    role: Role


def get_internal_service_key() -> str:
    key = os.getenv("INTERNAL_SERVICE_KEY", "")
    if not key and os.getenv("ENV", "development").lower() != "production":
        return "local-development-only-internal-service-key-32-bytes"
    return key


def require_internal_user(
    allowed_roles: Iterable[Role],
    x_internal_service_key: str = Header(default="", alias="X-Internal-Service-Key"),
    x_user_id: str = Header(default="", alias="X-User-Id"),
    x_user_role: str = Header(default="", alias="X-User-Role"),
) -> AuthenticatedUser:
    expected_key = get_internal_service_key()
    if not expected_key or x_internal_service_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Internal service authentication failed",
        )

    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authenticated user context",
        )

    try:
        role = Role(int(x_user_role))
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid user role",
        )

    allowed = set(allowed_roles)
    if role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    return AuthenticatedUser(user_id=x_user_id, role=role)


def require_roles(*allowed_roles: Role) -> Callable[..., AuthenticatedUser]:
    def dependency(
        x_internal_service_key: str = Header(default="", alias="X-Internal-Service-Key"),
        x_user_id: str = Header(default="", alias="X-User-Id"),
        x_user_role: str = Header(default="", alias="X-User-Role"),
    ) -> AuthenticatedUser:
        return require_internal_user(
            allowed_roles=allowed_roles,
            x_internal_service_key=x_internal_service_key,
            x_user_id=x_user_id,
            x_user_role=x_user_role,
        )

    return dependency
