#!/usr/bin/env python3
"""Print only validated inventory metadata; fail if report-only selection failed."""

import json
import re
import sys

REASONS = {
    "unowned",
    "active",
    "unknown_writer",
    "invalid_evidence",
    "identity_mismatch",
    "stale_claim_generation",
    "missing_or_partial_state",
    "stale_state_generation",
    "record_identity_mismatch",
    "unknown_outcome",
    "completed_claim_conflict",
    "cleanup_failure_not_established",
    "requires_explicit_reconciliation",
    "invalid_timestamp",
    "future_timestamp",
    "evidence_read_failed",
}
ERRORS = {
    "inventory_limit_or_shape",
    "duplicate_record_identity",
    "inventory_read_failed",
    "evidence_read_failed",
    "selection_failed",
}


def checked(raw: bytes) -> dict:
    try:
        if len(raw) > 131072:
            raise ValueError()
        value = json.loads(raw)
        if (
            set(value)
            != {
                "operation",
                "report_only",
                "rows",
                "errors",
                "scanned",
                "excluded",
                "stale_threshold_seconds",
            }
            or value["operation"] != "janitor_inventory"
            or value["report_only"] is not True
        ):
            raise ValueError()
        if (
            any(
                type(value[k]) is not int or not 0 <= value[k] <= 200
                for k in ("scanned", "excluded")
            )
            or value["excluded"] > value["scanned"]
            or type(value["stale_threshold_seconds"]) is not int
            or not 2100 <= value["stale_threshold_seconds"] <= 172800
        ):
            raise ValueError()
        if (
            not isinstance(value["errors"], list)
            or len(value["errors"]) > 5
            or any(type(error) is not str or error not in ERRORS for error in value["errors"])
        ):
            raise ValueError()
        if not isinstance(value["rows"], list) or len(value["rows"]) > value["scanned"]:
            raise ValueError()
        for row in value["rows"]:
            if (
                set(row)
                != {"run_prefix", "name", "record_id", "record_type", "age_seconds", "reason"}
                or not isinstance(row["run_prefix"], str)
                or len(row["run_prefix"]) > 63
                or re.fullmatch(r"gha-[1-9][0-9]*-[1-9][0-9]*-[1-9][0-9]*", row["run_prefix"])
                is None
                or row["record_type"] not in {"TXT", "CNAME"}
                or row["name"]
                != f'{row["run_prefix"]}.{row["record_type"].lower()}.ci.solomonhd.ai'
                or not isinstance(row["record_id"], str)
                or re.fullmatch(r"[0-9a-f]{32}", row["record_id"]) is None
                or row["reason"] not in REASONS
            ):
                raise ValueError()
            if row["age_seconds"] is not None and (
                type(row["age_seconds"]) is not int or row["age_seconds"] < 0
            ):
                raise ValueError()
        return value
    except Exception:
        raise ValueError("Invalid report-only inventory metadata") from None


if __name__ == "__main__":
    try:
        report = checked(sys.stdin.buffer.read(131073))
        print(json.dumps(report, sort_keys=True))
        raise SystemExit(1 if report["errors"] else 0)
    except ValueError:
        print("Report-only inventory could not be validated", file=sys.stderr)
        raise SystemExit(1) from None
