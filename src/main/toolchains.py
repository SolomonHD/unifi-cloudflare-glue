"""Reviewed execution identities; an absent pin must not select a moving tag."""

from dagger_clients.core import Container, File, Platform, core

DEFAULT_TERRAFORM_VERSION = "1.13.5"
DEFAULT_KCL_VERSION = "0.12.4"

TERRAFORM_IMAGE = (
    "hashicorp/terraform:1.13.5@"
    "sha256:6bbb82d575aa7bd4f0a2c6e3a0838ab9590426c08a71d7a2783643f01004d356"
)
KCL_RELEASE_URL = (
    "https://github.com/kcl-lang/cli/releases/download/v0.12.4/" "kcl-v0.12.4-linux-amd64.tar.gz"
)
KCL_RELEASE_SHA256 = "01dc1d8914ed8fdfac7e8b34cc155227cf7f155ef8760f741f35b0f8529f08ca"
KCL_BASE_IMAGE = (
    "python:3.12-bookworm@"
    "sha256:4209fae09a3e20afd863e528bfddc235da5fd5977983e1996cd54cc9a72e6267"
)
PYTHON_IMAGE = (
    "python:3.12-slim@" "sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b"
)


def terraform_image(version: str = DEFAULT_TERRAFORM_VERSION) -> str:
    if version != DEFAULT_TERRAFORM_VERSION:
        raise ValueError("Terraform version has no reviewed image pin")
    return TERRAFORM_IMAGE


def kcl_image(version: str = DEFAULT_KCL_VERSION) -> str:
    if version != DEFAULT_KCL_VERSION:
        raise ValueError("KCL version has no reviewed image pin")
    return KCL_BASE_IMAGE


def kcl_release_archive() -> File:
    """Verify release bytes before the native compiler can execute."""
    return core().http(KCL_RELEASE_URL, checksum=f"sha256:{KCL_RELEASE_SHA256}")


def kcl_container(version: str = DEFAULT_KCL_VERSION) -> Container:
    """Build the native compiler from verified bytes on the pinned glibc runtime."""
    return (
        core()
        .container(platform=Platform("linux/amd64"))
        .from_(kcl_image(version))
        .with_file("/tmp/kcl-release.tar.gz", kcl_release_archive())
        .with_exec(["tar", "-xzf", "/tmp/kcl-release.tar.gz", "-C", "/usr/local/bin", "kcl"])
        .with_exec(
            [
                "python",
                "-c",
                "import subprocess; "
                "version = subprocess.check_output(['kcl', 'version'], text=True).strip(); "
                "assert version == '0.12.4', 'KCL executable version mismatch'",
            ]
        )
    )


def kcl_binary() -> File:
    return kcl_container().file("/usr/local/bin/kcl")
