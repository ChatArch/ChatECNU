"""HTTP client and parsers for the ECNU self-service portal."""

from __future__ import annotations

import base64
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests

from chatnet.portal import (
    BrowserPortalClient,
    clean_text,
    curl_string,
    extract_meta_content,
    extract_summary_text,
    find_table_with_headers,
    first_multirow_table,
    parse_detail_view_table,
    parse_tables,
    request_spec,
    require_value,
    strip_tags,
    table_to_dicts,
)

BASE_URL = "https://login.ecnu.edu.cn:8800"
LOGIN_PATH = "/login"
VALIDATE_USER_PATH = "/site/validate-user"
VALIDATE_SMS_PATH = "/site/validate-smscode"
LOGOUT_PATH = "/site/logout"
HOME_PATH = "/home"
USER_INFO_PATH = "/users"
AUTH_LOG_PATH = "/log/auth"
DETAIL_LOG_PATH = "/log/detail"
VISITOR_LIST_PATH = "/visitors/manual/index"
VISITOR_CREATE_PATH = "/visitors/manual/create"
VISITOR_UPDATE_PATH = "/visitors/manual/update"
VISITOR_DELETE_PATH = "/visitors/manual/delete"
VISITOR_LOCK_PATH = "/visitors/manual/lock"


SAMPLE_LOGIN_HTML = """
<html><head>
<meta name="csrf-param" content="_csrf-8800">
<meta name="csrf-token" content="sample-token">
</head><body>
<form id="login-form" action="/login" method="post">
<input type="hidden" name="_csrf-8800" value="sample-token">
<input type="hidden" id="public" value="-----BEGIN PUBLIC KEY-----\nSAMPLE\n-----END PUBLIC KEY-----\n">
<img id="loginform-verifycode-image" src="/site/captcha?v=sample">
</form></body></html>
"""

SAMPLE_HOME_HTML = """
<div class="wrap home-patch">
  <div class="panel panel-default">
    <ul class="list-group">
      <li class="list-group-item"><label class="list-group-label">用户名</label>20260000000</li>
      <li class="list-group-item"><label class="list-group-label">姓名</label>Test User</li>
      <li class="list-group-item"><label class="list-group-label">状态</label><a class="btn btn-xs btn-success">正常</a></li>
    </ul>
  </div>
  <table><thead><tr><th>用户名</th><th>IP地址</th></tr></thead><tbody><tr><td>u</td><td>1.1.1.1</td></tr></tbody></table>
  <table><thead><tr><th>产品ID</th><th>产品名称</th></tr></thead><tbody><tr><td>2</td><td>统一身份认证-全日制学生</td></tr></tbody></table>
</div>
"""

SAMPLE_VISITOR_HTML = """
<html><head>
<meta name="csrf-param" content="_csrf-8800">
<meta name="csrf-token" content="sample-token">
</head><body>
<div class="summary">第<b>1-2</b>条，共<b>2</b>条数据.</div>
<table>
<thead><tr><th>#</th><th>账号</th><th>状态</th><th>已用流量</th><th>已用时长</th><th>备注信息</th><th>密码</th><th>操作</th></tr></thead>
<tbody>
<tr data-key="10256701"><td>1</td><td>20260000000m1</td><td>正常</td><td>0byte</td><td>0秒</td><td>temp</td><td>******</td><td><a href="/visitors/manual/update?id=10256701" title="更新"></a> <a href="/visitors/manual/lock?id=10256701" title="锁定"></a> <a href="/visitors/manual/delete?id=10256701" title="销户"></a></td></tr>
<tr data-key="10256703"><td>2</td><td>20260000000m2</td><td>正常</td><td>0byte</td><td>0秒</td><td>GuestB</td><td>******</td><td><a href="/visitors/manual/update?id=10256703" title="更新"></a> <a href="/visitors/manual/lock?id=10256703" title="锁定"></a> <a href="/visitors/manual/delete?id=10256703" title="销户"></a></td></tr>
</tbody></table>
</body></html>
"""


