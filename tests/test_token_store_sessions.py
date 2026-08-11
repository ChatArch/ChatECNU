import json

from click.testing import CliRunner
from chatenv import TokenStore

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
