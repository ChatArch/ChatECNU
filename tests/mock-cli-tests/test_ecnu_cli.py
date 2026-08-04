import json

from click.testing import CliRunner

from chatecnu.cli import main
import chatecnu.ecnu.cli as ecnu_cli


class FakePortalClient:
    def __init__(self):
        self.calls = []
        self.state = {"cookies": {"PHPSESSID_8800": "secret-cookie"}, "username": "mock-user"}
        self.visitor_rows = [
            {"visitor_id": "10256703", "account": "mock-userm1", "status": "正常", "remark": "GuestA"},
        ]
        self.next_id = 10256704

    def login_init(self, captcha_path):
        self.calls.append(("login_init", str(captcha_path)))
        return {"captcha_path": str(captcha_path), "csrf_param": "_csrf-8800"}

    def login(self, username, password, captcha, sms_code=None):
        self.calls.append(("login", username, password, captcha, sms_code))
        return {"submit_login": {"success": True}, "state_file": "mock-state.json"}

    def login_auto(self, username, password, sms_code, rounds, topk, captcha_path):
        self.calls.append(("login_auto", username, password, sms_code, rounds, topk, str(captcha_path)))
        return {"success": True, "attempts": [{"round": 1, "candidates": ["1234"]}]}

    def cookie_header(self):
        self.calls.append(("cookie_header",))
        return "PHPSESSID_8800=secret-cookie"

    def logout(self):
        self.calls.append(("logout",))
        return {"success": True}

    def home_summary(self):
        self.calls.append(("home_summary",))
        return {"user_info": {"用户名": "mock-user"}}

    def user_info(self):
        self.calls.append(("user_info",))
        return {"账号": "mock-user"}

    def auth_logs(self, start, end, limit):
        self.calls.append(("auth_logs", start, end, limit))
        return {"count": 1, "rows": [{"认证结果": "成功"}]}

    def detail_logs(self, start, end, limit):
        self.calls.append(("detail_logs", start, end, limit))
        return {"count": 1, "rows": [{"访问地址": "1.1.1.1"}]}

    def list_visitors(self):
        self.calls.append(("list_visitors",))
        return {"count": len(self.visitor_rows), "rows": [dict(row) for row in self.visitor_rows]}

    def get_visitor(self, visitor_id=None, account=None):
        self.calls.append(("get_visitor", visitor_id, account))
        for row in self.visitor_rows:
            if visitor_id and row["visitor_id"] == visitor_id:
                return dict(row)
            if account and row["account"] == account:
                return dict(row)
        return {"visitor_id": visitor_id or "10256703", "account": account or "mock-userm1"}

    def create_visitor(self, remark, dry_run=False):
        self.calls.append(("create_visitor", remark, dry_run))
        account = f"mock-userm{len(self.visitor_rows) + 1}"
        visitor_id = str(self.next_id)
        self.next_id += 1
        if not dry_run:
            self.visitor_rows.append(
                {"visitor_id": visitor_id, "account": account, "status": "正常", "remark": remark}
            )
        return {"dry_run": dry_run, "response": {"account": "mockm1", "password": "Init!234"}}

    def update_visitor(self, visitor_id, remark, password, dry_run=False):
        self.calls.append(("update_visitor", visitor_id, remark, password, dry_run))
        if not dry_run:
            for row in self.visitor_rows:
                if row["visitor_id"] == visitor_id:
                    row["remark"] = remark
        return {"dry_run": dry_run, "response": {"ok": True}}

    def delete_visitor(self, visitor_id, dry_run=False):
        self.calls.append(("delete_visitor", visitor_id, dry_run))
        return {"dry_run": dry_run, "response": {"ok": True}}

    def lock_visitor(self, visitor_id, dry_run=False):
        self.calls.append(("lock_visitor", visitor_id, dry_run))
        return {"dry_run": dry_run, "response": {"ok": True}}


def invoke_ok(runner, args):
    result = runner.invoke(main, args)
    assert result.exit_code == 0, result.output
    return json.loads(result.output) if result.output.strip().startswith("{") else result.output


