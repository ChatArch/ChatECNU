# CLI Tree

This page lists implemented visible commands only. Hidden diagnostics and legacy aliases stay out of the main tree. See [Capability Map](capability-map.md) for boundaries and [Interface Tree](interface-tree.md) for Python mapping.

## Top-level commands

```text
chatecnu
├── auth          # Network login
├── home          # Home summary
├── login         # Portal login
├── logout        # Logout
├── status        # Session status
├── user-info     # User info
└── visitor       # Visitor accounts
```

The old `network-auth` command still works as a hidden compatibility alias for `auth`.

## Network login

```text
chatecnu auth
├── check         # Check online state; no password needed
├── login         # Log in; argv password is refused by default
└── ensure-login  # Log in only when offline
```

Safety boundary: ChatECNU does not pass passwords to `auth_client -p PASSWORD` by default. Add `--allow-argv-password` only for legacy compatibility.

## Portal and session

```text
chatecnu login     # ECNU portal login
chatecnu status    # Local session state
chatecnu logout    # Logout
chatecnu home      # Home summary
chatecnu user-info # User info
```

`login` uses CAPTCHA recognition by default. Pass `--sms-code` when the server requires SMS.

## Visitor accounts

```text
chatecnu visitor
├── list           # List accounts
├── get            # Get one account
├── create         # Create
├── default        # Maintain default visitor accounts
├── update         # Update remark or password
└── delete         # Delete
```

Mutation commands support `--dry-run`.

## Update rules

- Update this page when a visible command is added.
- Do not list planned but unimplemented commands.
- Mention compatibility aliases in notes, not in the main tree.
