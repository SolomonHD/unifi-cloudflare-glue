"""Bounded read-only adapters; provider bodies never cross the report boundary."""

import hashlib
import re
import time
from datetime import datetime
from typing import Literal
from urllib.parse import urlencode

from .canary_dns import CloudflareDNSClient
from .canary_identity import ZONE_NAME, validate_record_name, validate_run_prefix
from .canary_janitor import ProtectedEvidence, RecordCandidate, RecordIdentity
from .canary_metrics import LedgerVersionObservation
from .canary_recovery import terminal_evidence
from .canary_s3 import Boto3S3Transport, _token
from .canary_store import StoreBinding, StoredLedger, StoreError, decode_ledger
from .canary_terraform import PROVIDER, _json


def namespace_records(client: CloudflareDNSClient, limit: int = 200) -> list[RecordCandidate]:
    """Use supported server-side prefix AND suffix filters, never a zone-wide list."""
    if type(limit) is not int or not 1 <= limit <= 200:
        raise StoreError("Invalid namespace inventory bound")
    deadline = time.monotonic() + 45
    client.verify_zone()
    result: list[RecordCandidate] = []
    expected_total = None
    seen = set()
    for page in (1, 2):
        payload = client._get(
            "/dns_records?"
            + urlencode(
                {
                    "name.endswith": ".ci.solomonhd.ai",
                    "name.startswith": "gha-",
                    "match": "all",
                    "order": "name",
                    "direction": "asc",
                    "page": page,
                    "per_page": 100,
                }
            ),
            deadline,
        )
        rows, info = payload["result"], payload.get("result_info")
        if (
            not isinstance(rows, list)
            or not isinstance(info, dict)
            or any(
                type(info.get(k)) is not int
                for k in ("page", "per_page", "count", "total_count", "total_pages")
            )
        ):
            raise StoreError("Namespace inventory pagination invalid")
        total = info["total_count"]
        pages = (total + 99) // 100
        if (
            info["page"] != page
            or info["per_page"] != 100
            or info["count"] != len(rows)
            or len(rows) != min(100, max(0, total - (page - 1) * 100))
            or not 0 <= total <= limit
            or info["total_pages"] not in ({0, 1} if total == 0 else {pages})
            or (expected_total is not None and total != expected_total)
        ):
            raise StoreError("Namespace inventory incomplete or changed")
        expected_total = total
        for row in rows:
            if not isinstance(row, dict):
                raise StoreError("Namespace inventory record shape invalid")
            name, record_id = row.get("name"), row.get("id")
            if (
                row.get("zone_id", client.zone_id) != client.zone_id
                or row.get("zone_name", ZONE_NAME) != ZONE_NAME
            ):
                raise StoreError("Namespace inventory zone mismatch")
            if (
                not isinstance(name, str)
                or not name.startswith("gha-")
                or not name.endswith(".ci.solomonhd.ai")
            ):
                raise StoreError("Namespace filter was not enforced")
            if (
                not isinstance(record_id, str)
                or re.fullmatch(r"[0-9a-f]{32}", record_id) is None
                or record_id in seen
            ):
                raise StoreError("Namespace inventory identity invalid")
            seen.add(record_id)
            kind, proxied, created = row.get("type"), row.get("proxied"), row.get("created_on")
            if (
                not isinstance(kind, str)
                or not isinstance(proxied, bool)
                or not isinstance(created, str)
            ):
                raise StoreError("Namespace inventory metadata invalid")
            # Do not retain content, comments, tags or arbitrary provider fields.
            result.append(
                RecordCandidate(
                    client.zone_id,
                    ZONE_NAME,
                    record_id,
                    name,
                    kind,
                    proxied,
                    created,
                )
            )
        if page >= max(1, pages):
            if len(result) != total:
                raise StoreError("Namespace inventory incomplete")
            return result
    raise StoreError("Namespace inventory page bound exceeded")


def state_identities(raw: bytes, prefix: str, zone_id: str) -> tuple[RecordIdentity, ...]:
    state = _json(raw)
    resources = state.get("resources")
    if state.get("version") != 4 or not isinstance(resources, list) or len(resources) > 2:
        raise StoreError("Protected inventory state invalid")
    found: list[RecordIdentity] = []
    for resource in resources:
        if not isinstance(resource, dict) or resource.get("provider") != f'provider["{PROVIDER}"]':
            raise StoreError("Protected inventory provider invalid")
        instances = resource.get("instances")
        if not isinstance(instances, list) or len(instances) > 2:
            raise StoreError("Protected inventory instances invalid")
        if any(
            not isinstance(instance, dict) or not isinstance(instance.get("attributes"), dict)
            for instance in instances
        ):
            raise StoreError("Protected inventory attributes invalid")
        if (
            resource.get("mode") == "data"
            and resource.get("type") == "cloudflare_zone"
            and resource.get("name") == "sandbox"
        ):
            if len(instances) != 1 or instances[0].get("attributes", {}).get("id") != zone_id:
                raise StoreError("Protected inventory zone invalid")
            continue
        if (
            resource.get("mode") != "managed"
            or resource.get("type") != "cloudflare_dns_record"
            or resource.get("name") != "canary"
        ):
            raise StoreError("Protected inventory resource invalid")
        for instance in instances:
            attrs = instance.get("attributes", {})
            name, kind, identity = attrs.get("name"), attrs.get("type"), attrs.get("id")
            validate_record_name(name, prefix)
            if (
                attrs.get("zone_id") != zone_id
                or attrs.get("proxied") is not False
                or kind not in {"TXT", "CNAME"}
                or name.split(".")[1] != kind.lower()
                or instance.get("index_key") != kind.lower()
                or not isinstance(identity, str)
                or re.fullmatch(r"[0-9a-f]{32}", identity) is None
            ):
                raise StoreError("Protected inventory record invalid")
            found.append(RecordIdentity(identity, name, kind))
    if (
        len(found) > 2
        or len(set(found)) != len(found)
        or len({r.name for r in found}) != len(found)
    ):
        raise StoreError("Protected inventory record set invalid")
    return tuple(found)


