"""Generation rejects public-zone origins before publishing usable output.

Reuse the existing real-KCL transport, translating only its subprocess failure
to the SDK error that a failed Dagger exec reports. No engine or credentials.
"""

import shutil
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import dagger
import pytest
import test_generator_output as transport
from dagger._exceptions import QueryErrorValue

pytestmark = pytest.mark.generator
FIXTURES = transport.FIXTURES / "dns-enforcement"
MAC = "aa:bb:cc:dd:ee:ff"


@pytest.fixture
def dns_source(tmp_path: Path):
    def prepare(name: str) -> Path:
        source = tmp_path / "source"
        source.mkdir(exist_ok=True)
        for directory in ("schemas", "generators"):
            shutil.copytree(transport.ROOT / directory, source / directory, dirs_exist_ok=True)
        shutil.copyfile(transport.FIXTURES / "kcl.mod", source / "kcl.mod")
        shutil.copyfile(FIXTURES / name / "main.k", source / "main.k")
        return source

    return prepare


class FailureAwareContainer(transport.LocalContainer):
    def with_exec(self, command):
        try:
            return super().with_exec(command)
        except subprocess.CalledProcessError as error:
            raise dagger.ExecError(
                [
                    QueryErrorValue(
                        "Local KCL execution failed",
                        extensions={
                            "_type": "EXEC_ERROR",
                            "cmd": command,
                            "exitCode": error.returncode,
                            "stdout": error.stdout,
                            "stderr": error.stderr,
                        },
                    )
                ],
                Mock(document=None),
            ) from error


@pytest.mark.parametrize("fixture", ["explicit", "entities", "fallback"])
async def test_public_generation_rejects_dns_loop_before_output(dns_source, tmp_path, fixture):
    container = FailureAwareContainer()
    with patch.object(transport, "LocalContainer", return_value=container):
        with pytest.raises(transport.KCLGenerationError) as error:
            await transport.generate_consumer(dns_source(fixture), "cloudflare", tmp_path)
    assert_dns_diagnostic(str(error.value), fixture)
    assert not list((tmp_path / "generated").iterdir())
    assert not any(command[:2] == ["yq", "eval"] for command in container.commands)


@pytest.mark.parametrize("fixture", ["entities", "fallback"])
async def test_safe_entity_output_passes_public_shape_validation(dns_source, tmp_path, fixture):
    source = dns_source(fixture)
    entry = source / "main.k"
    option = "hostname" if fixture == "entities" else "domain"
    original = "app.example.com" if fixture == "entities" else "example.com"
    replacement = "app.internal.lan" if fixture == "entities" else "internal.lan"
    entry.write_text(
        entry.read_text().replace(
            f'option("{option}", default="{original}")',
            f'option("{option}", default="{replacement}")',
        )
    )
    output = await transport.generate_consumer(source, "cloudflare", tmp_path)
    transport.assert_cloudflare_contract(output)
    assert output["tunnels"][MAC]["mac_address"] == MAC


def assert_dns_diagnostic(message: str, fixture: str) -> None:
    assert "DNS loop" in message
    assert "tunnel 'edge-server'" in message
    service = "app.example.com" if fixture == "explicit" else "app"
    assert f"service '{service}'" in message
    assert "example.com" in message
    assert "internal hostname" in message or "internal_hostname" in message


@pytest.mark.parametrize("fixture", ["explicit", "entities", "helper"])
@pytest.mark.parametrize("zone", ["example.com", "EXAMPLE.COM."])
@pytest.mark.parametrize(
    "hostname", ["example.com", "app.example.com", "APP.Example.COM", "app.example.com."]
)
def test_direct_kcl_rejects_zone_origins(dns_source, fixture, zone, hostname):
    option = (
        f"url=HTTPS://{hostname}:443/path?next=internal.lan"
        if fixture == "explicit"
        else f"hostname={hostname}"
    )
    with pytest.raises(subprocess.CalledProcessError) as error:
        transport.run_kcl(dns_source(fixture) / "main.k", "-D", option, "-D", f"zone={zone}")
    assert_dns_diagnostic(error.value.stderr, fixture)
    assert not error.value.stdout.strip()


@pytest.mark.parametrize("fixture", ["fallback", "helper"])
@pytest.mark.parametrize("domain", ["example.com", "EXAMPLE.COM."])
def test_direct_kcl_rejects_unsafe_fallback(dns_source, fixture, domain):
    options = ["-D", f"domain={domain}"]
    if fixture == "helper":
        options.extend(["-D", "fallback=True", "-D", "list=True"])
    with pytest.raises(subprocess.CalledProcessError) as error:
        transport.run_kcl(dns_source(fixture) / "main.k", *options)
    assert_dns_diagnostic(error.value.stderr, fixture)
    assert "edge-server.example.com" in error.value.stderr
    assert not error.value.stdout.strip()


@pytest.mark.parametrize("fixture", ["explicit", "entities", "helper"])
@pytest.mark.parametrize(
    "hostname",
    ["notexample.com", "app.internal.lan", "example.com.internal.lan", "APP.Internal.LAN."],
)
def test_safe_origins_preserve_generated_values(dns_source, fixture, hostname):
    options = [
        "-D",
        f"url=https://{hostname}:443/path" if fixture == "explicit" else f"hostname={hostname}",
        "-D",
        "zone=EXAMPLE.COM.",
    ]
    output = transport.run_kcl(dns_source(fixture) / "main.k", *options)["cf_output"]
    if fixture == "helper":
        service = output
    else:
        assert output["account_id"] == "test-account"
        assert output["zone_name"] == "EXAMPLE.COM."
        tunnel = output["tunnels"][MAC]
        assert tunnel["tunnel_name"] == "edge-server"
        service = tunnel["services"][-1]
        if fixture == "explicit":
            assert len(tunnel["services"]) == 2
            assert tunnel["mac_address"] == MAC
            assert service["path_prefix"] == "/app"
    assert service["local_service_url"] == f"https://{hostname}:443" + (
        "/path" if fixture == "explicit" else ""
    )
    assert service["no_tls_verify"] is (fixture != "helper")


def test_unifi_only_service_is_not_a_tunnel_origin(dns_source):
    output = transport.run_kcl(dns_source("entities") / "main.k", "-D", "distribution=unifi_only")
    assert output["cf_output"]["tunnels"] == {}


def test_safe_fallback_is_preserved(dns_source):
    output = transport.run_kcl(dns_source("fallback") / "main.k", "-D", "domain=internal.lan")
    service = output["cf_output"]["tunnels"][MAC]["services"][0]
    assert service["local_service_url"] == "http://edge-server.internal.lan:8080"


@pytest.mark.parametrize(
    "url",
    [
        "https://notexample.com:443/example.com?next=app.example.com#example.com",
        "https://example.com@origin.internal.lan:443/path",
        "tcp://origin.internal.lan:22",
    ],
)
def test_safe_origin_checks_only_the_hostname(dns_source, url):
    output = transport.run_kcl(dns_source("explicit") / "main.k", "-D", f"url={url}")
    assert output["cf_output"]["tunnels"][MAC]["services"][1]["local_service_url"] == url


@pytest.mark.parametrize(
    "url",
    [
        "https://app.example.com/path://origin.internal.lan",
        "https://app.example.com/?next=https://origin.internal.lan",
    ],
)
def test_url_path_cannot_hide_a_public_zone_origin(dns_source, url):
    with pytest.raises(subprocess.CalledProcessError) as error:
        transport.run_kcl(dns_source("explicit") / "main.k", "-D", f"url={url}")
    assert_dns_diagnostic(error.value.stderr, "explicit")
