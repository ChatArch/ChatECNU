# test_ecnu_cli

## Case 1: mock client should cover the full ECNU CLI command chain

### Setup

- Patch `chatnet.ecnu.cli.make_client` with an in-memory fake client.
- Set `CHATARCH_HOME` to a temporary directory.
- Do not perform network requests.

### Expected Behavior

- `chatnet ecnu login-init` calls `login_init`.
- `chatnet ecnu login` resolves explicit username, password, and captcha, then calls `login`.
- `chatnet ecnu login-auto` resolves explicit credentials and calls `login_auto`.
- `chatnet ecnu status` redacts cookie values.
- Advanced commands such as `cookie-header`, `login-init`, and `selftest` still work when called directly but are hidden from the default help surface.
- `chatnet ecnu cookie-header`, `home`, `user-info`, `auth-log`, `detail-log`, and visitor commands call their matching client methods.
- Visitor mutation commands support `--dry-run`.
- Visitor creation returns the server-issued initial account/password payload; password editing is a separate `visitor update` step.

## Case 2: default help should hide advanced or sensitive commands

### Setup

- Render Click help for `chatnet ecnu` and `chatnet ecnu visitor`.

### Expected Behavior

- Common commands such as `status`, `login-auto`, `visitor list`, `visitor create`, `visitor update`, and `visitor delete` are visible.
- Advanced or sensitive commands/options such as `cookie-header`, `login-init`, `selftest`, `visitor lock`, `--cookie`, and `--state-file` are hidden.

## Case 3: explicit env file should provide login defaults

### Setup

- Create a temporary env file with `ECNU_USERNAME`, `ECNU_PASSWORD`, and `ECNU_BASE_URL`.
- Patch `make_client` with an in-memory fake client.

### Expected Behavior

- Running `chatnet ecnu --env-file <file> login --captcha 1234 -I` succeeds without passing `--username` or `--password`.
- The fake client receives credentials loaded from the env file.
