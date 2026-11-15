"""Split-DNS intent is explicit, exact-origin scoped, and never DNS evidence."""

import subprocess
from unittest.mock import patch

import pytest
import test_generator_output as transport
from test_dns_loop_generation import MAC, FailureAwareContainer, dns_source  # noqa: F401

pytestmark = pytest.mark.generator


def generate(dns_source, **options):
    argv = [part for key, value in options.items() for part in ("-D", f"{key}={value}")]
    return transport.run_kcl(dns_source("split-dns") / "main.k", *argv)["cf_output"]


def services(output, mode):
    return (
        [output]
        if mode == "transform"
        else output if mode == "list" else output["tunnels"][MAC]["services"]
    )


@pytest.mark.parametrize("mode", ["explicit", "entities", "transform", "list", "fallback"])
def test_exact_split_dns_intent_is_supported_in_every_entry_point(dns_source, mode):
    output = generate(
        dns_source,
        allow=True,
        mode=mode,
        allowed_hostname="edge-server.sghd.io" if mode == "fallback" else "traefik-mid.sghd.io",
    )
    selected = services(output, mode)
    assert selected[0 if mode == "transform" else 1]["local_service_url"] == (
        "https://edge-server.sghd.io:443"
        if mode == "fallback"
        else (
            "https://traefik-mid.sghd.io:443/path?next=internal.lan#fragment"
            if mode == "explicit"
            else "https://traefik-mid.sghd.io:443"
        )
    )
    if mode != "transform":
        assert [s["public_hostname"] for s in selected] == [
            "safe.sghd.io",
            "first.sghd.io",
            "second.sghd.io",
        ]
    if mode not in {"transform", "list"}:
        assert set(output) == {"account_id", "zone_name", "tunnels"}
        assert output["tunnels"][MAC]["tunnel_name"] == "edge-server"
    assert all("split_dns_origins" not in service for service in selected)
    if mode == "explicit":
        assert selected[1]["path_prefix"] == "/first"
        assert selected[1]["no_tls_verify"] is True
        assert selected[2]["path_prefix"] == "/second"
        assert selected[2]["no_tls_verify"] is False


@pytest.mark.parametrize("mode", ["explicit", "entities", "transform", "list", "fallback"])
def test_default_policy_still_rejects_same_zone_in_every_entry_point(dns_source, mode):
    with pytest.raises(subprocess.CalledProcessError) as error:
        generate(dns_source, mode=mode)
    assert "DNS loop risk" in error.value.stderr
    assert "split_dns_origins" in error.value.stderr
    assert not error.value.stdout.strip()


@pytest.mark.parametrize("mode", ["explicit", "entities", "transform", "list"])
@pytest.mark.parametrize(
    "hostname,allowed_hostname",
    [
        ("TRAEFIK-MID.SGHD.IO", "traefik-mid.sghd.io"),
        ("traefik-mid.sghd.io.", "TRAEFIK-MID.SGHD.IO."),
        ("Traefik-Mid.sghd.io.", "traefik-mid.SGHD.IO"),
    ],
)
def test_hostname_normalization_only_affects_matching_not_emitted_values(
    dns_source, mode, hostname, allowed_hostname
):
    selected = services(
        generate(
            dns_source,
            allow=True,
            mode=mode,
            hostname=hostname,
            allowed_hostname=allowed_hostname,
            zone="SGHD.IO.",
        ),
        mode,
    )
    assert selected[0 if mode == "transform" else 1]["local_service_url"].startswith(
        f"https://{hostname}:443"
    )


@pytest.mark.parametrize(
    "url,protocol,port",
    [
        ("HTTPS://TRAEFIK-MID.SGHD.IO./path?next=https://other.test#fragment", "https", 443),
        ("https://traefik-mid.sghd.io:0443/path", "https", 443),
        ("http://traefik-mid.sghd.io/path", "http", 80),
        ("tcp://traefik-mid.sghd.io:22", "tcp", 22),
    ],
)
def test_scheme_and_effective_port_matching(dns_source, url, protocol, port):
    output = generate(dns_source, allow=True, url=url, allowed_protocol=protocol, allowed_port=port)
    assert output["tunnels"][MAC]["services"][1]["local_service_url"] == url


@pytest.mark.parametrize(
    "url",
    [
        "https://other.sghd.io:443",
        "https://child.traefik-mid.sghd.io:443",
        "https://eviltraefik-mid.sghd.io:443",
        "https://sghd.io:443",
        "http://traefik-mid.sghd.io:443",
        "https://traefik-mid.sghd.io:8443",
        "tcp://traefik-mid.sghd.io",
        "https://user@traefik-mid.sghd.io:443",
        "https://traefik-mid.sghd.io:",
        "https://traefik-mid.sghd.io:443:1",
        "https://traefik-mid.sghd.io:not-a-port",
    ],
)
def test_approval_does_not_extend_to_other_origins_or_ambiguous_authorities(dns_source, url):
    with pytest.raises(subprocess.CalledProcessError) as error:
        generate(dns_source, allow=True, url=url)
    assert "DNS loop risk" in error.value.stderr
    assert not error.value.stdout.strip()


@pytest.mark.parametrize(
    "hostname", ["notsghd.io", "sghd.io.internal.lan", "traefik-mid.sghd.io.evil.test"]
)
def test_dns_label_boundaries_do_not_reject_unrelated_zones(dns_source, hostname):
    output = generate(dns_source, hostname=hostname)
    assert output["tunnels"][MAC]["services"][1]["local_service_url"].startswith(
        f"https://{hostname}:443"
    )


