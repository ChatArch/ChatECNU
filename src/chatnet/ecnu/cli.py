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

VISITOR_DEFAULT_SCHEMA = CommandSchema(
    name="ecnu-visitor-default",
    fields=(CommandField("password1", prompt="visitor password1", required=True, sensitive=True),),
)


@click.group(name="ecnu")
@click.option(
    "--base-url",
    default=None,
    hidden=True,
    help="ECNU portal base URL. Defaults to chatenv ECNU_BASE_URL.",
)
@click.option(
    "--state-file",
    default=None,
    hidden=True,
    help="Session state JSON file. Defaults to $CHATARCH_HOME/cache/chatnet/ecnu-session.json.",
)
@click.option(
    "--cookie",
    default=None,
    hidden=True,
    help="Existing authenticated Cookie header. Defaults to chatenv ECNU_COOKIE.",
)
@click.option("-e", "--env", "env_profile", default=None, help="Use a named chatenv ECNU profile.")
@click.option("--env-file", default=None, hidden=True, help="Explicit env file override for ECNU values.")
@click.option("--timeout", default=20, show_default=True, type=int, hidden=True, help="HTTP timeout in seconds.")
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


@cli.command(name="selftest", hidden=True)
def selftest() -> None:
    """Run local parser self-test without network access."""

    from .portal import run_selftest

    echo_json(run_selftest())


