"""
Data encryption service for personally identifiable information (PII).

Uses Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256) from the
``cryptography`` library.  All encrypted values are URL-safe base64
encoded strings suitable for storage in text/varchar columns.

Usage::

    from services.storage.encryption import encryption_service

    cipher = encryption_service.encrypt("123-45-6789")
    plain  = encryption_service.decrypt(cipher)
"""

from __future__ import annotations

import base64
import hashlib

import structlog
from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

logger = structlog.get_logger(__name__)


class EncryptionService:
    """Symmetric encryption/decryption wrapper around Fernet.

    Parameters
    ----------
    key : str
        An arbitrary-length secret string.  It is derived into a valid
        32-byte URL-safe base64-encoded Fernet key via SHA-256 hashing.
        In production this should be a high-entropy secret stored in a
        vault or environment variable.
    """

    def __init__(self, key: str) -> None:
        # Fernet requires a 32-byte, URL-safe base64-encoded key.
        # We derive one deterministically from the settings value so
        # operators can use any string length they prefer.
        derived = hashlib.sha256(key.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(derived)
        self._fernet = Fernet(fernet_key)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string and return a URL-safe token.

        Parameters
        ----------
        plaintext : str
            The sensitive value to protect (e.g. SSN, account number).

        Returns
        -------
        str
            A Fernet-encrypted, URL-safe base64-encoded token.

        Raises
        ------
        ValueError
            If *plaintext* is empty.
        """
        if not plaintext:
            raise ValueError("Cannot encrypt an empty string")

        token: bytes = self._fernet.encrypt(plaintext.encode("utf-8"))
        return token.decode("utf-8")

    def decrypt(self, token: str) -> str:
        """Decrypt a previously encrypted token back to plaintext.

        Parameters
        ----------
        token : str
            The Fernet token returned by :meth:`encrypt`.

        Returns
        -------
        str
            The original plaintext value.

        Raises
        ------
        ValueError
            If the token is invalid, tampered with, or was encrypted
            with a different key.
        """
        try:
            plaintext: bytes = self._fernet.decrypt(token.encode("utf-8"))
            return plaintext.decode("utf-8")
        except InvalidToken as exc:
            logger.error("encryption.decrypt_failed", error=str(exc))
            raise ValueError(
                "Decryption failed — the token is invalid or was encrypted "
                "with a different key."
            ) from exc

    def rotate_encrypt(self, old_token: str, new_service: "EncryptionService") -> str:
        """Re-encrypt data under a new key during key rotation.

        Decrypts *old_token* with the current key, then encrypts the
        result with *new_service*'s key.

        Parameters
        ----------
        old_token : str
            Token encrypted with the current key.
        new_service : EncryptionService
            Service initialized with the new encryption key.

        Returns
        -------
        str
            Token encrypted with the new key.
        """
        plaintext = self.decrypt(old_token)
        return new_service.encrypt(plaintext)


# ---------------------------------------------------------------------------
# Module-level singleton — ready to import anywhere in the app
# ---------------------------------------------------------------------------

encryption_service = EncryptionService(key=settings.ENCRYPTION_KEY)