def protected_evidence(
    transport: Boto3S3Transport, binding: StoreBinding, prefix: str, deadline: float
) -> ProtectedEvidence | None:
    validate_run_prefix(prefix)
    if time.monotonic() >= deadline:
        raise StoreError("Protected inventory deadline exceeded")
    current = transport.get(binding, binding.prefix + "maintenance.json")
    if current is not None and current.ledger.run.run_prefix == prefix:
        claim = current
    else:
        archive = transport.get_archive(binding, binding.prefix + f"runs/{prefix}/completed.json")
        if archive is None:
            return None
        claim = StoredLedger(archive.receipt.ledger, archive.receipt.claim_version)
    run, ledger = claim.ledger.run, claim.ledger
    state = transport.get_blob(binding, binding.prefix + f"runs/{prefix}/terraform.tfstate")
    records = () if state is None else state_identities(state.data, prefix, run.zone_id)
    metadata: tuple[RecordIdentity, ...] = ()
    for receipt in reversed(ledger.receipts):
        if (
            receipt.phase in {"create", "update"}
            and receipt.outcome == "succeeded"
            and receipt.resulting_state_generation
        ):
            key = (
                binding.prefix
                + f"runs/{prefix}/checkpoints/"
                + hashlib.sha256(receipt.resulting_state_generation.encode()).hexdigest()
                + ".tfstate"
            )
            checkpoint = transport.get_blob(binding, key)
            if checkpoint is not None:
                metadata = state_identities(checkpoint.data, prefix, run.zone_id)
            break
    status: Literal["unknown", "active", "terminated_known"] = "unknown"
    if ledger.receipts and all(r.outcome in {"failed", "succeeded"} for r in ledger.receipts):
        try:
            terminal_evidence(prefix, run.revision)
            status = "terminated_known"
        except StoreError:
            pass
    # Fresh reread detects evidence drift without claiming a report acquired ownership.
    if current is not None and current.ledger.run.run_prefix == prefix:
        fresh = transport.get(binding, binding.prefix + "maintenance.json")
        if fresh != current:
            raise StoreError("Protected inventory claim changed")
    if time.monotonic() >= deadline:
        raise StoreError("Protected inventory deadline exceeded")
    return ProtectedEvidence(
        run,
        claim,
        claim.version,
        ledger.generation,
        None if state is None else state.version,
        ledger.state_generation,
        records,
        metadata,
        status,
        True,
        len(records) == 2,
    )


def ledger_observations(
    transport: Boto3S3Transport, binding: StoreBinding, prefix: str, revision: str
) -> tuple[LedgerVersionObservation, ...]:
    validate_run_prefix(prefix)
    if re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise StoreError("Invalid measurement revision")
    key = binding.prefix + "maintenance.json"
    transport._gate(binding, key)
    deadline = time.monotonic() + 90
    selected: list[LedgerVersionObservation] = []
    seen, markers = set(), set()
    params: dict = {"Prefix": key, "MaxKeys": 128}
    for _ in range(2):
        response = transport._call("list_object_versions", **params)
        versions = response.get("Versions", [])
        if (
            type(response.get("IsTruncated")) is not bool
            or not isinstance(versions, list)
            or len(versions) > 128
        ):
            raise StoreError("Protected version index invalid")
        for version in versions:
            if (
                time.monotonic() >= deadline
                or not isinstance(version, dict)
                or version.get("Key") != key
                or type(version.get("LastModified")) is not datetime
            ):
                raise StoreError("Protected version index invalid or expired")
            token = _token(version.get("VersionId"), version.get("ETag"))
            if token in seen:
                raise StoreError("Protected version index repeated")
            seen.add(token)
            blob = transport.get_blob(binding, key, version=token)
            if blob is None:
                raise StoreError("Protected historical version missing")
            ledger = decode_ledger(blob.data)
            if ledger.run.run_prefix == prefix and ledger.run.revision == revision:
                selected.append(LedgerVersionObservation(blob.data, token, version["LastModified"]))
        if not response["IsTruncated"]:
            if not selected:
                raise StoreError("Selected run version history missing")
            return tuple(selected)
        marker = (response.get("NextKeyMarker"), response.get("NextVersionIdMarker"))
        if (
            marker[0] != key
            or not isinstance(marker[1], str)
            or not 1 <= len(marker[1]) <= 1024
            or marker in markers
        ):
            raise StoreError("Protected version continuation invalid")
        markers.add(marker)
        params.update(KeyMarker=marker[0], VersionIdMarker=marker[1])
    raise StoreError("Protected version history exceeds read budget")
