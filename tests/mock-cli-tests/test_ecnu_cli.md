# test_ecnu_cli

## Case 1: mock client should cover the full ECNU command chain

### Setup

- Patch `chatecnu.ecnu.cli.make_client` with an in-memory fake client.
- Set `CHATARCH_HOME` to a temporary directory.
- Do not perform network requests.

### Expected Behavior

- `ecnu home login-init` calls `login_init`.
- `ecnu home login --captcha ...` supports the hidden manual captcha path and calls `login`.
- `ecnu home login` without `--captcha` resolves credentials and calls `login_auto`.
- `ecnu home status` defaults to a human summary and `--json` returns the redacted JSON payload.
- Advanced commands such as `home cookie-header`, `home login-init`, and `selftest` still work when called directly but are hidden from the default help surface.
- `ecnu home info`, `ecnu home user`, hidden `debug auth-log`, hidden `debug detail-log`, and visitor commands call their matching client methods.
- Visitor mutation commands support `--dry-run`.
- Visitor mutations default to readable summaries unless `--json` is requested.

## Case 2: visitor default should provision deterministic default visitor accounts

### Setup

- Set `ECNU_USERNAME`, `ECNU_VISITOR_PASSWORD1`, `ECNU_VISITOR_PASSWORD2`, and `ECNU_VISITOR_REMARK`.
- Patch `make_client` with an in-memory fake client that initially has only `mock-userm1`.

### Expected Behavior

- Running `ecnu visitor default -I` updates `mock-userm1`.
- The command creates `mock-userm2` if it does not exist, then updates its password.
- The command prints a short human summary by default.

## Case 3: default help should hide advanced or sensitive commands

### Setup

- Render Click help for `ecnu`, `ecnu home`, and `ecnu visitor`.

### Expected Behavior

- The top-level help shows only `home`, `net`, and `visitor`.
- Portal commands are visible under `ecnu home`.
- Advanced or sensitive commands/options such as `cookie-header`, `login-init`, `login-auto`, `selftest`, `auth-log`, `detail-log`, `debug`, `visitor lock`, `--cookie`, and `--state-file` are hidden from the top-level help surface.

## Case 4: explicit env file should provide login defaults

### Setup

- Create a temporary env file with `ECNU_USERNAME`, `ECNU_PASSWORD`, and `ECNU_BASE_URL`.
- Patch `make_client` with an in-memory fake client.

### Expected Behavior

- Running `ecnu --env-file <file> home login --rounds 1 --topk 1 -I` succeeds without passing `--username` or `--password`.
- The fake client receives credentials loaded from the env file and routes them through auto-login.
