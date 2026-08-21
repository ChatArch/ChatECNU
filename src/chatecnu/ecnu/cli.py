"""Click commands for ECNU self-service portal operations."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Callable

import click
from chatenv import TokenStore
from chatenv.fields import BaseEnvConfig
from chatenv.paths import get_paths
from chatstyle import (
    CommandField,
    CommandSchema,
    add_interactive_option,
    add_tree_option,
    resolve_command_inputs,
)

from chatecnu import __version__
from chatecnu.config import ECNUConfig
from chatecnu.network_auth import (
    DEFAULT_SETTING_FILE,
    NetworkAuthClient,
    NetworkAuthCredentials,
    NetworkAuthResult,
    redact_text,
    resolve_auth_client_path,
)
from .portal import BASE_URL
from .session_tokens import ECNU_SESSION_SERVICE, portal_session_profile


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

NETWORK_AUTH_LOGIN_SCHEMA = CommandSchema(
    name="ecnu-net-login",
    fields=(
        CommandField("username", prompt="ECNU username", required=True),
        CommandField("password", prompt="ECNU password", required=True, sensitive=True),
    ),
)

NETWORK_AUTH_USERNAME_SCHEMA = CommandSchema(
    name="ecnu-network-username",
    fields=(CommandField("username", prompt="ECNU username", required=True),),
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
@click.version_option(__version__)
@add_tree_option(renderer_options={"root_name": "ecnu"})
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
    help="Explicit legacy session state JSON file. Defaults to ChatEnv token-store tokens/ECNU/<profile>.json.",
)
@click.option(
    "--cookie",
    default=None,
    hidden=True,
    help="Explicit one-shot authenticated Cookie header override.",
)
@click.option("-e", "--env", "env_profile", default=None, help="ChatEnv 配置名。")
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
    """ECNU 门户工具。"""

    load_chatenv(env_profile=env_profile, env_file=env_file)
    token_profile = portal_session_profile(env_profile)
    ctx.obj = {
        "base_url": base_url or ECNUConfig.ECNU_BASE_URL.value or BASE_URL,
        "state_file": Path(state_file).expanduser() if state_file else None,
        "use_token_store": state_file is None,
        "token_profile": token_profile,
        "cookie": cookie,
        "timeout": timeout,
        "env_profile": env_profile,
        "env_file": env_file,
    }


@cli.group(name="home")
def home_group() -> None:
    """ECNU 门户。"""


@cli.command(name="selftest", hidden=True)
def selftest() -> None:
    """Run local parser self-test without network access."""

    from .portal import run_selftest

    echo_json(run_selftest())


@home_group.command(name="login-init", hidden=True)
@click.option(
    "--captcha-path",
    default=None,
    hidden=True,
    help="Where to save the captcha image. Defaults to $CHATARCH_HOME/cache/chatecnu-login-captcha.png.",
)
@click.pass_context
def login_init(ctx: click.Context, captcha_path: str | None) -> None:
    """Fetch login page, reset session state, and download captcha."""

    target_path = Path(captcha_path).expanduser() if captcha_path else default_captcha_path()
    echo_json(call_client(ctx, lambda client: client.login_init(target_path)))


@home_group.command(name="login")
@click.option("--username", default=None, help="ECNU 用户名，或设置 ECNU_USERNAME。")
@click.option("--password", default=None, help="ECNU 密码，或设置 ECNU_PASSWORD。")
@click.option("--captcha", default=None, hidden=True, help="Captcha text from login-init image.")
@click.option("--sms-code", default=None, help="服务端要求的短信码。")
@click.option(
    "--captcha-path",
    default=None,
    hidden=True,
    help="Where to save the latest captcha image. Defaults to $CHATARCH_HOME/cache/chatecnu-login-captcha.png.",
)
@click.option("--rounds", default=3, show_default=True, type=int, hidden=True, help="Captcha refresh rounds.")
@click.option("--topk", default=5, show_default=True, type=int, hidden=True, help="OCR candidates per captcha.")
@click.option("--json", "json_output", is_flag=True, help="输出 JSON。")
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
    """登录门户。"""

    values = resolve_login_inputs(username=username, password=password, interactive=interactive, command_name="home login")
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


@home_group.command(name="login-auto", hidden=True)
@click.option("--username", default=None, help="ECNU 用户名，或设置 ECNU_USERNAME。")
@click.option("--password", default=None, help="ECNU 密码，或设置 ECNU_PASSWORD。")
@click.option("--sms-code", default=None, help="服务端要求的短信码。")
@click.option(
    "--captcha-path",
    default=None,
    hidden=True,
    help="Where to save the latest captcha image. Defaults to $CHATARCH_HOME/cache/chatecnu-login-captcha.png.",
)
@click.option("--rounds", default=3, show_default=True, type=int, hidden=True, help="Captcha refresh rounds.")
@click.option("--topk", default=5, show_default=True, type=int, hidden=True, help="OCR candidates per captcha.")
@click.option("--json", "json_output", is_flag=True, hidden=True, help="输出 JSON。")
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
    """Hidden OCR-backed login helper."""

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


@home_group.command(name="status")
@click.option("--json", "json_output", is_flag=True, help="输出 JSON。")
@click.pass_context
def status(ctx: click.Context, json_output: bool) -> None:
    """门户会话状态。"""

    emit_status_result(session_status(ctx), json_output=json_output)


@home_group.command(name="session-info", hidden=True)
@click.option("--json", "json_output", is_flag=True, hidden=True, help="输出 JSON。")
@click.pass_context
def session_info(ctx: click.Context, json_output: bool) -> None:
    """Show saved session metadata with Cookie values redacted."""

    emit_status_result(session_status(ctx), json_output=json_output)


@home_group.command(name="cookie-header", hidden=True)
@click.pass_context
def cookie_header(ctx: click.Context) -> None:
    """Print the current Cookie header from state/session."""

    raise click.ClickException("Raw cookie output is disabled; use `ecnu home status --json` for redacted session metadata.")


@home_group.command(name="logout")
@click.option("--json", "json_output", is_flag=True, help="输出 JSON。")
@click.pass_context
def logout(ctx: click.Context, json_output: bool) -> None:
    """退出门户会话。"""

    emit_simple_result(
        call_client(ctx, lambda client: client.logout()),
        json_output=json_output,
        success_message="已退出登录。",
        failure_message="退出登录可能未完成。",
    )


@home_group.command(name="info")
@click.option("--json", "json_output", is_flag=True, help="输出 JSON。")
@click.pass_context
def home_info(ctx: click.Context, json_output: bool) -> None:
    """门户首页摘要。"""

    emit_home_result(call_client(ctx, lambda client: client.home_summary()), json_output=json_output)


@home_group.command(name="user")
@click.option("--json", "json_output", is_flag=True, help="输出 JSON。")
@click.pass_context
def user_info(ctx: click.Context, json_output: bool) -> None:
    """门户用户信息。"""

    emit_mapping_result(
        call_client(ctx, lambda client: client.user_info()),
        json_output=json_output,
        empty_message="没有返回用户信息。",
    )


@cli.group(name="debug", hidden=True)
def debug_group() -> None:
    """Hidden diagnostics and low-level queries."""


@debug_group.command(name="auth-log")
@click.option("--start", default=None, help="Start time.")
@click.option("--end", default=None, help="End time.")
@click.option("--limit", default=None, type=int, help="Maximum rows to print.")
@click.option("--json", "json_output", is_flag=True, hidden=True, help="输出 JSON。")
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
@click.option("--json", "json_output", is_flag=True, hidden=True, help="输出 JSON。")
@click.pass_context
def detail_log(ctx: click.Context, start: str | None, end: str | None, limit: int | None, json_output: bool) -> None:
    """Query network detail logs."""

    emit_log_result(
        call_client(ctx, lambda client: client.detail_logs(start, end, limit)),
        json_output=json_output,
        title="Network detail logs",
    )


@cli.group(name="net")
def network_auth_group() -> None:
    """校园网联网。"""


@network_auth_group.command(name="check")
@click.option("--auth-client", "auth_client_path", default=None, help="auth_client 路径。")
@click.option("--setting-file", default=None, help="设置文件。")
@click.option("--json", "json_output", is_flag=True, help="输出 JSON。")
@click.pass_context
def network_auth_check(
    ctx: click.Context,
    auth_client_path: str | None,
    setting_file: str | None,
    json_output: bool,
) -> None:
    """检查在线状态。"""

    prefer_loaded_chatenv = network_auth_prefers_loaded_chatenv(ctx)
    result = make_network_auth_client(
        auth_client_path=auth_client_path,
        setting_file=setting_file,
        prefer_loaded_chatenv=prefer_loaded_chatenv,
    ).check()
    emit_network_auth_result(result, json_output=json_output)


@network_auth_group.command(name="login")
@click.option("--auth-client", "auth_client_path", default=None, help="auth_client 路径。")
@click.option("--setting-file", default=None, help="设置文件。")
@click.option("--username", default=None, help="ECNU 用户名。")
@click.option("--password", default=None, help="ECNU 密码。")
@click.option(
    "--allow-argv-password",
    is_flag=True,
    help="危险：密码放入 argv。",
)
@click.option("--json", "json_output", is_flag=True, help="输出 JSON。")
@add_interactive_option
@click.pass_context
def network_auth_login(
    ctx: click.Context,
    auth_client_path: str | None,
    setting_file: str | None,
    username: str | None,
    password: str | None,
    allow_argv_password: bool,
    json_output: bool,
    interactive: bool | None,
) -> None:
    """登录。"""

    prefer_loaded_chatenv = network_auth_prefers_loaded_chatenv(ctx)
    credentials = resolve_network_auth_credentials(
        username=username,
        password=password,
        interactive=interactive,
        prefer_loaded_chatenv=prefer_loaded_chatenv,
    )
    result = make_network_auth_client(
        auth_client_path=auth_client_path,
        setting_file=setting_file,
        allow_argv_password=allow_argv_password,
        prefer_loaded_chatenv=prefer_loaded_chatenv,
    ).login(credentials)
    emit_network_auth_result(result, json_output=json_output, secret_values=(credentials.password,))


@network_auth_group.command(name="logout")
@click.option("--auth-client", "auth_client_path", default=None, help="auth_client 路径。")
@click.option("--setting-file", default=None, help="设置文件。")
@click.option("--username", default=None, help="ECNU 用户名。")
@click.option("--json", "json_output", is_flag=True, help="输出 JSON。")
@add_interactive_option
@click.pass_context
def network_auth_logout(
    ctx: click.Context,
    auth_client_path: str | None,
    setting_file: str | None,
    username: str | None,
    json_output: bool,
    interactive: bool | None,
) -> None:
    """退出校园网。"""

    prefer_loaded_chatenv = network_auth_prefers_loaded_chatenv(ctx)
    resolved_username = username or resolve_ecnu_config_value(
        "ECNU_USERNAME",
        ECNUConfig.ECNU_USERNAME,
        prefer_loaded_chatenv=prefer_loaded_chatenv,
    )
    client = make_network_auth_client(
        auth_client_path=auth_client_path,
        setting_file=setting_file,
        prefer_loaded_chatenv=prefer_loaded_chatenv,
    )
    result = client.logout(resolved_username) if resolved_username else client.logout_current()
    emit_network_auth_result(result, json_output=json_output)


@network_auth_group.command(name="ensure-login")
@click.option("--auth-client", "auth_client_path", default=None, help="auth_client 路径。")
@click.option("--setting-file", default=None, help="设置文件。")
@click.option("--username", default=None, help="ECNU 用户名。")
@click.option("--password", default=None, help="ECNU 密码。")
@click.option(
    "--allow-argv-password",
    is_flag=True,
    help="危险：密码放入 argv。",
)
@click.option("--json", "json_output", is_flag=True, help="输出 JSON。")
@add_interactive_option
@click.pass_context
def network_auth_ensure_login(
    ctx: click.Context,
    auth_client_path: str | None,
    setting_file: str | None,
    username: str | None,
    password: str | None,
    allow_argv_password: bool,
    json_output: bool,
    interactive: bool | None,
) -> None:
    """离线时登录。"""

    prefer_loaded_chatenv = network_auth_prefers_loaded_chatenv(ctx)
    credentials = resolve_network_auth_credentials(
        username=username,
        password=password,
        interactive=interactive,
        prefer_loaded_chatenv=prefer_loaded_chatenv,
    )
    result = make_network_auth_client(
        auth_client_path=auth_client_path,
        setting_file=setting_file,
        allow_argv_password=allow_argv_password,
        prefer_loaded_chatenv=prefer_loaded_chatenv,
    ).ensure_login(credentials)
    emit_network_auth_result(result, json_output=json_output, secret_values=(credentials.password,))


@cli.group(name="visitor")
def visitor_group() -> None:
    """访客账号。"""


@visitor_group.command(name="list")
@click.option("--json", "json_output", is_flag=True, help="输出 JSON。")
@click.pass_context
def visitor_list(ctx: click.Context, json_output: bool) -> None:
    """列出访客账号。"""

    emit_visitor_list_result(call_client(ctx, lambda client: client.list_visitors()), json_output=json_output)


@visitor_group.command(name="get")
@click.option("--id", "visitor_id", default=None, help="访客记录 id。")
@click.option("--account", default=None, help="访客账号名。")
@click.option("--json", "json_output", is_flag=True, help="输出 JSON。")
@click.pass_context
def visitor_get(ctx: click.Context, visitor_id: str | None, account: str | None, json_output: bool) -> None:
    """查询访客账号。"""

    if not visitor_id and not account:
        raise click.UsageError("Provide either --id or --account.")
    emit_mapping_result(
        call_client(ctx, lambda client: client.get_visitor(visitor_id=visitor_id, account=account)),
        json_output=json_output,
        empty_message="未找到访客账号。",
    )


@visitor_group.command(name="create")
@click.option("--remark", default=None, help="访客备注，2-14 位中英文字符。")
@click.option("--dry-run", is_flag=True, help="只输出请求，不提交。")
@click.option("--json", "json_output", is_flag=True, help="输出 JSON。")
@add_interactive_option
@click.pass_context
def visitor_create(
    ctx: click.Context,
    remark: str | None,
    dry_run: bool,
    json_output: bool,
    interactive: bool | None,
) -> None:
    """创建访客账号。"""

    values = resolve_command_inputs(
        schema=VISITOR_CREATE_SCHEMA,
        provided={"remark": remark},
        interactive=interactive,
        usage="Usage: ecnu visitor create --remark TEXT [-i|-I]",
    )
    emit_mutation_result(
        call_client(ctx, lambda client: client.create_visitor(values["remark"], dry_run=dry_run)),
        json_output=json_output,
        action="创建访客",
    )


@visitor_group.command(name="default")
@click.option("--password1", default=None, help="默认访客账号 m1 密码。")
@click.option("--password2", default=None, help="默认访客账号 m2 密码。")
@click.option("--remark", default=None, help="默认访客账号备注。")
@click.option("--json", "json_output", is_flag=True, help="输出 JSON。")
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
    """维护默认访客账号。"""

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
@click.option("--id", "visitor_id", default=None, help="访客记录 id。")
@click.option("--remark", default=None, help="访客备注，2-14 位中英文字符。")
@click.option("--password", default=None, help="新的访客密码。")
@click.option("--dry-run", is_flag=True, help="只输出请求，不提交。")
@click.option("--json", "json_output", is_flag=True, help="输出 JSON。")
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
    """更新访客备注和密码。"""

    values = resolve_command_inputs(
        schema=VISITOR_UPDATE_SCHEMA,
        provided={"visitor_id": visitor_id, "remark": remark, "password": password},
        interactive=interactive,
        usage="Usage: ecnu visitor update --id ID --remark TEXT --password TEXT [-i|-I]",
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
        action="更新访客",
    )


@visitor_group.command(name="delete")
@click.option("--id", "visitor_id", default=None, help="访客记录 id。")
@click.option("--dry-run", is_flag=True, help="只输出请求，不提交。")
@click.option("--json", "json_output", is_flag=True, help="输出 JSON。")
@add_interactive_option
@click.pass_context
def visitor_delete(
    ctx: click.Context,
    visitor_id: str | None,
    dry_run: bool,
    json_output: bool,
    interactive: bool | None,
) -> None:
    """删除访客账号。"""

    values = resolve_command_inputs(
        schema=VISITOR_ID_SCHEMA,
        provided={"visitor_id": visitor_id},
        interactive=interactive,
        usage="Usage: ecnu visitor delete --id ID [-i|-I]",
    )
    emit_mutation_result(
        call_client(ctx, lambda client: client.delete_visitor(values["visitor_id"], dry_run=dry_run)),
        json_output=json_output,
        action="Delete visitor",
    )


@visitor_group.command(name="lock", hidden=True)
@click.option("--id", "visitor_id", default=None, help="访客记录 id。")
@click.option("--dry-run", is_flag=True, help="只输出请求，不提交。")
@click.option("--json", "json_output", is_flag=True, hidden=True, help="输出 JSON。")
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
        usage="Usage: ecnu visitor lock --id ID [-i|-I]",
    )
    emit_mutation_result(
        call_client(ctx, lambda client: client.lock_visitor(values["visitor_id"], dry_run=dry_run)),
        json_output=json_output,
        action="Lock visitor",
    )


def make_network_auth_client(
    *,
    auth_client_path: str | None,
    setting_file: str | None,
    allow_argv_password: bool = False,
    prefer_loaded_chatenv: bool = False,
) -> NetworkAuthClient:
    configured_auth_client = auth_client_path or resolve_ecnu_config_value(
        "ECNU_AUTH_CLIENT",
        ECNUConfig.ECNU_AUTH_CLIENT,
        prefer_loaded_chatenv=prefer_loaded_chatenv,
    )
    resolved_auth_client = resolve_auth_client_path(configured_auth_client)
    resolved_setting_file = setting_file or resolve_ecnu_config_value(
        "ECNU_AUTH_SETTING_FILE",
        ECNUConfig.ECNU_AUTH_SETTING_FILE,
        prefer_loaded_chatenv=prefer_loaded_chatenv,
    ) or DEFAULT_SETTING_FILE
    return NetworkAuthClient(
        auth_client_path=resolved_auth_client,
        setting_file=resolved_setting_file,
        allow_argv_password=allow_argv_password,
    )


def resolve_network_auth_credentials(
    *,
    username: str | None,
    password: str | None,
    interactive: bool | None,
    prefer_loaded_chatenv: bool = False,
) -> NetworkAuthCredentials:
    values = resolve_command_inputs(
        schema=NETWORK_AUTH_LOGIN_SCHEMA,
        provided={
            "username": username
            or resolve_ecnu_config_value(
                "ECNU_USERNAME",
                ECNUConfig.ECNU_USERNAME,
                prefer_loaded_chatenv=prefer_loaded_chatenv,
            ),
            "password": password
            or resolve_ecnu_config_value(
                "ECNU_PASSWORD",
                ECNUConfig.ECNU_PASSWORD,
                prefer_loaded_chatenv=prefer_loaded_chatenv,
            ),
        },
        interactive=interactive,
        usage="Usage: ecnu net login --username USER --password PASSWORD [-i|-I]",
    )
    return NetworkAuthCredentials(username=values["username"], password=values["password"])


def resolve_network_auth_username(
    *,
    username: str | None,
    interactive: bool | None,
    prefer_loaded_chatenv: bool = False,
) -> str:
    values = resolve_command_inputs(
        schema=NETWORK_AUTH_USERNAME_SCHEMA,
        provided={
            "username": username
            or resolve_ecnu_config_value(
                "ECNU_USERNAME",
                ECNUConfig.ECNU_USERNAME,
                prefer_loaded_chatenv=prefer_loaded_chatenv,
            ),
        },
        interactive=interactive,
        usage="Usage: ecnu net logout --username USER [-i|-I]",
    )
    return values["username"]


def network_auth_prefers_loaded_chatenv(ctx: click.Context) -> bool:
    config = ctx.find_root().obj or ctx.obj or {}
    return bool(config.get("env_profile") or config.get("env_file"))


def resolve_ecnu_config_value(env_key: str, field: Any, *, prefer_loaded_chatenv: bool = False) -> str | None:
    loaded_value = field.value or field.default
    process_value = os.environ.get(env_key)
    if prefer_loaded_chatenv:
        return loaded_value or process_value
    return process_value or loaded_value


def emit_network_auth_result(
    result: NetworkAuthResult,
    *,
    json_output: bool,
    secret_values: tuple[str, ...] = (),
) -> None:
    payload = redact_network_auth_payload(result.to_dict(), secret_values=secret_values)
    if json_output:
        echo_json(redact_sensitive(payload))
    else:
        click.echo(format_network_auth_result(result))
    if not result.success:
        raise click.exceptions.Exit(1)


def redact_network_auth_payload(payload: dict[str, object], *, secret_values: tuple[str, ...]) -> dict[str, object]:
    """Redact resolved secret values from JSON payload strings."""

    return {
        key: redact_text(value, secret_values) if isinstance(value, str) else value
        for key, value in payload.items()
    }


def format_network_auth_result(result: NetworkAuthResult) -> str:
    if result.action == "ensure-login" and result.skipped:
        base = "Already online; skipped."
    elif result.action == "logout" and result.skipped:
        base = "Already offline; skipped."
    elif result.success:
        base = "Login OK." if result.action in {"login", "ensure-login"} else "auth_client OK."
    else:
        return "auth_client failed."

    details: list[str] = []
    if result.online is not None:
        details.append(f"Online: {str(result.online).lower()}")
    if result.account:
        details.append(f"Account: {result.account}")
    if result.username and result.username != result.account:
        details.append(f"Username: {result.username}")
    elif result.username and result.action == "check":
        details.append(f"Username: {result.username}")
    return " ".join([base, *details]) if details else base


def make_client(ctx: click.Context) -> Any:
    from .portal import PortalClient

    config = ctx.find_root().obj or ctx.obj or {}
    token_store = TokenStore() if config.get("use_token_store") else None
    token_profile = config.get("token_profile") or portal_session_profile(config.get("env_profile"))
    state_file = config.get("state_file")
    if token_store is not None:
        state_file = token_store.token_path(ECNU_SESSION_SERVICE, token_profile)
    elif state_file is None:
        state_file = default_state_file()
    return PortalClient(
        base_url=config["base_url"],
        state_file=Path(state_file),
        cookie_header=config.get("cookie"),
        timeout=config["timeout"],
        token_store=token_store,
        token_profile=token_profile,
    )


def call_client(ctx: click.Context, func: Callable[[Any], Any]) -> Any:
    try:
        return func(make_client(ctx))
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc


def echo_json(data: Any) -> None:
    click.echo(json.dumps(data, ensure_ascii=False, indent=2))


SENSITIVE_KEY_RE = re.compile(r"(password|passwd|token|csrf|cookie|secret)", re.I)


def redact_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        result: dict[Any, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if re.fullmatch(r"cookies?", key_text, flags=re.I) and isinstance(item, dict):
                result[key] = {cookie_key: "***" for cookie_key in item}
            elif SENSITIVE_KEY_RE.search(key_text):
                result[key] = "***"
            else:
                result[key] = redact_sensitive(item)
        return result
    if isinstance(value, list):
        return [redact_sensitive(item) for item in value]
    if isinstance(value, str):
        redacted = re.sub(r"(password=)[^&\s']+", r"\1***", value, flags=re.I)
        redacted = re.sub(r"(token=)[^&\s']+", r"\1***", redacted, flags=re.I)
        redacted = re.sub(r"(csrf[^=&\s']*=)[^&\s']+", r"\1***", redacted, flags=re.I)
        return redacted
    return value


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
        echo_json(redact_sensitive(result))
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
    if result.get("session_storage") == "token_store":
        lines.append(f"Session storage: token-store ({result.get('token_profile')})")
        if result.get("token_file"):
            lines.append(f"Token file: {result['token_file']}")
    elif result.get("state_file"):
        lines.append(f"Session storage: state-file ({result['state_file']})")
    if result.get("base_url"):
        lines.append(f"Base URL: {result['base_url']}")
    return "\n".join(lines)


def format_home_summary(result: dict[str, Any]) -> str:
    user_info = result.get("user_info") or {}
    online_info = result.get("online_info") or []
    product_info = result.get("product_info") or []
    lines = ["首页摘要"]
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
    lines = ["访客账号"]
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
        return f"{action}: 仅预览，未提交。"
    response = result.get("response") or {}
    if isinstance(response, dict) and "password" in response and "account" in response:
        return "\n".join([f"{action}: 成功。", f"账号: {response['account']}", "初始密码: ***"])
    if isinstance(response, dict) and response.get("ok"):
        return f"{action}: 成功。"
    return f"{action}: 已完成。"


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
    usage = f"Usage: chatecnu {command_name} --username TEXT --password TEXT [-i|-I]"
    if include_captcha:
        provided["captcha"] = captcha
        usage = "Usage: ecnu home login --username TEXT --password TEXT --captcha TEXT [-i|-I]"
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
        usage="Usage: ecnu visitor default --password1 TEXT [--password2 TEXT] [--remark TEXT] [-i|-I]",
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
        raise click.UsageError("ECNU_USERNAME must be set before running `ecnu visitor default`.")
    return {
        "username_prefix": username_prefix,
        "password1": resolved_password1,
        "password2": resolved_password2 or "",
        "remark": remark or ECNUConfig.ECNU_VISITOR_REMARK.value or "default",
    }


def session_status(ctx: click.Context) -> dict[str, Any]:
    client = make_client(ctx)
    result = redact_state(client.state)
    if hasattr(client, "session_storage_status"):
        result.update(client.session_storage_status())
    return result


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
    return get_paths().home_dir / "cache" / "chatecnu" / "ecnu-session.json"


def default_captcha_path() -> Path:
    return get_paths().home_dir / "cache" / "chatecnu" / "ecnu-login-captcha.png"


def redact_state(state: dict[str, Any]) -> dict[str, Any]:
    redacted = redact_sensitive(dict(state))
    cookies = redacted.get("cookies")
    if isinstance(cookies, dict):
        redacted["cookies"] = {key: "***" for key in cookies}
    return redacted
