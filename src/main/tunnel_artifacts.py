"""Protected tunnel artifacts and a stdlib-only in-container formatter/verifier."""

from __future__ import annotations

import json
import os
import shlex
import stat
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import dagger

OUTPUT_DIRECTORY = "/root/tunnel-credentials"
INPUT_DIRECTORY = "/root"
RUNTIME_SCRIPT = "/tooling/src/main/tunnel_artifacts.py"
OUTPUT_NAMES = ("tunnel_ids", "tunnel_tokens", "credentials_json")
FORMATS = {"json", "human", "shell"}
SUMMARY_KEYS = {
    "count",
    "ids_valid",
    "tokens_valid",
    "credentials_valid",
    "format_valid",
    "permissions_valid",
}


def _validate(values: object) -> dict:
    if not isinstance(values, dict) or not all(
        isinstance(values.get(key), dict) and values[key] for key in OUTPUT_NAMES
    ):
        raise ValueError("Invalid credential envelope")
    ids, tokens, credentials = (values[key] for key in OUTPUT_NAMES)
    if set(ids) != set(tokens) or set(ids) != set(credentials):
        raise ValueError("Credential identities differ")
    if not all(isinstance(key, str) and key for key in ids):
        raise ValueError("Invalid credential identity")
    if not all(isinstance(value, str) and value for value in [*ids.values(), *tokens.values()]):
        raise ValueError("Invalid credential identifiers/tokens")
    normalized = {}
    for key, value in credentials.items():
        decoded = json.loads(value) if isinstance(value, str) else value
        if not isinstance(decoded, dict) or not all(
            isinstance(decoded.get(field), str) and decoded[field]
            for field in ("AccountTag", "TunnelID", "TunnelName", "TunnelSecret")
        ):
            raise ValueError("Invalid credential payload")
        if decoded["TunnelID"] != ids[key]:
            raise ValueError("Credential tunnel identity differs")
        normalized[key] = {
            field: decoded[field]
            for field in ("AccountTag", "TunnelID", "TunnelName", "TunnelSecret")
        }
    return {
        "tunnel_ids": ids,
        "tunnel_tokens": tokens,
        "credentials_json": normalized,
        "count": len(ids),
    }


def _material(payload: dict, format: str) -> tuple[str, str] | None:
    if format == "human":
        lines = ["CLOUDFLARE TUNNEL SECRETS", "TUNNEL TOKENS", "CREDENTIALS JSON", ""]
        for key in sorted(payload["tunnel_ids"]):
            lines.extend(
                [
                    "Identity: " + key,
                    "Tunnel ID: " + payload["tunnel_ids"][key],
                    "Token: " + payload["tunnel_tokens"][key],
                    json.dumps(payload["credentials_json"][key], sort_keys=True, ensure_ascii=True),
                    "",
                ]
            )
        return "credentials.txt", "\n".join(lines) + "\n"
    if format == "shell":
        lines = ["# Protected credentials. Source only in an authorized, non-logging shell."]
        for index, key in enumerate(sorted(payload["tunnel_ids"])):
            for suffix, value in (
                ("KEY", key),
                ("ID", payload["tunnel_ids"][key]),
                ("TOKEN", payload["tunnel_tokens"][key]),
                ("CREDENTIALS_JSON", json.dumps(payload["credentials_json"][key], sort_keys=True)),
            ):
                lines.append(f"TUNNEL_{index}_{suffix}=" + shlex.quote(value))
        return "tunnel-secrets.sh", "\n".join(lines) + "\n"
    return None


def _write_private(path: Path, content: str) -> None:
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(content)


def _build(directory: Path, format: str) -> None:
    values = {}
    for name in OUTPUT_NAMES:
        with open(
            Path(INPUT_DIRECTORY) / (".tunnel-output-" + name + ".json"), encoding="utf-8"
        ) as stream:
            values[name] = json.load(stream)
    payload = _validate(values)
    directory.mkdir(mode=0o700)
    _write_private(
        directory / "credentials.json", json.dumps(payload, sort_keys=True, indent=2) + "\n"
    )
    material = _material(payload, format)
    if material is not None:
        _write_private(directory / material[0], material[1])