def test_ecnu_mock_cli_runs_full_command_chain(monkeypatch, tmp_path):
    fake = FakePortalClient()
    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path / "chatarch"))
    monkeypatch.setattr(ecnu_cli, "make_client", lambda ctx: fake)
    runner = CliRunner()

    invoke_ok(runner, ["home", "login-init", "--captcha-path", str(tmp_path / "captcha.png")])
    manual = invoke_ok(runner, ["home", "login", "--username", "mock-user", "--password", "secret", "--captcha", "1234", "-I"])
    assert "Login succeeded." in manual
    auto = invoke_ok(runner, ["home", "login", "--username", "mock-user", "--password", "secret", "--rounds", "1", "--topk", "1", "-I"])
    assert "Login succeeded." in auto
    session = invoke_ok(runner, ["home", "status"])
    assert "Username: mock-user" in session
    session_json = invoke_ok(runner, ["home", "status", "--json"])
    assert session_json["cookies"]["PHPSESSID_8800"] == "***"
    assert invoke_ok(runner, ["home", "cookie-header"]) == "PHPSESSID_8800=secret-cookie\n"
    assert "首页摘要" in invoke_ok(runner, ["home", "info"])
    assert "账号: mock-user" in invoke_ok(runner, ["home", "user"])
    assert "Authentication logs" in invoke_ok(runner, ["debug", "auth-log", "--limit", "1"])
    assert "Network detail logs" in invoke_ok(runner, ["debug", "detail-log", "--limit", "1"])
    assert "访客账号" in invoke_ok(runner, ["visitor", "list"])
    assert "visitor_id: 10256703" in invoke_ok(runner, ["visitor", "get", "--id", "10256703"])
    assert "account: mock-userm1" in invoke_ok(runner, ["visitor", "get", "--account", "mock-userm1"])
    created = invoke_ok(runner, ["visitor", "create", "--remark", "GuestB", "--dry-run", "-I"])
    assert created == "创建访客: 仅预览，未提交。\n"
    invoke_ok(
        runner,
        [
            "visitor",
            "update",
            "--id",
            "10256703",
            "--remark",
            "GuestC",
            "--password",
            "Temp!235",
            "--dry-run",
            "-I",
        ],
    )
    invoke_ok(runner, ["visitor", "delete", "--id", "10256703", "--dry-run", "-I"])
    invoke_ok(runner, ["visitor", "lock", "--id", "10256703", "--dry-run", "-I"])
    invoke_ok(runner, ["home", "logout"])

    call_names = [call[0] for call in fake.calls]
    assert call_names == [
        "login_init",
        "login",
        "login_auto",
        "cookie_header",
        "home_summary",
        "user_info",
        "auth_logs",
        "detail_logs",
        "list_visitors",
        "get_visitor",
        "get_visitor",
        "create_visitor",
        "update_visitor",
        "delete_visitor",
        "lock_visitor",
        "logout",
    ]


def test_ecnu_visitor_default_uses_env_passwords(monkeypatch, tmp_path):
    fake = FakePortalClient()
    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path / "chatarch"))
    monkeypatch.setattr(ecnu_cli, "make_client", lambda ctx: fake)
    env_file = tmp_path / "chatarch" / "envs" / "ECNU" / ".env"
    env_file.parent.mkdir(parents=True)
    env_file.write_text(
        "\n".join(
            [
                "ECNU_USERNAME='mock-user'",
                "ECNU_VISITOR_PASSWORD1='Temp!235'",
                "ECNU_VISITOR_PASSWORD2='Temp!236'",
                "ECNU_VISITOR_REMARK='default'",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = CliRunner().invoke(main, ["visitor", "default", "-I"])

    assert result.exit_code == 0, result.output
    assert "Default visitor sync complete. Accounts: 2" in result.output
    assert ("update_visitor", "10256703", "default", "Temp!235", False) in fake.calls
    assert any(call[:4] == ("update_visitor", "10256704", "default", "Temp!236") for call in fake.calls)
    assert ("create_visitor", "default", False) in fake.calls


def test_ecnu_env_file_override_supplies_login_defaults(monkeypatch, tmp_path):
    fake = FakePortalClient()
    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path / "chatarch"))
    monkeypatch.setattr(ecnu_cli, "make_client", lambda ctx: fake)
    env_file = tmp_path / "ecnu.env"
    env_file.write_text(
        "ECNU_USERNAME='env-user'\nECNU_PASSWORD='env-secret'\nECNU_BASE_URL='https://example.invalid'\n",
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        main,
        ["--env-file", str(env_file), "home", "login", "--rounds", "1", "--topk", "1", "-I"],
    )

    assert result.exit_code == 0, result.output
    assert ("login_auto", "env-user", "env-secret", None, 1, 1, str(tmp_path / "chatarch" / "cache" / "chatecnu" / "ecnu-login-captcha.png")) in fake.calls


def test_ecnu_help_keeps_advanced_commands_hidden():
    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "home" in result.output
    assert "net" in result.output
    assert "visitor" in result.output
    assert "login" not in result.output
    assert "status" not in result.output
    assert "user-info" not in result.output
    assert "cookie-header" not in result.output
    assert "login-init" not in result.output
    assert "login-auto" not in result.output
    assert "selftest" not in result.output
    assert "auth-log" not in result.output
    assert "detail-log" not in result.output
    assert "debug" not in result.output
    assert "--cookie" not in result.output
    assert "--state-file" not in result.output


def test_ecnu_visitor_help_keeps_lock_hidden():
    result = CliRunner().invoke(main, ["visitor", "--help"])

    assert result.exit_code == 0
    assert "list" in result.output
    assert "create" in result.output
    assert "update" in result.output
    assert "delete" in result.output
    assert "lock" not in result.output


def test_ecnu_home_help_shows_portal_commands():
    result = CliRunner().invoke(main, ["home", "--help"], prog_name="ecnu")

    assert result.exit_code == 0
    assert "info" in result.output
    assert "login" in result.output
    assert "logout" in result.output
    assert "status" in result.output
    assert "user" in result.output


def test_ecnu_removed_top_level_portal_commands_and_long_network_command():
    runner = CliRunner()
    for command in ["login", "logout", "status", "user-info", "network-auth", "auth"]:
        result = runner.invoke(main, [command, "--help"], prog_name="ecnu")
        assert result.exit_code != 0
