import os
import json
import hashlib
import binascii
from typing import Dict, Tuple

DEFAULT_ROUNDS = 200_000

USERS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'users.json')


def _ensure_data_dir():
    data_dir = os.path.dirname(USERS_PATH)
    os.makedirs(data_dir, exist_ok=True)


def _load_json(path: str) -> Dict:
    if not os.path.exists(path):
        return {"users": {}}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_json(path: str, obj: Dict) -> None:
    # Try to ensure file is 0600 on POSIX
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    mode = 0o600
    fd = os.open(path, flags, mode)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(obj, f, indent=2)
    finally:
        try:
            os.chmod(path, mode)
        except Exception:
            pass


def hash_password(password: str, salt: bytes = None, rounds: int = DEFAULT_ROUNDS) -> Tuple[str, int, str]:
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, rounds, dklen=32)
    return binascii.hexlify(salt).decode(), rounds, binascii.hexlify(dk).decode()


def verify_password(password: str, salt_hex: str, rounds: int, hash_hex: str) -> bool:
    try:
        salt = binascii.unhexlify(salt_hex)
        expected = binascii.unhexlify(hash_hex)
    except (binascii.Error, ValueError):
        return False
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, rounds, dklen=32)
    # Constant-time compare
    return hashlib.sha256(dk).digest() == hashlib.sha256(expected).digest()


def load_users() -> Dict:
    _ensure_data_dir()
    return _load_json(USERS_PATH)


def save_users(obj: Dict) -> None:
    _ensure_data_dir()
    _save_json(USERS_PATH, obj)


def register_user(username: str, password: str) -> bool:
    username = username.strip()
    if not username:
        raise ValueError('Username required')
    users = load_users()
    if username in users.get('users', {}):
        return False
    salt_hex, rounds, hash_hex = hash_password(password)
    users['users'][username] = {
        'salt': salt_hex,
        'rounds': rounds,
        'hash': hash_hex,
    }
    save_users(users)
    return True


def authenticate_user(username: str, password: str) -> bool:
    username = username.strip()
    users = load_users().get('users', {})
    rec = users.get(username)
    if not rec:
        return False
    return verify_password(password, rec.get('salt', ''), int(rec.get('rounds', DEFAULT_ROUNDS)), rec.get('hash', ''))
