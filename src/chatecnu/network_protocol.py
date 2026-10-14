"""SRun portal byte-level protocol, recovered against native client vectors."""
import base64
import hashlib
import json
import struct

B64_ALPHABET = 'LVoJPiCN2R8G90yg+hmFHuacZ1OWMnrsSTXkYpUq/3dlbfKwv6xztjI7DeBE45QA'
STANDARD_B64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
TRANSLATE = str.maketrans(STANDARD_B64, B64_ALPHABET)
MASK32 = 0xFFFFFFFF
DELTA = 0x9E3779B9


def _words(data, append_length=False):
    padded = data + b'\0' * (-len(data) % 4)
    words = list(struct.unpack('<' + 'I' * (len(padded) // 4), padded))
    if append_length:
        words.append(len(data))
    return words


def xencode(data, key):
    if not data:
        return b''
    values = _words(data, True)
    keys = _words(key)
    if len(keys) < 4:
        raise ValueError('Challenge must contain at least four uint32 words')
    n = len(values) - 1
    z = values[n]
    total = 0
    for _ in range(6 + 52 // (n + 1)):
        total = (total + DELTA) & MASK32
        e = (total >> 2) & 3
        for index in range(n + 1):
            y = values[index + 1] if index < n else values[0]
            mix = (z >> 5) ^ (y << 2)
            mix += ((y >> 3) ^ (z << 4)) ^ (total ^ y)
            mix += keys[(index & 3) ^ e] ^ z
            values[index] = z = (values[index] + mix) & MASK32
    return struct.pack('<' + 'I' * len(values), *values)


def password_digest(password):
    # This binary uses MD5(password), not HMAC-MD5(challenge, password).
    return '{MD5}' + hashlib.md5(password.encode('utf-8')).hexdigest()


def encode_info(username, password, ip, acid, challenge, *, action="login"):
    info = {'username': username, 'ip': ip, 'acid': str(acid), 'enc_ver': 'srun_bx1'}
    if action == 'login':
        info['password'] = password
    text = json.dumps(info, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    # Match Go encoding/json's default HTML and line-separator escaping.
    for old, new in [('&', '\\u0026'), ('<', '\\u003c'), ('>', '\\u003e'),
                     ('\u2028', '\\u2028'), ('\u2029', '\\u2029')]:
        text = text.replace(old, new)
    encoded = xencode(text.encode('utf-8'), challenge.encode('utf-8'))
    return '{SRBX1}' + base64.b64encode(encoded).decode('ascii').translate(TRANSLATE)


def build_auth_params(username, password, ip, acid, challenge, *, action="login"):
    if action not in {"login", "logout"}:
        raise ValueError("Unsupported authentication action")
    info = encode_info(username, password, ip, acid, challenge, action=action)
    fields = [username]
    result = {'ac_id': str(acid), 'action': action, 'callback': 'C_a_l_l_b_a_c_k',
              'double_stack': '1', 'info': info, 'ip': ip, 'n': '200',
              'type': '1', 'username': username}
    if action == 'login':
        digest = password_digest(password)
        result['password'] = digest
        fields.append(digest.removeprefix('{MD5}'))
    fields.extend([str(acid), ip, '200', '1', info])
    result['chksum'] = hashlib.sha1(''.join(challenge + x for x in fields).encode('utf-8')).hexdigest()
    return result
