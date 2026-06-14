"""Click commands for ECNU self-service portal operations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import click
from chatstyle import CommandField, CommandSchema, add_interactive_option, resolve_command_inputs
from chatenv.fields import BaseEnvConfig
from chatenv.paths import get_paths

from chatnet.config import ECNUConfig
from .portal import BASE_URL

LOGIN_SCHEMA = CommandSchema(
    name="ecnu-login",
    fields=(
        CommandField("username", prompt="ECNU username", required=True),
        CommandField("password", prompt="ECNU password", required=True, sensitive=True),
        CommandField("captcha", prompt="captcha", required=True),
    ),
)

LOGIN_AUTO_SCHEMA = CommandSchema(
    name="ecnu-login-auto",
    fields=(
        CommandField("username", prompt="ECNU username", required=True),
        CommandField("password", prompt="ECNU password", required=True, sensitive=True),
    ),
)

VISITOR_CREATE_SCHEMA = CommandSchema(
    name="ecnu-visitor-create",
    fields=(CommandField("remark", prompt="visitor remark", required=True),),
)

VISITOR_UPDATE_SCHEMA = CommandSchema(
    name="ecnu-visitor-update",
    fields=(
        CommandField("visitor_id", prompt="visitor id", required=True),
        CommandField("remark", prompt="visitor remark", required=True),
        CommandField("password", prompt="visitor password", required=True, sensitive=True),
    ),
)

VISITOR_ID_SCHEMA = CommandSchema(
    name="ecnu-visitor-id",
    fields=(CommandField("visitor_id", prompt="visitor id", required=True),),
)


@click.group(name="ecnu")
@click.option("--base-url", default=None, help="ECNU portal base URL. Defaults to chatenv ECNU_BASE_URL.")
@click.option(
    "--state-file",
    default=None,
    help="Session state JSON file. Defaults to $CHATARCH_HOME/cache/chatnet/ecnu-session.json.",
)
@click.option("--cookie", default=None, help="Existing authenticated Cookie header. Defaults to chatenv ECNU_COOKIE.")
@click.option("-e", "--env", "env_profile", default=None, help="Use a named chatenv ECNU profile.")
@click.option("--env-file", default=None, help="Explicit env file override for ECNU values.")
@click.option("--timeout", default=20, show_default=True, type=int, help="HTTP timeout in seconds.")
@click.pass_context
def cli(
    ctx: click.Context,
    base_url: str | None,
    state_file: str | None,
    cookie: str | None,
    env_profile: str | None,
    env_file: str | None,
    timeout: int,
) -> None:
    """ECNU self-service portal helpers."""

    load_chatenv(env_profile=env_profile, env_file=env_file)
    ctx.obj = {
        "base_url": base_url or ECNUConfig.ECNU_BASE_URL.value or BASE_URL,
        "state_file": Path(state_file).expanduser() if state_file else default_state_file(),
        "cookie": cookie or ECNUConfig.ECNU_COOKIE.value,
        "timeout": timeout,
    }


@cli.command(name="selftest")
def selftest() -> None:
    """Run local parser self-test without network access."""

    from .portal import run_selftest

    echo_json(run_selftest())


@cli.command(name="login-init")
@click.option(
    "--captcha-path",
    default=None,
    help="Where to save the captcha image. Defaults to $CHATARCH_HOME/cache/chatnet/ecnu-login-captcha.png.",
)
@click.pass_context
def login_init(ctx: click.Context, captcha_path: str | None) -> None:
    """Fetch login page, reset session state, and download captcha."""

    target_path = Path(captcha_path).expanduser() if captcha_path else default_captcha_path()
    echo_json(call_client(ctx, lambda client: client.login_init(target_path)))


@cli.command(name="login")
@click.option("--username", default=None, help="ECNU username, or set ECNU_USERNAME.")
@click.option("--password", default=None, help="ECNU password, or set ECNU_PASSWORD.")
@click.option("--captcha", default=None, help="Captcha text from login-init image.")
@click.option("--sms-code", default=None, help="SMS code when required by the server.")
@add_interactive_option
@click.pass_context
def login(
    ctx: click.Context,
    username: str | None,
    password: str | None,
    captcha: str | None,
    sms_code: str | None,
    interactive: bool | None,
) -> None:
    """Complete login using username, password, and captcha."""

    values = resolve_command_inputs(
        schema=LOGIN_SCHEMA,
        provided={
            "username": username or ECNUConfig.ECNU_USERNAME.value,
            "password": password or ECNUConfig.ECNU_PASSWORD.value,
            "captcha": captcha,
        },
        interactive=interactive,
        usage="Usage: chatnet ecnu login --username TEXT --password TEXT --captcha TEXT [-i|-I]",
    )
    echo_json(call_client(ctx, lambda client: client.login(values["username"], values["password"], values["captcha"], sms_code=sms_code)))


@cli.command(name="login-auto")
@click.option("--username", default=None, help="ECNU username, or set ECNU_USERNAME.")
@click.option("--password", default=None, help="ECNU password, or set ECNU_PASSWORD.")
@click.option("--sms-code", default=None, help="SMS code when required by the server.")
@click.option(
    "--captcha-path",
    default=None,
    help="Where to save the latest captcha image. Defaults to $CHATARCH_HOME/cache/chatnet/ecnu-login-captcha.png.",
)
@click.option("--rounds", default=3, show_default=True, type=int, help="Captcha refresh rounds.")
@click.option("--topk", default=5, show_default=True, type=int, help="OCR candidates per captcha.")
@add_interactive_option
@click.pass_context
def login_auto(
    ctx: click.Context,
    username: str | None,
    password: str | None,
    sms_code: str | None,
    captcha_path: str | None,
    rounds: int,
    topk: int,
    interactive: bool | None,
) -> None:
    """Auto-solve captcha with optional OCR dependencies and try login."""

    values = resolve_command_inputs(
        schema=LOGIN_AUTO_SCHEMA,
        provided={"username": username or ECNUConfig.ECNU_USERNAME.value, "password": password or ECNUConfig.ECNU_PASSWORD.value},
        interactive=interactive,
        usage="Usage: chatnet ecnu login-auto --username TEXT --password TEXT [-i|-I]",
    )
    target_path = Path(captcha_path).expanduser() if captcha_path else default_captcha_path()
    echo_json(
        call_client(
            ctx,
            lambda client: client.login_auto(
                values["username"],
                values["password"],
                sms_code=sms_code,
                rounds=rounds,
                topk=topk,
                captcha_path=target_path,
            ),
        )
    )


@cli.command(name="session-info")
@click.pass_context
def session_info(ctx: click.Context) -> None:
    """Show saved session metadata with Cookie values redacted."""

    echo_json(redact_state(make_client(ctx).state))


@cli.command(name="cookie-header")
@click.pass_context
def cookie_header(ctx: click.Context) -> None:
    """Print the current Cookie header from state/session."""

    click.echo(make_client(ctx).cookie_header())


@cli.command(name="logout")
@click.pass_context
def logout(ctx: click.Context) -> None:
    """Logout and update saved session state."""

    echo_json(call_client(ctx, lambda client: client.logout()))


@cli.command(name="home")
@click.pass_context
def home(ctx: click.Context) -> None:
    """Fetch home summary."""

    echo_json(call_client(ctx, lambda client: client.home_summary()))


@cli.command(name="user-info")
@click.pass_context
def user_info(ctx: click.Context) -> None:
    """Fetch user information."""

    echo_json(call_client(ctx, lambda client: client.user_info()))


@cli.command(name="auth-log")
@click.option("--start", default=None, help="Start time.")
@click.option("--end", default=None, help="End time.")
@click.option("--limit", default=None, type=int, help="Maximum rows to print.")
@click.pass_context
def auth_log(ctx: click.Context, start: str | None, end: str | None, limit: int | None) -> None:
    """Query authentication logs."""

    echo_json(call_client(ctx, lambda client: client.auth_logs(start, end, limit)))


@cli.command(name="detail-log")
@click.option("--start", default=None, help="Start time.")
@click.option("--end", default=None, help="End time.")
@click.option("--limit", default=None, type=int, help="Maximum rows to print.")
@click.pass_context
def detail_log(ctx: click.Context, start: str | None, end: str | None, limit: int | None) -> None:
    """Query network detail logs."""

    echo_json(call_client(ctx, lambda client: client.detail_logs(start, end, limit)))


@cli.group(name="visitor")
def visitor_group() -> None:
    """Visitor account management."""


@visitor_group.command(name="list")
@click.pass_context
def visitor_list(ctx: click.Context) -> None:
    """List visitor accounts."""

    echo_json(call_client(ctx, lambda client: client.list_visitors()))


@visitor_group.command(name="get")
@click.option("--id", "visitor_id", default=None, help="Visitor record id.")
@click.option("--account", default=None, help="Visitor account name.")
@click.pass_context
def visitor_get(ctx: click.Context, visitor_id: str | None, account: str | None) -> None:
    """Get one visitor by id or account."""

    if not visitor_id and not account:
        raise click.UsageError("Provide either --id or --account.")
    echo_json(call_client(ctx, lambda client: client.get_visitor(visitor_id=visitor_id, account=account)))


@visitor_group.command(name="create")
@click.option("--remark", default=None, help="Visitor remark, 2-14 Chinese or English letters.")
@click.option("--dry-run", is_flag=True, help="Print request spec without submitting.")
@add_interactive_option
@click.pass_context
def visitor_create(ctx: click.Context, remark: str | None, dry_run: bool, interactive: bool | None) -> None:
    """Create a visitor account."""

    values = resolve_command_inputs(
        schema=VISITOR_CREATE_SCHEMA,
        provided={"remark": remark},
        interactive=interactive,
        usage="Usage: chatnet ecnu visitor create --remark TEXT [-i|-I]",
    )
    echo_json(call_client(ctx, lambda client: client.create_visitor(values["remark"], dry_run=dry_run)))


@visitor_group.command(name="update")
@click.option("--id", "visitor_id", default=None, help="Visitor record id.")
@click.option("--remark", default=None, help="Visitor remark, 2-14 Chinese or English letters.")
@click.option("--password", default=None, help="New visitor password.")
@click.option("--dry-run", is_flag=True, help="Print request spec without submitting.")
@add_interactive_option
@click.pass_context
def visitor_update(
    ctx: click.Context,
    visitor_id: str | None,
    remark: str | None,
    password: str | None,
    dry_run: bool,
    interactive: bool | None,
) -> None:
    """Update visitor remark and password."""

    values = resolve_command_inputs(
        schema=VISITOR_UPDATE_SCHEMA,
        provided={"visitor_id": visitor_id, "remark": remark, "password": password},
        interactive=interactive,
        usage="Usage: chatnet ecnu visitor update --id ID --remark TEXT --password TEXT [-i|-I]",
    )
    echo_json(
        call_client(
            ctx,
            lambda client: client.update_visitor(
                values["visitor_id"],
                values["remark"],
                values["password"],
                dry_run=dry_run,
            ),
        )
    )


@visitor_group.command(name="delete")
@click.option("--id", "visitor_id", default=None, help="Visitor record id.")
@click.option("--dry-run", is_flag=True, help="Print request spec without submitting.")
@add_interactive_option
@click.pass_context
def visitor_delete(ctx: click.Context, visitor_id: str | None, dry_run: bool, interactive: bool | None) -> None:
    """Delete a visitor account."""

    values = resolve_command_inputs(
        schema=VISITOR_ID_SCHEMA,
        provided={"visitor_id": visitor_id},
        interactive=interactive,
        usage="Usage: chatnet ecnu visitor delete --id ID [-i|-I]",
    )
    echo_json(call_client(ctx, lambda client: client.delete_visitor(values["visitor_id"], dry_run=dry_run)))


@visitor_group.command(name="lock")
@click.option("--id", "visitor_id", default=None, help="Visitor record id.")
@click.option("--dry-run", is_flag=True, help="Print request spec without submitting.")
@add_interactive_option
@click.pass_context
def visitor_lock(ctx: click.Context, visitor_id: str | None, dry_run: bool, interactive: bool | None) -> None:
    """Lock a visitor account."""

    values = resolve_command_inputs(
        schema=VISITOR_ID_SCHEMA,
        provided={"visitor_id": visitor_id},
        interactive=interactive,
        usage="Usage: chatnet ecnu visitor lock --id ID [-i|-I]",
    )
    echo_json(call_client(ctx, lambda client: client.lock_visitor(values["visitor_id"], dry_run=dry_run)))


def make_client(ctx: click.Context) -> Any:
    from .portal import PortalClient

    config = ctx.find_root().obj or ctx.obj or {}
    return PortalClient(
        base_url=config["base_url"],
        state_file=config["state_file"],
        cookie_header=config.get("cookie"),
        timeout=config["timeout"],
    )


def call_client(ctx: click.Context, func: Callable[[Any], Any]) -> Any:
    try:
        return func(make_client(ctx))
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc


def echo_json(data: Any) -> None:
    click.echo(json.dumps(data, ensure_ascii=False, indent=2))


def load_chatenv(env_profile: str | None = None, env_file: str | None = None) -> None:
    envs_dir = get_paths().envs_dir
    if env_profile:
        BaseEnvConfig.load_all_with_override(
            envs_dir,
            ECNUConfig.get_profile_env_file(envs_dir, env_profile),
        )
        return
    if env_file:
        BaseEnvConfig.load_all_with_override(envs_dir, Path(env_file).expanduser())
        return
    BaseEnvConfig.load_all(envs_dir)


def default_state_file() -> Path:
    return get_paths().home_dir / "cache" / "chatnet" / "ecnu-session.json"


def default_captcha_path() -> Path:
    return get_paths().home_dir / "cache" / "chatnet" / "ecnu-login-captcha.png"


def redact_state(state: dict[str, Any]) -> dict[str, Any]:
    redacted = dict(state)
    cookies = redacted.get("cookies")
    if isinstance(cookies, dict):
        redacted["cookies"] = {key: "***" for key in cookies}
    return redacted
