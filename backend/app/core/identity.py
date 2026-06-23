from __future__ import annotations

from typing import Optional
from uuid import UUID, uuid4

from fastapi import Request, Response

from app.core.config import Settings

ANONYMOUS_HEADER = "X-Anonymous-Id"


def _is_valid_uuid(value: Optional[str]) -> bool:
    if not value:
        return False
    try:
        UUID(value)
        return True
    except ValueError:
        return False


def _set_identity_cookie(response: Response, settings: Settings, user_id: str) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=user_id,
        max_age=settings.session_cookie_max_age_seconds,
        httponly=False,
        secure=settings.session_cookie_secure,
        samesite="lax",
    )


def resolve_or_create_user_id(request: Request, response: Response, settings: Settings) -> str:
    cookie_value = request.cookies.get(settings.session_cookie_name)
    header_value = request.headers.get(ANONYMOUS_HEADER)

    if _is_valid_uuid(cookie_value):
        return str(cookie_value)
    if _is_valid_uuid(header_value):
        user_id = str(header_value)
        _set_identity_cookie(response, settings, user_id)
        return user_id

    user_id = str(uuid4())
    _set_identity_cookie(response, settings, user_id)
    return user_id
