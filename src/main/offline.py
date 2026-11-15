"""Credential-free baseline graph; bootstrap is separate from offline checks."""

from dagger_clients import core

try:
    from .toolchains import PYTHON_IMAGE, kcl_binary, terraform_image
except ImportError:  # Direct-module imports used by the offline unit suite.
    from toolchains import (  # type: ignore[no-redef,import-not-found]
        PYTHON_IMAGE,
        kcl_binary,
        terraform_image,
    )

UV_IMAGE = (
    "ghcr.io/astral-sh/uv:python3.14-alpine@"
    "sha256:a7eb1d733796a8ccaeb6fe6f395e7e9d02a620f6e63ee5c1e9dfde33ba5df1d6"
)

# Import only verification inputs, not a caller's credentials, state or saved plans.
SOURCE_INCLUDE = (
    "pyproject.toml",
    "uv.lock",
    "sdk/**",
    "clients/core/**",
    "src/**",
    "tests/unit/**",
    "tests/fixtures/**",
    "schemas/**",
    "generators/**",
    "*.k",
    "kcl.mod",
    "kcl.mod.lock",
    "terraform/**/*.tf",
    "terraform/**/.terraform.lock.hcl",
    "scripts/verify-offline.sh",
    "scripts/dagger-qualified.sh",
    "scripts/bootstrap-canary-dagger.py",
    "scripts/check-canary-inventory.py",
    ".github/workflows/cloudflare-live-ci.gha.yaml",
)
SOURCE_EXCLUDE = (
    "**/__pycache__/**",
    "**/.venv/**",
    "**/.git/**",
    "**/.terraform/**",
    "**/.env",
    "**/.env.*",
    "**/*.tfstate*",
    "**/*.tfplan*",
    "**/*.tfbackend",
    "**/plan.json",
    "**/plan.out",
)


def offline_verification_container(source: core.Directory) -> core.Container:
    """Build prerequisites, then run the complete repository baseline offline.

    The returned container is lazy. Evaluating stdout/sync propagates a failing
    check as a failed Dagger exec, never a successful report containing an error.
    No Secret, host service, privileged nesting or checkout export is involved.
    """
    client = core.core()
    uv = (
        client.container(platform=core.Platform("linux/amd64"))
        .from_(UV_IMAGE)
        .file("/usr/local/bin/uv")
    )
    kcl = kcl_binary()
    bootstrap = (
        client.container(platform=core.Platform("linux/amd64"))
        .from_(PYTHON_IMAGE)
        .with_file("/usr/local/bin/uv", uv)
        .with_file("/usr/local/bin/kcl", kcl)
        .with_file(
            "/usr/local/bin/terraform",
            client.container().from_(terraform_image()).file("/bin/terraform"),
        )
        .with_directory(
            "/workspace",
            source,
            include=list(SOURCE_INCLUDE),
            exclude=list(SOURCE_EXCLUDE),
        )
        .with_workdir("/workspace")
        .with_env_variable("UV_PYTHON_DOWNLOADS", "never")
        .with_env_variable("PYTHONDONTWRITEBYTECODE", "1")
        .with_exec(["python", "--version"])
        .with_exec(["uv", "--version"])
        .with_exec(["kcl", "version"])
        .with_exec(["terraform", "version", "-json"])
        .with_exec(["uv", "sync", "--frozen"])
        .with_exec(
            ["uv", "run", "--frozen", "--no-sync"]
            + [
                "python",
                "-c",
                "import pytest, pytest_asyncio, black, isort, mypy, yaml, dagger; "
                "from dagger_clients import core",
            ]
        )
    )
    return bootstrap.with_env_variable("UV_OFFLINE", "true").with_exec(
        ["bash", "scripts/verify-offline.sh"]
    )
