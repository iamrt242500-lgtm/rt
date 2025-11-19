"""
Secure store for users dict with optional PQC protection.

If liboqs is available, generate a one-time shared secret via KEM
(encapsulate to local static public key) and derive an AES-256-GCM key
from it to encrypt the JSON. Store alongside the KEM ciphertext.

Format (users.enc):
  magic: b'PQC1' (4)
  alg_len: 1 byte
  alg_name: bytes
  ct_len: 2 bytes big-endian
  kem_ct: bytes
  nonce_len: 1 byte (12)
  nonce: bytes
  tag: 16 bytes
  ciphertext: rest

If liboqs is not available, fallback to AES-256-GCM with a locally
stored master key (data/master.key, 32 bytes). This still gives strong
at-rest encryption, just not PQC-derived.
"""
from __future__ import annotations
import os
import json
import struct
from typing import Dict, Tuple

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore
    from cryptography.hazmat.primitives import hashes  # type: ignore
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF  # type: ignore
    HAS_CRYPTO = True
except Exception:  # ImportError or environment issues
    AESGCM = None  # type: ignore
    hashes = None  # type: ignore
    HKDF = None  # type: ignore
    HAS_CRYPTO = False

from . import pqc_envelope

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
ENC_PATH = os.path.join(DATA_DIR, 'users.enc')
MASTER_KEY_PATH = os.path.join(DATA_DIR, 'master.key')
MAGIC = b'PQC1'


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _hkdf_sha256(key_material: bytes, info: bytes = b'users-store') -> bytes:
    if not HAS_CRYPTO:
        raise RuntimeError('cryptography not available for HKDF')
    hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=info)
    return hkdf.derive(key_material)


def _get_fallback_master_key() -> bytes:
    _ensure_data_dir()
    if os.path.exists(MASTER_KEY_PATH):
        with open(MASTER_KEY_PATH, 'rb') as f:
            return f.read()
    import secrets
    key = secrets.token_bytes(32)
    with open(MASTER_KEY_PATH, 'wb') as f:
        f.write(key)
    try:
        os.chmod(MASTER_KEY_PATH, 0o600)
    except Exception:
        pass
    return key


def _aesgcm_encrypt(key: bytes, plaintext: bytes, aad: bytes = b'') -> Tuple[bytes, bytes, bytes]:
    if not HAS_CRYPTO:
        raise RuntimeError('cryptography not available for AES-GCM')
    import secrets
    aesgcm = AESGCM(key)
    nonce = secrets.token_bytes(12)
    ct = aesgcm.encrypt(nonce, plaintext, aad)
    # cryptography returns nonce + ct (with tag) or ct? For AESGCM.encrypt returns ciphertext with tag appended.
    # Split tag (last 16 bytes)
    tag = ct[-16:]
    ciphertext = ct[:-16]
    return nonce, tag, ciphertext


def _aesgcm_decrypt(key: bytes, nonce: bytes, tag: bytes, ciphertext: bytes, aad: bytes = b'') -> bytes:
    if not HAS_CRYPTO:
        raise RuntimeError('cryptography not available for AES-GCM')
    aesgcm = AESGCM(key)
    ct = ciphertext + tag
    return aesgcm.decrypt(nonce, ct, aad)


def save_users_secure(obj: Dict) -> None:
    _ensure_data_dir()
    if not HAS_CRYPTO:
        raise RuntimeError('cryptography not available')
    plaintext = json.dumps(obj, indent=2).encode('utf-8')
    if pqc_envelope.has_pqc():
        ct_kem, ss, alg = pqc_envelope.encapsulate_for_self()
        key = _hkdf_sha256(ss, info=b'users-store-pqc')
        nonce, tag, ciphertext = _aesgcm_encrypt(key, plaintext, aad=alg.encode('utf-8'))
        header = MAGIC + bytes([len(alg)]) + alg.encode('utf-8') + struct.pack('>H', len(ct_kem)) + ct_kem + bytes([len(nonce)]) + nonce + tag
        blob = header + ciphertext
    else:
        mk = _get_fallback_master_key()
        key = _hkdf_sha256(mk, info=b'users-store-fallback')
        nonce, tag, ciphertext = _aesgcm_encrypt(key, plaintext, aad=b'fallback')
        header = MAGIC + b'\x00'  # alg_len=0 means fallback
        blob = header + bytes([len(nonce)]) + nonce + tag + ciphertext
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(ENC_PATH, flags, 0o600)
    with os.fdopen(fd, 'wb') as f:
        f.write(blob)
    try:
        os.chmod(ENC_PATH, 0o600)
    except Exception:
        pass


def load_users_secure() -> Dict:
    _ensure_data_dir()
    if not os.path.exists(ENC_PATH):
        return {"users": {}}
    if not HAS_CRYPTO:
        # Encrypted file present but we can't decrypt
        raise RuntimeError('Encrypted users.enc present but cryptography is not available')
    with open(ENC_PATH, 'rb') as f:
        data = f.read()
    if not data.startswith(MAGIC):
        # legacy or corrupt: ignore
        return {"users": {}}
    p = 4
    alg_len = data[p]
    p += 1
    if alg_len > 0:
        alg = data[p:p+alg_len].decode('utf-8')
        p += alg_len
        (ct_len,) = struct.unpack('>H', data[p:p+2]); p += 2
        ct_kem = data[p:p+ct_len]; p += ct_len
        nonce_len = data[p]; p += 1
        nonce = data[p:p+nonce_len]; p += nonce_len
        tag = data[p:p+16]; p += 16
        ciphertext = data[p:]
        # derive key
        if not pqc_envelope.has_pqc():
            # library missing → cannot open PQC-protected store
            raise RuntimeError('PQC-protected users.enc present but liboqs is not available')
        ss, _ = pqc_envelope.decapsulate(ct_kem)
        key = _hkdf_sha256(ss, info=b'users-store-pqc')
        plaintext = _aesgcm_decrypt(key, nonce, tag, ciphertext, aad=alg.encode('utf-8'))
    else:
        nonce_len = data[p]; p += 1
        nonce = data[p:p+nonce_len]; p += nonce_len
        tag = data[p:p+16]; p += 16
        ciphertext = data[p:]
        mk = _get_fallback_master_key()
        key = _hkdf_sha256(mk, info=b'users-store-fallback')
        plaintext = _aesgcm_decrypt(key, nonce, tag, ciphertext, aad=b'fallback')
    try:
        return json.loads(plaintext.decode('utf-8'))
    except Exception:
        return {"users": {}}
