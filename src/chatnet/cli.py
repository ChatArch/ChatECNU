"""CLI entrypoint for chatnet."""

from __future__ import annotations

import click


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


if __name__ == "__main__":
    main()
