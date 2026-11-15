"""Unreviewed versions never become image tags or implicit downloads."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src/main"))

import toolchains
from toolchains import kcl_image, terraform_image


@pytest.mark.parametrize("resolve", [kcl_image, terraform_image])
def test_default_identity_is_immutable(resolve):
    assert "@sha256:" in resolve()
    assert len(resolve().rsplit("sha256:", 1)[1]) == 64


@pytest.mark.parametrize("resolve", [kcl_image, terraform_image])
@pytest.mark.parametrize("version", ["latest", "beta", "", "1.2.3", "x;touch /tmp/payload"])
def test_missing_pin_fails_instead_of_resolving_an_image(resolve, version):
    with pytest.raises(ValueError, match="no reviewed image pin"):
        resolve(version)


def test_native_release_checksum_precedes_extraction_and_version_verification(monkeypatch):
    calls = []

    class FakeCore:
        def http(self, url, *, checksum):
            calls.append(("download", url, checksum))
            return "verified-archive"

        def container(self, **kwargs):
            calls.append(("platform", str(kwargs["platform"])))
            return self

        def from_(self, image):
            calls.append(("base", image))
            return self

        def with_file(self, path, source):
            calls.append(("archive", path, source))
            return self

        def with_exec(self, argv):
            calls.append(("exec", argv))
            return self

        def file(self, path):
            calls.append(("output", path))
            return "qualified-binary"

    monkeypatch.setattr(toolchains, "core", FakeCore)
    assert toolchains.kcl_binary() == "qualified-binary"
    assert calls[0] == ("platform", "linux/amd64")
    assert calls[1] == ("base", toolchains.KCL_BASE_IMAGE)
    assert calls[2] == (
        "download",
        toolchains.KCL_RELEASE_URL,
        f"sha256:{toolchains.KCL_RELEASE_SHA256}",
    )
    assert calls[3] == ("archive", "/tmp/kcl-release.tar.gz", "verified-archive")
    assert calls[4] == (
        "exec",
        ["tar", "-xzf", "/tmp/kcl-release.tar.gz", "-C", "/usr/local/bin", "kcl"],
    )
    assert calls[5][0] == "exec"
    assert "version == '0.12.4'" in calls[5][1][2]
    assert calls[6] == ("output", "/usr/local/bin/kcl")
