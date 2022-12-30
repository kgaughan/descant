import base64
import os
import sys

from cryptography.hazmat.primitives.ciphers import aead

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


def parse_key(raw_key: str):
    cipher, b64_key = raw_key.split(":", 1)
    if cipher not in CIPHERS:
        sys.exit(f"Bad cipher: {cipher}")
    return CIPHERS[cipher]["cls"](base64.b64decode(b64_key))


def generate_key(cipher: str) -> str:
    key = CIPHERS[cipher]["generate_key"]()
    return f"{cipher}:{base64.b64encode(key).decode('ascii')}"


def b64decode(v):
    return base64.b64decode(v).decode("ascii")


def b64encode(v):
    return base64.b64encode(v).decode("ascii")
