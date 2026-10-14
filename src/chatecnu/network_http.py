"""Direct, credential-safe SRun HTTP client; never invokes auth_client."""
from __future__ import annotations

from dataclasses import replace
import ipaddress
import json
from pathlib import Path
import re
from urllib.parse import parse_qs, urljoin, urlsplit

import requests

from .network_auth import NetworkAuthCredentials, NetworkAuthResult
from .network_protocol import build_auth_params

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

CALLBACK = 'C_a_l_l_b_a_c_k'
MAX_BODY = 1024 * 1024


class PortalProtocolError(ValueError):
    """An intentionally value-free protocol/transport failure."""


def _json_body(text: str) -> dict:
    body = text.strip()
    match = re.fullmatch(re.escape(CALLBACK) + r'\((.*)\)\s*;?', body, re.S)
    if match:
        body = match.group(1)
    try:
        result = json.loads(body)
    except (ValueError, TypeError):
        raise PortalProtocolError('Invalid portal JSON response') from None
    if not isinstance(result, dict):
        raise PortalProtocolError('Invalid portal JSON object')
    return result


class PythonNetworkAuthClient:
    """Python implementation sharing the existing NetworkAuthResult contract.

    Settings are read only. No third-party AC discovery, binary fallback,
    secret-bearing command display, or unsafe redirect/retry is performed.
    """

    def __init__(self, base_url: str, *, acid: int = 1, session=None, timeout: float = 10):
        try:
            parsed = urlsplit(base_url)
            valid = (parsed.scheme in {'http', 'https'} and parsed.hostname
                     and not parsed.username and not parsed.password
                     and parsed.path in {'', '/'} and not parsed.query and not parsed.fragment)
            parsed.port
        except (ValueError, TypeError):
            valid = False
        if not valid:
            raise ValueError('Invalid network portal endpoint')
        if type(acid) is not int or acid < 1:
            raise ValueError('AC ID must be a positive integer')
        if timeout <= 0:
            raise ValueError('Timeout must be positive')
        self.base_url = base_url.rstrip('/')
        self.acid = acid
        self.timeout = timeout
        self.session = session if session is not None else requests.Session()
        self.session.trust_env = False

    @classmethod
    def from_setting_file(cls, setting_file: str | Path | None = None, **kwargs):
        if not setting_file:
            raise ValueError('Explicit network settings filename required')
        path = Path(setting_file).expanduser()
        if not path.exists():
            raise ValueError('Network settings file not found')
        try:
            data = tomllib.loads(path.read_text(encoding='utf-8'))
            host = data['host']
            acid = data.get('acid', 1)
            if isinstance(acid, str) and re.fullmatch(r'[0-9]+', acid):
                acid = int(acid)
            if not isinstance(host, str):
                raise ValueError
            return cls(host if '://' in host else 'http://' + host, acid=acid, **kwargs)
        except (OSError, UnicodeError, ValueError, KeyError, TypeError):
            raise ValueError('Invalid network settings') from None

    def _get(self, path: str, params=None, *, mutation: bool = False) -> str:
        url = self.base_url + path
        for _ in range(3):
            response = None
            try:
                response = self.session.get(url, params=params or {}, timeout=self.timeout,
                                            allow_redirects=False, stream=True)
                if response.status_code in {301, 302, 303, 307, 308}:
                    target = urljoin(url, response.headers.get('Location', ''))
                    old, new = urlsplit(url), urlsplit(target)
                    same_host_upgrade = (old.scheme == 'http' and new.scheme == 'https'
                                         and old.hostname == new.hostname
                                         and old.port in {None, 80} and new.port in {None, 443}
                                         and old.path == new.path and not new.username
                                         and not new.password and not new.fragment
                                         and (not new.query or parse_qs(new.query, keep_blank_values=True)
                                              == {k: [str(v)] for k, v in (params or {}).items()}))
                    if mutation or not same_host_upgrade:
                        raise PortalProtocolError('Portal redirect refused')
                    self.base_url = 'https://' + new.netloc
                    url = self.base_url + path
                    continue
                if response.status_code != 200:
                    raise PortalProtocolError('Portal HTTP request failed')
                chunks = []
                length = 0
                for chunk in response.iter_content(chunk_size=16384):
                    length += len(chunk)
                    if length > MAX_BODY:
                        raise PortalProtocolError('Portal response too large')
                    chunks.append(chunk)
                return b''.join(chunks).decode('utf-8')
            except requests.RequestException as exc:
                # requests exceptions can contain a full credential-bearing URL.
                raise PortalProtocolError('Portal transport failed: ' + type(exc).__name__) from None
            except UnicodeError:
                raise PortalProtocolError('Portal response encoding invalid') from None
            finally:
                if response is not None:
                    response.close()
        raise PortalProtocolError('Portal redirect limit reached')

    @staticmethod
    def _result(action: str, success: bool, *, online=None, username=None,
                message: str = '', skipped: bool = False) -> NetworkAuthResult:
        return NetworkAuthResult(action=action, success=success, returncode=0 if success else 1,
                                 stdout=message if success else '', stderr='' if success else message,
                                 redacted_command='python-http ' + action, online=online,
                                 account=username, username=username, skipped=skipped, backend='python')

    def check(self) -> NetworkAuthResult:
        try:
            text = self._get('/cgi-bin/rad_user_info').strip()
            if text == 'not_online_error':
                return self._result('check', True, online=False)
            if text.startswith(('{', CALLBACK + '(')):
                data = _json_body(text)
                if data.get('error') == 'not_online_error':
                    return self._result('check', True, online=False)
                name = data.get('user_name') or data.get('username')
                if data.get('error') == 'ok' and isinstance(name, str) and name:
                    return self._result('check', True, online=True, username=name)
            else:
                row = text.split(',')
                if (len(row) >= 9 and re.fullmatch(r'[^\s,<>{}]{1,128}', row[0])
                        and all(re.fullmatch(r'[0-9]+(?:\.[0-9]+)?', cell) for cell in row[1:8])):
                    try:
                        ipaddress.ip_address(row[8])
                    except ValueError:
                        raise PortalProtocolError('Invalid portal status IP') from None
                    return self._result('check', True, online=True, username=row[0])
            raise PortalProtocolError('Unknown portal online status')
        except PortalProtocolError as exc:
            return self._result('check', False, message=str(exc))

    def _challenge(self, username: str):
        data = _json_body(self._get('/cgi-bin/get_challenge',
                                   {'callback': CALLBACK, 'double_stack': '1', 'ip': '', 'username': username}))
        token = data.get('challenge')
        error = data.get('error')
        if error is not None and (not isinstance(error, str) or error != 'ok'):
            raise PortalProtocolError('Portal challenge invalid')
        if not isinstance(token, str) or len(token.encode('utf-8')) < 13:
            raise PortalProtocolError('Portal challenge invalid')
        for key in ('client_ip', 'online_ip'):
            value = data.get(key)
            if value is not None and not isinstance(value, str):
                raise PortalProtocolError('Portal client IP invalid')
        ip = data.get('client_ip') or data.get('online_ip')
        if not isinstance(ip, str):
            raise PortalProtocolError('Portal client IP invalid')
        try:
            ipaddress.ip_address(ip)
        except (ValueError, TypeError):
            raise PortalProtocolError('Portal client IP invalid') from None
        return token, ip

    def _authenticate(self, action: str, username: str, password: str = '') -> NetworkAuthResult:
        if not username or (action == 'login' and not password):
            return self._result(action, False, message='Network credentials missing')
        try:
            token, ip = self._challenge(username)
            params = build_auth_params(username, password, ip, self.acid, token, action=action)
            data = _json_body(self._get('/cgi-bin/srun_portal', params, mutation=True))
            if data.get('error') != 'ok':
                codes = sorted(set(re.findall(r'\bE[0-9]{4}\b', ' '.join(str(data.get(k, '')) for k in ['error','ecode','error_msg']))))
                suffix = ': ' + ','.join(codes) if codes else ''
                raise PortalProtocolError('Portal rejected authentication' + suffix)
            current = self.check()
            expected = action == 'login'
            if not current.success or current.online is not expected:
                return self._result(action, False, online=current.online, message='Authentication state not verified')
            return self._result(action, True, online=current.online, username=current.username,
                                message='Login success' if expected else 'Logout success')
        except (PortalProtocolError, ValueError) as exc:
            # Only protocol-owned constant messages may cross this boundary.
            message = str(exc) if isinstance(exc, PortalProtocolError) else 'Invalid authentication parameters'
            return self._result(action, False, message=message)

    def login(self, credentials: NetworkAuthCredentials) -> NetworkAuthResult:
        return self._authenticate('login', credentials.username, credentials.password)

    def logout(self, username: str) -> NetworkAuthResult:
        return self._authenticate('logout', username)

    def logout_current(self) -> NetworkAuthResult:
        current = self.check()
        if not current.success:
            return replace(current, action='logout')
        if not current.online:
            return replace(current, action='logout', skipped=True)
        if not current.username:
            return self._result('logout', False, message='Online username unavailable')
        return self.logout(current.username)

    def ensure_login(self, credentials: NetworkAuthCredentials) -> NetworkAuthResult:
        current = self.check()
        if not current.success:
            return replace(current, action='ensure-login')
        if current.online:
            return replace(current, action='ensure-login', skipped=True)
        return replace(self.login(credentials), action='ensure-login')
