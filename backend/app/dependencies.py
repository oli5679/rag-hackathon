import httpx
import logging
from typing import Any
from fastapi import Header, HTTPException

from app.config import settings

logger = logging.getLogger(__name__)

async def verify_token(authorization: str = Header(None)) -> dict[str, Any]:
    """Verify the Supabase access token and return user info."""
    if not authorization:
        logger.warning("Request missing authorization header")
        raise HTTPException(status_code=401, detail="Missing authorization header")

    if not authorization.startswith("Bearer "):
        logger.warning("Invalid authorization format (not Bearer)")
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    token = authorization.replace("Bearer ", "")
    logger.info(f"Verifying token with Supabase at {settings.SUPABASE_URL}")
    logger.debug(f"Token (first 20 chars): {token[:20]}...")

    # Verify token with Supabase
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.SUPABASE_URL}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": settings.SUPABASE_ANON_KEY,
                },
                timeout=10.0
            )
            logger.info(f"Supabase auth response status: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            raise HTTPException(status_code=500, detail="Authentication service unavailable")

    if response.status_code != 200:
        logger.warning(f"Token verification failed: {response.status_code} - {response.text[:200]}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_info = response.json()
    logger.info(f"Token verified successfully for user: {user_info.get('email', 'unknown')}")
    return user_info
