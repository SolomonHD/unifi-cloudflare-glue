"""No installer execution, archive traversal, or unverified CLI execution."""

import hashlib
import importlib.util
import io
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "canary_bootstrap", ROOT / "scripts/bootstrap-canary-dagger.py"
)
bootstrap = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bootstrap)


def archive(name="dagger", *, kind=tarfile.REGTYPE, repeat=False):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w:gz") as bundle:
        for _ in range(2 if repeat else 1):
            member = tarfile.TarInfo(name)
            member.type = kind
            member.size = 4 if kind == tarfile.REGTYPE else 0
            member.linkname = "/etc/passwd" if kind == tarfile.SYMTYPE else ""
            bundle.addfile(member, io.BytesIO(b"test") if member.size else None)
    return stream.getvalue()


@pytest.mark.parametrize(
    "kwargs", [dict(name="../dagger"), dict(kind=tarfile.SYMTYPE), dict(repeat=True), {}]
)
def test_bad_archive_or_unqualified_binary_rejected(kwargs):
    with pytest.raises(ValueError):
        bootstrap.executable(archive(**kwargs))


def test_regular_executable_checked_before_any_install(monkeypatch):
    monkeypatch.setattr(bootstrap, "SHA256", hashlib.sha256(b"test").hexdigest())
    assert bootstrap.executable(archive()) == b"test"


def test_pin_is_the_accepted_beta27_identity():
    assert bootstrap.SHA256 == "d8a5c186090f92062fe773508f3b4d609ea75658802d5f5b75d6f627f2f2a075"
    assert "1.0.0-beta.27" in bootstrap.URL
