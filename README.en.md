# ChatECNU

ChatECNU is a tool package for ECNU portal access and campus-network access. The package name remains `ChatECNU`; the daily command is `ecnu`.

## Documentation

| Task | Link |
| --- | --- |
| Installation and smoke checks | https://arch.gh.wzhecnu.cn/ChatECNU/en/quickstart/ |
| CLI tree | https://arch.gh.wzhecnu.cn/ChatECNU/en/cli-tree/ |
| ChatEnv variables | https://arch.gh.wzhecnu.cn/ChatECNU/en/chatenv/ |
| ECNU usage | https://arch.gh.wzhecnu.cn/ChatECNU/en/ecnu/ |

## Install

```bash
pip install ChatECNU
```

For CAPTCHA OCR support:

```bash
pip install "ChatECNU[captcha]"
```

## Command Shape

```text
ecnu
├── home      # ECNU portal
├── net       # Campus network access
└── visitor   # Visitor accounts
```

Portal commands live under `home`:

```bash
ecnu home login -i
ecnu home info
ecnu home status
ecnu home user
ecnu home logout
```

Campus-network commands live under `net`:

```bash
ecnu net check --auth-client /usr/local/bin/auth_client --json
ecnu net login --auth-client /usr/local/bin/auth_client -I
ecnu net logout --auth-client /usr/local/bin/auth_client --username "$ECNU_USERNAME" -I
ecnu net ensure-login --auth-client /usr/local/bin/auth_client -I
```

ChatECNU does not bundle `auth_client`. Use `--auth-client` or `ECNU_AUTH_CLIENT`. Portal access and campus-network access share `ECNU_USERNAME` / `ECNU_PASSWORD`.

Do not print or commit passwords, cookies, SMS codes, or session values.
