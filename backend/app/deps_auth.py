"""Optional API key and/or JWT for protected routes (Phase 7)."""
from __future__ import annotations

import os

import jwt
from fastapi import Header, HTTPException, Request


def _unauthorized(request: Request) -> None:
    rid = getattr(request.state, "request_id", None)
    raise HTTPException(
        status_code=401,
        detail={
            "error": "unauthorized",
            "message": "Invalid or missing credentials. Use X-API-Key, Bearer application API key, or Bearer JWT when auth is enabled.",
            "request_id": rid,
        },
    )


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    return authorization[7:].strip()


def _jwt_valid(token: str, secret: str) -> bool:
    try:
        jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"require": ["exp", "sub"]},
        )
        return True
    except jwt.PyJWTError:
        return False


async def require_api_key_if_configured(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    authorization: str | None = Header(default=None),
) -> None:
    expected_key = os.getenv("DOC2ACTION_API_KEY", "").strip()
    jwt_secret = os.getenv("DOC2ACTION_JWT_SECRET", "").strip()
    if not expected_key and not jwt_secret:
        return

    if expected_key and x_api_key and x_api_key.strip() == expected_key:
        return

    token = _bearer_token(authorization)
    if token:
        if expected_key and token == expected_key:
            return
        if jwt_secret and _jwt_valid(token, jwt_secret):
            return

    _unauthorized(request)


def get_optional_user_sub(
    authorization: str | None = Header(default=None),
) -> str | None:
    """JWT `sub` when Authorization bears a valid HS256 token; else None (API key Bearer ignored)."""
    jwt_secret = os.getenv("DOC2ACTION_JWT_SECRET", "").strip()
    if not jwt_secret or not authorization:
        return None
    token = _bearer_token(authorization)
    if not token:
        return None
    expected_key = os.getenv("DOC2ACTION_API_KEY", "").strip()
    if expected_key and token == expected_key:
        return None
    try:
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            options={"require": ["exp", "sub"]},
        )
        return str(payload.get("sub", "")) or None
    except jwt.PyJWTError:
        return None
