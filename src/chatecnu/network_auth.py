"""ECNU campus-network ``auth_client`` wrapper.

This module intentionally wraps an external ``auth_client`` executable instead
of vendoring the binary. The upstream ECNU scripts shell out to a Linux-only
client distributed outside ChatECNU. That binary appears to accept passwords
only through ``-p`` argv, so ChatECNU fails closed by default and requires an
explicit unsafe opt-in before using that legacy argv-password channel.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import shlex
import subprocess
from typing import Callable, Protocol, Sequence


MSG_TIMEOUT = "context deadline exceeded (Client.Timeout exceeded while awaiting headers)"
NOT_ONLINE_BUG = "Account not_online_error is online."
DEFAULT_SETTING_FILE = "auth_setting"
ARGV_PASSWORD_DISABLED_RETURNCODE = 126
ARGV_PASSWORD_DISABLED_MESSAGE = (
    "Refusing to pass ECNU password through auth_client process argv. "
    "The upstream auth_client binary appears to support only '-p PASSWORD'; "
    "use CLI --allow-argv-password or the API allow_argv_password opt-in "
    "only after accepting local process-list exposure."
)


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
        return self._result("logout", argv, completed, success=success)

    def check(self) -> NetworkAuthResult:
        """Run ``auth_client check`` and parse whether someone is online."""

        argv = [self.auth_client_path]
        if self.setting_file:
            argv.extend(["-c", self.setting_file])
        argv.append("check")
        completed = self._run(argv)
        stdout = completed.stdout or ""
        online = is_online_output(stdout)
        return self._result("check", argv, completed, success=completed.returncode == 0, online=online)

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
        )


def is_online_output(output: str) -> bool:
    """Parse ``auth_client check`` output.

    ``auth_client`` has a known bug where ``Account not_online_error is online.``
    means the account is not actually online.
    """

    if MSG_TIMEOUT in output:
        return False
    if NOT_ONLINE_BUG in output:
        return False
    return "is online" in output


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
    "DEFAULT_SETTING_FILE",
    "MSG_TIMEOUT",
    "NOT_ONLINE_BUG",
    "NetworkAuthClient",
    "NetworkAuthCredentials",
    "NetworkAuthResult",
    "is_online_output",
    "redact_command",
    "redact_text",
]
