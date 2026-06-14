"""CLI entrypoint for chatnet."""

from __future__ import annotations

import click
from chatstyle import (
    CommandField,
    CommandSchema,
    add_interactive_option,
    render_success,
    resolve_command_inputs,
)


HELLO_SCHEMA = CommandSchema(
    name="hello",
    fields=(CommandField("name", prompt="name", required=True),),
)


class ChatNetGroup(click.Group):
    """Top-level group that loads heavier feature groups on demand."""

    def list_commands(self, ctx: click.Context) -> list[str]:
        commands = set(super().list_commands(ctx))
        commands.add("ecnu")
        return sorted(commands)

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        if cmd_name == "ecnu":
            from chatnet.ecnu.cli import cli as ecnu_cli

            return ecnu_cli
        return super().get_command(ctx, cmd_name)


@click.group(cls=ChatNetGroup)
def main() -> None:
    """chatnet command line interface."""


@main.command()
@click.argument("name", required=False)
@add_interactive_option
def hello(name: str | None, interactive: bool | None) -> None:
    """Print a greeting with ChatStyle-backed input resolution."""

    values = resolve_command_inputs(
        schema=HELLO_SCHEMA,
        provided={"name": name},
        interactive=interactive,
        usage="Usage: chatnet hello [NAME]",
    )
    render_success(f"Hello, {values['name']}!")


if __name__ == "__main__":
    main()
