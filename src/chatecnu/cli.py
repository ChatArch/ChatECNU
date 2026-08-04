"""CLI entrypoint for ChatECNU."""

from __future__ import annotations

from chatecnu import __version__
from chatecnu.ecnu.cli import cli as main

main = main
main.help = "ECNU tools."
main.version = __version__


if __name__ == "__main__":
    main()
