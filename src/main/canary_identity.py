"""Offline identity checks, shared by canary preparation and exact-record cleanup.

These checks establish namespace membership, not deletion authorization, durable
ownership, writer termination, or fencing. Callers must establish those separately.
"""

import re

ZONE_NAME = "solomonhd.ai"
NAMESPACE = "ci.solomonhd.ai"
RECORD_TYPES = {"txt": "TXT", "cname": "CNAME"}
RESOURCE_TYPE = "cloudflare_dns_record"
_PREFIX = re.compile(r"gha-[1-9][0-9]*-[1-9][0-9]*-[1-9][0-9]*")
_ZONE_ID = re.compile(r"[0-9a-f]{32}")


def validate_run_prefix(prefix: str) -> str:
    """Reject noncanonical identities and overlong labels; never truncate them."""
    if not isinstance(prefix, str) or len(prefix) > 63 or _PREFIX.fullmatch(prefix) is None:
        raise ValueError("Invalid canary run prefix")
    return prefix


def build_run_prefix(unix: int | str, run_id: int | str, attempt: int | str) -> str:
    """Build gha-<unix>-<run-id>-<attempt> from positive decimal identifiers."""
    for value in (unix, run_id, attempt):
        if type(value) not in (int, str) or re.fullmatch(r"[1-9][0-9]*", str(value)) is None:
            raise ValueError("Canary identity requires positive decimal identifiers")
    return validate_run_prefix(f"gha-{unix}-{run_id}-{attempt}")


def record_name(run_prefix: str, record: str) -> str:
    """Return one of the two fixture names, without normalization or wildcards."""
    validate_run_prefix(run_prefix)
    if not isinstance(record, str) or record not in RECORD_TYPES:
        raise ValueError("Unsupported canary record label")
    name = f"{run_prefix}.{record}.{NAMESPACE}"
    if len(name) > 253 or any(len(label) > 63 for label in name.split(".")):
        raise ValueError("Canary name exceeds DNS limits")
    return name


def validate_record_name(name: str, run_prefix: str) -> str:
    """Require an exact intended name before either apply or cleanup."""
    if not isinstance(name, str) or name not in {
        record_name(run_prefix, record) for record in RECORD_TYPES
    }:
        raise ValueError("Record is outside the exact canary run namespace")
    return name


def validate_canary_record(
    *,
    run_prefix: str,
    name: str,
    zone_name: str,
    zone_id: str,
    expected_zone_id: str,
    record_type: str,
    proxied: bool,
    resource_type: str,
) -> None:
    """Fail closed on zone identity, resource kind, type/name pairing and proxying.

    expected_zone_id must come from the caller's trusted run metadata, not from
    the candidate record itself. No credentials or API operations are used here.
    """
    if (
        zone_name != ZONE_NAME
        or not isinstance(expected_zone_id, str)
        or _ZONE_ID.fullmatch(expected_zone_id) is None
        or zone_id != expected_zone_id
    ):
        raise ValueError("Canary zone identity does not match the sandbox")
    validate_record_name(name, run_prefix)
    label = name.split(".")[1]
    if resource_type != RESOURCE_TYPE or record_type != RECORD_TYPES[label] or proxied is not False:
        raise ValueError("Unsupported canary resource, record type or proxy setting")
