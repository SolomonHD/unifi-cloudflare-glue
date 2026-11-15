"""Private Dagger-side adapters; stdout is a strict metadata-only result."""

import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import cast
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, HTTPSHandler, ProxyHandler, Request, build_opener

from .canary_entrypoint import BUCKET, ENDPOINT, PREFIX, REGION, RUNTIME_ID
from .canary_identity import ZONE_NAME, record_name, validate_run_prefix
from .canary_lifecycle import Outcome, run_canary
from .canary_s3 import Boto3S3Transport
from .canary_store import (
    CanaryStore,
    Phase,
    Qualification,
    RunIdentity,
    StoreBinding,
    StoreError,
)
from .canary_terraform import (
    BackendConfig,
    LockEvidence,
    TerraformDriver,
    qualify_native_lock,
    states_match,
)


def in_runtime() -> bool:
    return Path("/run/canary/runtime-marker").is_file()


def validate_config(config: dict) -> None:
    if (
        not in_runtime()
        or any(
            config.get(k) != v
            for k, v in {
                "bucket": BUCKET,
                "region": REGION,
                "endpoint": ENDPOINT,
                "prefix": PREFIX,
                "runtime_identity": RUNTIME_ID,
                "policy_reviewed": True,
                "fixture": "/canary/fixture",
            }.items()
        )
        or not re.fullmatch(r"[0-9a-f]{40}", str(config.get("revision", "")))
    ):
        raise StoreError("Approved Dagger sandbox configuration required")
    validate_run_prefix(config["run_prefix"])
    if config.get("operation") not in {"normal", "qualify"}:
        raise StoreError("Unsupported canary operation")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def discover_zone() -> str:
    """Resolve only the exact approved zone, never a general account inventory."""
    result = None
    try:
        token = os.environ["CLOUDFLARE_API_TOKEN"]
        request = Request(
            "https://api.cloudflare.com/client/v4/zones?"
            + urlencode({"name": ZONE_NAME, "per_page": 1}),
            headers={"Authorization": "Bearer " + token},
        )
        with build_opener(ProxyHandler({}), NoRedirect(), HTTPSHandler()).open(
            request, timeout=15
        ) as response:
            raw = response.read(262145)
            if response.status != 200 or len(raw) > 262144:
                raise ValueError()
        payload = json.loads(raw)
        records = payload["result"]
        info = payload["result_info"]
        if (
            payload["success"] is not True
            or payload["errors"] != []
            or len(records) != 1
            or info["total_count"] != 1
            or info["total_pages"] != 1
            or records[0]["name"] != ZONE_NAME
        ):
            raise ValueError()
        zone = records[0]["id"]
        if not isinstance(zone, str) or re.fullmatch(r"[0-9a-f]{32}", zone) is None:
            raise ValueError()
        result = zone
    except Exception:
        pass
    if result is None:
        raise StoreError("Exact sandbox zone preflight failed")
    return result


class S3LockHolder:
    def __init__(self, transport: Boto3S3Transport, binding: StoreBinding):
        self.transport, self.binding = transport, binding

    def create_lock(self, key: str, body: bytes) -> LockEvidence:
        blob = self.transport.create_blob(self.binding, key, body)
        return LockEvidence(key, blob.version, blob.data)

    def read_lock(self, key: str) -> LockEvidence | None:
        blob = self.transport.get_blob(self.binding, key)
        return None if blob is None else LockEvidence(key, blob.version, blob.data)

    def release_lock(self, key: str, version: str) -> None:
        self.transport.delete_blob(self.binding, key, version)


def qualify_backend(
    transport: Boto3S3Transport,
    binding: StoreBinding,
    run_prefix: str,
    zone_id: str,
    receipt_key: str,
) -> Qualification:
    transport.qualify_backend()
    qualifier_key = PREFIX + "qualification/" + str(uuid.uuid4()) + "/terraform.tfstate"
    transport.create_blob(
        binding,
        receipt_key,
        json.dumps(
            {
                "key": qualifier_key,
                "runtime_identity": RUNTIME_ID,
                "run_prefix": run_prefix,
            },
            sort_keys=True,
        ).encode(),
    )
    with tempfile.TemporaryDirectory(prefix="canary-lock-") as directory:
        root = Path(directory) / "fixture"
        root.mkdir()
        (root / "versions.tf").write_text(
            'terraform {\n required_version = ">= 1.13.5, < 2.0.0"\n backend "s3" {}\n}\n'
        )
        qualifier = TerraformDriver(
            root,
            run_prefix=run_prefix,
            zone_id=zone_id,
            backend=BackendConfig(ENDPOINT, REGION, BUCKET, qualifier_key),
            state_generation=lambda: "absent",
            checkpoint=lambda *_: None,
            runtime=True,
            runtime_check=in_runtime,
        )
        qualifier.initialize()
        qualify_native_lock(
            qualifier,
            S3LockHolder(transport, binding),
            qualification_prefix=PREFIX + "qualification/",
        )
    # S3/native locking are measured; access, retention and external exclusion
    # remain separately reviewed operator prerequisites, not an API fence.
    return Qualification(binding, True, True, True, True, True, True, True, True, True)


