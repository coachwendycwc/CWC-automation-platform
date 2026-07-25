"""Symmetric field-level encryption for sensitive at-rest values (e.g. SSN/EIN).

The database must never hold a plaintext tax identifier. Values are encrypted
with Fernet (AES-128-CBC + HMAC-SHA256) using TAX_ID_ENCRYPTION_KEY. Reads
decrypt transparently; a decryption failure surfaces loudly rather than
silently returning ciphertext or None.

In production a real key is mandatory — get_settings() fails closed at startup
if it is still the built-in default (see app.config), mirroring SECRET_KEY.
"""
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings


@lru_cache()
def _fernet() -> Fernet:
    key = get_settings().tax_id_encryption_key
    # A Fernet key is 32 url-safe-base64 bytes. Accept it verbatim; let Fernet
    # raise on a malformed key rather than papering over a misconfiguration.
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_value(plaintext: str | None) -> str | None:
    """Encrypt a plaintext string for storage. None/empty passes through as None."""
    if plaintext is None or plaintext == "":
        return None
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str | None) -> str | None:
    """Decrypt a stored value. None passes through; tampered/undecryptable data
    raises rather than leaking ciphertext."""
    if ciphertext is None or ciphertext == "":
        return None
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise ValueError(
            "Stored encrypted value could not be decrypted — wrong "
            "TAX_ID_ENCRYPTION_KEY or corrupted data."
        ) from exc


def mask_tax_id(plaintext: str | None) -> str | None:
    """Return a display-safe form exposing only the last 4 characters."""
    if not plaintext:
        return None
    last4 = plaintext[-4:]
    return f"•••••{last4}"