def _verify(directory: Path, format: str) -> dict:
    expected = {"credentials.json"}
    additional = {"human": "credentials.txt", "shell": "tunnel-secrets.sh"}.get(format)
    if additional is not None:
        expected.add(additional)
    if not stat.S_ISDIR(directory.lstat().st_mode) or set(os.listdir(directory)) != expected:
        raise ValueError("Unexpected artifact entries")
    # Refuse links and wrong permissions before opening any credential-bearing path.
    for name in expected:
        info = (directory / name).lstat()
        if (
            not stat.S_ISREG(info.st_mode)
            or stat.S_IMODE(info.st_mode) != 0o600
            or info.st_uid != os.getuid()
        ):
            raise ValueError("Invalid credential artifact permissions")
    with (directory / "credentials.json").open(encoding="utf-8") as stream:
        original = json.load(stream)
    payload = _validate(original)
    if type(original.get("count")) is not int or original != payload:
        raise ValueError("Invalid normalized credential artifact")
    material = _material(payload, format)
    if material is not None:
        if (directory / material[0]).read_text(encoding="utf-8") != material[1]:
            raise ValueError("Invalid formatted credential material")
    return {"count": payload["count"], **{key: True for key in SUMMARY_KEYS if key != "count"}}


def main() -> int:
    try:
        action, format = sys.argv[1:]
        if format not in FORMATS:
            raise ValueError("Invalid output format")
        if action == "build":
            _build(Path(OUTPUT_DIRECTORY), format)
        elif action == "verify":
            print(json.dumps(_verify(Path(OUTPUT_DIRECTORY), format), sort_keys=True))
        else:
            raise ValueError("Invalid processing action")
        return 0
    except Exception:
        sys.stderr.write("Protected credential processing failed\n")
        return 1


async def protected_tunnel_artifact(container: dagger.Container, format: str) -> dagger.Directory:
    """Capture native output into private files, never through application stdout."""
    import dagger

    try:
        from .execution import PhaseFailure, live_exec
    except ImportError:
        from execution import PhaseFailure, live_exec  # type: ignore[no-redef,import-not-found]
    if format not in FORMATS:
        raise ValueError("Invalid protected credential format")
    for name in OUTPUT_NAMES:
        container = live_exec(
            container,
            ["terraform", "output", "-json", name],
            redirect_stdout="/root/.tunnel-output-" + name + ".json",
            redirect_stderr="/root/.tunnel-output.stderr",
            expect=dagger.ReturnType.ANY,
        )
        await container.sync()
        exit_code = await container.exit_code()
        if exit_code != 0:
            raise PhaseFailure("Terraform credential output", exit_code)
    container = live_exec(
        container,
        ["python", RUNTIME_SCRIPT, "build", format],
        redirect_stdout="/root/.credential-runtime.stdout",
        redirect_stderr="/root/.credential-runtime.stderr",
    )
    await container.sync()
    return container.directory(OUTPUT_DIRECTORY)


async def verify_tunnel_artifact(
    container: dagger.Container, artifact: dagger.Directory, format: str
) -> dict:
    """Only the fixed verifier's bounded booleans/count cross the process boundary."""
    try:
        from .execution import live_exec
    except ImportError:
        from execution import live_exec  # type: ignore[no-redef,import-not-found]
    if format not in FORMATS:
        raise ValueError("Invalid protected credential format")
    container = container.with_directory(OUTPUT_DIRECTORY, artifact, owner="root")
    container = live_exec(
        container,
        ["python", RUNTIME_SCRIPT, "verify", format],
        redirect_stderr="/root/.credential-runtime.stderr",
    )
    summary = json.loads(await container.stdout())
    if (
        not isinstance(summary, dict)
        or set(summary) != SUMMARY_KEYS
        or (
            type(summary.get("count")) is not int
            or summary["count"] < 1
            or any(summary.get(key) is not True for key in SUMMARY_KEYS if key != "count")
        )
    ):
        raise ValueError("Invalid bounded credential verification response")
    return summary


if __name__ == "__main__":
    sys.exit(main())
