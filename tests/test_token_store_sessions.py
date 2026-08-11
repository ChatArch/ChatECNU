import json

import pytest
from click.testing import CliRunner
from chatenv import EnvStore, TokenRefreshResult, TokenStore
import chatenv.token_refreshers as chatenv_refreshers
from chatenv.token_refreshers import refresh_token

from chatecnu.cli import main
from chatecnu.config import ECNUConfig


def test_ecnu_config_does_not_persist_portal_cookie_in_stable_env_schema():
    assert not hasattr(ECNUConfig, "ECNU_COOKIE")


def test_portal_session_state_roundtrips_through_chatenv_token_store(tmp_path):
    from chatecnu.ecnu.session_tokens import (
        ECNU_PORTAL_TOKEN_TYPE,
        load_portal_session_state,
        portal_session_status,
        save_portal_session_state,
    )

    store = TokenStore(tokens_dir=tmp_path / "tokens")
    state = {
        "base_url": "https://login.ecnu.edu.cn:8800",
        "username": "student001",
        "authenticated_at": "2026-08-11T12:34:56",
        "cookies": {"PHPSESSID_8800": "secret-cookie"},
        "login_bootstrap": {"csrf_param": "_csrf-8800", "csrf_token": "secret-csrf"},
    }

    written = save_portal_session_state(
        state,
        env_profile="RexWzh",
        token_store=store,
        source="login",
    )

    assert written["service"] == "ECNU"
    assert written["profile"] == "RexWzh"
    assert written["token_type"] == ECNU_PORTAL_TOKEN_TYPE
    assert written["token_present"] is True
    assert written["summary"] == {
        "base_url": "https://login.ecnu.edu.cn:8800",
        "username": "student001",
        "authenticated_at": "2026-08-11T12:34:56",
        "cookie_count": 1,
        "has_login_bootstrap": True,
    }
    assert "secret-cookie" not in json.dumps(written)
    assert "secret-csrf" not in json.dumps(written)

    assert load_portal_session_state(env_profile="RexWzh", token_store=store) == state
    status = portal_session_status(env_profile="RexWzh", token_store=store)
    assert status["token_file"].endswith("tokens/ECNU/RexWzh.json")
    assert status["summary"]["cookie_count"] == 1


def test_home_status_reads_profile_token_store_and_redacts_session_values(tmp_path, monkeypatch):
    chatarch_home = tmp_path / "chatarch"
    monkeypatch.setenv("CHATARCH_HOME", str(chatarch_home))
    env_file = chatarch_home / "envs" / "ECNU" / "RexWzh.env"
    env_file.parent.mkdir(parents=True)
    env_file.write_text("ECNU_BASE_URL='https://login.ecnu.edu.cn:8800'\n", encoding="utf-8")
    TokenStore(home=chatarch_home).write(
        "ECNU",
        "RexWzh",
        values={
            "base_url": "https://login.ecnu.edu.cn:8800",
            "username": "student001",
            "authenticated_at": "2026-08-11T12:34:56",
            "cookies": {"PHPSESSID_8800": "secret-cookie"},
            "login_bootstrap": {"csrf_param": "_csrf-8800", "csrf_token": "secret-csrf"},
        },
        token_type="portal_session",
        summary={
            "base_url": "https://login.ecnu.edu.cn:8800",
            "username": "student001",
            "authenticated_at": "2026-08-11T12:34:56",
            "cookie_count": 1,
            "has_login_bootstrap": True,
        },
        source="test",
    )

    result = CliRunner().invoke(main, ["-e", "RexWzh", "home", "status", "--json"])

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["username"] == "student001"
    assert data["cookies"] == {"PHPSESSID_8800": "***"}
    assert data["token_profile"] == "RexWzh"
    assert data["token_type"] == "portal_session"
    assert data["token_file"].endswith("tokens/ECNU/RexWzh.json")
    assert "secret-cookie" not in result.output
    assert "secret-csrf" not in result.output


