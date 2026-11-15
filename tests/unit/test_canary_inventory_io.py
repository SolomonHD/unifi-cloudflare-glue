"""Read adapters are complete/bounded and never fall back to broad inventory."""

import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from urllib.parse import parse_qs, urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "canary_read_test_package",
    ROOT / "src/main/__init__.py",
    submodule_search_locations=[str(ROOT / "src/main")],
)
package = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = package
from canary_read_test_package import canary_inventory_io as readers
from canary_read_test_package import canary_store as store
from canary_read_test_package.canary_s3 import StoredBlob, _token

ZONE = "a" * 32
RUN = "gha-1794714939-43674454065-1"
PREFIX = "cloudflare-live-ci/v1/"
BINDING = store.StoreBinding(
    "https://s3.us-east-1.wasabisys.com", "us-east-1", "sandbox-ghe-actions-ci", PREFIX, "test"
)
KEY = PREFIX + "maintenance.json"
SENTINEL = "synthetic-private-provider-body"


@pytest.mark.parametrize("errors,exit_code", [([], 0), (["inventory_read_failed"], 1)])
def test_inventory_status_checker_preserves_safe_report_and_fails_incomplete_selection(
    errors, exit_code
):
    report = {
        "operation": "janitor_inventory",
        "report_only": True,
        "rows": [],
        "errors": errors,
        "scanned": 0,
        "excluded": 0,
        "stale_threshold_seconds": 2100,
    }
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check-canary-inventory.py")],
        input=json.dumps(report).encode(),
        capture_output=True,
        env={},
        check=False,
    )
    assert result.returncode == exit_code
    assert json.loads(result.stdout) == report


def record(label="txt", identity="b" * 32):
    return {
        "id": identity,
        "name": f"{RUN}.{label}.ci.solomonhd.ai",
        "type": label.upper(),
        "proxied": False,
        "created_on": "2026-11-15T03:55:00Z",
        "content": SENTINEL,
    }


def page(rows, *, total=None, number=1):
    total = len(rows) if total is None else total
    return {
        "result": rows,
        "result_info": {
            "page": number,
            "per_page": 100,
            "count": len(rows),
            "total_count": total,
            "total_pages": (total + 99) // 100,
        },
    }


def test_cf_reader_uses_exact_server_namespace_filters_and_discards_content():
    client = SimpleNamespace(
        zone_id=ZONE, verify_zone=Mock(), _get=Mock(return_value=page([record()]))
    )
    rows = readers.namespace_records(client)
    query = parse_qs(urlsplit(client._get.call_args.args[0]).query)
    assert query["name.endswith"] == [".ci.solomonhd.ai"]
    assert query["name.startswith"] == ["gha-"] and query["match"] == ["all"]
    assert rows[0].record_id == "b" * 32
    assert not hasattr(rows[0], "content") and SENTINEL not in repr(rows)


@pytest.mark.parametrize(
    "payload",
    [
        page([record()], total=201),
        page([record()], total=101),
        page([{**record(), "name": SENTINEL + ".sghd.io"}]),
        page([record(), record()]),
    ],
)
def test_bad_partial_oversized_or_unrelated_cf_inventory_fails_without_echo(payload):
    client = SimpleNamespace(zone_id=ZONE, verify_zone=Mock(), _get=Mock(return_value=payload))
    with pytest.raises(store.StoreError) as error:
        readers.namespace_records(client)
    assert SENTINEL not in str(error.value)


def state():
    return {
        "version": 4,
        "resources": [
            {
                "provider": f'provider["{readers.PROVIDER}"]',
                "mode": "managed",
                "type": "cloudflare_dns_record",
                "name": "canary",
                "instances": [
                    {
                        "index_key": label,
                        "attributes": {
                            "id": identity,
                            "name": f"{RUN}.{label}.ci.solomonhd.ai",
                            "type": kind,
                            "proxied": False,
                            "zone_id": ZONE,
                            "content": SENTINEL,
                        },
                    }
                    for label, kind, identity in (
                        ("txt", "TXT", "b" * 32),
                        ("cname", "CNAME", "c" * 32),
                    )
                ],
            }
        ],
    }


def test_state_identity_projection_retains_no_values():
    identities = readers.state_identities(json.dumps(state()).encode(), RUN, ZONE)
    assert len(identities) == 2
    assert {r.record_type for r in identities} == {"TXT", "CNAME"}
    assert SENTINEL not in repr(identities)


@pytest.mark.parametrize(
    "field,value",
    [("zone_id", "d" * 32), ("proxied", True), ("name", "outside.example.org"), ("type", "A")],
)
def test_protected_state_wrong_identity_rejected(field, value):
    raw = state()
    raw["resources"][0]["instances"][0]["attributes"][field] = value
    with pytest.raises((store.StoreError, ValueError)):
        readers.state_identities(json.dumps(raw).encode(), RUN, ZONE)


def ledger(prefix=RUN, revision="d" * 40):
    run = store.RunIdentity(
        prefix,
        revision,
        ZONE,
        "solomonhd.ai",
        ((f"{prefix}.txt.ci.solomonhd.ai", "TXT"), (f"{prefix}.cname.ci.solomonhd.ai", "CNAME")),
    )
    return store.Ledger(run, "owner", 0, "absent")


def version(identity="version-1", **changes):
    return {
        "Key": KEY,
        "VersionId": identity,
        "ETag": '"etag"',
        "LastModified": datetime(2026, 11, 15, 13, tzinfo=timezone.utc),
        **changes,
    }


def test_historical_reader_selects_exact_run_revision_without_raw_output():
    listing = [version(), version("version-2")]
    transport = Mock()
    transport._call.return_value = {"IsTruncated": False, "Versions": listing}
    transport.get_blob.side_effect = [
        StoredBlob(store.encode_ledger(ledger()), _token("version-1", '"etag"')),
        StoredBlob(
            store.encode_ledger(ledger("gha-1794714939-999-1")), _token("version-2", '"etag"')
        ),
    ]
    observations = readers.ledger_observations(transport, BINDING, RUN, "d" * 40)
    assert len(observations) == 1 and "owner" not in repr(observations)
    assert transport._call.call_args.kwargs == {"Prefix": KEY, "MaxKeys": 128}
    transport.create_blob.assert_not_called()


@pytest.mark.parametrize(
    "response",
    [
        {"IsTruncated": False, "Versions": [version(Key=PREFIX + "other")]},
        {"IsTruncated": False, "Versions": [version(), version()]},
        {
            "IsTruncated": True,
            "Versions": [],
            "NextKeyMarker": KEY,
            "NextVersionIdMarker": "repeat",
        },
    ],
)
def test_bad_version_index_cannot_be_reported_as_complete(response):
    transport = Mock()
    transport._call.return_value = response
    transport.get_blob.return_value = StoredBlob(
        store.encode_ledger(ledger()), _token("version-1", '"etag"')
    )
    with pytest.raises(store.StoreError):
        readers.ledger_observations(transport, BINDING, RUN, "d" * 40)
    transport.create_blob.assert_not_called()
