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

# Supported ciphers
CIPHERS = {
    "ChaCha20": {
        "cls": aead.ChaCha20Poly1305,
        "generate_key": aead.ChaCha20Poly1305.generate_key,
    },
    "AESGCM": {
        "cls": aead.AESGCM,
        "generate_key": lambda: aead.AESGCM.generate_key(256),
    },
}


def parse_key(raw_key: str) -> bytes:
    cipher, b64_key = raw_key.split(":", 1)
    if cipher not in CIPHERS:
        sys.exit(f"Bad cipher: {cipher}")
    return CIPHERS[cipher]["cls"](base64.b64decode(b64_key))


def generate_key(cipher: str) -> str:
    key = CIPHERS[cipher]["generate_key"]()
    return f"{cipher}:{base64.b64encode(key).decode('ascii')}"


def b64decode(v: t.Union[str, bytes]) -> str:
    return base64.b64decode(v).decode("ascii")


def b64encode(v: bytes) -> str:
    return base64.b64encode(v).decode("ascii")


def decode_thread_token(
    thread_token: t.Optional[str],
    secret_key: bytes,
) -> t.Optional[str]:
    if thread_token is None:
        return None
    try:
        claims = jwt.decode(
            thread_token.encode("ascii"),
            secret_key,
            algorithms=["HS256", "HS384", "HS512"],
            options=dict(verify_signature=True),
        )
    except jwt.DecodeError:
        return None
    return claims.get("thread")
