#!/usr/bin/env python3
"""Install only the qualified beta27 executable, without running a remote installer."""

import hashlib
import io
import os
import pathlib
import sys
import tarfile
import urllib.request

URL = (
    "https://dl.dagger.io/dagger/releases/1.0.0-beta.27/" "dagger_v1.0.0-beta.27_linux_amd64.tar.gz"
)
SHA256 = "d8a5c186090f92062fe773508f3b4d609ea75658802d5f5b75d6f627f2f2a075"
MAX_BYTES = 150 * 1024 * 1024


def executable(archive: bytes) -> bytes:
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as bundle:
        members = [m for m in bundle.getmembers() if m.name == "dagger"]
        if len(members) != 1 or not members[0].isfile() or members[0].size > MAX_BYTES:
            raise ValueError("Unexpected qualified CLI archive shape")
        stream = bundle.extractfile(members[0])
        if stream is None:
            raise ValueError("Qualified CLI is absent")
        binary = stream.read(MAX_BYTES + 1)
    if len(binary) > MAX_BYTES or hashlib.sha256(binary).hexdigest() != SHA256:
        raise ValueError("Qualified CLI checksum mismatch")
    return binary


def bootstrap(destination: pathlib.Path) -> None:
    if destination.exists() or destination.is_symlink():
        raise ValueError("CLI destination must not already exist")
    with urllib.request.urlopen(URL, timeout=60) as response:
        archive = response.read(MAX_BYTES + 1)
    if len(archive) > MAX_BYTES:
        raise ValueError("Qualified CLI archive exceeds limit")
    binary = executable(archive)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as output:
        output.write(binary)
    os.chmod(destination, 0o755)
    print("Qualified beta27 CLI checksum verified")


if __name__ == "__main__":
    try:
        bootstrap(pathlib.Path(sys.argv[1]))
    except Exception:
        print("Qualified CLI bootstrap failed", file=sys.stderr)
        raise SystemExit(1) from None
