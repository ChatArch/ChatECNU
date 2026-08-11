"""ECNU portal session adapter for ChatEnv's generic token store."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from chatenv import EnvStore, TokenRefreshResult, TokenStore, get_paths
from chatenv.tokens import normalize_token_profile

from chatecnu.config import ECNUConfig

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


def _load_refresh_profile_values(
    profile: str | None,
    *,
    home: str | Path | None = None,
    env_store: EnvStore | None = None,
) -> tuple[str, dict[str, str]]:
    profile_name = normalize_token_profile(profile)
    store = env_store or EnvStore(get_paths(home).envs_dir)
    try:
        profile_path = (
            store.active_path(ECNUConfig)
            if profile_name == "default"
            else store.profile_path(ECNUConfig, profile_name)
        )
    except ValueError as exc:
        raise ValueError(f"ECNU ChatEnv profile not found or invalid: {profile_name}") from exc
    if not profile_path.exists():
        raise ValueError(f"ECNU ChatEnv profile not found or invalid: {profile_name}")
    try:
        values = store.load_active(ECNUConfig) if profile_name == "default" else store.load_profile(ECNUConfig, profile_name)
    except ValueError as exc:
        raise ValueError(f"ECNU ChatEnv profile not found or invalid: {profile_name}") from exc
    return profile_name, {str(key): str(value) for key, value in values.items() if value is not None}


def _refresh_portal_client_class():
    from .portal import PortalClient

    return PortalClient


def _default_base_url() -> str:
    from .portal import BASE_URL

    return BASE_URL


def refresh_chatenv_token(
    *,
    service: str,
    profile: str,
    home: str | Path | None = None,
    env_store: EnvStore | None = None,
    token_store: TokenStore | None = None,
) -> TokenRefreshResult:
    """Refresh an ECNU portal session for ChatEnv's provider lifecycle.

    The ECNU portal requires captcha OCR and can require SMS. This provider is
    intentionally non-interactive: it runs the existing best-effort auto-login
    path from a matching stable ChatEnv profile and fails closed if the portal
    asks for SMS or rejects all captcha candidates. ChatEnv owns persistence
    after this function returns, so the provider itself never writes the
    token-store record.
    """

    del token_store  # ChatEnv persists the returned TokenRefreshResult.
    if service != ECNU_SESSION_SERVICE:
        raise ValueError(f"ChatECNU can refresh only {ECNU_SESSION_SERVICE} tokens")
    profile_name, values = _load_refresh_profile_values(profile, home=home, env_store=env_store)
    for key in ["ECNU_USERNAME", "ECNU_PASSWORD"]:
        if not values.get(key):
            raise ValueError(f"ECNU ChatEnv profile {profile_name} is missing {key}")

    base_url = (values.get("ECNU_BASE_URL") or _default_base_url()).rstrip("/")
    with TemporaryDirectory(prefix=f"chatecnu-refresh-{profile_name}-") as tmpdir:
        tmp = Path(tmpdir)
        client = _refresh_portal_client_class()(
            base_url=base_url,
            state_file=tmp / "ecnu-session.json",
            cookie_header=None,
            timeout=20,
            token_store=None,
            token_profile=profile_name,
        )
        result = client.login_auto(
            values["ECNU_USERNAME"],
            values["ECNU_PASSWORD"],
            sms_code=None,
            rounds=3,
            topk=5,
            captcha_path=tmp / "ecnu-login-captcha.png",
        )
        state = dict(getattr(client, "state", {}) or {})

    if result.get("requires_sms"):
        raise ValueError("ECNU portal refresh requires SMS verification and cannot run non-interactively")
    if not result.get("success"):
        raise ValueError("ECNU portal automatic refresh failed")
    cookies = state.get("cookies")
    if not isinstance(cookies, dict) or not cookies:
        raise ValueError("ECNU portal refresh completed without cookies")
    state.setdefault("base_url", base_url)
    state.setdefault("username", values["ECNU_USERNAME"])
    return TokenRefreshResult(
        values=state,
        token_type=ECNU_PORTAL_TOKEN_TYPE,
        summary=portal_session_summary(state),
    )


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
    "refresh_chatenv_token",
    "save_portal_session_state",
]
