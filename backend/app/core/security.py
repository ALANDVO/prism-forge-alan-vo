from dataclasses import dataclass
from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db_session
from app.models.agent import Agent  # For user model reference


@dataclass
class User:
    """Authenticated user."""
    id: str
    email: str
    name: str
    roles: list[str]
    is_demo: bool = False


class DemoUser(User):
    """Demo mode user for local development."""
    def __init__(self):
        super().__init__(
            id="demo-user",
            email="demo@localhost",
            name="Demo User",
            roles=["operator", "admin"],
            is_demo=True,
        )


# Demo user singleton
_demo_user = DemoUser()


security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Get current authenticated user.
    - In demo mode: returns a demo user without validation
    - In production: validates OIDC token (stub for now)
    """
    settings = get_settings()

    # Demo mode: bypass auth for local development
    if settings.is_demo_allowed:
        # Check if request is from localhost
        client_host = request.client.host if request.client else "unknown"
        if client_host in ("127.0.0.1", "localhost", "::1"):
            return _demo_user
        else:
            # Demo mode only allowed on localhost
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Demo mode only allowed on localhost",
            )

    # Production mode: require valid OIDC token
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # OIDC validation not implemented - requires Keycloak setup
    # Production deployments must configure OIDC credentials
    if settings.is_production:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="OIDC authentication requires Keycloak configuration",
        )

    # Fallback for development with token (not demo mode)
    return User(
        id="dev-user",
        email="dev@localhost",
        name="Dev User",
        roles=["operator"],
        is_demo=False,
    )


def require_role(*required_roles: str):
    """Dependency factory for role-based access control."""
    async def role_checker(user: User = Depends(get_current_user)) -> User:
        if not any(role in user.roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(required_roles)}",
            )
        return user
    return role_checker