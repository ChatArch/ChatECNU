import json

from click.testing import CliRunner

from chatnet.cli import main
import chatnet.ecnu.cli as ecnu_cli


class FakePortalClient:
    def __init__(self):
        self.calls = []
        self.state = {"cookies": {"PHPSESSID_8800": "secret-cookie"}, "username": "mock-user"}

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
        return {"count": 1, "rows": [{"visitor_id": "10256703", "account": "mockm1"}]}

    def get_visitor(self, visitor_id=None, account=None):
        self.calls.append(("get_visitor", visitor_id, account))
        return {"visitor_id": visitor_id or "10256703", "account": account or "mockm1"}

    def create_visitor(self, remark, dry_run=False):
        self.calls.append(("create_visitor", remark, dry_run))
        return {"dry_run": dry_run, "response": {"account": "mockm1", "password": "Init!234"}}

    def update_visitor(self, visitor_id, remark, password, dry_run=False):
        self.calls.append(("update_visitor", visitor_id, remark, password, dry_run))
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

    invoke_ok(runner, ["ecnu", "login-init", "--captcha-path", str(tmp_path / "captcha.png")])
    invoke_ok(runner, ["ecnu", "login", "--username", "mock-user", "--password", "secret", "--captcha", "1234", "-I"])
    invoke_ok(runner, ["ecnu", "login-auto", "--username", "mock-user", "--password", "secret", "--rounds", "1", "--topk", "1", "-I"])
    session = invoke_ok(runner, ["ecnu", "session-info"])
    assert session["cookies"]["PHPSESSID_8800"] == "***"
    assert invoke_ok(runner, ["ecnu", "cookie-header"]) == "PHPSESSID_8800=secret-cookie\n"
    invoke_ok(runner, ["ecnu", "home"])
    invoke_ok(runner, ["ecnu", "user-info"])
    invoke_ok(runner, ["ecnu", "auth-log", "--limit", "1"])
    invoke_ok(runner, ["ecnu", "detail-log", "--limit", "1"])
    invoke_ok(runner, ["ecnu", "visitor", "list"])
    invoke_ok(runner, ["ecnu", "visitor", "get", "--id", "10256703"])
    invoke_ok(runner, ["ecnu", "visitor", "get", "--account", "mockm1"])
    created = invoke_ok(runner, ["ecnu", "visitor", "create", "--remark", "GuestB", "--dry-run", "-I"])
    assert created["response"]["password"] == "Init!234"
    invoke_ok(
        runner,
        [
            "ecnu",
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
    invoke_ok(runner, ["ecnu", "visitor", "delete", "--id", "10256703", "--dry-run", "-I"])
    invoke_ok(runner, ["ecnu", "visitor", "lock", "--id", "10256703", "--dry-run", "-I"])
    invoke_ok(runner, ["ecnu", "logout"])

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
        ["ecnu", "--env-file", str(env_file), "login", "--captcha", "1234", "-I"],
    )

    assert result.exit_code == 0, result.output
    assert ("login", "env-user", "env-secret", "1234", None) in fake.calls
