"""FastAPI dependencies — current-user extraction and role enforcement."""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import decode_access_token
from app.db.models import Farmer, Role
from app.db.postgres import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Farmer:
    """Extract and validate the current user from the Bearer token."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        raw_id = payload.get("sub")
        if raw_id is None:
            raise credentials_exc
        user_id = uuid.UUID(raw_id)
    except (JWTError, ValueError):
        raise credentials_exc

    result = await db.execute(select(Farmer).where(Farmer.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exc
    return user


def require_role(*roles: Role):
    """Return a dependency that enforces one or more allowed roles.

    Usage:
        @router.get("/admin", dependencies=[Depends(require_role(Role.EXTENSION_OFFICER))])
    Or:
        current_user: Farmer = Depends(require_role(Role.FARMER, Role.SHOP_OWNER))
    """

    async def _role_checker(
        current_user: Farmer = Depends(get_current_user),
    ) -> Farmer:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {', '.join(r.value for r in roles)}",
            )
        return current_user

    return _role_checker
