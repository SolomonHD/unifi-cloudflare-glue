"""Static contracts for the reviewed filipowm/unifi baseline."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UNIFI_MAIN = ROOT / "terraform/modules/unifi-dns/main.tf"
UNIFI_VERSIONS = ROOT / "terraform/modules/unifi-dns/versions.tf"
GLUE_VERSIONS = ROOT / "terraform/modules/glue/versions.tf"
FIXTURE = ROOT / "terraform/fixtures/unifi-provider-baseline"
DAGGER_MAIN = ROOT / "src/main/main.py"


def _hcl_block(source: str, kind: str, type_name: str, name: str) -> str:
    pattern = re.compile(
        rf'{kind}\s+"{re.escape(type_name)}"\s+"{re.escape(name)}"\s*\{{(.*?)\n\}}',
        re.DOTALL,
    )
    match = pattern.search(source)
    assert match is not None, f"missing {kind} {type_name}.{name}"
    return match.group(1)


def test_mac_values_are_normalized_before_provider_use() -> None:
    source = UNIFI_MAIN.read_text()

    assert 'join(":", regexall("[0-9a-fA-F]{2}", nic.mac_address))' in source
    assert 'replace(lower(nic.mac_address), "-", ":")' in source
    assert "mac_lookup_map = { for lookup in local.mac_lookups : lookup.key => lookup }" in source


def test_clients_are_adopted_and_retained_on_destroy() -> None:
    source = UNIFI_MAIN.read_text()
    resource = _hcl_block(source, "resource", "unifi_user", "device")

    assert "for_each = local.mac_lookup_map" in resource
    assert "mac                    = each.value.mac_normalized" in resource
    assert "allow_existing         = true" in resource
    assert "skip_forget_on_destroy = true" in resource


def test_client_read_explicitly_depends_on_registration() -> None:
    source = UNIFI_MAIN.read_text()
    lookup = _hcl_block(source, "data", "unifi_user", "device")

    assert "for_each = local.mac_lookup_map" in lookup
    assert "mac        = each.value.mac_normalized" in lookup
    assert "depends_on = [unifi_user.device]" in lookup


def test_dns_keys_remain_static_while_ip_uses_dependent_read() -> None:
    source = UNIFI_MAIN.read_text()

    assert "for device in local.effective_config.devices : device.friendly_hostname => {" in source
    assert 'ip       = data.unifi_user.device["${device.friendly_hostname}-0"].ip' in source
    assert "if contains(keys(local.devices_with_found_macs)" not in source


def test_all_unifi_constraints_select_reviewed_v1_1_baseline() -> None:
    for path in (UNIFI_VERSIONS, GLUE_VERSIONS, FIXTURE / "versions.tf"):
        source = path.read_text()
        assert 'source  = "filipowm/unifi"' in source
        assert 'version = "~> 1.1.0"' in source


def test_disposable_fixture_is_confined_to_safe_namespace() -> None:
    source = "\n".join(path.read_text() for path in sorted(FIXTURE.glob("*.tf")))

    assert 'sandbox_zone = "unifi-poc-${var.run_id}.solomonhd.ai"' in source
    assert 'cidrhost("10.255.0.0/16", index + 10)' in source
    assert '"10.255.255.254"' in source
    assert 'resource "unifi_dns_record" "a"' in source
    assert 'resource "unifi_dns_record" "cname"' in source
    assert 'endswith(each.value.name, ".${local.sandbox_zone}")' in source
    assert "sghd.io" not in source
    assert "mac_address" not in source
    assert "cloudflare" not in source.lower()


def test_disposable_fixture_defaults_to_representative_cardinality() -> None:
    variables = (FIXTURE / "variables.tf").read_text()

    assert 'variable "a_record_count"' in variables
    assert 'variable "cname_record_count"' in variables
    assert variables.count("default     = 64") == 2


def test_dagger_baseline_lifecycle_keeps_cleanup_mandatory() -> None:
    source = DAGGER_MAIN.read_text()

    assert "async def test_unifi_dns_baseline(" in source
    assert '.with_secret_variable("UNIFI_API_KEY", unifi_api_key)' in source
    assert '"plan",\n                    "-detailed-exitcode"' in source
    assert '"destroy",' in source
    assert "async def _unifi_dns_prefix_count(" in source
    assert "API absence verification found {remaining} records" in source