@cli.command(name="login-init", hidden=True)
@click.option(
    "--captcha-path",
    default=None,
    hidden=True,
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
@click.option("--captcha", default=None, hidden=True, help="Captcha text from login-init image.")
@click.option("--sms-code", default=None, help="SMS code when required by the server.")
@click.option(
    "--captcha-path",
    default=None,
    hidden=True,
    help="Where to save the latest captcha image. Defaults to $CHATARCH_HOME/cache/chatnet/ecnu-login-captcha.png.",
)
@click.option("--rounds", default=3, show_default=True, type=int, hidden=True, help="Captcha refresh rounds.")
@click.option("--topk", default=5, show_default=True, type=int, hidden=True, help="OCR candidates per captcha.")
@click.option("--json", "json_output", is_flag=True, help="Print raw JSON instead of a human summary.")
@add_interactive_option
@click.pass_context
def login(
    ctx: click.Context,
    username: str | None,
    password: str | None,
    captcha: str | None,
    sms_code: str | None,
    captcha_path: str | None,
    rounds: int,
    topk: int,
    json_output: bool,
    interactive: bool | None,
) -> None:
    """Login to ECNU. Uses OCR-backed captcha solving unless --captcha is provided."""

    values = resolve_login_inputs(username=username, password=password, interactive=interactive, command_name="login")
    target_path = Path(captcha_path).expanduser() if captcha_path else default_captcha_path()
    if captcha:
        result = call_client(
            ctx,
            lambda client: client.login(values["username"], values["password"], captcha, sms_code=sms_code),
        )
    else:
        result = call_client(
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
    emit_login_result(result, json_output=json_output)


@cli.command(name="login-auto", hidden=True)
@click.option("--username", default=None, help="ECNU username, or set ECNU_USERNAME.")
@click.option("--password", default=None, help="ECNU password, or set ECNU_PASSWORD.")
@click.option("--sms-code", default=None, help="SMS code when required by the server.")
@click.option(
    "--captcha-path",
    default=None,
    hidden=True,
    help="Where to save the latest captcha image. Defaults to $CHATARCH_HOME/cache/chatnet/ecnu-login-captcha.png.",
)
@click.option("--rounds", default=3, show_default=True, type=int, hidden=True, help="Captcha refresh rounds.")
@click.option("--topk", default=5, show_default=True, type=int, hidden=True, help="OCR candidates per captcha.")
@click.option("--json", "json_output", is_flag=True, hidden=True, help="Print raw JSON instead of a human summary.")
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
    json_output: bool,
    interactive: bool | None,
) -> None:
    """Hidden compatibility alias for OCR-backed login."""

    values = resolve_login_inputs(username=username, password=password, interactive=interactive, command_name="login-auto")
    target_path = Path(captcha_path).expanduser() if captcha_path else default_captcha_path()
    result = call_client(
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
    emit_login_result(result, json_output=json_output)


@cli.command(name="status")
@click.option("--json", "json_output", is_flag=True, help="Print raw JSON instead of a human summary.")
@click.pass_context
def status(ctx: click.Context, json_output: bool) -> None:
    """Show saved login/session status with Cookie values redacted."""

    emit_status_result(session_status(ctx), json_output=json_output)


@cli.command(name="session-info", hidden=True)
@click.option("--json", "json_output", is_flag=True, hidden=True, help="Print raw JSON instead of a human summary.")
@click.pass_context
def session_info(ctx: click.Context, json_output: bool) -> None:
    """Show saved session metadata with Cookie values redacted."""

    emit_status_result(session_status(ctx), json_output=json_output)


@cli.command(name="cookie-header", hidden=True)
@click.pass_context
def cookie_header(ctx: click.Context) -> None:
    """Print the current Cookie header from state/session."""

    click.echo(make_client(ctx).cookie_header())


@cli.command(name="logout")
@click.option("--json", "json_output", is_flag=True, help="Print raw JSON instead of a human summary.")
@click.pass_context
def logout(ctx: click.Context, json_output: bool) -> None:
    """Logout and update saved session state."""

    emit_simple_result(
        call_client(ctx, lambda client: client.logout()),
        json_output=json_output,
        success_message="Logout succeeded.",
        failure_message="Logout may not have completed cleanly.",
    )


@cli.command(name="home")
@click.option("--json", "json_output", is_flag=True, help="Print raw JSON instead of a human summary.")
@click.pass_context
def home(ctx: click.Context, json_output: bool) -> None:
    """Fetch home summary."""

    emit_home_result(call_client(ctx, lambda client: client.home_summary()), json_output=json_output)


@cli.command(name="user-info")
@click.option("--json", "json_output", is_flag=True, help="Print raw JSON instead of a human summary.")
@click.pass_context
def user_info(ctx: click.Context, json_output: bool) -> None:
    """Fetch user information."""

    emit_mapping_result(
        call_client(ctx, lambda client: client.user_info()),
        json_output=json_output,
        empty_message="No user information returned.",
    )


@cli.group(name="debug", hidden=True)
def debug_group() -> None:
    """Hidden diagnostics and low-level queries."""


@debug_group.command(name="auth-log")
@click.option("--start", default=None, help="Start time.")
@click.option("--end", default=None, help="End time.")
@click.option("--limit", default=None, type=int, help="Maximum rows to print.")
@click.option("--json", "json_output", is_flag=True, hidden=True, help="Print raw JSON instead of a human summary.")
@click.pass_context
def auth_log(ctx: click.Context, start: str | None, end: str | None, limit: int | None, json_output: bool) -> None:
    """Query authentication logs."""

    emit_log_result(
        call_client(ctx, lambda client: client.auth_logs(start, end, limit)),
        json_output=json_output,
        title="Authentication logs",
    )


@debug_group.command(name="detail-log")
@click.option("--start", default=None, help="Start time.")
@click.option("--end", default=None, help="End time.")
@click.option("--limit", default=None, type=int, help="Maximum rows to print.")
@click.option("--json", "json_output", is_flag=True, hidden=True, help="Print raw JSON instead of a human summary.")
@click.pass_context
def detail_log(ctx: click.Context, start: str | None, end: str | None, limit: int | None, json_output: bool) -> None:
    """Query network detail logs."""

    emit_log_result(
        call_client(ctx, lambda client: client.detail_logs(start, end, limit)),
        json_output=json_output,
        title="Network detail logs",
    )


@cli.command(name="auth-log", hidden=True)
@click.option("--start", default=None, help="Start time.")
@click.option("--end", default=None, help="End time.")
@click.option("--limit", default=None, type=int, help="Maximum rows to print.")
@click.option("--json", "json_output", is_flag=True, hidden=True, help="Print raw JSON instead of a human summary.")
@click.pass_context
def auth_log_alias(ctx: click.Context, start: str | None, end: str | None, limit: int | None, json_output: bool) -> None:
    """Hidden compatibility alias for debug auth-log."""

    emit_log_result(
        call_client(ctx, lambda client: client.auth_logs(start, end, limit)),
        json_output=json_output,
        title="Authentication logs",
    )


@cli.command(name="detail-log", hidden=True)
@click.option("--start", default=None, help="Start time.")
@click.option("--end", default=None, help="End time.")
@click.option("--limit", default=None, type=int, help="Maximum rows to print.")
@click.option("--json", "json_output", is_flag=True, hidden=True, help="Print raw JSON instead of a human summary.")
@click.pass_context
def detail_log_alias(ctx: click.Context, start: str | None, end: str | None, limit: int | None, json_output: bool) -> None:
    """Hidden compatibility alias for debug detail-log."""

    emit_log_result(
        call_client(ctx, lambda client: client.detail_logs(start, end, limit)),
        json_output=json_output,
        title="Network detail logs",
    )


@cli.group(name="visitor")
def visitor_group() -> None:
    """Visitor account management."""


@visitor_group.command(name="list")
@click.option("--json", "json_output", is_flag=True, help="Print raw JSON instead of a human summary.")
@click.pass_context
def visitor_list(ctx: click.Context, json_output: bool) -> None:
    """List visitor accounts."""

    emit_visitor_list_result(call_client(ctx, lambda client: client.list_visitors()), json_output=json_output)


@visitor_group.command(name="get")
@click.option("--id", "visitor_id", default=None, help="Visitor record id.")
@click.option("--account", default=None, help="Visitor account name.")
@click.option("--json", "json_output", is_flag=True, help="Print raw JSON instead of a human summary.")
@click.pass_context
def visitor_get(ctx: click.Context, visitor_id: str | None, account: str | None, json_output: bool) -> None:
    """Get one visitor by id or account."""

    if not visitor_id and not account:
        raise click.UsageError("Provide either --id or --account.")
    emit_mapping_result(
        call_client(ctx, lambda client: client.get_visitor(visitor_id=visitor_id, account=account)),
        json_output=json_output,
        empty_message="Visitor not found.",
    )


@visitor_group.command(name="create")
@click.option("--remark", default=None, help="Visitor remark, 2-14 Chinese or English letters.")
@click.option("--dry-run", is_flag=True, help="Print request spec without submitting.")
@click.option("--json", "json_output", is_flag=True, help="Print raw JSON instead of a human summary.")
@add_interactive_option
@click.pass_context
def visitor_create(
    ctx: click.Context,
    remark: str | None,
    dry_run: bool,
    json_output: bool,
    interactive: bool | None,
) -> None:
    """Create a visitor account."""

    values = resolve_command_inputs(
        schema=VISITOR_CREATE_SCHEMA,
        provided={"remark": remark},
        interactive=interactive,
        usage="Usage: chatnet ecnu visitor create --remark TEXT [-i|-I]",
    )
    emit_mutation_result(
        call_client(ctx, lambda client: client.create_visitor(values["remark"], dry_run=dry_run)),
        json_output=json_output,
        action="Create visitor",
    )


@visitor_group.command(name="default")
@click.option("--password1", default=None, help="Password for default visitor account suffix m1.")
@click.option("--password2", default=None, help="Password for default visitor account suffix m2.")
@click.option("--remark", default=None, help="Remark for default visitor account(s). Defaults to ECNU_VISITOR_REMARK.")
@click.option("--json", "json_output", is_flag=True, help="Print raw JSON instead of a human summary.")
@add_interactive_option
@click.pass_context
def visitor_default(
    ctx: click.Context,
    password1: str | None,
    password2: str | None,
    remark: str | None,
    json_output: bool,
    interactive: bool | None,
) -> None:
    """Ensure default visitor account(s) exist and update their passwords."""

    resolved = resolve_default_visitor_inputs(
        password1=password1,
        password2=password2,
        remark=remark,
        interactive=interactive,
    )
    result = call_client(
        ctx,
        lambda client: ensure_default_visitors(
            client,
            username_prefix=resolved["username_prefix"],
            password1=resolved["password1"],
            password2=resolved["password2"],
            remark=resolved["remark"],
        ),
    )
    emit_default_visitor_result(result, json_output=json_output)


@visitor_group.command(name="update")
@click.option("--id", "visitor_id", default=None, help="Visitor record id.")
@click.option("--remark", default=None, help="Visitor remark, 2-14 Chinese or English letters.")
@click.option("--password", default=None, help="New visitor password.")
@click.option("--dry-run", is_flag=True, help="Print request spec without submitting.")
@click.option("--json", "json_output", is_flag=True, help="Print raw JSON instead of a human summary.")
@add_interactive_option
@click.pass_context
def visitor_update(
    ctx: click.Context,
    visitor_id: str | None,
    remark: str | None,
    password: str | None,
    dry_run: bool,
    json_output: bool,
    interactive: bool | None,
) -> None:
    """Update visitor remark and password."""

    values = resolve_command_inputs(
        schema=VISITOR_UPDATE_SCHEMA,
        provided={"visitor_id": visitor_id, "remark": remark, "password": password},
        interactive=interactive,
        usage="Usage: chatnet ecnu visitor update --id ID --remark TEXT --password TEXT [-i|-I]",
    )
    emit_mutation_result(
        call_client(
            ctx,
            lambda client: client.update_visitor(
                values["visitor_id"],
                values["remark"],
                values["password"],
                dry_run=dry_run,
            ),
        ),
        json_output=json_output,
        action="Update visitor",
    )


@visitor_group.command(name="delete")
@click.option("--id", "visitor_id", default=None, help="Visitor record id.")
@click.option("--dry-run", is_flag=True, help="Print request spec without submitting.")
@click.option("--json", "json_output", is_flag=True, help="Print raw JSON instead of a human summary.")
@add_interactive_option
@click.pass_context
def visitor_delete(
    ctx: click.Context,
    visitor_id: str | None,
    dry_run: bool,
    json_output: bool,
    interactive: bool | None,
) -> None:
    """Delete a visitor account."""

    values = resolve_command_inputs(
        schema=VISITOR_ID_SCHEMA,
        provided={"visitor_id": visitor_id},
        interactive=interactive,
        usage="Usage: chatnet ecnu visitor delete --id ID [-i|-I]",
    )
    emit_mutation_result(
        call_client(ctx, lambda client: client.delete_visitor(values["visitor_id"], dry_run=dry_run)),
        json_output=json_output,
        action="Delete visitor",
    )


@visitor_group.command(name="lock", hidden=True)
@click.option("--id", "visitor_id", default=None, help="Visitor record id.")
@click.option("--dry-run", is_flag=True, help="Print request spec without submitting.")
@click.option("--json", "json_output", is_flag=True, hidden=True, help="Print raw JSON instead of a human summary.")
@add_interactive_option
@click.pass_context
def visitor_lock(
    ctx: click.Context,
    visitor_id: str | None,
    dry_run: bool,
    json_output: bool,
    interactive: bool | None,
) -> None:
    """Lock a visitor account."""

    values = resolve_command_inputs(
        schema=VISITOR_ID_SCHEMA,
        provided={"visitor_id": visitor_id},
        interactive=interactive,
        usage="Usage: chatnet ecnu visitor lock --id ID [-i|-I]",
    )
    emit_mutation_result(
        call_client(ctx, lambda client: client.lock_visitor(values["visitor_id"], dry_run=dry_run)),
        json_output=json_output,
        action="Lock visitor",
    )


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


def emit_login_result(result: dict[str, Any], *, json_output: bool) -> None:
    if json_output:
        echo_json(result)
        return
    click.echo(format_login_summary(result))


def emit_status_result(result: dict[str, Any], *, json_output: bool) -> None:
    if json_output:
        echo_json(result)
        return
    click.echo(format_status_summary(result))


def emit_home_result(result: dict[str, Any], *, json_output: bool) -> None:
    if json_output:
        echo_json(result)
        return
    click.echo(format_home_summary(result))


def emit_log_result(result: dict[str, Any], *, json_output: bool, title: str) -> None:
    if json_output:
        echo_json(result)
        return
    click.echo(format_log_summary(result, title=title))


def emit_mapping_result(result: dict[str, Any], *, json_output: bool, empty_message: str) -> None:
    if json_output:
        echo_json(result)
        return
    click.echo(format_mapping_summary(result, empty_message=empty_message))


def emit_simple_result(
    result: dict[str, Any],
    *,
    json_output: bool,
    success_message: str,
    failure_message: str,
) -> None:
    if json_output:
        echo_json(result)
        return
    click.echo(success_message if result.get("success") else failure_message)


def emit_visitor_list_result(result: dict[str, Any], *, json_output: bool) -> None:
    if json_output:
        echo_json(result)
        return
    click.echo(format_visitor_list_summary(result))


def emit_mutation_result(result: dict[str, Any], *, json_output: bool, action: str) -> None:
    if json_output:
        echo_json(result)
        return
    click.echo(format_mutation_summary(result, action=action))


def emit_default_visitor_result(result: dict[str, Any], *, json_output: bool) -> None:
    if json_output:
        echo_json(result)
        return
    click.echo(format_default_visitor_summary(result))


def format_login_summary(result: dict[str, Any]) -> str:
    if "attempts" in result:
        return format_auto_login_summary(result)
    return format_manual_login_summary(result)


def format_auto_login_summary(result: dict[str, Any]) -> str:
    attempts = result.get("attempts") or []
    round_count = len(attempts)
    candidate_count = sum(len(item.get("attempts") or []) for item in attempts)
    if result.get("success"):
        final_candidate = ""
        if attempts:
            last_round = attempts[-1].get("attempts") or []
            if last_round:
                final_candidate = last_round[-1].get("candidate") or ""
        lines = [
            "Login succeeded.",
            f"Rounds tried: {round_count}",
            f"Captcha attempts: {candidate_count}",
        ]
        if final_candidate:
            lines.append(f"Accepted captcha candidate: {final_candidate}")
        return "\n".join(lines)
    message = result.get("message") or "Login failed."
    lines = [
        "Login failed.",
        message,
        f"Rounds tried: {round_count}",
        f"Captcha attempts: {candidate_count}",
    ]
    if result.get("aborted"):
        lines.append("Stopped early because the server returned a non-retryable response.")
    return "\n".join(lines)


def format_manual_login_summary(result: dict[str, Any]) -> str:
    validated = result.get("validate_user") or {}
    submit = result.get("submit_login") or {}
    sms = result.get("validate_sms") or {}
    if submit.get("success"):
        return "Login succeeded."
    lines = ["Login failed."]
    if result.get("message"):
        lines.append(result["message"])
    elif sms and not sms.get("success"):
        lines.append(str(sms.get("message") or "SMS verification failed."))
    elif validated and not validated.get("success"):
        lines.append(str(validated.get("message") or "Username, password, or captcha was rejected."))
    elif submit.get("error"):
        lines.append(str(submit["error"]))
    return "\n".join(lines)


def format_status_summary(result: dict[str, Any]) -> str:
    cookies = result.get("cookies")
    username = result.get("username") or "(unknown)"
    lines = [f"Username: {username}"]
    if result.get("authenticated_at"):
        lines.append(f"Authenticated at: {result['authenticated_at']}")
    else:
        lines.append("Authenticated at: not logged in")
    lines.append(f"Cookies saved: {len(cookies) if isinstance(cookies, dict) else 0}")
    if result.get("base_url"):
        lines.append(f"Base URL: {result['base_url']}")
    return "\n".join(lines)


def format_home_summary(result: dict[str, Any]) -> str:
    user_info = result.get("user_info") or {}
    online_info = result.get("online_info") or []
    product_info = result.get("product_info") or []
    lines = ["Home summary"]
    if user_info:
        for key, value in user_info.items():
            lines.append(f"{key}: {value}")
    lines.append(f"Online sessions: {len(online_info)}")
    lines.append(f"Products: {len(product_info)}")
    return "\n".join(lines)


def format_log_summary(result: dict[str, Any], *, title: str) -> str:
    rows = result.get("rows") or []
    lines = [title]
    if result.get("summary"):
        lines.append(str(result["summary"]))
    lines.append(f"Rows: {len(rows)}")
    for row in rows[:3]:
        lines.append("- " + ", ".join(f"{key}={value}" for key, value in row.items()))
    return "\n".join(lines)


def format_mapping_summary(result: dict[str, Any], *, empty_message: str) -> str:
    if not result:
        return empty_message
    return "\n".join(f"{key}: {value}" for key, value in result.items())


def format_visitor_list_summary(result: dict[str, Any]) -> str:
    rows = result.get("rows") or []
    lines = ["Visitor accounts"]
    if result.get("summary"):
        lines.append(str(result["summary"]))
    lines.append(f"Count: {result.get('count', len(rows))}")
    for row in rows[:5]:
        lines.append(
            "- "
            + ", ".join(
                [
                    f"id={row.get('visitor_id')}",
                    f"account={row.get('account')}",
                    f"status={row.get('status')}",
                    f"remark={row.get('remark')}",
                ]
            )
        )
    return "\n".join(lines)


def format_mutation_summary(result: dict[str, Any], *, action: str) -> str:
    if result.get("dry_run"):
        return f"{action}: dry run ready."
    response = result.get("response") or {}
    if isinstance(response, dict) and "password" in response and "account" in response:
        lines = [f"{action}: success.", f"Account: {response['account']}"]
        if response.get("password"):
            lines.append(f"Initial password: {response['password']}")
        return "\n".join(lines)
    if isinstance(response, dict) and response.get("ok"):
        return f"{action}: success."
    return f"{action}: completed."


def format_default_visitor_summary(result: dict[str, Any]) -> str:
    items = result.get("visitors") or []
    lines = [f"Default visitor sync complete. Accounts: {len(items)}"]
    for item in items:
        created = "created" if item.get("created") else "existing"
        lines.append(
            "- "
            + ", ".join(
                [
                    f"account={item.get('account')}",
                    f"id={item.get('visitor_id')}",
                    f"state={created}",
                    f"remark={item.get('remark')}",
                    f"password_updated={item.get('password_updated')}",
                ]
            )
        )
    return "\n".join(lines)


def resolve_login_inputs(
    *,
    username: str | None,
    password: str | None,
    interactive: bool | None,
    captcha: str | None = None,
    include_captcha: bool = False,
    command_name: str = "login",
) -> dict[str, str]:
    schema = LOGIN_SCHEMA if include_captcha else LOGIN_AUTO_SCHEMA
    provided = {
        "username": username or ECNUConfig.ECNU_USERNAME.value,
        "password": password or ECNUConfig.ECNU_PASSWORD.value,
    }
    usage = f"Usage: chatnet ecnu {command_name} --username TEXT --password TEXT [-i|-I]"
    if include_captcha:
        provided["captcha"] = captcha
        usage = "Usage: chatnet ecnu login --username TEXT --password TEXT --captcha TEXT [-i|-I]"
    return resolve_command_inputs(schema=schema, provided=provided, interactive=interactive, usage=usage)


def resolve_default_visitor_inputs(
    *,
    password1: str | None,
    password2: str | None,
    remark: str | None,
    interactive: bool | None,
) -> dict[str, str]:
    values = resolve_command_inputs(
        schema=VISITOR_DEFAULT_SCHEMA,
        provided={"password1": password1 or ECNUConfig.ECNU_VISITOR_PASSWORD1.value},
        interactive=interactive,
        usage="Usage: chatnet ecnu visitor default --password1 TEXT [--password2 TEXT] [--remark TEXT] [-i|-I]",
    )
    resolved_password1 = values["password1"]
    resolved_password2 = password2 or ECNUConfig.ECNU_VISITOR_PASSWORD2.value
    if not resolved_password1 and not resolved_password2:
        raise click.UsageError(
            "Set ECNU_VISITOR_PASSWORD1 (and optionally ECNU_VISITOR_PASSWORD2) or pass --password1/--password2."
        )
    if resolved_password2 and not resolved_password1:
        raise click.UsageError("Password2 requires password1 so the default visitor order remains deterministic.")
    username_prefix = ECNUConfig.ECNU_USERNAME.value
    if not username_prefix:
        raise click.UsageError("ECNU_USERNAME must be set before running `chatnet ecnu visitor default`.")
    return {
        "username_prefix": username_prefix,
        "password1": resolved_password1,
        "password2": resolved_password2 or "",
        "remark": remark or ECNUConfig.ECNU_VISITOR_REMARK.value or "default",
    }


def session_status(ctx: click.Context) -> dict[str, Any]:
    return redact_state(make_client(ctx).state)


def ensure_default_visitors(
    client: Any,
    *,
    username_prefix: str,
    password1: str,
    password2: str,
    remark: str,
) -> dict[str, Any]:
    desired = [(1, password1)]
    if password2:
        desired.append((2, password2))

    visitors = client.list_visitors()
    rows = visitors.get("rows") or []
    results: list[dict[str, Any]] = []

    for suffix, password in desired:
        target_account = f"{username_prefix}m{suffix}"
        row = find_visitor_row(rows, target_account)
        created = False
        if row is None:
            client.create_visitor(remark, dry_run=False)
            created = True
            rows = (client.list_visitors().get("rows") or [])
            row = find_visitor_row(rows, target_account)
            if row is None:
                raise click.ClickException(f"Visitor account {target_account} was not found after creation.")
        client.update_visitor(row["visitor_id"], remark, password, dry_run=False)
        results.append(
            {
                "account": target_account,
                "visitor_id": row["visitor_id"],
                "created": created,
                "remark": remark,
                "password_updated": True,
            }
        )
    return {"count": len(results), "visitors": results}


def find_visitor_row(rows: list[dict[str, Any]], account: str) -> dict[str, Any] | None:
    for row in rows:
        if row.get("account") == account:
            return row
    return None


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
