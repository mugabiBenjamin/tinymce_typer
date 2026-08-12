import base64
import os
from dataclasses import dataclass
from typing import Any


class SessionCryptoError(Exception):
    pass


@dataclass(frozen=True)
class EncryptedPayload:
    encrypted: bool
    algorithm: str
    salt: str
    token: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "encrypted": self.encrypted,
            "algorithm": self.algorithm,
            "salt": self.salt,
            "token": self.token,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EncryptedPayload":
        return cls(
            encrypted=bool(data.get("encrypted", False)),
            algorithm=str(data.get("algorithm", "")),
            salt=str(data.get("salt", "")),
            token=str(data.get("token", "")),
        )


class SessionCrypto:
    algorithm = "fernet-pbkdf2-sha256-v1"
    iterations = 390000
    salt_size = 16

    def is_available(self) -> bool:
        try:
            import cryptography
            from cryptography.fernet import Fernet
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        except ImportError:
            return False

        return True

    def encrypt_json_bytes(self, data: bytes, password: str) -> dict[str, Any]:
        if not password:
            raise SessionCryptoError("Encryption password cannot be empty.")

        self._ensure_available()

        from cryptography.fernet import Fernet

        salt = os.urandom(self.salt_size)
        key = self._derive_key(password=password, salt=salt)
        token = Fernet(key).encrypt(data)

        payload = EncryptedPayload(
            encrypted=True,
            algorithm=self.algorithm,
            salt=base64.urlsafe_b64encode(salt).decode("ascii"),
            token=token.decode("ascii"),
        )

        return payload.to_dict()

    def decrypt_json_bytes(self, payload: dict[str, Any], password: str) -> bytes:
        if not password:
            raise SessionCryptoError("Decryption password cannot be empty.")

        self._ensure_available()

        from cryptography.fernet import Fernet, InvalidToken

        encrypted_payload = EncryptedPayload.from_dict(payload)

        if not encrypted_payload.encrypted:
            raise SessionCryptoError("Payload is not encrypted.")

        if encrypted_payload.algorithm != self.algorithm:
            raise SessionCryptoError(f"Unsupported encryption algorithm: {encrypted_payload.algorithm}")

        try:
            salt = base64.urlsafe_b64decode(encrypted_payload.salt.encode("ascii"))
            token = encrypted_payload.token.encode("ascii")
        except Exception as exc:
            raise SessionCryptoError("Encrypted session payload is malformed.") from exc

        key = self._derive_key(password=password, salt=salt)

        try:
            return Fernet(key).decrypt(token)
        except InvalidToken as exc:
            raise SessionCryptoError("Invalid password or corrupted encrypted session.") from exc

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        self._ensure_available()

        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

        if not salt:
            raise SessionCryptoError("Encryption salt cannot be empty.")

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.iterations,
        )

        return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))

    def _ensure_available(self) -> None:
        if not self.is_available():
            raise SessionCryptoError(
                "Session encryption requires the cryptography package. Install it or disable encrypted sessions."
            )