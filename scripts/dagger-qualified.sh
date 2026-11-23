#!/usr/bin/env bash
# Use the qualified Linux/amd64 CLI and engine without changing global selection.
set -euo pipefail

CLI="${DAGGER_BIN:-$HOME/.local/opt/dagger/1.0.0-beta.28/bin/dagger}"
EXPECTED="d0f8648c48418fe23773da40879f98d5db03b0d86d0ab4308174a42ad043300f"
ENGINE="image://registry.dagger.io/engine@sha256:06d04ebed5f4042a0aad7fcff7dd3734bc06f9f994a7338e0138326c9605fb5c"

if [[ ! -x "$CLI" ]]; then
    printf '%s\n' 'Qualified Dagger CLI is unavailable; bootstrap the recorded binary first.' >&2
    exit 2
fi
read -r actual _ < <(sha256sum -- "$CLI")
if [[ "$actual" != "$EXPECTED" ]]; then
    printf '%s\n' 'Dagger CLI checksum differs from the qualified identity.' >&2
    exit 2
fi
for argument in "$@"; do
    case "$argument" in
        --engine|--engine=*)
            printf '%s\n' 'Engine overrides require a separately qualified runtime.' >&2
            exit 2
            ;;
    esac
done
exec "$CLI" --engine "$ENGINE" "$@"
