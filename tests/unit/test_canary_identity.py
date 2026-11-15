"""Offline namespace, resource boundary and Terraform fixture contracts."""

import sys
from pathlib import Path

import hcl2
import pytest
from hcl2.utils import SerializationOptions

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/main"))

import canary_identity as identity

PREFIX = "gha-1794700000-123456789-1"
ZONE_ID = "a" * 32
FIXTURE = ROOT / "terraform/cloudflare-canary"
HCL_OPTIONS = SerializationOptions(
    with_comments=False, explicit_blocks=False, strip_string_quotes=True
)


def candidate(**changes):
    values = dict(
        run_prefix=PREFIX,
        name=identity.record_name(PREFIX, "txt"),
        zone_name="solomonhd.ai",
        zone_id=ZONE_ID,
        expected_zone_id=ZONE_ID,
        record_type="TXT",
        proxied=False,
        resource_type="cloudflare_dns_record",
    )
    values.update(changes)
    return values


def test_build_exact_names():
    assert identity.build_run_prefix(1794700000, "123456789", 1) == PREFIX
    for label, kind in (("txt", "TXT"), ("cname", "CNAME")):
        name = f"{PREFIX}.{label}.ci.solomonhd.ai"
        assert identity.record_name(PREFIX, label) == name
        identity.validate_canary_record(**candidate(name=name, record_type=kind))


@pytest.mark.parametrize(
    "value", [0, -1, True, False, 1.0, None, "", "01", "1.0", "１", "1\n", " 1", "1-2"]
)
@pytest.mark.parametrize("position", range(3))
def test_reject_noncanonical_identifiers(value, position):
    parts = [1794700000, 123456789, 1]
    parts[position] = value
    with pytest.raises(ValueError):
        identity.build_run_prefix(*parts)


def test_label_boundary_is_rejected_not_truncated():
    prefix = identity.build_run_prefix("1" * 55, 1, 1)
    assert len(prefix) == 63
    assert identity.record_name(prefix, "cname").split(".")[0] == prefix
    with pytest.raises(ValueError):
        identity.build_run_prefix("1" * 56, 1, 1)


@pytest.mark.parametrize(
    "prefix",
    ["gha-1-2", "gha-1-2-3-4", "GHA-1-2-3", "gha-01-2-3", "gha-1-2-3\n", "gha-1-2-3.evil", None],
)
def test_prefix_validation(prefix):
    with pytest.raises(ValueError):
        identity.validate_run_prefix(prefix)


@pytest.mark.parametrize("label", ["a", "TXT", "", "*", "txt.evil", "x" * 64, None, []])
def test_record_labels_are_fixed(label):
    with pytest.raises(ValueError):
        identity.record_name(PREFIX, label)


@pytest.mark.parametrize(
    "name",
    [
        f"{PREFIX}.txt.ci.solomonhd.ai.evil",
        f"{PREFIX}.txt.evilci.solomonhd.ai",
        f"{PREFIX}.txt.ci.solomonhd.ai.",
        f"{PREFIX}.TXT.ci.solomonhd.ai",
        f"{PREFIX}.extra.txt.ci.solomonhd.ai",
        "gha-1794700000-123456789-2.txt.ci.solomonhd.ai",
        f"{PREFIX}.txt.ci.sghd.io",
        f"{PREFIX}.txt.solomonhd.ai",
        None,
    ],
)
def test_exact_name_required_for_apply_and_cleanup(name):
    with pytest.raises(ValueError):
        identity.validate_record_name(name, PREFIX)


@pytest.mark.parametrize(
    "changes",
    [
        {"zone_name": "sghd.io"},
        {"zone_name": "SolomonHD.ai"},
        {"zone_name": "solomonhd.ai."},
        {"zone_id": "b" * 32},
        {"expected_zone_id": ""},
        {"expected_zone_id": None},
        {"zone_id": "not-a-zone", "expected_zone_id": "not-a-zone"},
        {"record_type": "A"},
        {"record_type": "AAAA"},
        {"record_type": "MX"},
        {"record_type": "CNAME"},
        {"record_type": "txt"},
        {"proxied": True},
        {"proxied": None},
        {"proxied": 0},
        {"proxied": "false"},
        {"resource_type": "cloudflare_zero_trust_tunnel_cloudflared"},
        {"resource_type": "cloudflare_zero_trust_tunnel_cloudflared_config"},
        {"resource_type": "cloudflare_zone"},
        {"resource_type": "cloudflare_workers_route"},
        {"resource_type": "unifi_dns_record"},
    ],
)
def test_record_boundary_fails_closed(changes):
    with pytest.raises(ValueError):
        identity.validate_canary_record(**candidate(**changes))


def test_fixture_hcl_parses_and_has_only_reviewed_resource_and_data_kinds():
    blocks = [
        hcl2.loads(path.read_text(), serialization_options=HCL_OPTIONS)
        for path in sorted(FIXTURE.glob("*.tf"))
    ]
    resources = [item for block in blocks for item in block.get("resource", [])]
    data = [item for block in blocks for item in block.get("data", [])]
    assert len(resources) == len(data) == 1
    assert set(resources[0]) == {"cloudflare_dns_record"}
    assert set(data[0]) == {"cloudflare_zone"}
    assert not any(block.get("module") or block.get("import") for block in blocks)
    records = next(block["locals"][0]["records"] for block in blocks if "locals" in block)
    assert set(records) == {"txt", "cname"}
    assert {key: value["type"] for key, value in records.items()} == identity.RECORD_TYPES
    resource = resources[0]["cloudflare_dns_record"]["canary"]
    assert resource["for_each"] == "${local.records}"
    assert resource["proxied"] is False
    assert resource["zone_id"] == "${var.zone_id}"


def test_fixture_names_types_zone_and_no_credential_or_backend_configuration():
    source = (FIXTURE / "main.tf").read_text()
    assert 'namespace = "ci.solomonhd.ai"' in source
    assert 'name    = "${var.run_prefix}.${each.key}.${local.namespace}"' in source
    assert "content = var.cname_target" in source
    assert 'type    = "TXT"' in source and 'type    = "CNAME"' in source
    assert "proxied = false" in source
    assert 'data.cloudflare_zone.sandbox.name == "solomonhd.ai"' in source
    assert "precondition {" in source
    variables = (FIXTURE / "variables.tf").read_text()
    assert "length(var.run_prefix) <= 63" in variables
    assert "^gha-[1-9][0-9]*-[1-9][0-9]*-[1-9][0-9]*$" in variables
    versions = hcl2.loads((FIXTURE / "versions.tf").read_text(), serialization_options=HCL_OPTIONS)
    assert versions["provider"] == [{"cloudflare": {}}]
    assert versions["terraform"][0]["backend"] == [{"s3": {}}]
    assert '"example.com", "example.org"' in variables