class RuntimeJournal:
    def __init__(
        self,
        store: CanaryStore,
        run: RunIdentity,
        generation: Callable[[], str],
        checkpoint_generation: Callable[[], str],
    ):
        self.store, self.run, self.generation = store, run, generation
        self.checkpoint_generation = checkpoint_generation
        self.owner = str(uuid.uuid4())
        self.expected = "absent"
        self.pending = False
        self.dispatched = False

    def prepare(self) -> None:
        self.expected = self.generation()
        if self.expected != "absent":
            raise StoreError("New canary run must not reuse existing state")
        self.store.claim(self.owner, self.run, self.expected)

    def assert_owned(self) -> None:
        if not self.dispatched and self.generation() != self.expected:
            raise StoreError("State changed before effect")
        self.store.check_ownership(self.expected)
        if self.pending and not self.dispatched:
            self.store.check_before_effect(self.expected)
            self.dispatched = True

    def intent(self, phase: str) -> None:
        self.store.begin_intent(cast(Phase, phase), self.expected)
        self.pending, self.dispatched = True, False

    def result(self, phase: str, outcome: Outcome) -> None:
        if outcome not in {"verified", "failed", "unknown"}:
            raise StoreError("Invalid lifecycle outcome")
        observed = self.generation()
        if phase in {"create", "update", "destroy"} and self.checkpoint_generation() != observed:
            raise StoreError("Effect result lacks its exact durable checkpoint generation")
        self.store.record_result(
            "succeeded" if outcome == "verified" else outcome, self.expected, observed
        )
        self.expected = observed
        self.pending, self.dispatched = False, False

    def complete(self) -> None:
        self.assert_owned()
        self.store.complete_verified(self.owner, self.expected)


def run(config: dict) -> dict:
    validate_config(config)
    prefix, revision = config["run_prefix"], config["revision"]
    report = {
        "run_prefix": prefix,
        "revision": revision,
        "phase": "preflight",
        "primary": "unknown",
        "cleanup": "not_attempted",
        "qualified": False,
        "operation": config["operation"],
    }
    try:
        zone = discover_zone()
        binding = StoreBinding(ENDPOINT, REGION, BUCKET, PREFIX, RUNTIME_ID)
        transport = Boto3S3Transport(binding, runtime=True, runtime_check=in_runtime)
        report["phase"] = "qualification"
        qualification = qualify_backend(
            transport, binding, prefix, zone, PREFIX + f"runs/{prefix}/qualification.json"
        )
        report["qualified"] = True
        if config["operation"] == "qualify":
            report.update(phase="qualification", primary="verified", cleanup="verified")
            return report
        state_key = PREFIX + f"runs/{prefix}/terraform.tfstate"

        def generation() -> str:
            blob = transport.get_blob(binding, state_key)
            return "absent" if blob is None else blob.version

        checkpointed_generation = [""]

        def checkpoint(raw: bytes, state_version: str) -> None:
            blob = transport.get_blob(binding, state_key)
            if blob is None or blob.version != state_version or not states_match(blob.data, raw):
                raise StoreError("State/checkpoint generation mismatch")
            key = (
                PREFIX
                + f"runs/{prefix}/checkpoints/"
                + hashlib.sha256(state_version.encode()).hexdigest()
                + ".tfstate"
            )
            transport.create_blob(binding, key, blob.data)
            checkpointed_generation[0] = state_version

        identity = RunIdentity(
            prefix,
            revision,
            zone,
            ZONE_NAME,
            (
                (record_name(prefix, "txt"), "TXT"),
                (record_name(prefix, "cname"), "CNAME"),
            ),
        )
        journal = RuntimeJournal(
            CanaryStore(transport, binding, qualification),
            identity,
            generation,
            lambda: checkpointed_generation[0],
        )
        with tempfile.TemporaryDirectory(prefix="canary-run-") as directory:
            root = Path(directory) / "fixture"
            shutil.copytree(config["fixture"], root)
            driver = TerraformDriver(
                root,
                run_prefix=prefix,
                zone_id=zone,
                backend=BackendConfig(ENDPOINT, REGION, BUCKET, state_key),
                state_generation=generation,
                checkpoint=checkpoint,
                runtime=True,
                runtime_check=in_runtime,
            )
            outcome = run_canary(prefix, journal, driver)
        report.update(phase=outcome.phase, primary=outcome.primary, cleanup=outcome.cleanup)
    except Exception:
        # Do not echo Python/provider exceptions or run a second cleanup path.
        pass
    return report


def main() -> int:
    os.umask(0o077)
    try:
        config = json.loads(Path(sys.argv[1]).read_text())
        report = run(config)
    except Exception:
        print("Canary runtime preflight failed", file=sys.stderr)
        return 1
    print(json.dumps(report, sort_keys=True))
    return (
        0
        if report["primary"] == report["cleanup"] == "verified" and report["qualified"] is True
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
