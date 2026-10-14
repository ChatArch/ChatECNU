from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests

GOLDEN = {
    'username': 'offline-fixture-user',
    'password': 'DUMMY_PASSWORD_NOT_A_REAL_ACCOUNT_123!',
    'ip': '192.0.2.23', 'acid': '7', 'token': '0123456789abcdef' * 4,
    'info': '{SRBX1}IMFfp0yaboqcZ5Q9z0n5ULmm/jbFgtSApOj0K5gYbBiB8ItiASHcOY1x6zd2X/mwHymrkYhNTgzVKi3m5wgAOtVQpzKAKO3aCVQg1u3OP5rY/qf8RDT3f39C+ZMnxcdM7iF0D54V/oOxwumTsf3w1nXDwm1hlMr+sTXk8n0KNK8huVJdeP5lGtzTy11siLmh',
    'chksum': 'a11c26880a8c3c31bf71202e26cbcfa2490b855a',
}


def protocol():
    assert importlib.util.find_spec('chatecnu.network_protocol'), 'pure protocol is missing'
    return importlib.import_module('chatecnu.network_protocol')


def client_class():
    assert importlib.util.find_spec('chatecnu.network_http'), 'pure HTTP client is missing'
    return importlib.import_module('chatecnu.network_http').PythonNetworkAuthClient


class Response:
    def __init__(self, value, status=200, headers=None):
        self.text = json.dumps(value) if isinstance(value, dict) else value
        self.status_code = status
        self.headers = headers or {}
    def iter_content(self, chunk_size):
        yield self.text.encode()
    def close(self):
        pass


class Session:
    def __init__(self, values):
        self.values = iter(values)
        self.calls = []
        self.trust_env = True
    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        result = next(self.values)
        if isinstance(result, Exception):
            raise result
        return result if isinstance(result, Response) else Response(result)


def make(values, **kwargs):
    session = Session(values)
    return client_class()('http://portal.example', acid=7, session=session, **kwargs), session


def challenge():
    return {'error': 'ok', 'challenge': GOLDEN['token'], 'client_ip': GOLDEN['ip']}


def test_native_golden_login_parameters():
    p = protocol().build_auth_params(GOLDEN['username'], GOLDEN['password'], GOLDEN['ip'], 7, GOLDEN['token'])
    assert p['password'] == '{MD5}49b95d9f0c28d3d2db688eb59b70e7d6'
    assert p['info'] == GOLDEN['info']
    assert p['chksum'] == GOLDEN['chksum']


def test_logout_has_no_password_and_distinct_info_checksum():
    p = protocol().build_auth_params('fixture', 'NEVER_IN_LOGOUT', '192.0.2.2', 7, GOLDEN['token'], action='logout')
    empty = protocol().build_auth_params('fixture', '', '192.0.2.2', 7, GOLDEN['token'], action='logout')
    assert p == empty
    assert 'password' not in p and p['action'] == 'logout'


def test_short_challenge_rejected():
    with pytest.raises(ValueError):
        protocol().build_auth_params('fixture', 'canary', '192.0.2.2', 1, 'short')


@pytest.mark.parametrize('text', ['', '<html>login</html>', 'unexpected', '{"error":"unknown"}', 'garbage,a,b,c,d,e,f,g,not-ip'])
def test_unknown_status_fails_closed(text):
    client, _ = make([text])
    r = client.check()
    assert not r.success and r.online is None


def test_offline_sentinel_is_not_online():
    client, _ = make(['not_online_error'])
    r = client.check()
    assert r.success and r.online is False and r.username is None


def test_legacy_csv_online_username():
    client, _ = make(['fixture,0,0,0,0,0,0,0,192.0.2.2'])
    r = client.check()
    assert r.success and r.online is True and r.username == 'fixture'


def test_json_online_and_offline():
    client, _ = make([{'error':'ok','user_name':'fixture','online_ip':'192.0.2.2'}, {'error':'not_online_error'}])
    assert client.check().online is True
    assert client.check().online is False


def test_login_uses_http_and_postcheck_without_subprocess(monkeypatch):
    from chatecnu.network_auth import NetworkAuthCredentials
    monkeypatch.setattr('subprocess.run', lambda *a, **k: pytest.fail('binary must not run'))
    client, s = make([challenge(), {'error':'ok','suc_msg':'login_ok'}, 'fixture,0,0,0,0,0,0,0,192.0.2.2'])
    result = client.login(NetworkAuthCredentials('fixture', 'secret-canary'))
    assert result.success and result.online is True and result.backend == 'python'
    assert [u.rsplit('/',1)[-1] for u,k in s.calls] == ['get_challenge','srun_portal','rad_user_info']
    assert 'secret-canary' not in json.dumps(result.to_dict())
    assert s.trust_env is False
    assert all(k['allow_redirects'] is False and k['timeout'] for u,k in s.calls)


