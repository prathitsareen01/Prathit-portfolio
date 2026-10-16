"""Deployment boundary for the shared, synthetic-data portfolio demo."""
import base64
import binascii
import os
import secrets
from urllib.parse import urlsplit


def hosted():
    return os.environ.get('FINANCEOS_MODE','local')=='hosted'


def allowed_hosts():
    hosts={'127.0.0.1','localhost'}
    if not hosted():
        hosts.add('testserver')
    configured=os.environ.get('FINANCEOS_ALLOWED_HOSTS','')
    render_host=os.environ.get('RENDER_EXTERNAL_HOSTNAME','')
    for value in [*configured.split(','),render_host]:
        value=value.strip().lower()
        if value and '*' not in value and '/' not in value and ':' not in value:
            hosts.add(value)
    return hosts


def validate_startup():
    mode=os.environ.get('FINANCEOS_MODE','local')
    if mode not in ('local','hosted'):
        raise RuntimeError('FINANCEOS_MODE must be local or hosted.')
    if hosted():
        password=os.environ.get('FINANCEOS_AUTH_PASSWORD','')
        if len(password)<20:
            raise RuntimeError('Hosted mode requires FINANCEOS_AUTH_PASSWORD with at least 20 characters.')
        if not os.environ.get('FINANCEOS_AUTH_USERNAME','demo'):
            raise RuntimeError('Hosted mode requires a username.')
        if allowed_hosts()<={'localhost','127.0.0.1'}:
            raise RuntimeError('Hosted mode requires RENDER_EXTERNAL_HOSTNAME or FINANCEOS_ALLOWED_HOSTS.')


def request_host(raw):
    try:
        return (urlsplit('//'+raw).hostname or '').lower()
    except ValueError:
        return ''


def authorized(header):
    try:
        scheme,value=header.split(' ',1)
        if scheme.lower()!='basic':
            return False
        decoded=base64.b64decode(value,validate=True).decode('utf-8')
        username,password=decoded.split(':',1)
    except (ValueError,UnicodeError,binascii.Error):
        return False
    username_ok=secrets.compare_digest(username.encode(),os.environ.get('FINANCEOS_AUTH_USERNAME','demo').encode())
    password_ok=secrets.compare_digest(password.encode(),os.environ.get('FINANCEOS_AUTH_PASSWORD','').encode())
    return bool(os.environ.get('FINANCEOS_AUTH_PASSWORD')) and username_ok and password_ok


# Signed, expiring HTTPS sessions keep credentials out of browser authentication popups.
import hashlib
import hmac
import json
import threading
import time

COOKIE_NAME='__Host-financeos_session'
SESSION_SECONDS=8*60*60
_login_failures={}
_login_lock=threading.Lock()


def credentials_valid(username,password):
    username_ok=secrets.compare_digest(username.encode(),os.environ.get('FINANCEOS_AUTH_USERNAME','demo').encode())
    password_ok=secrets.compare_digest(password.encode(),os.environ.get('FINANCEOS_AUTH_PASSWORD','').encode())
    return bool(os.environ.get('FINANCEOS_AUTH_PASSWORD')) and username_ok and password_ok


def _session_key():
    return hmac.digest(os.environ.get('FINANCEOS_AUTH_PASSWORD','').encode(),b'FinanceOS session signing v1','sha256')


def create_session():
    now=int(time.time())
    payload={'sub':os.environ.get('FINANCEOS_AUTH_USERNAME','demo'),'iat':now,'exp':now+SESSION_SECONDS,'nonce':secrets.token_urlsafe(16)}
    encoded=base64.urlsafe_b64encode(json.dumps(payload,separators=(',',':')).encode()).rstrip(b'=').decode()
    signature=hmac.new(_session_key(),encoded.encode(),'sha256').hexdigest()
    return encoded+'.'+signature


def session_valid(token):
    if not token or len(token)>1024 or not os.environ.get('FINANCEOS_AUTH_PASSWORD'):
        return False
    try:
        encoded,signature=token.split('.',1)
        expected=hmac.new(_session_key(),encoded.encode('ascii'),'sha256').hexdigest()
        if not hmac.compare_digest(expected.encode(),signature.encode('ascii')):
            return False
        payload=json.loads(base64.urlsafe_b64decode(encoded+'='*(-len(encoded)%4)))
        if not isinstance(payload,dict):
            return False
        now=int(time.time())
        return (payload.get('sub')==os.environ.get('FINANCEOS_AUTH_USERNAME','demo')
                and type(payload.get('iat')) is int and type(payload.get('exp')) is int
                and payload['iat']<=now+30 and now<payload['exp']
                and 0<payload['exp']-payload['iat']<=SESSION_SECONDS)
    except (ValueError,UnicodeError,TypeError,KeyError,binascii.Error):
        return False


def login_blocked(client_id):
    now=time.time()
    with _login_lock:
        for key,(started,count) in list(_login_failures.items()):
            if now-started>=300:
                _login_failures.pop(key,None)
        if len(_login_failures)>5000:
            _login_failures.clear()
        return _login_failures.get(client_id,(now,0))[1]>=10


def record_login(client_id,success):
    with _login_lock:
        if success:
            _login_failures.pop(client_id,None)
        else:
            started,count=_login_failures.get(client_id,(time.time(),0))
            _login_failures[client_id]=(started,count+1)
