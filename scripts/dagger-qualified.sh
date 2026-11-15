#!/usr/bin/env bash
# Use the qualified Linux/amd64 CLI and engine without changing global selection.
set -euo pipefail

CLI="${DAGGER_BIN:-$HOME/.local/opt/dagger/1.0.0-beta.27/bin/dagger}"
EXPECTED="d8a5c186090f92062fe773508f3b4d609ea75658802d5f5b75d6f627f2f2a075"
ENGINE="image://registry.dagger.io/engine@sha256:ad121f720ed9bfb8e740f99dd783fa8472965a5e262fc64ff3ef2634cea1e6dd"

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
