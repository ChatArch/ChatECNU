"""ECNU campus-network ``auth_client`` wrapper.

The upstream ECNU helper scripts shell out to a Linux-only ``auth_client``:
``checklogin`` runs ``auth_client check`` and ``mylogout`` extracts
``Username=...`` from that check before calling ``auth_client -u USER auth
--logout``. ChatECNU keeps that command contract but ships the Linux x86_64
client inside the PyPI wheel so pip installs do not depend on internal network
URLs. The binary appears to accept passwords only through ``-p`` argv, so
ChatECNU still fails closed by default and requires explicit unsafe opt-in
before using that legacy argv-password channel.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from importlib.resources import files as resource_files
from pathlib import Path
import platform
import re
import shlex
import shutil
import subprocess
from typing import Callable, Protocol, Sequence


MSG_TIMEOUT = "context deadline exceeded (Client.Timeout exceeded while awaiting headers)"
NOT_ONLINE_BUG = "Account not_online_error is online."
DEFAULT_SETTING_FILE: str | None = None
AUTH_CLIENT_ERROR_MARKERS = (
    "level=error",
    "level=fatal",
    "can not open auth setting file",
)
ARGV_PASSWORD_DISABLED_RETURNCODE = 126
ARGV_PASSWORD_DISABLED_MESSAGE = "默认拒绝通过 auth_client argv 传密码；接受本机进程列表暴露风险后再使用 --allow-argv-password。"
IMPLICIT_AUTH_CLIENT_NAMES = {"", "auth_client"}
ACCOUNT_RE = re.compile(r"\bAccount\s+(?P<account>\S+)\s+is\s+online\b", re.I)
USERNAME_RE = re.compile(r"\bUsername=(?P<username>\S+)")
ONLINE_FIELD_RE = re.compile(r"\bOnline=(?P<online>true|false)\b", re.I)


@dataclass(frozen=True)
class NetworkAuthCheckInfo:
    """Parsed login state reported by ``auth_client check``."""

    online: bool
    account: str | None = None
    username: str | None = None

class CompletedProcessLike(Protocol):
    """Minimal subprocess result protocol used for dependency injection."""

    args: Sequence[str]
    returncode: int
    stdout: str | None
    stderr: str | None


Runner = Callable[..., CompletedProcessLike]


@dataclass
class AuthClientCompletedProcess:
    """Small completed-process value for local error normalization."""

    args: Sequence[str]
    returncode: int
    stdout: str | None = ""
    stderr: str | None = ""


def run_auth_client(argv: Sequence[str], **kwargs: object) -> CompletedProcessLike:
    """Default subprocess runner with a stable callable type for tests."""

    return subprocess.run(list(argv), **kwargs)  # type: ignore[arg-type]


@dataclass(frozen=True)
class NetworkAuthCredentials:
    """Credentials for ECNU campus-network authentication."""

    username: str
    password: str


@dataclass(frozen=True)
class NetworkAuthResult:
    """Structured result returned by the ECNU network auth wrapper."""

    action: str
    success: bool
    returncode: int
    stdout: str
    stderr: str
    redacted_command: str
    online: bool | None = None
    account: str | None = None
    username: str | None = None
    skipped: bool = False

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable, secret-safe result mapping."""

        return asdict(self)


