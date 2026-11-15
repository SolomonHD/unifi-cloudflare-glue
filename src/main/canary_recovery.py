"""Explicit, version-bound cleanup of one terminated hosted canary run."""

import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
import uuid
from pathlib import Path
from urllib.request import HTTPSHandler, ProxyHandler, Request, build_opener

from .canary_dns import CloudflareDNSClient
from .canary_entrypoint import BUCKET, ENDPOINT, PREFIX, REGION, RUNTIME_ID
from .canary_identity import record_name, validate_run_prefix
from .canary_runtime import NoRedirect, RuntimeJournal, in_runtime, qualify_backend
from .canary_s3 import Boto3S3Transport, _untoken
from .canary_store import CanaryStore, RecoveryAuthorization, StoreBinding, StoreError
from .canary_terraform import BackendConfig, TerraformDriver, states_match

REPOSITORY = "SolomonHD/unifi-cloudflare-glue"


def public_json(path: str) -> dict:
    result = None
    try:
        request = Request(
            "https://api.github.com/" + path,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "cloudflare-canary-recovery",
            },
        )
        with build_opener(ProxyHandler({}), NoRedirect(), HTTPSHandler()).open(
            request, timeout=15
        ) as response:
            raw = response.read(1048577)
            if response.status != 200 or len(raw) > 1048576:
                raise ValueError()
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError()
        result = payload
    except Exception:
        pass
    if result is None:
        raise StoreError("Prior Actions status could not be verified")
    return result


def terminal_evidence(run_prefix: str, revision: str) -> str:
    validate_run_prefix(run_prefix)
    _, _, run_id, attempt = run_prefix.split("-")
    path = f"repos/{REPOSITORY}/actions/runs/{run_id}/attempts/{attempt}"
    run = public_json(path)
    if (
        run.get("id") != int(run_id)
        or run.get("run_attempt") != int(attempt)
        or run.get("status") != "completed"
        or not run.get("conclusion")
        or run.get("head_sha") != revision
        or run.get("repository", {}).get("full_name") != REPOSITORY
        or run.get("head_repository", {}).get("full_name") != REPOSITORY
        or run.get("head_branch") not in {"main", "change/add-cloudflare-live-ci-canary"}
        or run.get("path") != ".github/workflows/cloudflare-live-ci.gha.yaml"
        or run.get("event") not in {"push", "workflow_dispatch", "schedule"}
    ):
        raise StoreError("Exact prior Actions identity is not terminal")
    response = public_json(path + "/jobs?per_page=100")
    jobs = response.get("jobs")
    if (
        not isinstance(jobs, list)
        or not jobs
        or response.get("total_count") != len(jobs)
        or len(jobs) > 100
        or any(
            job.get("status") != "completed"
            or not job.get("completed_at")
            or not job.get("conclusion")
            for job in jobs
        )
    ):
        raise StoreError("Prior Actions jobs are not all terminal")
    return f"https://github.com/{REPOSITORY}/actions/runs/{run_id}/attempts/{attempt}"