def test_logout_and_fresh_offline_verification():
    client, s = make([challenge(), {'error':'ok','suc_msg':'logout_ok'}, 'not_online_error'])
    result = client.logout('fixture')
    assert result.success and result.online is False
    assert s.calls[1][1]['params']['action'] == 'logout'
    assert 'password' not in s.calls[1][1]['params']


def test_false_login_success_is_not_verified_online():
    from chatecnu.network_auth import NetworkAuthCredentials
    client, _ = make([challenge(), {'error':'ok'}, 'not_online_error'])
    assert not client.login(NetworkAuthCredentials('fixture','canary')).success


def test_portal_failure_does_not_leak_raw_reply_or_request():
    from chatecnu.network_auth import NetworkAuthCredentials
    client, _ = make([challenge(), {'error':'E2901','error_msg':'SECRET_REPLY_RAW'}])
    r = client.login(NetworkAuthCredentials('fixture','secret-canary'))
    out = json.dumps(r.to_dict())
    assert not r.success and 'E2901' in out
    assert all(s not in out for s in ['SECRET_REPLY_RAW','secret-canary',GOLDEN['token'],'{SRBX1}'])


def test_transport_error_never_echoes_secret_url():
    client, _ = make([requests.ConnectionError('http://portal.example/?password=SECRET_URL')])
    result = client.check()
    assert not result.success and 'SECRET_URL' not in json.dumps(result.to_dict())


def test_only_same_host_upgrade_redirect_is_followed():
    client, s = make([Response('',301,{'Location':'https://portal.example/cgi-bin/rad_user_info'}), 'not_online_error'])
    assert client.check().success
    assert s.calls[-1][0].startswith('https://portal.example/')
    client, s = make([Response('',302,{'Location':'https://other.example/steal'})])
    assert not client.check().success and len(s.calls) == 1


@pytest.mark.parametrize('query,accepted', [('username=fixture&ip=',True),('username=other&ip=',False),('username=fixture&ip=&extra=x',False)])
def test_upgrade_redirect_must_preserve_original_query(query, accepted):
    client, s = make([Response('',301,{'Location':'https://portal.example/cgi-bin/get_challenge?'+query}), '{}'])
    if accepted:
        assert client._get('/cgi-bin/get_challenge', {'username':'fixture','ip':''}) == '{}'
        assert len(s.calls) == 2
    else:
        from chatecnu.network_http import PortalProtocolError
        with pytest.raises(PortalProtocolError):
            client._get('/cgi-bin/get_challenge', {'username':'fixture','ip':''})
        assert len(s.calls) == 1


def test_ensure_online_skips_login():
    from chatecnu.network_auth import NetworkAuthCredentials
    client, s = make(['fixture,0,0,0,0,0,0,0,192.0.2.2'])
    r = client.ensure_login(NetworkAuthCredentials('fixture','canary'))
    assert r.success and r.skipped and len(s.calls) == 1


@pytest.mark.parametrize('changed', [{'error':[]},{'error':{}},{'client_ip':123},{'client_ip':False},{'client_ip':[]},{'online_ip':{}},{'challenge':123}])
def test_malformed_challenge_fields_fail_safely(changed):
    from chatecnu.network_auth import NetworkAuthCredentials
    value = challenge()
    value.update(changed)
    client, session = make([value])
    result = client.login(NetworkAuthCredentials('fixture', 'SECRET_CANARY_BAD_RESPONSE'))
    assert result.success is False and result.backend == 'python'
    assert len(session.calls) == 1
    assert 'SECRET_CANARY_BAD_RESPONSE' not in json.dumps(result.to_dict())


def test_credential_mutation_redirect_is_never_followed():
    from chatecnu.network_auth import NetworkAuthCredentials
    client, session = make([challenge(), Response('',302,{'Location':'https://portal.example/cgi-bin/srun_portal'})])
    result = client.login(NetworkAuthCredentials('fixture', 'SECRET_REDIRECT_CANARY'))
    assert result.success is False and len(session.calls) == 2
    assert result.stderr == 'Portal redirect refused'
    assert 'SECRET_REDIRECT_CANARY' not in json.dumps(result.to_dict())


def test_from_legacy_toml_accepts_string_acid(tmp_path):
    p = tmp_path/'settings'
    p.write_text('host="portal.example"\nacid="7"\ncampus_url=""\ncampus_postfix=""\n')
    c = client_class().from_setting_file(p)
    assert c.acid == 7 and c.base_url == 'http://portal.example'


def test_cli_factory_defaults_to_python_without_binary_resolution(monkeypatch):
    import chatecnu.ecnu.cli as cli
    monkeypatch.setattr(cli,'resolve_auth_client_path', lambda *a: pytest.fail('binary resolution'))
    monkeypatch.delenv('ECNU_NETWORK_BACKEND',raising=False)
    from chatecnu.config import ECNUConfig
    monkeypatch.setattr(ECNUConfig.ECNU_NETWORK_BACKEND,'value',None)
    c = cli.make_network_auth_client(auth_client_path=None, setting_file=None)
    assert isinstance(c, client_class())