@pytest.mark.parametrize(
    "hostname",
    [
        "",
        "*.sghd.io",
        "https://traefik-mid.sghd.io",
        "traefik-mid.sghd.io:443",
        "traefik-mid.sghd.io/path",
        ".sghd.io",
        "a..sghd.io",
        "sghd.io..",
        "10.0.0.0/8",
        "a*b.sghd.io",
        "traefik-mid.sghd.io?all=true",
    ],
)
@pytest.mark.parametrize("mode", ["explicit", "entities", "transform", "list", "fallback"])
def test_exception_declarations_require_concrete_dns_names(dns_source, hostname, mode):
    with pytest.raises(subprocess.CalledProcessError) as error:
        generate(dns_source, allow=True, allowed_hostname=hostname, mode=mode)
    assert "split-DNS hostname" in error.value.stderr
    assert not error.value.stdout.strip()


@pytest.mark.parametrize("mode", ["explicit", "entities", "transform", "list", "fallback"])
@pytest.mark.parametrize(
    "hostname",
    ["192.168.100.100", "192.168.100.100.", "2001:db8::1", "::ffff:192.168.100.100"],
)
def test_ip_declarations_fail_even_when_the_origin_does_not_need_an_exception(
    dns_source, mode, hostname
):
    with pytest.raises(subprocess.CalledProcessError) as error:
        generate(
            dns_source,
            allow=True,
            mode=mode,
            hostname="safe.internal.lan",
            allowed_hostname=hostname,
        )
    assert "split-DNS hostname" in error.value.stderr
    assert not error.value.stdout.strip()


@pytest.mark.parametrize(
    "field,value",
    [
        ("allowed_port", 0),
        ("allowed_port", 65536),
        ("allowed_port", -1),
        ("allowed_port", "443x"),
        ("allowed_protocol", "ftp"),
        ("allowed_port", True),
        ("allowed_port", False),
        ("allowed_port", 1.5),
    ],
)
def test_invalid_declaration_types_and_bounds_fail_closed(dns_source, field, value):
    with pytest.raises(subprocess.CalledProcessError) as error:
        generate(dns_source, allow=True, **{field: value})
    assert not error.value.stdout.strip()


def test_allowing_zone_apex_never_grants_its_subdomains(dns_source):
    with pytest.raises(subprocess.CalledProcessError) as error:
        generate(dns_source, allow=True, allowed_hostname="sghd.io")
    assert "DNS loop risk" in error.value.stderr


def test_zone_apex_can_be_declared_only_as_its_exact_origin(dns_source):
    url = "https://sghd.io:443"
    output = generate(dns_source, allow=True, allowed_hostname="SGHD.IO.", url=url)
    assert output["tunnels"][MAC]["services"][1]["local_service_url"] == url


@pytest.mark.parametrize("declaration", ["True", '"*"', '["https://traefik-mid.sghd.io:443"]'])
def test_root_allowlist_cannot_be_a_global_bypass_or_untyped_url_list(dns_source, declaration):
    source = dns_source("split-dns")
    entry = source / "main.k"
    entry.write_text(
        entry.read_text().replace(
            "split_dns_origins = _origins", f"split_dns_origins = {declaration}"
        )
    )
    with pytest.raises(subprocess.CalledProcessError) as error:
        transport.run_kcl(entry)
    assert not error.value.stdout.strip()


@pytest.mark.parametrize("mode", ["explicit", "entities", "transform", "list"])
@pytest.mark.parametrize("valid", [False, True])
def test_structural_declarations_still_obey_schema_checks(dns_source, mode, valid):
    source = dns_source("split-dns")
    entry = source / "main.k"
    entry.write_text(entry.read_text().replace("cloudflare.SplitDNSOrigin {", "{"))
    options = ["-D", "allow=True", "-D", f"mode={mode}"]
    if valid:
        assert transport.run_kcl(entry, *options)["cf_output"]
    else:
        with pytest.raises(subprocess.CalledProcessError) as error:
            transport.run_kcl(
                entry,
                *options,
                "-D",
                "allowed_hostname=*.sghd.io",
                "-D",
                "hostname=safe.internal.lan",
            )
        assert not error.value.stdout.strip()


def test_approved_origin_does_not_bypass_validation_of_later_ingress(dns_source):
    with pytest.raises(subprocess.CalledProcessError) as error:
        generate(dns_source, allow=True, second_url="https://unapproved.sghd.io:443")
    assert "service 'second.sghd.io'" in error.value.stderr
    assert not error.value.stdout.strip()


@pytest.mark.parametrize("approved", [False, True])
async def test_public_generation_preserves_the_same_policy_and_export_boundary(
    dns_source, tmp_path, approved
):
    source = dns_source("split-dns")
    if approved:
        entry = source / "main.k"
        entry.write_text(
            entry.read_text().replace(
                'option("allow", default=False)', 'option("allow", default=True)'
            )
        )
    container = FailureAwareContainer()
    with patch.object(transport, "LocalContainer", return_value=container):
        if not approved:
            with pytest.raises(transport.KCLGenerationError, match="KCL execution failed"):
                await transport.generate_consumer(source, "cloudflare", tmp_path)
            assert not list((tmp_path / "generated").iterdir())
            return
        output = await transport.generate_consumer(source, "cloudflare", tmp_path)
    transport.assert_cloudflare_contract(output)
    assert [s["public_hostname"] for s in output["tunnels"][MAC]["services"]] == [
        "safe.sghd.io",
        "first.sghd.io",
        "second.sghd.io",
    ]
    assert set(output) == {"zone_name", "account_id", "tunnels"}