def test_cookie_header_command_is_disabled_instead_of_printing_raw_cookie(tmp_path):
    state_file = tmp_path / "legacy-session.json"
    state_file.write_text(
        json.dumps({"cookies": {"PHPSESSID_8800": "secret-cookie"}}),
        encoding="utf-8",
    )

    result = CliRunner().invoke(main, ["--state-file", str(state_file), "home", "cookie-header"])

    assert result.exit_code != 0
    assert "secret-cookie" not in result.output
    assert "disabled" in result.output.lower()


def _save_ecnu_profile(env_store: EnvStore, name: str = "RexWzh") -> None:
    env_store.save_profile(
        ECNUConfig,
        name,
        {
            "ECNU_BASE_URL": "https://login.ecnu.edu.cn:8800",
            "ECNU_USERNAME": "student001",
            "ECNU_PASSWORD": "secret-password-fixture",
        },
    )


def _save_active_ecnu_profile(env_store: EnvStore) -> None:
    env_store.save_active(
        ECNUConfig,
        {
            "ECNU_BASE_URL": "https://login.ecnu.edu.cn:8800",
            "ECNU_USERNAME": "active-student",
            "ECNU_PASSWORD": "active-secret-password-fixture",
        },
    )


def test_refresh_chatenv_token_uses_matching_stable_profile_without_writing_store(tmp_path, monkeypatch):
    from chatecnu.ecnu import session_tokens

    home = tmp_path / "chatarch"
    env_store = EnvStore(home / "envs")
    _save_ecnu_profile(env_store)
    captured: dict[str, object] = {}

    class FakePortalClient:
        def __init__(self, *, base_url, state_file, cookie_header=None, timeout=20, token_store=None, token_profile=None):
            captured.update(
                {
                    "base_url": base_url,
                    "state_file": str(state_file),
                    "cookie_header": cookie_header,
                    "timeout": timeout,
                    "token_store": token_store,
                    "token_profile": token_profile,
                }
            )
            self.state: dict[str, object] = {}

        def login_auto(self, username, password, sms_code, rounds, topk, captcha_path):
            captured.update(
                {
                    "username": username,
                    "password": password,
                    "sms_code": sms_code,
                    "rounds": rounds,
                    "topk": topk,
                    "captcha_path": str(captcha_path),
                }
            )
            self.state = {
                "base_url": "https://login.ecnu.edu.cn:8800",
                "username": username,
                "authenticated_at": "2026-08-11T12:34:56",
                "cookies": {"PHPSESSID_8800": "secret-cookie"},
                "login_bootstrap": {"csrf_param": "_csrf-8800", "csrf_token": "secret-csrf"},
            }
            return {"success": True, "requires_sms": False}

    monkeypatch.setattr(session_tokens, "_refresh_portal_client_class", lambda: FakePortalClient)

    result = session_tokens.refresh_chatenv_token(
        service="ECNU",
        profile="RexWzh",
        home=home,
        env_store=env_store,
    )

    assert result.token_type == "portal_session"
    assert result.values["cookies"] == {"PHPSESSID_8800": "secret-cookie"}
    assert result.summary == {
        "base_url": "https://login.ecnu.edu.cn:8800",
        "username": "student001",
        "authenticated_at": "2026-08-11T12:34:56",
        "cookie_count": 1,
        "has_login_bootstrap": True,
    }
    assert "secret-cookie" not in json.dumps(result.summary)
    assert "secret-csrf" not in json.dumps(result.summary)
    assert captured["token_store"] is None
    assert captured["token_profile"] == "RexWzh"
    assert captured["password"] == "secret-password-fixture"
    assert captured["rounds"] == 3
    assert captured["topk"] == 5
    assert not TokenStore(home=home).token_path("ECNU", "RexWzh").exists()