@dataclass
class LoginBootstrap:
    csrf_param: str
    csrf_token: str
    public_key: str
    captcha_url: str
    fetched_at: str


@dataclass
class VisitorRow:
    visitor_id: str
    index: str
    account: str
    status: str
    used_flow: str
    used_time: str
    remark: str
    masked_password: str
    update_url: str | None
    lock_url: str | None
    delete_url: str | None


class PortalClient(BrowserPortalClient):
    def _authenticated_response(self, resp: requests.Response) -> requests.Response:
        resp.raise_for_status()
        if urlparse(resp.url).path == LOGIN_PATH:
            raise RuntimeError("Not authenticated: request was redirected to the login page.")
        return resp

    def reset_login_session(self) -> None:
        self.session.cookies.clear()
        for key in ["authenticated_at", "login_bootstrap", "captcha_path", "username"]:
            self.state.pop(key, None)
        self._save_state()

    def fetch_login_bootstrap(self) -> tuple[LoginBootstrap, str]:
        resp = self.get(LOGIN_PATH)
        resp.raise_for_status()
        html = resp.text
        bootstrap = LoginBootstrap(
            csrf_param=require_value(extract_meta_content(html, "csrf-param"), "missing login csrf-param"),
            csrf_token=require_value(extract_meta_content(html, "csrf-token"), "missing login csrf-token"),
            public_key=require_value(extract_login_public_key(html), "missing login RSA public key"),
            captcha_url=require_value(extract_captcha_url(html), "missing login captcha url"),
            fetched_at=datetime.now().isoformat(timespec="seconds"),
        )
        self._save_state({"login_bootstrap": asdict(bootstrap)})
        return bootstrap, html

    def login_init(self, captcha_path: Path) -> dict[str, Any]:
        self.reset_login_session()
        bootstrap, _ = self.fetch_login_bootstrap()
        captcha_path.parent.mkdir(parents=True, exist_ok=True)
        resp = self.session.get(self._url(bootstrap.captcha_url), timeout=self.timeout)
        resp.raise_for_status()
        captcha_path.write_bytes(resp.content)
        self._save_state({"login_bootstrap": asdict(bootstrap), "captcha_path": str(captcha_path)})
        return {
            "captcha_path": str(captcha_path),
            "captcha_url": self._url(bootstrap.captcha_url),
            "csrf_param": bootstrap.csrf_param,
            "fetched_at": bootstrap.fetched_at,
        }

    def login(self, username: str, password: str, verify_code: str, sms_code: str | None = None) -> dict[str, Any]:
        bootstrap = self._ensure_login_bootstrap()
        encrypted_password = self._encrypt_password(password, bootstrap.public_key)
        validated = self._validate_user(username, encrypted_password, verify_code, bootstrap)
        result: dict[str, Any] = {
            "validate_user": validated,
            "captcha_url": self._url(bootstrap.captcha_url),
            "state_file": str(self.state_file),
        }
        if not validated.get("success"):
            return result
        if validated.get("inputSms"):
            if not sms_code:
                result["message"] = "SMS verification is required; rerun login with --sms-code."
                return result
            sms_result = self._validate_sms(username, sms_code, bootstrap)
            result["validate_sms"] = sms_result
            if not sms_result.get("success"):
                return result
        submit_result = self._submit_login(username, encrypted_password, verify_code, sms_code, bootstrap)
        result["submit_login"] = submit_result
        return result

    def login_auto(
        self,
        username: str,
        password: str,
        sms_code: str | None,
        rounds: int,
        topk: int,
        captcha_path: Path,
    ) -> dict[str, Any]:
        from .captcha import recognize_captcha_topk

        attempts: list[dict[str, Any]] = []
        for round_index in range(1, rounds + 1):
            init_result = self.login_init(captcha_path)
            candidates = recognize_captcha_topk(captcha_path.read_bytes(), topk=topk)
            round_info: dict[str, Any] = {
                "round": round_index,
                "captcha_path": str(captcha_path),
                "captcha_url": init_result["captcha_url"],
                "candidates": candidates,
                "attempts": [],
            }
            for candidate in candidates:
                login_result = self.login(username, password, candidate, sms_code=sms_code)
                candidate_info = {
                    "candidate": candidate,
                    "validate_user": login_result.get("validate_user"),
                    "validate_sms": login_result.get("validate_sms"),
                    "submit_login": login_result.get("submit_login"),
                    "message": login_result.get("message"),
                }
                round_info["attempts"].append(candidate_info)
                validated = login_result.get("validate_user") or {}
                if validated.get("success"):
                    return {
                        "success": bool(login_result.get("submit_login", {}).get("success")),
                        "requires_sms": bool(login_result.get("message")),
                        "login_result": login_result,
                        "attempts": attempts + [round_info],
                    }
                if not is_retryable_captcha_error(validated):
                    return {"success": False, "login_result": login_result, "attempts": attempts + [round_info], "aborted": True}
            attempts.append(round_info)
        return {"success": False, "attempts": attempts, "message": f"Captcha auto-login failed after {rounds} rounds x {topk} candidates."}

    def logout(self) -> dict[str, Any]:
        csrf_param, csrf_token, _ = self.fetch_csrf(HOME_PATH)
        resp = self.post(LOGOUT_PATH, data={csrf_param: csrf_token}, headers={"Referer": self._url(HOME_PATH)})
        resp.raise_for_status()
        self.state.pop("authenticated_at", None)
        self._save_state()
        return {"success": urlparse(resp.url).path == LOGIN_PATH, "final_url": resp.url}

    def home_summary(self) -> dict[str, Any]:
        resp = self.fetch_page(HOME_PATH)
        html = resp.text
        tables = parse_tables(html)
        return {
            "user_info": parse_home_user_info(html),
            "online_info": table_to_dicts(find_table_with_headers(tables, ["用户名", "IP地址"]) or {"headers": [], "rows": []}),
            "product_info": table_to_dicts(find_table_with_headers(tables, ["产品ID", "产品名称"]) or {"headers": [], "rows": []}),
        }

    def user_info(self) -> dict[str, str]:
        resp = self.fetch_page(USER_INFO_PATH)
        tables = parse_tables(resp.text)
        return parse_detail_view_table(tables[0] if tables else {"headers": [], "rows": []})

    def auth_logs(self, start_time: str | None, end_time: str | None, limit: int | None) -> dict[str, Any]:
        return self._query_log_page(AUTH_LOG_PATH, "AuthLogSearch[start_time]", "AuthLogSearch[end_time]", start_time, end_time, limit)

    def detail_logs(self, start_time: str | None, end_time: str | None, limit: int | None) -> dict[str, Any]:
        return self._query_log_page(DETAIL_LOG_PATH, "DetailLogSearch[start_time]", "DetailLogSearch[end_time]", start_time, end_time, limit)

    def list_visitors(self) -> dict[str, Any]:
        _, _, html = self.fetch_csrf(VISITOR_LIST_PATH)
        rows = [asdict(row) for row in parse_visitor_rows(html)]
        return {"count": len(rows), "summary": extract_summary_text(html), "rows": rows}

    def get_visitor(self, visitor_id: str | None = None, account: str | None = None) -> dict[str, Any]:
        if not visitor_id and not account:
            raise ValueError("Provide either id or account.")
        rows = parse_visitor_rows(self.fetch_csrf(VISITOR_LIST_PATH)[2])
        for row in rows:
            if visitor_id and row.visitor_id == visitor_id:
                return asdict(row)
            if account and row.account == account:
                return asdict(row)
        raise ValueError("Visitor not found.")

    def create_visitor(self, remark: str, dry_run: bool = False) -> dict[str, Any]:
        validate_remark(remark)
        csrf_param, csrf_token, _ = self.fetch_csrf(VISITOR_LIST_PATH)
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Origin": self.base_url,
            "Referer": self._url(VISITOR_LIST_PATH),
            "X-CSRF-Token": csrf_token,
            "X-Requested-With": "XMLHttpRequest",
        }
        data = {"remark": remark, "agreement": "true"}
        return self._maybe_post(VISITOR_CREATE_PATH, headers, data, dry_run, json_response=True, csrf_param=csrf_param)

    def update_visitor(self, visitor_id: str, remark: str, password: str, dry_run: bool = False) -> dict[str, Any]:
        validate_remark(remark)
        validate_password(password)
        path = f"{VISITOR_UPDATE_PATH}?id={visitor_id}"
        csrf_param, csrf_token, _ = self.fetch_csrf(path)
        headers = {"Content-Type": "application/x-www-form-urlencoded", "Origin": self.base_url, "Referer": self._url(path)}
        data = {
            csrf_param: csrf_token,
            "VisitorsPasswordForm[remark]": remark,
            "VisitorsPasswordForm[password]": password,
            "VisitorsPasswordForm[password1]": password,
        }
        return self._maybe_post(path, headers, data, dry_run)

    def delete_visitor(self, visitor_id: str, dry_run: bool = False) -> dict[str, Any]:
        return self._post_csrf_action(VISITOR_LIST_PATH, f"{VISITOR_DELETE_PATH}?id={visitor_id}", dry_run)

    def lock_visitor(self, visitor_id: str, dry_run: bool = False) -> dict[str, Any]:
        return self._post_csrf_action(VISITOR_LIST_PATH, f"{VISITOR_LOCK_PATH}?id={visitor_id}", dry_run)

    def fetch_page(self, path: str) -> requests.Response:
        return self._authenticated_response(self.get(path))

    def fetch_csrf(self, path: str) -> tuple[str, str, str]:
        resp = self.fetch_page(path)
        html = resp.text
        param = extract_meta_content(html, "csrf-param")
        token = extract_meta_content(html, "csrf-token")
        if not param or not token:
            raise RuntimeError(f"Failed to locate CSRF meta tags on {path}.")
        return param, token, html

    def _ensure_login_bootstrap(self) -> LoginBootstrap:
        raw = self.state.get("login_bootstrap")
        if raw:
            return LoginBootstrap(**raw)
        bootstrap, _ = self.fetch_login_bootstrap()
        return bootstrap

    def _encrypt_password(self, password: str, public_key: str) -> str:
        from Crypto.Cipher import PKCS1_v1_5
        from Crypto.PublicKey import RSA

        rsa_key = RSA.import_key(public_key)
        cipher = PKCS1_v1_5.new(rsa_key)
        return base64.b64encode(cipher.encrypt(password.encode("utf-8"))).decode("ascii")

    def _validate_user(self, username: str, encrypted_password: str, verify_code: str, bootstrap: LoginBootstrap) -> dict[str, Any]:
        headers = {"Accept": "*/*", "Origin": self.base_url, "Referer": self._url(LOGIN_PATH), "X-CSRF-Token": bootstrap.csrf_token, "X-Requested-With": "XMLHttpRequest"}
        data = {"LoginForm[username]": username, "LoginForm[password]": encrypted_password, "LoginForm[verifyCode]": verify_code}
        resp = self.post(VALIDATE_USER_PATH, headers=headers, data=data)
        resp.raise_for_status()
        return json.loads(resp.text)

    def _validate_sms(self, username: str, sms_code: str, bootstrap: LoginBootstrap) -> dict[str, Any]:
        headers = {"Accept": "*/*", "Origin": self.base_url, "Referer": self._url(LOGIN_PATH), "X-CSRF-Token": bootstrap.csrf_token, "X-Requested-With": "XMLHttpRequest"}
        resp = self.post(VALIDATE_SMS_PATH, headers=headers, data={"uname": username, "code": sms_code})
        resp.raise_for_status()
        return json.loads(resp.text)

    def _submit_login(
        self,
        username: str,
        encrypted_password: str,
        verify_code: str,
        sms_code: str | None,
        bootstrap: LoginBootstrap,
    ) -> dict[str, Any]:
        data = {
            bootstrap.csrf_param: bootstrap.csrf_token,
            "LoginForm[username]": username,
            "LoginForm[password]": encrypted_password,
            "LoginForm[verifyCode]": verify_code,
            "LoginForm[smsCode]": sms_code or "",
        }
        resp = self.post(LOGIN_PATH, headers={"Origin": self.base_url, "Referer": self._url(LOGIN_PATH)}, data=data)
        resp.raise_for_status()
        success = urlparse(resp.url).path != LOGIN_PATH
        if success:
            self._save_state({"authenticated_at": datetime.now().isoformat(timespec="seconds"), "login_bootstrap": asdict(bootstrap), "username": username})
        return {"success": success, "final_url": resp.url, "error": None if success else extract_error_summary(resp.text)}

    def _query_log_page(
        self,
        path: str,
        start_field: str,
        end_field: str,
        start_time: str | None,
        end_time: str | None,
        limit: int | None,
    ) -> dict[str, Any]:
        csrf_param, csrf_token, html = self.fetch_csrf(path)
        if start_time or end_time:
            data = {csrf_param: csrf_token, start_field: start_time or "", end_field: end_time or ""}
            html = self._authenticated_response(self.post(path, data=data, headers={"Referer": self._url(path)})).text
        table = first_multirow_table(parse_tables(html))
        rows = table_to_dicts(table) if table else []
        return {"count": len(rows[:limit] if limit is not None else rows), "rows": rows[:limit] if limit is not None else rows, "summary": extract_summary_text(html)}

    def _post_csrf_action(self, referer_path: str, action_path: str, dry_run: bool) -> dict[str, Any]:
        csrf_param, csrf_token, _ = self.fetch_csrf(referer_path)
        headers = {"Content-Type": "application/x-www-form-urlencoded", "Origin": self.base_url, "Referer": self._url(referer_path)}
        return self._maybe_post(action_path, headers, {csrf_param: csrf_token}, dry_run)

    def _maybe_post(
        self,
        path: str,
        headers: dict[str, str],
        data: dict[str, str],
        dry_run: bool,
        json_response: bool = False,
        csrf_param: str | None = None,
    ) -> dict[str, Any]:
        spec = request_spec("POST", self._url(path), headers, data)
        if csrf_param:
            spec["csrf_param"] = csrf_param
        if dry_run:
            spec["dry_run"] = True
            spec["curl"] = curl_string("POST", self._url(path), headers, data)
            return spec
        resp = self.post(path, headers=headers, data=data)
        resp.raise_for_status()
        if json_response:
            return {"request": spec, "response": resp.json()}
        return {"request": spec, "response": {"status_code": resp.status_code, "ok": "操作成功" in resp.text, "url": resp.url}}


