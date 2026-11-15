"""Read-only, projected diagnosis of one retained canary run inside Dagger."""

import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

from .canary_dns import CloudflareDNSClient
from .canary_entrypoint import BUCKET, ENDPOINT, PREFIX, REGION, RUNTIME_ID
from .canary_identity import record_name, validate_run_prefix
from .canary_runtime import in_runtime
from .canary_s3 import Boto3S3Transport
from .canary_store import StoreBinding, StoreError
from .canary_terraform import BackendConfig, TerraformDriver, TerraformUnknown, states_match


def observe(run_prefix: str) -> dict:
    validate_run_prefix(run_prefix)
    if not in_runtime():
        raise StoreError("Dagger observation runtime required")
    binding = StoreBinding(ENDPOINT, REGION, BUCKET, PREFIX, RUNTIME_ID)
    transport = Boto3S3Transport(
        binding, runtime=True, runtime_check=in_runtime, observation_only=True
    )
    retained = transport.get(binding, PREFIX + "maintenance.json")
    if retained is None or retained.ledger.run.run_prefix != run_prefix:
        raise StoreError("Exact retained run identity not found")
    ledger = retained.ledger
    state_key = PREFIX + f"runs/{run_prefix}/terraform.tfstate"
    result = {
        "operation": "read_only_observation",
        "run_prefix": run_prefix,
        "revision": ledger.run.revision,
        "claim_completed": ledger.completed is not None,
        "last_phase": ledger.receipts[-1].phase if ledger.receipts else "prepare",
        "last_outcome": ledger.receipts[-1].outcome if ledger.receipts else None,
        "state_present": None,
        "state_shape_valid": False,
        "state_read_error_kind": None,
        "native_pull_matches_remote": None,
        "differing_top_level_keys": [],
        "resources": [],
    }
    try:
        blob = transport.get_blob(binding, state_key)
    except StoreError:
        result["state_read_error_kind"] = transport.last_read_error_kind or "unclassified"
        return result
    result["state_present"] = blob is not None
    if blob is None:
        return result
    remote = json.loads(blob.data)
    dns = CloudflareDNSClient(ledger.run.zone_id, run_prefix)
    with tempfile.TemporaryDirectory(prefix="canary-observe-") as directory:
        root = Path(directory) / "fixture"
        shutil.copytree("/canary/fixture", root)
        driver = TerraformDriver(
            root,
            run_prefix=run_prefix,
            zone_id=ledger.run.zone_id,
            backend=BackendConfig(ENDPOINT, REGION, BUCKET, state_key),
            state_generation=lambda: blob.version,
            checkpoint=lambda *_: None,
            runtime=True,
            runtime_check=in_runtime,
            dns_client=dns,
        )
        # init and state pull only: no plan, apply, import, destroy or lock test.
        driver.initialize()
        _, raw = driver._run(["state", "pull", "-no-color"], capture=True)
        pulled = json.loads(raw)
        result["native_pull_matches_remote"] = pulled == remote
        result["check_results_order_only"] = pulled != remote and states_match(blob.data, raw)
        result["check_results_empty"] = {
            "remote": remote.get("check_results") in (None, []),
            "native": pulled.get("check_results") in (None, []),
        }
        result["differing_top_level_keys"] = [
            key
            for key in (
                "version",
                "terraform_version",
                "serial",
                "lineage",
                "outputs",
                "resources",
                "check_results",
            )
            if pulled.get(key) != remote.get(key)
        ]
        try:
            driver._state(raw)
        except TerraformUnknown as error:
            code = str(error)
            result["state_shape_error"] = (
                code
                if code
                in {
                    "unexpected_state_zone",
                    "unexpected_state_resource",
                    "unexpected_state_provider",
                    "unexpected_state_instances",
                    "unexpected_state_identity",
                    "duplicate_state_resource",
                    "unexpected_state_instance",
                    "invalid_remote_state",
                    "invalid_terraform_json",
                }
                else "unclassified"
            )
            return result
        result["state_shape_valid"] = True
        safe_resources = []
        for resource in pulled["resources"]:
            if resource["mode"] != "managed":
                continue
            for instance in resource["instances"]:
                attrs = instance["attributes"]
                label = instance["index_key"]
                observed = dns._records(record_name(run_prefix, label), time.monotonic() + 30)
                safe_resources.append(
                    {
                        "name": record_name(run_prefix, label),
                        "type": attrs["type"],
                        "state_id_matches_api": len(observed) == 1
                        and observed[0]["id"] == attrs["id"],
                        "api_count": len(observed),
                    }
                )
        result["resources"] = safe_resources
    return result


if __name__ == "__main__":
    os.umask(0o077)
    try:
        print(json.dumps(observe(sys.argv[1]), sort_keys=True))
    except Exception:
        print("Read-only canary observation unconfirmed", file=sys.stderr)
        raise SystemExit(1) from None