def reconcile(config: dict) -> dict:
    prefix = config["run_prefix"]
    validate_run_prefix(prefix)
    if (
        not in_runtime()
        or config.get("exclusive_writer") is not True
        or config.get("prior_writer_terminated") is not True
    ):
        raise StoreError("Explicit termination and exclusive recovery authorization required")
    report = {
        "operation": "reconcile",
        "run_prefix": prefix,
        "original_outcome": "unknown",
        "cleanup": "not_attempted",
        "phase": "preflight",
        "ownership_transferred": False,
    }
    try:
        binding = StoreBinding(ENDPOINT, REGION, BUCKET, PREFIX, RUNTIME_ID)
        observer = Boto3S3Transport(
            binding, runtime=True, runtime_check=in_runtime, observation_only=True
        )
        prior = observer.get(binding, PREFIX + "maintenance.json")
        state_key = PREFIX + f"runs/{prefix}/terraform.tfstate"
        state = observer.get_blob(binding, state_key)
        if (
            prior is None
            or state is None
            or prior.ledger.run.run_prefix != prefix
            or prior.ledger.completed is not None
            or (
                _untoken(prior.version)[0] != config["expected_claim_version_id"]
                or _untoken(state.version)[0] != config["expected_state_version_id"]
            )
        ):
            raise StoreError("Requested retained claim/state versions do not match")
        evidence = terminal_evidence(prefix, prior.ledger.run.revision)
        if prior.ledger.receipts and all(
            receipt.outcome in {"succeeded", "failed"} for receipt in prior.ledger.receipts
        ):
            report["original_outcome"] = "failed"
        transport = Boto3S3Transport(binding, runtime=True, runtime_check=in_runtime)
        report["phase"] = "qualification"
        owner = str(uuid.uuid4())
        qualification = qualify_backend(
            transport,
            binding,
            prefix,
            prior.ledger.run.zone_id,
            PREFIX + f"runs/{prefix}/recovery/{owner}/qualification.json",
        )

        def generation() -> str:
            current = transport.get_blob(binding, state_key)
            return "absent" if current is None else current.version

        checkpointed = [""]

        def checkpoint(raw: bytes, expected: str) -> None:
            current = transport.get_blob(binding, state_key)
            if (
                current is None
                or current.version != expected
                or not states_match(current.data, raw)
            ):
                raise StoreError("Recovery state/checkpoint generation changed")
            transport.create_blob(
                binding,
                PREFIX
                + f"runs/{prefix}/checkpoints/"
                + hashlib.sha256(expected.encode()).hexdigest()
                + ".tfstate",
                current.data,
            )
            checkpointed[0] = expected

        with tempfile.TemporaryDirectory(prefix="canary-recovery-") as directory:
            root = Path(directory) / "fixture"
            shutil.copytree("/canary/fixture", root)
            dns = CloudflareDNSClient(prior.ledger.run.zone_id, prefix)
            driver = TerraformDriver(
                root,
                run_prefix=prefix,
                zone_id=prior.ledger.run.zone_id,
                backend=BackendConfig(ENDPOINT, REGION, BUCKET, state_key),
                state_generation=generation,
                checkpoint=checkpoint,
                runtime=True,
                runtime_check=in_runtime,
                dns_client=dns,
            )
            report["phase"] = "preflight"
            driver.initialize()
            raw, parsed, count = driver._state()
            if count != 2 or generation() != state.version or not states_match(raw, state.data):
                raise StoreError("Recovery requires exact complete retained state")
            for resource in parsed["resources"]:
                if resource["mode"] != "managed":
                    continue
                for instance in resource["instances"]:
                    attrs = instance["attributes"]
                    records = dns._records(
                        record_name(prefix, instance["index_key"]), time.monotonic() + 30
                    )
                    if len(records) != 1 or records[0]["id"] != attrs["id"]:
                        raise StoreError("Recovery API identity differs from retained state")
            store = CanaryStore(transport, binding, qualification)
            authorization = RecoveryAuthorization(
                prior.ledger.run,
                prior.version,
                prior.ledger.generation,
                state.version,
                True,
                True,
                evidence,
            )
            report["phase"] = "ownership"
            restored = store.recover(owner, authorization, generation())
            report["ownership_transferred"] = True
            journal = RuntimeJournal(
                store, restored.ledger.run, generation, lambda: checkpointed[0]
            )
            journal.owner, journal.expected = owner, state.version
            journal.assert_owned()
            checkpoint(raw, state.version)
            for phase, action in (("destroy", driver.destroy), ("absence", driver.verify_absence)):
                report["phase"] = phase
                journal.intent(phase)
                journal.assert_owned()
                action()
                journal.result(phase, "verified")
            journal.complete()
        report["cleanup"] = "verified"
    except Exception:
        if report["phase"] == "ownership":
            report["ownership_transferred"] = None
            report["cleanup"] = "unknown"
        elif report["ownership_transferred"]:
            report["cleanup"] = "unknown"
    return report


if __name__ == "__main__":
    os.umask(0o077)
    try:
        result = reconcile(json.loads(Path(sys.argv[1]).read_text()))
        print(json.dumps(result, sort_keys=True))
        raise SystemExit(0 if result["cleanup"] == "verified" else 1)
    except Exception:
        print("Canary reconciliation unconfirmed", file=sys.stderr)
        raise SystemExit(1) from None