class NetworkAuthClient:
    """Wrapper around ECNU's external ``auth_client`` binary.

    Login fails closed unless ``allow_argv_password`` is set because the
    external binary's legacy interface exposes ``-p PASSWORD`` in process argv.
    """

    def __init__(
        self,
        auth_client_path: str | Path,
        *,
        setting_file: str | Path | None = DEFAULT_SETTING_FILE,
        runner: Runner | None = None,
        timeout: int = 20,
        allow_argv_password: bool = False,
    ) -> None:
        self.auth_client_path = str(Path(auth_client_path).expanduser())
        self.setting_file = str(Path(setting_file).expanduser()) if setting_file else None
        self.runner: Runner = runner or run_auth_client
        self.timeout = timeout
        self.allow_argv_password = allow_argv_password

    def login(self, credentials: NetworkAuthCredentials) -> NetworkAuthResult:
        """Run ``auth_client`` login with username/password."""

        if not self.allow_argv_password:
            return self._argv_password_disabled_result("login", credentials.username)

        argv = self._login_argv(credentials.username, credentials.password)
        completed = self._run(argv)
        stdout = completed.stdout or ""
        success = completed.returncode == 0 and "Login success" in stdout
        return self._result("login", argv, completed, success=success, secret_values=(credentials.password,))

    def logout(self, username: str) -> NetworkAuthResult:
        """Run ``auth_client`` logout for a username."""

        argv = [self.auth_client_path, "-u", username]
        if self.setting_file:
            argv.extend(["-c", self.setting_file])
        argv.extend(["auth", "--logout"])
        completed = self._run(argv)
        stdout = completed.stdout or ""
        success = completed.returncode == 0 and "Logout success" in stdout
        return self._result("logout", argv, completed, success=success, username=username)

    def logout_current(self) -> NetworkAuthResult:
        """Match ``mylogout``: check current session, extract Username, then logout."""

        check_result = self.check()
        username = check_result.username or check_result.account
        if check_result.success and check_result.online is False:
            return NetworkAuthResult(
                action="logout",
                success=True,
                returncode=check_result.returncode,
                stdout=check_result.stdout,
                stderr=check_result.stderr,
                redacted_command=check_result.redacted_command,
                online=False,
                account=check_result.account,
                username=check_result.username,
                skipped=True,
            )
        if not check_result.success or not username:
            return NetworkAuthResult(
                action="logout",
                success=False,
                returncode=check_result.returncode,
                stdout=check_result.stdout,
                stderr=check_result.stderr or "auth_client check did not report Username for logout.",
                redacted_command=check_result.redacted_command,
                online=check_result.online,
                account=check_result.account,
                username=check_result.username,
                skipped=False,
            )
        return self.logout(username)

    def check(self) -> NetworkAuthResult:
        """Run ``auth_client check`` and parse whether someone is online."""

        argv = [self.auth_client_path]
        if self.setting_file:
            argv.extend(["-c", self.setting_file])
        argv.append("check")
        completed = self._run(argv)
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        info = parse_check_login_info(stdout, stderr)
        success = completed.returncode == 0 and not has_auth_client_error(stdout, stderr)
        return self._result(
            "check",
            argv,
            completed,
            success=success,
            online=info.online,
            account=info.account,
            username=info.username,
        )

    def ensure_login(self, credentials: NetworkAuthCredentials) -> NetworkAuthResult:
        """Login only when ``auth_client check`` says the network session is offline."""

        check_result = self.check()
        if check_result.success and check_result.online:
            return NetworkAuthResult(
                action="ensure-login",
                success=True,
                returncode=check_result.returncode,
                stdout=check_result.stdout,
                stderr=check_result.stderr,
                redacted_command=check_result.redacted_command,
                online=True,
                account=check_result.account,
                username=check_result.username,
                skipped=True,
            )
        if not check_result.success:
            return NetworkAuthResult(
                action="ensure-login",
                success=False,
                returncode=check_result.returncode,
                stdout=check_result.stdout,
                stderr=check_result.stderr,
                redacted_command=check_result.redacted_command,
                online=check_result.online,
                account=check_result.account,
                username=check_result.username,
                skipped=False,
            )
        login_result = self.login(credentials)
        return NetworkAuthResult(
            action="ensure-login",
            success=login_result.success,
            returncode=login_result.returncode,
            stdout=login_result.stdout,
            stderr=login_result.stderr,
            redacted_command=login_result.redacted_command,
            online=False,
            skipped=False,
        )

    def _run(self, argv: Sequence[str]) -> CompletedProcessLike:
        try:
            return self.runner(
                list(argv),
                capture_output=True,
                check=False,
                shell=False,
                text=True,
                timeout=self.timeout,
            )
        except FileNotFoundError:
            return AuthClientCompletedProcess(
                args=list(argv),
                returncode=127,
                stderr=f"auth_client not found: {self.auth_client_path}",
            )
        except subprocess.TimeoutExpired:
            return AuthClientCompletedProcess(
                args=list(argv),
                returncode=124,
                stderr=f"auth_client command timed out after {self.timeout} seconds",
            )
        except OSError as exc:
            return AuthClientCompletedProcess(
                args=list(argv),
                returncode=126,
                stderr=f"auth_client execution failed: {type(exc).__name__}: {exc}",
            )

    def _login_argv(self, username: str, password: str) -> list[str]:
        argv = [self.auth_client_path, "-u", username, "-p", password]
        if self.setting_file:
            argv.extend(["-c", self.setting_file])
        return argv

    def _argv_password_disabled_result(self, action: str, username: str) -> NetworkAuthResult:
        return NetworkAuthResult(
            action=action,
            success=False,
            returncode=ARGV_PASSWORD_DISABLED_RETURNCODE,
            stdout="",
            stderr=ARGV_PASSWORD_DISABLED_MESSAGE,
            redacted_command=redact_command(self._login_argv(username, "<redacted>")),
        )

    def _result(
        self,
        action: str,
        argv: Sequence[str],
        completed: CompletedProcessLike,
        *,
        success: bool,
        online: bool | None = None,
        account: str | None = None,
        username: str | None = None,
        secret_values: Sequence[str] = (),
    ) -> NetworkAuthResult:
        return NetworkAuthResult(
            action=action,
            success=success,
            returncode=completed.returncode,
            stdout=redact_text(completed.stdout or "", secret_values),
            stderr=redact_text(completed.stderr or "", secret_values),
            redacted_command=redact_command(argv),
            online=online,
            account=account,
            username=username,
        )


