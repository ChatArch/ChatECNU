# ChatECNU Documentation

ChatECNU provides Python APIs and command-line tools for ECNU portal access and campus-network access. The daily command is `ecnu`.

<div class="grid cards" markdown>

-   :material-home: **Portal**

    ---

    Login, read the portal home summary, inspect session state, and read user info.

    [`ecnu home ...`](cli-tree.md#home)

-   :material-lan-connect: **Campus network**

    ---

    Use the PyPI-bundled Linux x86_64 `auth_client` to check, login, logout, or ensure local network access.

    [`ecnu net ...`](cli-tree.md#net)

-   :material-account-group: **Visitor accounts**

    ---

    Manage ECNU visitor accounts with dry-run support for mutations.

    [`ecnu visitor ...`](cli-tree.md#visitor)

-   :material-key: **ChatEnv config**

    ---

    Store credentials, Cookies, and local network settings under the `ecnu` type.

    [View variables](chatenv.md)

</div>

## Start Here

| Goal | Entry |
| --- | --- |
| Install and verify | [Quickstart](quickstart.md) |
| Read the command tree | [CLI Tree](cli-tree.md) |
| Check capability boundaries | [Capability Map](capability-map.md) |
| Map to Python APIs | [Interface Tree](interface-tree.md) |
| Use portal and network commands | [ECNU Usage](ecnu.md) |
