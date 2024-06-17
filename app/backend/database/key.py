from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import hashlib

from app.backend.database.models import Key


class KeyService:
    """Private keys storage"""
    keys_path = Path('keys/')

    @staticmethod
    def _make(private_key: Ed25519PrivateKey = None) -> Key:
        if private_key is None:
            private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        address = hashlib.sha256(public_key.public_bytes_raw()).digest()
        return Key(private_key=private_key, public_key=public_key, address=address)

    @staticmethod
    def _make_cryptor(password: str) -> Fernet:
        salt = b'^<;;s\xe0P2|\x8f\xe0\xb08\x0c\x860'  # os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        crypt_key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return Fernet(crypt_key)

    @classmethod
    def load(cls, actor_address: str | bytes, password: str) -> Key | None:
        if isinstance(actor_address, bytes):
            actor_address = hex(int.from_bytes(actor_address))[2:]
        cryptor = cls._make_cryptor(password)
        try:
            with open(cls.keys_path / actor_address, 'rb') as f:
                raw_key = cryptor.decrypt(f.read())
        except FileNotFoundError:
            return
        except InvalidToken:
            return
        return cls._make(Ed25519PrivateKey.from_private_bytes(raw_key))

    @classmethod
    def generate(cls, password: str) -> Key:
        cryptor = cls._make_cryptor(password)
        key = cls._make()
        raw_key = cryptor.encrypt(key.private_key.private_bytes_raw())
        with open(cls.keys_path / key.hexaddress, 'wb') as f:
            f.write(raw_key)
        return key