def resolve_auth_client_path(configured: str | Path | None = None) -> str:
    """Resolve auth_client path, preferring the PyPI-bundled Linux binary by default."""

    configured_text = str(configured).strip() if configured is not None else ""
    if configured_text not in IMPLICIT_AUTH_CLIENT_NAMES:
        return str(Path(configured_text).expanduser())

    bundled = bundled_auth_client_path()
    if bundled:
        return bundled

    found = shutil.which("auth_client")
    return found or (configured_text or "auth_client")


def bundled_auth_client_path() -> str | None:
    """Return bundled Linux x86_64 auth_client path when supported and present."""

    if platform.system().lower() != "linux":
        return None
    machine = platform.machine().lower()
    if machine not in {"x86_64", "amd64"}:
        return None
    candidate = resource_files("chatecnu").joinpath("bin", "linux-x86_64", "auth_client")
    try:
        if candidate.is_file():
            return str(candidate)
    except OSError:
        return None
    return None


def parse_check_login_info(stdout: str, stderr: str = "") -> NetworkAuthCheckInfo:
    """Parse ``auth_client check`` stdout/stderr into online/account/username."""

    combined = f"{stdout}\n{stderr}"
    online = is_online_output(combined)
    account_match = ACCOUNT_RE.search(combined)
    username_match = USERNAME_RE.search(combined)
    account = account_match.group("account") if account_match else None
    username = username_match.group("username") if username_match else None
    if not online and (account == "not_online_error" or username == "not_online_error"):
        account = None
        username = None
    return NetworkAuthCheckInfo(online=online, account=account, username=username)


def is_online_output(output: str) -> bool:
    """Parse ``auth_client check`` output.

    ``auth_client`` has a known bug where ``Account not_online_error is online.``
    means the account is not actually online.
    """

    if MSG_TIMEOUT in output:
        return False
    if NOT_ONLINE_BUG in output or "not_online_error" in output:
        return False
    online_field = ONLINE_FIELD_RE.search(output)
    if online_field:
        return online_field.group("online").lower() == "true"
    return "is online" in output


def has_auth_client_error(stdout: str, stderr: str) -> bool:
    """Return whether auth_client logged an error despite a zero return code."""

    combined = f"{stdout}\n{stderr}".lower()
    return any(marker in combined for marker in AUTH_CLIENT_ERROR_MARKERS)


def redact_command(argv: Sequence[str]) -> str:
    """Return a shell-display string with ``-p`` argument redacted."""

    redacted: list[str] = []
    hide_next = False
    for item in argv:
        if hide_next:
            redacted.append("<redacted>")
            hide_next = False
            continue
        redacted.append(item)
        if item == "-p":
            hide_next = True
    return " ".join("<redacted>" if item == "<redacted>" else shlex.quote(item) for item in redacted)


def redact_text(text: str, secret_values: Sequence[str]) -> str:
    """Redact exact resolved secret values from subprocess output."""

    redacted = text
    for secret in secret_values:
        if secret:
            redacted = redacted.replace(secret, "<redacted>")
    return redacted


__all__ = [
    "ARGV_PASSWORD_DISABLED_MESSAGE",
    "ARGV_PASSWORD_DISABLED_RETURNCODE",
    "AUTH_CLIENT_ERROR_MARKERS",
    "DEFAULT_SETTING_FILE",
    "MSG_TIMEOUT",
    "NOT_ONLINE_BUG",
    "NetworkAuthCheckInfo",
    "NetworkAuthClient",
    "NetworkAuthCredentials",
    "NetworkAuthResult",
    "bundled_auth_client_path",
    "has_auth_client_error",
    "is_online_output",
    "parse_check_login_info",
    "redact_command",
    "redact_text",
    "resolve_auth_client_path",
]
