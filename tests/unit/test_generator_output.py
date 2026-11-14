"""Real KCL transformations and the public Dagger consumer extraction boundary.

Standalone modules publish result; dedicated consumers publish unifi_output/cf_output.
Only Dagger transport is replaced: KCL runs locally, without credentials or an engine.
Missing KCL is a failure, never a skip.
"""

import copy
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/fixtures/generator-output"
sys.path.insert(0, str(ROOT / "src/main"))

from main import KCLGenerationError, UnifiCloudflareGlue  # noqa: E402

pytestmark = pytest.mark.generator
MAC_PATTERN = r"[0-9a-f]{2}(?::[0-9a-f]{2}){5}"


def run_kcl(path: Path, *options: str) -> dict:
    completed = subprocess.run(
        ["kcl", "run", str(path), *options],
        cwd=path.parent,
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    return yaml.safe_load(completed.stdout)


def assert_unifi_contract(output: dict) -> None:
    """Fields consumed by terraform/modules/unifi-dns/main.tf."""
    assert isinstance(output, dict), "unifi_output must be an object"
    assert isinstance(output["default_domain"], str)
    assert isinstance(output["site"], str)
    assert isinstance(output["devices"], list), "devices must be an array"
    for device in output["devices"]:
        assert isinstance(device["friendly_hostname"], str)
        assert isinstance(device["domain"], str)
        assert isinstance(device["service_cnames"], list)
        assert all(isinstance(name, str) for name in device["service_cnames"])
        assert isinstance(device["nics"], list)
        for nic in device["nics"]:
            assert re.fullmatch(MAC_PATTERN, nic["mac_address"])
            assert nic.get("nic_name") is None or isinstance(nic["nic_name"], str)
            assert isinstance(nic["service_cnames"], list)
            assert all(isinstance(name, str) for name in nic["service_cnames"])


def assert_cloudflare_contract(output: dict) -> None:
    """Object type declared by terraform/modules/cloudflare-tunnel/variables.tf."""
    assert isinstance(output, dict), "cf_output must be an object"
    assert isinstance(output["zone_name"], str)
    assert isinstance(output["account_id"], str)
    assert isinstance(output["tunnels"], dict), "tunnels must be an object"
    for mac, tunnel in output["tunnels"].items():
        assert re.fullmatch(MAC_PATTERN, mac)
        assert tunnel["mac_address"] == mac
        assert isinstance(tunnel["tunnel_name"], str)
        assert isinstance(tunnel["services"], list)
        for service in tunnel["services"]:
            assert isinstance(service["public_hostname"], str)
            assert isinstance(service["local_service_url"], str)
            assert isinstance(service.get("no_tls_verify", False), bool)


@pytest.fixture
def consumer_source(tmp_path: Path):
    def prepare(name: str) -> Path:
        shutil.copytree(ROOT / "schemas", tmp_path / "schemas", dirs_exist_ok=True)
        shutil.copytree(ROOT / "generators", tmp_path / "generators", dirs_exist_ok=True)
        shutil.copyfile(FIXTURES / "kcl.mod", tmp_path / "kcl.mod")
        shutil.copytree(FIXTURES / name, tmp_path, dirs_exist_ok=True)
        return tmp_path

    return prepare


class LocalFile:
    def __init__(self, path: Path):
        self.path = path

    async def contents(self):
        return self.path.read_text()


class LocalDirectory:
    def __init__(self, path: Path):
        self.path = path

    def file(self, name):
        return LocalFile(self.path / name)


class LocalContainer:
    """Transport double; executes real KCL and models only yq extraction/encoding."""

    def __init__(self):
        self.source = None
        self.files = {}
        self.commands = []
        self.output = ""

    def from_(self, image):
        self.image = image
        return self

    def with_directory(self, destination, source):
        assert destination == "/src"
        self.source = source.path
        return self

    def with_workdir(self, path):
        assert path == "/src"
        return self

    def with_new_file(self, path, contents):
        self.files[path] = contents
        return self

    def with_exec(self, command):
        self.commands.append(command)
        if command == ["kcl", "run", "main.k"]:
            completed = subprocess.run(
                command, cwd=self.source, capture_output=True, text=True, check=True, timeout=60
            )
            self.output = completed.stdout
        elif command[:2] == ["yq", "eval"]:
            data = yaml.safe_load(self.files[command[-1]])
            self.output = (
                json.dumps(data)
                if command[2] == "-o=json"
                else (
                    "null\n"
                    if data.get(command[2].removeprefix(".")) is None
                    else yaml.safe_dump(data[command[2].removeprefix(".")])
                )
            )
        else:
            # Bootstrap/dependency acquisition is outside this offline unit boundary.
            assert command[0] == "sh" or command == ["kcl", "mod", "update"]
            self.output = ""
        return self

    async def stdout(self):
        return self.output


async def generate_consumer(source: Path, provider: str, tmp_path: Path):
    container = LocalContainer()
    output_directory = tmp_path / "generated"
    output_directory.mkdir(exist_ok=True)

    class OutputDirectory(LocalDirectory):
        def with_new_file(self, name, contents):
            (self.path / name).write_text(contents)
            return self

    with (
        patch("main.dagger.dag.container", return_value=container),
        patch("main.dagger.dag.directory", return_value=OutputDirectory(output_directory)),
    ):
        method = getattr(UnifiCloudflareGlue(), f"generate_{provider}_config")
        result = await method(LocalDirectory(source), kcl_version="0.12.4")
    assert ["kcl", "run", "main.k"] in container.commands
    key = "unifi_output" if provider == "unifi" else "cf_output"
    assert ["yq", "eval", f".{key}", "/tmp/kcl-output.yaml"] in container.commands
    assert container.image == "kcllang/kcl:0.12.4"
    return json.loads(await result.contents())


@pytest.mark.parametrize("provider", ["unifi", "cloudflare"])
def test_standalone_result_matches_terraform_contract(provider):
    data = run_kcl(ROOT / "generators" / f"{provider}.k")
    assert "result" in data
    assert "unifi_output" not in data and "cf_output" not in data
    output = data["result"]
    if provider == "unifi":
        assert_unifi_contract(output)
        assert len(output["devices"]) == 3
        assert output["devices"][1]["nics"][1]["mac_address"] == "aa:bb:cc:dd:ee:03"
    else:
        assert_cloudflare_contract(output)
        assert len(output["tunnels"]) == 3
        assert output["tunnels"]["aa:bb:cc:dd:ee:02"]["services"][0]["no_tls_verify"]


@pytest.mark.parametrize("provider", ["unifi", "cloudflare"])
async def test_valid_consumer_main_uses_public_generation(consumer_source, tmp_path, provider):
    source = consumer_source("valid")
    output = await generate_consumer(source, provider, tmp_path)
    key = "unifi_output" if provider == "unifi" else "cf_output"
    assert output == run_kcl(source / "main.k")[key]
    (assert_unifi_contract if provider == "unifi" else assert_cloudflare_contract)(output)


@pytest.mark.parametrize("provider,key", [("unifi", "unifi_output"), ("cloudflare", "cf_output")])
async def test_missing_consumer_key_reports_actionable_error(
    consumer_source, tmp_path, provider, key
):
    source = consumer_source("missing-key")
    with pytest.raises(KCLGenerationError, match=f"main.k does not export '{key}'") as error:
        await generate_consumer(source, provider, tmp_path)
    assert "Hint:" in str(error.value)
    assert not list((tmp_path / "generated").iterdir())


@pytest.mark.parametrize("provider", ["unifi", "cloudflare"])
async def test_missing_main_reports_public_entrypoint_error(consumer_source, tmp_path, provider):
    source = consumer_source("valid")
    (source / "main.k").unlink()
    with pytest.raises(KCLGenerationError, match="Entry point file not found: main.k"):
        await generate_consumer(source, provider, tmp_path)


@pytest.mark.parametrize("provider", ["unifi", "cloudflare"])
async def test_malformed_consumer_structure_is_rejected(consumer_source, tmp_path, provider):
    with pytest.raises(KCLGenerationError) as error:
        await generate_consumer(consumer_source("malformed"), provider, tmp_path)
    assert str(error.value) == (
        "unifi_output.devices: expected array; found string"
        if provider == "unifi"
        else "cf_output.tunnels: expected object; found array"
    )
    assert not list((tmp_path / "generated").iterdir())


@pytest.fixture
def malformed_source(consumer_source):
    source = consumer_source("valid")
    outputs = run_kcl(source / "main.k")
    consumer_source("malformed")

    def prepare(provider, path, value, remove=False):
        payload = copy.deepcopy(outputs)
        key = "unifi_output" if provider == "unifi" else "cf_output"
        if not path:
            payload[key] = value
        else:
            target = payload[key]
            for part in path[:-1]:
                target = target[part]
            if remove:
                del target[path[-1]]
            else:
                target[path[-1]] = value
        (source / "payload.k").write_text(
            f"unifi_output = {payload['unifi_output']!r}\ncf_output = {payload['cf_output']!r}\n"
        )
        return source

    return prepare


UNIFI_FIELDS = [
    (("devices",), "devices", "array"),
    (("default_domain",), "default_domain", "string"),
    (("site",), "site", "string"),
    (("devices", 0), "devices[0]", "object"),
    (("devices", 0, "friendly_hostname"), "devices[0].friendly_hostname", "string"),
    (("devices", 0, "domain"), "devices[0].domain", "string or null"),
    (("devices", 0, "nics"), "devices[0].nics", "array"),
    (("devices", 0, "service_cnames"), "devices[0].service_cnames", "array or null"),
    (("devices", 0, "service_cnames", 0), "devices[0].service_cnames[0]", "string"),
    (("devices", 0, "nics", 0), "devices[0].nics[0]", "object"),
    (("devices", 0, "nics", 0, "mac_address"), "devices[0].nics[0].mac_address", "string"),
    (
        ("devices", 0, "nics", 0, "service_cnames"),
        "devices[0].nics[0].service_cnames",
        "array or null",
    ),
    (
        ("devices", 0, "nics", 0, "service_cnames", 0),
        "devices[0].nics[0].service_cnames[0]",
        "string",
    ),
    (("devices", 0, "nics", 0, "nic_name"), "devices[0].nics[0].nic_name", "string or null"),
]
TUNNEL = ("tunnels", "aa:bb:cc:dd:ee:ff")
CF_FIELDS = [
    (("zone_name",), "zone_name", "string"),
    (("account_id",), "account_id", "string"),
    (("tunnels",), "tunnels", "object"),
    (TUNNEL, "tunnels[0]", "object"),
    ((*TUNNEL, "tunnel_name"), "tunnels[0].tunnel_name", "string"),
    ((*TUNNEL, "mac_address"), "tunnels[0].mac_address", "string"),
    ((*TUNNEL, "services"), "tunnels[0].services", "array"),
    ((*TUNNEL, "services", 0), "tunnels[0].services[0]", "object"),
    (
        (*TUNNEL, "services", 0, "public_hostname"),
        "tunnels[0].services[0].public_hostname",
        "string",
    ),
    (
        (*TUNNEL, "services", 0, "local_service_url"),
        "tunnels[0].services[0].local_service_url",
        "string",
    ),
    (
        (*TUNNEL, "services", 0, "no_tls_verify"),
        "tunnels[0].services[0].no_tls_verify",
        "boolean or null",
    ),
]


@pytest.mark.parametrize(
    "provider,root,case",
    [
        *[("unifi", "unifi_output", case) for case in UNIFI_FIELDS],
        *[("cloudflare", "cf_output", case) for case in CF_FIELDS],
    ],
)
async def test_nested_wrong_types_have_safe_field_paths(
    malformed_source, tmp_path, provider, root, case
):
    path, field, expected = case
    with pytest.raises(KCLGenerationError) as error:
        await generate_consumer(malformed_source(provider, path, 17), provider, tmp_path)
    assert str(error.value) == f"{root}.{field}: expected {expected}; found number"
    assert not list((tmp_path / "generated").iterdir())


@pytest.mark.parametrize(
    "provider,root,case",
    [
        *[
            ("unifi", "unifi_output", case)
            for case in UNIFI_FIELDS
            if isinstance(case[0][-1], str) and case[0][-1] != "nic_name"
        ],
        *[
            ("cloudflare", "cf_output", case)
            for case in CF_FIELDS
            if isinstance(case[0][-1], str)
            and case[0][-1] not in ("aa:bb:cc:dd:ee:ff", "no_tls_verify")
        ],
    ],
)
async def test_missing_nested_fields_are_rejected(malformed_source, tmp_path, provider, root, case):
    path, field, expected = case
    with pytest.raises(KCLGenerationError) as error:
        await generate_consumer(
            malformed_source(provider, path, None, remove=True), provider, tmp_path
        )
    assert str(error.value) == f"{root}.{field}: expected {expected}; found missing"


@pytest.mark.parametrize(
    "provider,root,case",
    [
        *[("unifi", "unifi_output", case) for case in UNIFI_FIELDS if "or null" not in case[2]],
        *[("cloudflare", "cf_output", case) for case in CF_FIELDS if "or null" not in case[2]],
    ],
)
async def test_required_nested_fields_reject_null(malformed_source, tmp_path, provider, root, case):
    path, field, expected = case
    with pytest.raises(KCLGenerationError) as error:
        await generate_consumer(malformed_source(provider, path, None), provider, tmp_path)
    assert str(error.value) == f"{root}.{field}: expected {expected}; found null"


@pytest.mark.parametrize(
    "provider,path,field,expected",
    [
        (
            "unifi",
            ("devices", 0, "nics", 0, "nic_name"),
            "unifi_output.devices[0].nics[0].nic_name",
            "string or null",
        ),
        (
            "cloudflare",
            (*TUNNEL, "services", 0, "no_tls_verify"),
            "cf_output.tunnels[0].services[0].no_tls_verify",
            "boolean or null",
        ),
    ],
)
async def test_optional_wrong_types_do_not_echo_config(
    malformed_source, tmp_path, provider, path, field, expected
):
    value = {"SENTINEL_CONFIG_KEY": "SENTINEL_CONFIG_VALUE"}
    with pytest.raises(KCLGenerationError) as error:
        await generate_consumer(malformed_source(provider, path, value), provider, tmp_path)
    assert str(error.value) == f"{field}: expected {expected}; found object"
    assert "SENTINEL" not in str(error.value)


@pytest.mark.parametrize("provider,root", [("unifi", "unifi_output"), ("cloudflare", "cf_output")])
@pytest.mark.parametrize(
    "value,found",
    [("SENTINEL_CONFIG_VALUE", "string"), ([], "array"), (True, "boolean"), (17, "number")],
)
async def test_top_level_scalars_are_rejected(
    malformed_source, tmp_path, provider, root, value, found
):
    with pytest.raises(KCLGenerationError) as error:
        await generate_consumer(malformed_source(provider, (), value), provider, tmp_path)
    assert str(error.value) == f"{root}: expected object; found {found}"
    assert "SENTINEL" not in str(error.value)


@pytest.mark.parametrize("provider,key", [("unifi", "unifi_output"), ("cloudflare", "cf_output")])
async def test_null_consumer_export_is_rejected(malformed_source, tmp_path, provider, key):
    with pytest.raises(KCLGenerationError, match=f"main.k does not export '{key}'"):
        await generate_consumer(malformed_source(provider, (), None), provider, tmp_path)


@pytest.mark.parametrize("provider,root", [("unifi", "unifi_output"), ("cloudflare", "cf_output")])
async def test_invalid_json_diagnostic_does_not_echo_payload(
    consumer_source, tmp_path, monkeypatch, provider, root
):
    original_exec = LocalContainer.with_exec

    def corrupt_json(container, command):
        result = original_exec(container, command)
        if command[:3] == ["yq", "eval", "-o=json"]:
            container.output = '{"SENTINEL_JSON": "SENTINEL_VALUE"'
        return result

    monkeypatch.setattr(LocalContainer, "with_exec", corrupt_json)
    with pytest.raises(KCLGenerationError) as error:
        await generate_consumer(consumer_source("valid"), provider, tmp_path)
    assert f"{root}: expected valid JSON" in str(error.value)
    assert "line 1, column" in str(error.value)
    assert "SENTINEL" not in str(error.value)
    assert not list((tmp_path / "generated").iterdir())


@pytest.mark.parametrize(
    "provider,path,field",
    [
        (
            "unifi",
            ("devices", 0, "nics", 0, "mac_address"),
            "unifi_output.devices[0].nics[0].mac_address",
        ),
        ("cloudflare", (*TUNNEL, "mac_address"), "cf_output.tunnels[0].mac_address"),
    ],
)
@pytest.mark.parametrize(
    "value", ["AA:BB:CC:DD:EE:FF", "aabbccddeeff", "aa-bb-cc-dd-ee-ff", "SENTINEL_CONFIG_VALUE"]
)
async def test_non_normalized_macs_are_rejected_without_values(
    malformed_source, tmp_path, provider, path, field, value
):
    with pytest.raises(KCLGenerationError) as error:
        await generate_consumer(malformed_source(provider, path, value), provider, tmp_path)
    assert str(error.value) == f"{field}: expected normalized MAC string; found string"
    assert value not in str(error.value)


async def test_tunnel_keys_are_not_disclosed(malformed_source, tmp_path):
    with pytest.raises(KCLGenerationError) as error:
        await generate_consumer(
            malformed_source("cloudflare", ("tunnels",), {"SENTINEL_SECRET_KEY": {}}),
            "cloudflare",
            tmp_path,
        )
    assert (
        str(error.value) == "cf_output.tunnels[0].key: expected normalized MAC string; found string"
    )


@pytest.mark.parametrize(
    "provider,path,value",
    [
        ("unifi", ("devices",), []),
        ("unifi", ("devices", 0, "nics"), []),
        ("unifi", ("devices", 0, "domain"), None),
        ("unifi", ("devices", 0, "service_cnames"), None),
        ("unifi", ("devices", 0, "nics", 0, "service_cnames"), None),
        ("unifi", ("devices", 0, "nics", 0, "nic_name"), None),
        ("cloudflare", ("tunnels",), {}),
        ("cloudflare", (*TUNNEL, "services"), []),
        ("cloudflare", (*TUNNEL, "services", 0, "no_tls_verify"), None),
        ("cloudflare", (*TUNNEL, "services", 0, "no_tls_verify"), False),
    ],
)
async def test_valid_empty_and_nullable_fields_are_preserved(
    malformed_source, tmp_path, provider, path, value
):
    output = await generate_consumer(malformed_source(provider, path, value), provider, tmp_path)
    for part in path:
        output = output[part]
    assert output == value


@pytest.mark.parametrize(
    "provider,path",
    [
        ("unifi", ("devices", 0, "nics", 0, "nic_name")),
        ("cloudflare", (*TUNNEL, "services", 0, "no_tls_verify")),
    ],
)
async def test_optional_fields_can_be_omitted(malformed_source, tmp_path, provider, path):
    output = await generate_consumer(
        malformed_source(provider, path, None, remove=True), provider, tmp_path
    )
    for part in path[:-1]:
        output = output[part]
    assert path[-1] not in output


@pytest.mark.parametrize(
    "mac",
    [
        "AA:BB:CC:DD:EE:FF",
        "aa-bb-cc-dd-ee-ff",
        "AABBCCDDEEFF",
        "Aa:Bb:Cc:Dd:Ee:Ff",
    ],
)
def test_generators_normalize_actual_mac_inputs(consumer_source, mac):
    output = run_kcl(consumer_source("valid") / "main.k", "-D", f"mac={mac}")
    assert output["unifi_output"]["devices"][0]["nics"][0]["mac_address"] == "aa:bb:cc:dd:ee:ff"
    assert set(output["cf_output"]["tunnels"]) == {"aa:bb:cc:dd:ee:ff"}
    assert output["cf_output"]["tunnels"]["aa:bb:cc:dd:ee:ff"]["mac_address"] == "aa:bb:cc:dd:ee:ff"


def test_service_distribution_and_hostname_resolution(consumer_source):
    output = run_kcl(consumer_source("valid") / "main.k")
    device = output["unifi_output"]["devices"][0]
    assert device["service_cnames"] == [
        "explicit.internal.lan",
        "both.internal.lan",
        "local.internal.lan",
    ]
    tunnel = output["cf_output"]["tunnels"]["aa:bb:cc:dd:ee:ff"]
    assert tunnel["services"] == [
        {
            "public_hostname": "both.example.com",
            "local_service_url": "https://both.internal.lan:443",
            "no_tls_verify": True,
        },
        {
            "public_hostname": "remote.example.com",
            "local_service_url": "http://server.internal.lan:8080",
            "no_tls_verify": True,
        },
    ]
    assert output["origin_checks"] == [True, True]


def test_multiple_nics_preserve_aliases_and_one_tunnel(consumer_source):
    output = run_kcl(consumer_source("valid") / "main.k")
    assert output["unifi_output"]["devices"][0]["nics"] == [
        {
            "mac_address": "aa:bb:cc:dd:ee:ff",
            "nic_name": "eth0",
            "service_cnames": ["wired.internal.lan"],
        },
        {"mac_address": "11:22:33:44:55:66", "service_cnames": []},
    ]
    assert len(output["cf_output"]["tunnels"]) == 1
    assert output["cf_output"]["tunnels"]["aa:bb:cc:dd:ee:ff"]["tunnel_name"] == "server"


def test_empty_devices_and_services_are_generated(consumer_source):
    source = consumer_source("valid")
    empty = run_kcl(source / "main.k", "-D", "empty=True")
    assert empty["unifi_output"]["devices"] == []
    assert empty["cf_output"]["tunnels"] == {}
    no_services = run_kcl(source / "main.k", "-D", "no_services=True")
    assert no_services["unifi_output"]["devices"][0]["service_cnames"] == ["explicit.internal.lan"]
    assert no_services["cf_output"]["tunnels"]["aa:bb:cc:dd:ee:ff"]["services"] == []


def test_empty_nics_follow_each_supported_schema_boundary(consumer_source):
    source = consumer_source("empty-nics")
    assert run_kcl(source / "main.k")["cf_output"]["tunnels"] == {}
    with pytest.raises(subprocess.CalledProcessError) as error:
        run_kcl(source / "main.k", "-D", "unifi=True")
    assert "Each device must have at least one endpoint" in error.value.stderr


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://example.com:443", False),
        ("http://app.example.com:80/path", False),
        ("https://app.internal.lan:443", True),
        ("http://notexample.com:80", True),
        ("https://example.com.internal.lan:443", True),
    ],
)
def test_actual_dns_loop_predicate(consumer_source, url, expected):
    # Existing detection API; generation does not itself enforce this predicate.
    output = run_kcl(consumer_source("dns-loop") / "main.k", "-D", f"url={url}")
    assert output["allowed"] is expected
