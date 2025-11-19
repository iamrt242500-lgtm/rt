"""
PQC envelope for local data-at-rest key protection.

- Tries to use liboqs (Kyber512 / ML-KEM-512) if available.
- Stores static KEM keypair under data/: kem_pub.bin, kem_priv.bin
- Provides: ensure_keys(), encapsulate_for_self() -> (ct, ss), decapsulate(ct) -> ss

If liboqs is unavailable, raises ImportError so caller can fallback.
"""
from __future__ import annotations
import os
from typing import Tuple

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
PUB_PATH = os.path.join(DATA_DIR, 'kem_pub.bin')
PRIV_PATH = os.path.join(DATA_DIR, 'kem_priv.bin')
ALG_CANDIDATES = (
    'Kyber512',        # old naming sometimes used
    'ML-KEM-512',      # NIST name in liboqs recent builds
)

try:
    import oqs  # type: ignore
    _HAS_OQS = True
except Exception:
    oqs = None  # type: ignore
    _HAS_OQS = False


def _select_alg() -> str:
    assert _HAS_OQS
    available = set(oqs.get_enabled_kem_mechanisms())
    for name in ALG_CANDIDATES:
        if name in available:
            return name
    # pick any Kyber-like
    for name in available:
        if 'KEM' in name or 'Kyber' in name:
            return name
    raise RuntimeError('No suitable PQC KEM found in liboqs')


def ensure_keys() -> Tuple[bytes, bytes, str]:
    """Load or create local static KEM keypair. Returns (pub, priv, alg)."""
    if not _HAS_OQS:
        raise ImportError('liboqs (pyoqs) not available')
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(PUB_PATH) and os.path.exists(PRIV_PATH):
        with open(PUB_PATH, 'rb') as f:
            pub = f.read()
        with open(PRIV_PATH, 'rb') as f:
            priv = f.read()
        # alg hint stored at beginning of pub as ASCII? keep external file later if needed
        alg = _select_alg()
        return pub, priv, alg
    # create new
    alg = _select_alg()
    with oqs.KeyEncapsulation(alg) as kem:
        pub = kem.generate_keypair()
        priv = kem.export_secret_key()
    with open(PUB_PATH, 'wb') as f:
        f.write(pub)
    with open(PRIV_PATH, 'wb') as f:
        f.write(priv)
    try:
        os.chmod(PUB_PATH, 0o644)
        os.chmod(PRIV_PATH, 0o600)
    except Exception:
        pass
    return pub, priv, alg


def encapsulate_for_self() -> Tuple[bytes, bytes, str]:
    """Encapsulate to our own public key. Returns (ct, shared_secret, alg)."""
    if not _HAS_OQS:
        raise ImportError('liboqs (pyoqs) not available')
    pub, _priv, alg = ensure_keys()
    with oqs.KeyEncapsulation(alg) as kem:
        kem.import_public_key(pub)
        ct, ss = kem.encap_secret()
        return ct, ss, alg


def decapsulate(ciphertext: bytes) -> Tuple[bytes, str]:
    """Decapsulate ciphertext with our private key. Returns (shared_secret, alg)."""
    if not _HAS_OQS:
        raise ImportError('liboqs (pyoqs) not available')
    pub, priv, alg = ensure_keys()
    with oqs.KeyEncapsulation(alg) as kem:
        kem.import_public_key(pub)
        kem.import_secret_key(priv)
        ss = kem.decap_secret(ciphertext)
        return ss, alg


def has_pqc() -> bool:
    return _HAS_OQS
