import base64
import hashlib
import json
import os
import typing as t

# File extensions to generate SRI hashes for
SUFFIXES = (
    ".css",
    ".js",
)


def generate_sri(
    fh: t.BinaryIO,
    alg: str = "sha384",
    block_size: int = 8192,
) -> str:
    """
    A basic [subresource integrity](https://www.w3.org/TR/SRI/) hashing
    implementation. This doesn't check the algorithm chosen nor does it support
    multiple algorithms.
    """
    hashed = hashlib.new(alg)
    while True:
        if blk := fh.read(block_size):
            hashed.update(blk)
        else:
            break
    digest = base64.b64encode(hashed.digest()).decode("UTF-8")
    return f"{alg}-{digest}"


def load_sris() -> dict[str, str]:
    sris_path = os.path.join(os.path.dirname(__file__), "sri.json")
    if not os.path.exists(sris_path):
        return {}
    with open(sris_path, encoding="UTF-8") as fh:
        return json.load(fh)


def generate_hashes() -> None:
    app_root = os.path.dirname(__file__)
    static_root = os.path.join(app_root, "static")
    hashes = {}
    for root, _, files in os.walk(static_root):
        for filename in files:
            if filename.endswith(SUFFIXES):
                filepath = os.path.join(root, filename)
                with open(filepath, "rb") as fh:
                    hashes[filepath[len(static_root) + 1 :]] = generate_sri(fh)
    with open(os.path.join(app_root, "sri.json"), "w", encoding="UTF-8") as fh:
        json.dump(hashes, fh, indent=2, sort_keys=True)
        fh.write("\n")


if __name__ == "__main__":
    generate_hashes()
