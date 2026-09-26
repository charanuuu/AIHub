import re
from dataclasses import dataclass
from typing import Optional
from fastapi import Header, HTTPException, Request, status
from app.core.config import settings
from app.core.logging import logger

# Safe identifier pattern for session tokens/IDs (alphanumeric, hyphens, underscores, dots)
SESSION_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-\.]{3,128}$")


@dataclass
class AuthenticatedUser:
    user_id: str
    auth_type: str
    is_authenticated: bool = True


async def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> AuthenticatedUser:
    """
    Authenticate and extract user/session identity from request headers.
    Supports:
    1. X-Session-ID: Client-managed session UUID for isolated device/user chats
    2. Authorization: Bearer <token> (JWT or API token)
    3. X-API-Key: Server-to-server or pre-shared key
    4. Development fallback: Enabled only when ENVIRONMENT != 'production' and REQUIRE_AUTH is False.
    """
    # 1. Check X-Session-ID header
    if x_session_id and x_session_id.strip():
        clean_session = x_session_id.strip()
        if not SESSION_ID_PATTERN.match(clean_session):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid X-Session-ID format. Must be 3-128 alphanumeric characters, hyphens, or underscores.",
            )
        return AuthenticatedUser(user_id=clean_session, auth_type="session")

    # 2. Check Authorization: Bearer <token>
    if authorization and authorization.strip():
        parts = authorization.strip().split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Authorization header format. Expected 'Bearer <token>'",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = parts[1].strip()
        if not token or len(token) < 4:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid bearer token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # If client secret is configured, validate against it
        if settings.APP_CLIENT_SECRET and token != settings.APP_CLIENT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or unauthorized token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return AuthenticatedUser(user_id=f"bearer_{token[:16]}", auth_type="bearer")

    # 3. Check X-API-Key
    if x_api_key and x_api_key.strip():
        clean_key = x_api_key.strip()
        if settings.API_KEYS and clean_key not in settings.API_KEYS:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid X-API-Key",
            )
        return AuthenticatedUser(user_id=f"key_{clean_key[:12]}", auth_type="api_key")

    # 4. Check if authentication is strictly enforced
    enforce = settings.is_auth_enforced or request.headers.get("X-Enforce-Auth") == "true"
    if enforce:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Authorization or X-Session-ID header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 5. Non-production development fallback
    logger.debug("Request without auth headers; using development default session.")
    return AuthenticatedUser(user_id="dev-default-user", auth_type="dev_default")


def apply_security_headers(response):
    """Adds standard production security headers to HTTP responses."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none';"
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
