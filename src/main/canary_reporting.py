"""Dagger-side report-only inventory and protected phase measurements."""

import json
import os
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone

from .canary_dns import CloudflareDNSClient
from .canary_entrypoint import BUCKET, ENDPOINT, PREFIX, REGION, RUNTIME_ID
from .canary_inventory_io import ledger_observations, namespace_records, protected_evidence
from .canary_janitor import inventory
from .canary_metrics import measure_phases
from .canary_runtime import discover_zone, in_runtime
from .canary_s3 import Boto3S3Transport
from .canary_store import StoreBinding, StoreError


def report(operation: str, run_prefix: str = "", revision: str = "") -> dict:
    if not in_runtime() or operation not in {"janitor", "metrics"}:
        raise StoreError("Read-only reporting runtime required")
    binding = StoreBinding(ENDPOINT, REGION, BUCKET, PREFIX, RUNTIME_ID)
    transport = Boto3S3Transport(
        binding, runtime=True, runtime_check=in_runtime, observation_only=True
    )
    now = datetime.now(timezone.utc)
    if operation == "metrics":
        timings = measure_phases(
            ledger_observations(transport, binding, run_prefix, revision),
            run_prefix=run_prefix,
            revision=revision,
            now=now,
        )
        return {
            "operation": "phase_measurements",
            "run_prefix": run_prefix,
            "revision": revision,
            "phases": [
                {**asdict(item), "start": item.start.isoformat(), "end": item.end.isoformat()}
                for item in timings
            ],
        }
    zone = discover_zone()
    # A transport context only, never an asserted owner or persisted canary run.
    client = CloudflareDNSClient(zone, f"gha-{int(now.timestamp())}-1-1")
    deadline = time.monotonic() + 90
    result = inventory(
        zone_id=zone,
        zone_name="solomonhd.ai",
        now=now,
        read_candidates=lambda limit: namespace_records(client, limit),
        read_evidence=lambda prefix: protected_evidence(transport, binding, prefix, deadline),
    )
    return result.to_dict()


if __name__ == "__main__":
    os.umask(0o077)
    try:
        args = json.loads(sys.argv[1])
        print(json.dumps(report(**args), sort_keys=True))
    except Exception:
        print("Read-only canary reporting unconfirmed", file=sys.stderr)
        raise SystemExit(1) from None
