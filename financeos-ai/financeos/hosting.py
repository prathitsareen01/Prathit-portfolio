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