def test_refresh_chatenv_token_default_uses_active_env_profile(tmp_path, monkeypatch):
    from chatecnu.ecnu import session_tokens

    home = tmp_path / "chatarch"
    env_store = EnvStore(home / "envs")
    _save_active_ecnu_profile(env_store)
    captured: dict[str, object] = {}

    class ActivePortalClient:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.state: dict[str, object] = {}

        def login_auto(self, username, password, sms_code, rounds, topk, captcha_path):
            captured.update({"username": username, "password": password})
            self.state = {
                "base_url": "https://login.ecnu.edu.cn:8800",
                "username": username,
                "authenticated_at": "2026-08-11T13:00:00",
                "cookies": {"PHPSESSID_8800": "active-secret-cookie"},
            }
            return {"success": True, "requires_sms": False}

    monkeypatch.setattr(session_tokens, "_refresh_portal_client_class", lambda: ActivePortalClient)

    result = session_tokens.refresh_chatenv_token(
        service="ECNU",
        profile="default",
        home=home,
        env_store=env_store,
    )

    assert result.token_type == "portal_session"
    assert result.summary["username"] == "active-student"
    assert captured["token_profile"] == "default"
    assert captured["username"] == "active-student"
    assert captured["password"] == "active-secret-password-fixture"
    assert not TokenStore(home=home).token_path("ECNU", "default").exists()


def test_refresh_chatenv_token_fails_without_matching_stable_profile(tmp_path):
    from chatecnu.ecnu.session_tokens import refresh_chatenv_token

    home = tmp_path / "chatarch"
    env_store = EnvStore(home / "envs")

    with pytest.raises(ValueError, match="profile not found"):
        refresh_chatenv_token(service="ECNU", profile="RexWzh", home=home, env_store=env_store)


def test_refresh_chatenv_token_fails_closed_when_auto_login_requires_sms(tmp_path, monkeypatch):
    from chatecnu.ecnu import session_tokens

    home = tmp_path / "chatarch"
    env_store = EnvStore(home / "envs")
    _save_ecnu_profile(env_store)

    class SmsPortalClient:
        def __init__(self, **kwargs):
            self.state = {"cookies": {"PHPSESSID_8800": "secret-cookie"}}

        def login_auto(self, username, password, sms_code, rounds, topk, captcha_path):
            return {"success": False, "requires_sms": True, "message": "SMS verification is required"}

    monkeypatch.setattr(session_tokens, "_refresh_portal_client_class", lambda: SmsPortalClient)

    with pytest.raises(ValueError, match="requires SMS") as exc_info:
        session_tokens.refresh_chatenv_token(service="ECNU", profile="RexWzh", home=home, env_store=env_store)
    assert "secret-cookie" not in str(exc_info.value)


def test_chat_env_refresh_writes_ecnu_provider_result(tmp_path, monkeypatch):
    home = tmp_path / "chatarch"
    env_store = EnvStore(home / "envs")
    _save_ecnu_profile(env_store)

    def fake_provider(**kwargs):
        return TokenRefreshResult(
            values={
                "base_url": "https://login.ecnu.edu.cn:8800",
                "username": "student001",
                "authenticated_at": "2026-08-11T12:34:56",
                "cookies": {"PHPSESSID_8800": "secret-cookie"},
                "login_bootstrap": {"csrf_token": "secret-csrf"},
            },
            token_type="portal_session",
            summary={
                "base_url": "https://login.ecnu.edu.cn:8800",
                "username": "student001",
                "authenticated_at": "2026-08-11T12:34:56",
                "cookie_count": 1,
                "has_login_bootstrap": True,
            },
        )

    chatenv_refreshers.clear_token_refreshers()
    monkeypatch.setitem(chatenv_refreshers._token_refreshers, "ecnu", fake_provider)
    monkeypatch.setattr(chatenv_refreshers, "_loaded", True)

    status = refresh_token("ECNU", "RexWzh", home=home, env_store=env_store)

    assert status["service"] == "ECNU"
    assert status["profile"] == "RexWzh"
    assert status["token_type"] == "portal_session"
    assert status["token_present"] is True
    assert status["source"] == "refresh"
    assert status["summary"]["cookie_count"] == 1
    dumped = json.dumps(status)
    assert "secret-cookie" not in dumped
    assert "secret-csrf" not in dumped