def extract_login_public_key(html: str) -> str | None:
    match = re.search(r'<input[^>]+id=["\']public["\'][^>]+value=["\'](.*?-----END PUBLIC KEY-----\s*)["\']', html, re.S | re.I)
    return unescape(match.group(1)).strip() if match else None


def extract_captcha_url(html: str) -> str | None:
    match = re.search(r'<img[^>]+id=["\']loginform-verifycode-image["\'][^>]+src=["\']([^"\']+)["\']', html, re.I)
    return unescape(match.group(1)) if match else None


def extract_error_summary(html: str) -> str | None:
    items = re.findall(r'<div class="alert alert-danger error-summary".*?<li>(.*?)</li>', html, re.S | re.I)
    return clean_text("; ".join(strip_tags(x) for x in items)) if items else None


def parse_home_user_info(html: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for label, value in re.findall(r'<li class="list-group-item">.*?<label class="list-group-label">(.*?)</label>(.*?)</li>', html, re.S | re.I):
        out[clean_text(label)] = strip_tags(value)
    return out


def parse_action_url(action_cell: str, action: str) -> str | None:
    match = re.search(rf'href=["\']([^"\']*{re.escape(action)}[^"\']*)["\']', action_cell, re.I)
    return unescape(match.group(1)) if match else None


def parse_visitor_rows(html: str) -> list[VisitorRow]:
    rows: list[VisitorRow] = []
    for row_match in re.finditer(r'<tr\s+data-key=["\'](\d+)["\']>(.*?)</tr>', html, re.S | re.I):
        visitor_id = row_match.group(1)
        cells = re.findall(r"<td.*?>(.*?)</td>", row_match.group(2), re.S | re.I)
        if len(cells) < 8:
            continue
        rows.append(
            VisitorRow(
                visitor_id=visitor_id,
                index=strip_tags(cells[0]),
                account=strip_tags(cells[1]),
                status=strip_tags(cells[2]),
                used_flow=strip_tags(cells[3]),
                used_time=strip_tags(cells[4]),
                remark=strip_tags(cells[5]),
                masked_password=strip_tags(cells[6]),
                update_url=parse_action_url(cells[7], "/update"),
                lock_url=parse_action_url(cells[7], "/lock"),
                delete_url=parse_action_url(cells[7], "/delete"),
            )
        )
    return rows


def validate_remark(remark: str) -> None:
    if not re.fullmatch(r"[A-Za-z\u4e00-\u9fa5]{2,14}", remark):
        raise ValueError("Remark must be 2-14 Chinese or English letters.")


def validate_password(password: str) -> None:
    pattern = re.compile(r"^(?![a-zA-Z]+$)(?!\d+$)(?![!@#$%^&*()_\-+=\{\}\[\]|\\:;\"',.?`~/<>]+$)[a-zA-Z\d!@#$%^&*()_\-+=\{\}\[\]|\\:;\"',.?`~/<>]{8,20}$")
    if not pattern.fullmatch(password):
        raise ValueError("Password must be 8-20 chars and include letters, digits, and special characters.")


def is_retryable_captcha_error(payload: dict[str, Any]) -> bool:
    message = str(payload.get("message", ""))
    lowered = message.lower()
    return "验证码" in message or "captcha" in lowered or "verify" in lowered


def run_selftest() -> dict[str, Any]:
    bootstrap = LoginBootstrap(
        csrf_param=require_value(extract_meta_content(SAMPLE_LOGIN_HTML, "csrf-param"), "csrf-param"),
        csrf_token=require_value(extract_meta_content(SAMPLE_LOGIN_HTML, "csrf-token"), "csrf-token"),
        public_key=require_value(extract_login_public_key(SAMPLE_LOGIN_HTML), "public"),
        captcha_url=require_value(extract_captcha_url(SAMPLE_LOGIN_HTML), "captcha"),
        fetched_at="2026-06-15T03:00:00",
    )
    home = parse_home_user_info(SAMPLE_HOME_HTML)
    tables = parse_tables(SAMPLE_HOME_HTML)
    visitors = parse_visitor_rows(SAMPLE_VISITOR_HTML)
    validate_remark("GuestB")
    validate_password("Temp!234")
    assert bootstrap.csrf_param == "_csrf-8800"
    assert home["用户名"] == "20260000000"
    assert find_table_with_headers(tables, ["产品ID", "产品名称"]) is not None
    assert len(visitors) == 2
    assert visitors[1].remark == "GuestB"
    return {"ok": True, "visitors": len(visitors)}
