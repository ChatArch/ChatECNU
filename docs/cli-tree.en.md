# CLI Tree

This page lists only visible implemented commands. Hidden diagnostics are not part of the main user tree. See [Capability Map](capability-map.md) for boundaries and [Interface Tree](interface-tree.md) for Python mappings.

## Top-Level Commands

```text
ecnu
├── home      # ECNU portal
├── net       # Campus network access
└── visitor   # Visitor accounts
```

## home {#home}

```text
ecnu home
├── info      # Portal home summary
├── login     # Login to the portal
├── logout    # Logout from the portal session
├── status    # Portal session state
└── user      # Portal user info
```

Portal state is an ECNU Web/API session used by `info`, `user`, `visitor`, and related portal APIs.

## net {#net}

```text
ecnu net
├── check         # Check online state; no password required
├── login         # Login to the campus network
├── logout        # Logout from the campus network
└── ensure-login  # Login only when offline
```

`net` manages local campus-network access. It wraps an external `auth_client` binary and does not bundle it.

## visitor {#visitor}

```text
ecnu visitor
├── list      # List accounts
├── get       # Read one account
├── create    # Create an account
├── default   # Maintain default visitor accounts
├── update    # Update remark or password
└── delete    # Delete an account
```

Mutation commands support `--dry-run`.

## Update Rules

- Update this page whenever a visible command changes.
- Do not list planned commands as implemented commands.
- Do not put old command names in the main tree.
