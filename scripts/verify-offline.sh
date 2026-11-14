#!/usr/bin/env bash
# Credential-free verification after the bootstrap documented in CONTRIBUTING.md.
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

verify() {
    uv run --offline --frozen \
        --with pytest==9.2.0 --with pytest-asyncio==1.5.0 \
        --with black==26.10.1 --with isort==9.0.2 \
        --with mypy==2.4.1 --with types-PyYAML==6.0.12.20261113 "$@"
}

verify black --check src tests
verify isort --check-only src tests
verify mypy src/main
verify python -m compileall -q src tests
verify python -m pytest tests/unit -ra

# These are executable check files, not KCL's *_test.k discovery convention.
for entry in main.k test_validation.k test_error_validation.k test_error_format.k \
    test_cloudflare.k generators/unifi.k generators/cloudflare.k; do
    printf 'KCL: %s\n' "$entry"
    kcl run "$entry" >/dev/null
done
