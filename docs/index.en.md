# ChatECNU Documentation

ChatECNU provides ECNU portal automation and a campus-network `auth_client` wrapper. ECNU-specific behavior belongs here; generic network helpers belong to ChatNet.

## Pick a path

| Goal | Page |
| --- | --- |
| Install and smoke test | [Quickstart](quickstart.md) |
| Review visible commands | [CLI Tree](cli-tree.md) |
| Check ChatECNU / ChatNet / `auth_client` boundaries | [Capability Map](capability-map.md) |
| Review Python interfaces and CLI mapping | [Interface Tree](interface-tree.md) |
| Use portal login, sessions, and visitors | [ECNU Usage](ecnu.md) |
| Check campus-network login state | [Network Login](ecnu.md#network-login) |

## Sections

<div class="grid cards" markdown>

- **Getting Started**

  [Quickstart](quickstart.md): install, configure, and run the smallest checks.

- **Commands and Interfaces**

  [CLI Tree](cli-tree.md) shows the real command surface; [Capability Map](capability-map.md) shows package boundaries; [Interface Tree](interface-tree.md) maps Python and CLI interfaces.

- **Usage Guide**

  [ECNU Usage](ecnu.md): portal login, session reads, visitor accounts, and network login.

</div>

## Boundary

| Component | Responsibility |
| --- | --- |
| ChatECNU | ECNU portal, visitor accounts, and `auth_client` wrapper |
| ChatNet | Generic network, browser, table, and session helpers |
| `auth_client` | External Linux binary, not bundled |
| ChatDNS / certificates / Nginx | Out of scope for this package |

## Common entry points

```bash
chatecnu --help
chatecnu auth check --auth-client /usr/local/bin/auth_client --json
chatecnu visitor --help
```
