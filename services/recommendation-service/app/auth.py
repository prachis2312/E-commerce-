import os
import hmac
from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError  # swap to `import jwt` if your project uses PyJWT instead

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

bearer_scheme = HTTPBearer()
optional_bearer = HTTPBearer(auto_error=False)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    """Decodes and verifies the JWT, returning its claims."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Ensures the authenticated user has admin privileges."""
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


def require_admin_or_internal(
    x_internal_key: Optional[str] = Header(None),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer),
) -> dict:
    """
    Allows EITHER a trusted service (valid x-internal-key, e.g. product-service
    telling us a product changed) OR a logged-in admin (JWT with is_admin).
    """
    internal_key = os.getenv("INTERNAL_API_KEY")
    if x_internal_key and internal_key and hmac.compare_digest(x_internal_key, internal_key):
        return {"internal": True}

    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user = get_current_user(credentials)
    if not user.get("is_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return user
