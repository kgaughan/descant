import abc
import base64
import sys
import typing as t

from cryptography.hazmat.primitives.ciphers import aead
import jwt

__all__ = [
    "CIPHERS",
    "generate_key",
    "parse_key",
    "b64decode",
    "b64encode",
]


class CipherInstance(t.Protocol):
    def encrypt(self, nonce: bytes, data: bytes, associated_data: bytes) -> bytes: ...
    def decrypt(self, nonce: bytes, data: bytes, associated_data: bytes) -> bytes: ...


class Cipher(t.Protocol):
    @staticmethod
    @abc.abstractmethod
    def make(key: bytes) -> CipherInstance: ...

    @staticmethod
    @abc.abstractmethod
    def generate_key() -> bytes: ...


class ChaCha20(Cipher):
    @staticmethod
    def make(key: bytes) -> CipherInstance:
        return aead.ChaCha20Poly1305(key)

    @staticmethod
    def generate_key() -> bytes:
        return aead.ChaCha20Poly1305.generate_key()


class AESGCM(Cipher):
    @staticmethod
    def make(key: bytes) -> CipherInstance:
        return aead.AESGCM(key)

    @staticmethod
    def generate_key() -> bytes:
        return aead.AESGCM.generate_key(256)


# Supported ciphers
CIPHERS: t.Mapping[str, Cipher] = {
    "ChaCha20": ChaCha20,
    "AESGCM": AESGCM,
}


def parse_key(raw_key: str) -> CipherInstance:
    cipher, b64_key = raw_key.split(":", 1)
    if cipher not in CIPHERS:
        sys.exit(f"Bad cipher: {cipher}")
    return CIPHERS[cipher].make(base64.b64decode(b64_key))


def generate_key(cipher: str) -> str:
    return f"{cipher}:{base64.b64encode(CIPHERS[cipher].generate_key()).decode('ascii')}"


def b64decode(v: t.Union[str, bytes]) -> str:
    return base64.b64decode(v).decode("ascii")


def b64encode(v: bytes) -> str:
    return base64.b64encode(v).decode("ascii")


def decode_thread_token(
    thread_token: t.Optional[str],
    secret_key: str,
) -> t.Optional[str]:
    if thread_token is None:
        return None
    try:
        claims = jwt.decode(
            thread_token,
            secret_key,
            algorithms=["HS256", "HS384", "HS512"],
            options={"verify_signature": True},
        )
    except jwt.DecodeError:
        return None
    return claims.get("thread")
