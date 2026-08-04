# ECNU Usage

## Configuration

ChatECNU reads the ChatEnv `ecnu` config type and accepts CLI overrides.

```bash
chatenv test -t ecnu
chatenv cat -t ecnu
```

Common fields:

```text
ECNU_USERNAME
ECNU_PASSWORD
ECNU_COOKIE
ECNU_BASE_URL
ECNU_AUTH_CLIENT
ECNU_AUTH_SETTING_FILE
```

For multiple profiles:

```bash
chatenv save work -t ecnu
chatenv use work -t ecnu
chatecnu -e work status
```

## Portal login

```bash
chatecnu login --rounds 3 --topk 5 -I
```

With an SMS code:

```bash
chatecnu login --sms-code 123456 --rounds 3 --topk 5 -I
```

When automatic CAPTCHA solving is not available:

```bash
chatecnu login-init
chatecnu login --captcha ABCD -I
```

## Session and reads

```bash
chatecnu status
chatecnu home
chatecnu user-info
chatecnu logout
```

Debug log commands are hidden under `debug`:

```bash
chatecnu debug auth-log --limit 10
chatecnu debug detail-log --limit 10
```

## Network login

ChatECNU wraps an external Linux `auth_client` binary and does not bundle it.

Check online state without a password:

```bash
chatecnu auth check   --auth-client /usr/local/bin/auth_client   --json
```

Log in only when offline:

```bash
chatecnu auth ensure-login   --auth-client /usr/local/bin/auth_client   -I
```

ChatECNU refuses argv passwords by default. Enable the legacy path only after accepting the local exposure risk:

```bash
chatecnu auth ensure-login   --auth-client /usr/local/bin/auth_client   --allow-argv-password   -I
```

`ensure-login` runs `check` first. No `-c` setting file is passed unless `--setting-file` or `ECNU_AUTH_SETTING_FILE` is set. The old `network-auth` command remains as a hidden compatibility alias.

## Visitor accounts

```bash
chatecnu visitor list
chatecnu visitor get --id 10256703
chatecnu visitor create --remark GuestA -I
chatecnu visitor update --id 10256703 --remark GuestA --password 'Temp!235' -I
chatecnu visitor delete --id 10256703 -I
```

Default visitor accounts:

```bash
chatecnu visitor default -I
```

Mutation commands support `--dry-run`.

## Interaction rules

- `-i`: force prompts.
- `-I`: disable prompts and fail fast when input is missing.
- Use `-I` in scripts and CI.
- Do not print or commit passwords, cookies, SMS codes, or sessions.
