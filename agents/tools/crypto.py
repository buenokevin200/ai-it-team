import os

from cryptography.fernet import Fernet


class SecretCrypto:
    def __init__(self, key: str | None = None):
        raw_key = key or os.getenv("ENCRYPTION_KEY", "dev-key-change-me")
        self._fernet = Fernet(self._derive_key(raw_key))

    @staticmethod
    def _derive_key(raw: str) -> bytes:
        from cryptography.fernet import Fernet
        import hashlib
        import base64

        digest = hashlib.sha256(raw.encode()).digest()
        return base64.urlsafe_b64encode(digest[:32])

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        return self._fernet.decrypt(ciphertext.encode()).decode()
