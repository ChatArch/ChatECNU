"""ECNU portal session adapter for ChatEnv's generic token store."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from chatenv import TokenStore
from chatenv.tokens import normalize_token_profile

ECNU_SESSION_SERVICE = "ECNU"
ECNU_PORTAL_TOKEN_TYPE = "portal_session"


def portal_session_profile(env_profile: str | None = None) -> str:
    """Return the token-store profile paired with the selected ChatEnv profile."""

    return normalize_token_profile(env_profile)


def portal_session_summary(state: dict[str, Any]) -> dict[str, Any]:
    """Return safe metadata for a stored ECNU portal session."""

    cookies = state.get("cookies") if isinstance(state, dict) else {}
    cookie_count = len(cookies) if isinstance(cookies, dict) else 0
    login_bootstrap = state.get("login_bootstrap") if isinstance(state, dict) else None
    return {
        "base_url": state.get("base_url") or "",
        "username": state.get("username") or "",
        "authenticated_at": state.get("authenticated_at") or "",
        "cookie_count": cookie_count,
        "has_login_bootstrap": isinstance(login_bootstrap, dict) and bool(login_bootstrap),
    }


def _store(token_store: TokenStore | None = None, *, home: str | Path | None = None) -> TokenStore:
    return token_store or TokenStore(home=home)


def save_portal_session_state(
    state: dict[str, Any],
    *,
    env_profile: str | None = None,
    token_store: TokenStore | None = None,
    home: str | Path | None = None,
    source: str = "refresh",
) -> dict[str, Any]:
    """Persist opaque ECNU portal runtime state in ChatEnv's token store."""

    values = dict(state)
    return _store(token_store, home=home).write(
        ECNU_SESSION_SERVICE,
        portal_session_profile(env_profile),
        values=values,
        token_type=ECNU_PORTAL_TOKEN_TYPE,
        summary=portal_session_summary(values),
        source=source,
    )


def load_portal_session_state(
    *,
    env_profile: str | None = None,
    token_store: TokenStore | None = None,
    home: str | Path | None = None,
) -> dict[str, Any]:
    """Load opaque ECNU portal runtime state from ChatEnv's token store."""

    payload = _store(token_store, home=home).read(ECNU_SESSION_SERVICE, portal_session_profile(env_profile))
    values = payload.get("values") if isinstance(payload, dict) else None
    return dict(values) if isinstance(values, dict) else {}


def portal_session_status(
    *,
    env_profile: str | None = None,
    token_store: TokenStore | None = None,
    home: str | Path | None = None,
) -> dict[str, Any]:
    """Return safe token-store metadata for the ECNU portal session."""

    status = _store(token_store, home=home).status(ECNU_SESSION_SERVICE, portal_session_profile(env_profile))
    if not status.get("token_file_exists"):
        status["token_type"] = ECNU_PORTAL_TOKEN_TYPE
    return status


__all__ = [
    "ECNU_PORTAL_TOKEN_TYPE",
    "ECNU_SESSION_SERVICE",
    "load_portal_session_state",
    "portal_session_profile",
    "portal_session_status",
    "portal_session_summary",
    "save_portal_session_state",
]
