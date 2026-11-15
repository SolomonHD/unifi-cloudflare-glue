"""Synchronous native Terraform adapter, instantiated only inside Dagger runtime.

Subprocess output is private, including errors, state and plan JSON. A terminated
effect is checkpointed before reporting failure. A timeout is an unknown effect,
even after killing/reaping the process group, and must never trigger cleanup.
The caller owns encryption, durable checkpoint storage and writer fencing.
"""

import json
import math
import os
import re
import signal
import subprocess
import tempfile
import uuid
from collections.abc import Callable
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Protocol
from urllib.parse import urlsplit

import hcl2
from hcl2.utils import SerializationOptions

from .canary_dns import (
    CloudflareDNSClient,
    CloudflareDoHResolver,
    DNSValidationError,
    ExpectedRecord,
    PublicResolver,
    verify_public_dns,
)
from .canary_identity import RESOURCE_TYPE, ZONE_NAME, record_name, validate_canary_record
from .canary_lifecycle import CompletedFailure

PROVIDER = "registry.terraform.io/cloudflare/cloudflare"
ADDRESSES = {f'cloudflare_dns_record.canary["{label}"]': label for label in ("txt", "cname")}
DATA_ADDRESS = "data.cloudflare_zone.sandbox"
MAX_CAPTURE = 8 * 1024 * 1024
Revision = Literal["create", "update"]


class TerraformUnknown(RuntimeError):
    """A fixed diagnostic, never raw process output; lifecycle must retain claim."""


@dataclass(frozen=True)
class BackendConfig:
    endpoint: str
    region: str
    bucket: str
    key: str

    def hcl(self) -> str:
        endpoint = urlsplit(self.endpoint)
        hosts = {f"s3.{self.region}.wasabisys.com"}
        if self.region == "us-east-1":
            hosts.add("s3.wasabisys.com")
        if (
            endpoint.scheme != "https"
            or not endpoint.hostname
            or endpoint.username
            or endpoint.password
            or endpoint.query
            or endpoint.fragment
            or endpoint.path not in ("", "/")
            or endpoint.hostname not in hosts
            or endpoint.netloc != endpoint.hostname
            or re.fullmatch(r"[a-z0-9.-]+", endpoint.hostname) is None
            or re.fullmatch(r"[a-z0-9-]{1,63}", self.region) is None
            or re.fullmatch(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]", self.bucket) is None
            or re.fullmatch(r"[A-Za-z0-9/_-]+\.tfstate", self.key) is None
            or any(part in ("", ".", "..") for part in self.key.split("/"))
        ):
            raise ValueError("invalid_canary_backend")
        values = {
            "bucket": self.bucket,
            "key": self.key,
            "region": self.region,
            "encrypt": True,
            "use_lockfile": True,
            "skip_credentials_validation": True,
            "skip_region_validation": True,
            "skip_requesting_account_id": True,
            "skip_metadata_api_check": True,
            "use_path_style": True,
        }
        return "\n".join(f"{key} = {json.dumps(value)}" for key, value in values.items()) + (
            "\nendpoints = { s3 = " + json.dumps(self.endpoint) + " }\n"
        )


@dataclass(frozen=True)
class LockEvidence:
    key: str
    version: str
    body: bytes = field(repr=False)


class LockHolder(Protocol):
    """Conditional create, exact current read and version-owned release, no retries."""

    def create_lock(self, key: str, body: bytes) -> LockEvidence: ...

    def read_lock(self, key: str) -> LockEvidence | None: ...

    def release_lock(self, key: str, version: str) -> None: ...


def _dagger_runtime() -> bool:
    # A diagnostic guard created by the integration's Dagger graph, not proof
    # of authorization, isolation or writer exclusion.
    return Path("/run/canary/runtime-marker").is_file()


def _json(raw: bytes) -> Any:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError()
            result[key] = value
        return result

    parsed = None
    try:
        parsed = json.loads(raw, object_pairs_hook=unique)
    except Exception:
        pass
    if not isinstance(parsed, dict):
        raise TerraformUnknown("invalid_terraform_json")
    return parsed


def states_match(left: bytes, right: bytes) -> bool:
    """Keep every state value, normalizing only unordered check-result lists."""

    def normalized(raw: bytes) -> dict:
        state = _json(raw)
        checks = state.get("check_results")
        if isinstance(checks, list):
            ordered = []
            for check in checks:
                if not isinstance(check, dict):
                    raise TerraformUnknown("invalid_check_metadata")
                check = dict(check)
                objects = check.get("objects")
                if isinstance(objects, list):
                    check["objects"] = sorted(
                        objects, key=lambda value: json.dumps(value, sort_keys=True)
                    )
                ordered.append(check)
            state["check_results"] = sorted(
                ordered, key=lambda value: json.dumps(value, sort_keys=True)
            )
        return state

    return normalized(left) == normalized(right)


class TerraformDriver:
    def __init__(
        self,
        root: Path,
        *,
        run_prefix: str,
        zone_id: str,
        backend: BackendConfig,
        state_generation: Callable[[], str],
        checkpoint: Callable[[bytes, str], None],
        runtime: bool = False,
        runtime_check: Callable[[], bool] = _dagger_runtime,
        dns_client: CloudflareDNSClient | None = None,
        resolver: PublicResolver | None = None,
        timeout_seconds: float = 120,
        process_factory: Callable[..., Any] = subprocess.Popen,
    ) -> None:
        if not runtime or not runtime_check():
            raise TerraformUnknown("dagger_runtime_required")
        if not math.isfinite(timeout_seconds) or not 0 < timeout_seconds <= 1800:
            raise ValueError("invalid_terraform_timeout")
        self.root = root.resolve(strict=True)
        self.run_prefix, self.zone_id = run_prefix, zone_id
        self.backend = backend
        self._backend_hcl = backend.hcl()
        if (
            not backend.key.endswith(f"/runs/{run_prefix}/terraform.tfstate")
            and re.search(
                r"/qualification/[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}/terraform\.tfstate$",
                backend.key,
            )
            is None
        ):
            raise ValueError("backend_run_identity_mismatch")
        self._generation, self._checkpoint = state_generation, checkpoint
        self._qualification = "/qualification/" in backend.key
        self._process, self._timeout = process_factory, timeout_seconds
        self.dns = dns_client or CloudflareDNSClient(zone_id, run_prefix)
        self.resolver = resolver or CloudflareDoHResolver(run_prefix)
        self._revision: Revision = "create"
        self._initialized = False
        self._initialized_backend: BackendConfig | None = None
        self._records: dict[str, ExpectedRecord] = {}
        self._validate_identity()

    def _validate_identity(self) -> None:
        for label, kind in (("txt", "TXT"), ("cname", "CNAME")):
            validate_canary_record(
                run_prefix=self.run_prefix,
                name=record_name(self.run_prefix, label),
                zone_name=ZONE_NAME,
                zone_id=self.zone_id,
                expected_zone_id=self.zone_id,
                record_type=kind,
                proxied=False,
                resource_type=RESOURCE_TYPE,
            )

    def _fixture(self) -> None:
        """Reject additional native configuration, providers, modules or hooks."""
        self._validate_identity()
        options = SerializationOptions(
            with_comments=False, explicit_blocks=False, strip_string_quotes=True
        )
        if self._qualification:
            try:
                files = {
                    p.name for p in self.root.iterdir() if p.name.endswith((".tf", ".tf.json"))
                }
                path = self.root / "versions.tf"
                if files != {"versions.tf"} or path.is_symlink():
                    raise ValueError()
                config = hcl2.loads(path.read_text(), serialization_options=options)
                if config != {
                    "terraform": [
                        {
                            "required_version": ">= 1.13.5, < 2.0.0",
                            "backend": [{"s3": {}}],
                        }
                    ]
                }:
                    raise ValueError()
            except Exception:
                raise TerraformUnknown("invalid_qualification_root") from None
            return
        if {p.name for p in self.root.iterdir() if p.name.endswith((".tf", ".tf.json"))} != {
            "main.tf",
            "variables.tf",
            "outputs.tf",
            "versions.tf",
        }:
            raise TerraformUnknown("unexpected_fixture_file")
        blocks = []
        try:
            for name in ("main.tf", "variables.tf", "outputs.tf", "versions.tf"):
                path = self.root / name
                if path.is_symlink():
                    raise ValueError()
                blocks.append(hcl2.loads(path.read_text(), serialization_options=options))
        except Exception:
            raise TerraformUnknown("invalid_fixture") from None
        try:
            lockpath = self.root / ".terraform.lock.hcl"
            if lockpath.is_symlink() or not lockpath.is_file():
                raise ValueError()
            lock = hcl2.loads(lockpath.read_text(), serialization_options=options)
            if set(lock) != {"provider"} or len(lock["provider"]) != 1:
                raise ValueError()
            selection = lock["provider"][0]
            if set(selection) != {PROVIDER} or selection[PROVIDER].get("version") != "5.16.0":
                raise ValueError()
            hashes = selection[PROVIDER].get("hashes")
            if (
                not isinstance(hashes, list)
                or not hashes
                or any(
                    not isinstance(value, str)
                    or re.fullmatch(r"(?:h1:[A-Za-z0-9+/]{43}=|zh:[0-9a-f]{64})", value) is None
                    for value in hashes
                )
            ):
                raise ValueError()
        except Exception:
            raise TerraformUnknown("invalid_provider_lock") from None
        if any(
            set(block)
            - {"resource", "data", "locals", "variable", "output", "terraform", "provider"}
            for block in blocks
        ):
            raise TerraformUnknown("unexpected_fixture_block")
        resources = [r for b in blocks for r in b.get("resource", [])]
        data = [r for b in blocks for r in b.get("data", [])]
        providers = [r for b in blocks for r in b.get("provider", [])]
        if (
            len(resources) != 1
            or set(resources[0]) != {RESOURCE_TYPE}
            or set(resources[0][RESOURCE_TYPE]) != {"canary"}
            or data != [{"cloudflare_zone": {"sandbox": {"zone_id": "${var.zone_id}"}}}]
            or providers != [{"cloudflare": {}}]
        ):
            raise TerraformUnknown("unexpected_fixture_resource")
        resource = resources[0][RESOURCE_TYPE]["canary"]
        if resource != {
            "for_each": "${local.records}",
            "zone_id": "${var.zone_id}",
            "name": "${var.run_prefix}.${each.key}.${local.namespace}",
            "type": "${each.value.type}",
            "content": "${each.value.content}",
            "ttl": 60,
            "proxied": False,
            "comment": "${var.run_prefix}",
            "lifecycle": [
                {
                    "precondition": [
                        {
                            "condition": '${data.cloudflare_zone.sandbox.name == "solomonhd.ai"}',
                            "error_message": "Canary records are restricted to the existing solomonhd.ai zone.",
                        }
                    ]
                }
            ],
        }:
            raise TerraformUnknown("unexpected_fixture_definition")
        locals_ = [r for b in blocks for r in b.get("locals", [])]
        variables = [r for b in blocks for r in b.get("variable", [])]
        outputs = [r for b in blocks for r in b.get("output", [])]
        terraform = [r for b in blocks for r in b.get("terraform", [])]
        if (
            locals_
            != [
                {
                    "namespace": "ci.solomonhd.ai",
                    "records": {
                        "txt": {"type": "TXT", "content": "${var.txt_value}"},
                        "cname": {"type": "CNAME", "content": "${var.cname_target}"},
                    },
                }
            ]
            or len(variables) != 4
            or {name for block in variables for name in block}
            != {"zone_id", "run_prefix", "txt_value", "cname_target"}
            or len(outputs) != 1
            or set(outputs[0]) != {"records"}
            or len(terraform) != 1
            or set(terraform[0]) != {"required_version", "required_providers", "backend"}
            or terraform[0]["backend"] != [{"s3": {}}]
            or terraform[0]["required_providers"]
            != [
                {
                    "cloudflare": {
                        "source": "cloudflare/cloudflare",
                        "version": "~> 5.0",
                    }
                }
            ]
        ):
            raise TerraformUnknown("unexpected_fixture_configuration")

    def _env(self) -> dict[str, str]:
        env = {
            k: v
            for k, v in os.environ.items()
            if not k.startswith(("TF_", "TERRAFORM_"))
            and k
            not in {
                "AWS_PROFILE",
                "AWS_DEFAULT_PROFILE",
                "AWS_WEB_IDENTITY_TOKEN_FILE",
                "AWS_ROLE_ARN",
            }
        }
        env.update(
            {
                "TF_IN_AUTOMATION": "1",
                "TF_INPUT": "0",
                "TF_WORKSPACE": "default",
                "TF_VAR_zone_id": self.zone_id,
                "TF_VAR_run_prefix": self.run_prefix,
                "TF_VAR_txt_value": f"canary_{self._revision}",
                "TF_VAR_cname_target": (
                    "example.com" if self._revision == "create" else "example.org"
                ),
                "AWS_SHARED_CREDENTIALS_FILE": "/dev/null",
                "AWS_CONFIG_FILE": "/dev/null",
                "AWS_EC2_METADATA_DISABLED": "true",
            }
        )
        return env

    def _run(
        self,
        args: list[str],
        allowed: tuple[int, ...] = (0,),
        *,
        capture: bool = False,
        diagnostic: bool = False,
    ) -> tuple[int, bytes]:
        # Regular temporary files avoid pipe deadlock and never stream output to
        # Dagger logs. TemporaryFile is unlinked and mode 0600 on supported Unix.
        with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
            process = None
            try:
                process = self._process(
                    ["terraform", *args],
                    cwd=self.root,
                    env=self._env(),
                    stdin=subprocess.DEVNULL,
                    stdout=stdout,
                    stderr=stderr,
                    start_new_session=True,
                )
                code = process.wait(timeout=self._timeout)
            except subprocess.TimeoutExpired:
                if process is not None:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except Exception:
                        pass
                    try:
                        process.wait(timeout=5)
                    except Exception:
                        pass
                raise TerraformUnknown("terraform_effect_unknown") from None
            except Exception:
                raise TerraformUnknown("terraform_process_unknown") from None
            if type(code) is not int or code < 0:
                raise TerraformUnknown("terraform_process_unknown")
            if code not in allowed:
                raise CompletedFailure("terraform_command_failed")
            if not capture:
                return code, b""
            stdout.seek(0)
            raw = stdout.read(MAX_CAPTURE + 1)
            if diagnostic:
                stderr.seek(0)
                raw += stderr.read(MAX_CAPTURE + 1)
            if len(raw) > MAX_CAPTURE:
                raise TerraformUnknown("terraform_capture_limit")
            return code, raw

    def initialize(self) -> None:
        self._fixture()
        if self._backend_hcl != self.backend.hcl():
            raise TerraformUnknown("backend_configuration_changed")
        if not self._qualification:
            self.dns.verify_zone()
        with tempfile.TemporaryDirectory(prefix="canary-backend-") as directory:
            path = Path(directory) / "backend.hcl"
            path.write_text(self._backend_hcl)
            path.chmod(0o600)
            self._run(
                ["init", "-input=false", "-no-color", "-reconfigure", f"-backend-config={path}"]
                + ([] if self._qualification else ["-lockfile=readonly"])
            )
        self._initialized = True
        self._initialized_backend = self.backend

    def _ready(self) -> None:
        if not self._initialized:
            raise TerraformUnknown("terraform_not_initialized")
        if self.backend != self._initialized_backend:
            raise TerraformUnknown("initialized_backend_changed")
        self._fixture()

    def _values(self, value: Any, label: str) -> None:
        if not isinstance(value, dict):
            raise TerraformUnknown("invalid_resource_values")
        try:
            validate_canary_record(
                run_prefix=self.run_prefix,
                name=value["name"],
                zone_name=ZONE_NAME,
                zone_id=value["zone_id"],
                expected_zone_id=self.zone_id,
                record_type=value["type"],
                proxied=value["proxied"],
                resource_type=RESOURCE_TYPE,
            )
        except Exception:
            raise TerraformUnknown("unexpected_state_identity") from None
        if value["name"] != record_name(self.run_prefix, label):
            raise TerraformUnknown("unexpected_state_identity")

    def _state(self, raw: bytes | None = None) -> tuple[bytes, dict[str, Any], int]:
        if raw is None:
            _, raw = self._run(["state", "pull", "-no-color"], capture=True)
        state = _json(raw)
        if state.get("version") != 4 or not isinstance(state.get("resources"), list):
            raise TerraformUnknown("invalid_remote_state")
        count = 0
        seen = set()
        for resource in state["resources"]:
            if not isinstance(resource, dict) or resource.get("module") is not None:
                raise TerraformUnknown("unexpected_state_resource")
            if resource.get("provider") != f'provider["{PROVIDER}"]':
                raise TerraformUnknown("unexpected_state_provider")
            instances = resource.get("instances")
            if not isinstance(instances, list):
                raise TerraformUnknown("unexpected_state_instances")
            identity = (resource.get("mode"), resource.get("type"), resource.get("name"))
            if identity in seen:
                raise TerraformUnknown("duplicate_state_resource")
            seen.add(identity)
            if identity == ("data", "cloudflare_zone", "sandbox"):
                for instance in instances:
                    attrs = instance.get("attributes", {})
                    if (
                        instance.get("index_key") is not None
                        or attrs.get("id") != self.zone_id
                        or attrs.get("name") != ZONE_NAME
                    ):
                        raise TerraformUnknown("unexpected_state_zone")
                if len(instances) > 1:
                    raise TerraformUnknown("unexpected_state_zone")
            elif identity == ("managed", RESOURCE_TYPE, "canary"):
                labels = set()
                for instance in instances:
                    label = instance.get("index_key")
                    if label not in ("txt", "cname") or label in labels or instance.get("deposed"):
                        raise TerraformUnknown("unexpected_state_instance")
                    self._values(instance.get("attributes"), label)
                    labels.add(label)
                    count += 1
            else:
                raise TerraformUnknown("unexpected_state_resource")
        return raw, state, count

    def _plan(
        self, *, destroy: bool = False, revision: Revision | None = None
    ) -> tuple[int, Path, tempfile.TemporaryDirectory[str]]:
        directory = tempfile.TemporaryDirectory(prefix="canary-plan-")
        path = Path(directory.name) / "plan"
        try:
            code, _ = self._run(
                [
                    "plan",
                    "-input=false",
                    "-no-color",
                    "-lock-timeout=0s",
                    "-detailed-exitcode",
                    f"-out={path}",
                ]
                + (["-destroy"] if destroy else []),
                (0, 2),
            )
            _, raw = self._run(["show", "-json", str(path)], capture=True)
            plan = _json(raw)
            if revision is not None and code != 2:
                raise TerraformUnknown("revision_changes_not_observed")
            config = plan.get("configuration", {})
            providers = config.get("provider_config", {})
            root = config.get("root_module", {})
            if self._qualification:
                if (
                    providers
                    or root.get("resources")
                    or root.get("module_calls")
                    or plan.get("resource_changes")
                ):
                    raise TerraformUnknown("unexpected_qualification_plan")
                return code, path, directory
            if (
                set(providers) != {"cloudflare"}
                or providers["cloudflare"].get("full_name") != PROVIDER
                or root.get("module_calls")
            ):
                raise TerraformUnknown("unexpected_plan_provider_or_module")
            configured = root.get("resources", [])
            if (
                not isinstance(configured, list)
                or len(configured) != 2
                or {r.get("address") for r in configured}
                != {"cloudflare_dns_record.canary", DATA_ADDRESS}
            ):
                raise TerraformUnknown("unexpected_plan_configuration")
            for resource in configured:
                address = resource.get("address")
                if (
                    address not in ("cloudflare_dns_record.canary", DATA_ADDRESS)
                    or resource.get("provider_config_key") != "cloudflare"
                    or resource.get("provisioners")
                ):
                    raise TerraformUnknown("unexpected_plan_configuration")
            seen = set()
            for resource in plan.get("resource_changes", []):
                address = resource.get("address")
                if address in seen or resource.get("provider_name") != PROVIDER:
                    raise TerraformUnknown("unexpected_plan_resource")
                seen.add(address)
                if (
                    address == DATA_ADDRESS
                    and resource.get("mode") == "data"
                    and resource.get("type") == "cloudflare_zone"
                    and resource.get("name") == "sandbox"
                ):
                    continue
                if (
                    address not in ADDRESSES
                    or resource.get("mode") != "managed"
                    or resource.get("type") != RESOURCE_TYPE
                    or resource.get("name") != "canary"
                    or resource.get("index") != ADDRESSES[address]
                ):
                    raise TerraformUnknown("unexpected_plan_resource")
                change = resource.get("change", {})
                if change.get("actions") not in (["no-op"], ["create"], ["update"], ["delete"]):
                    raise TerraformUnknown("unexpected_plan_action")
                for key in ("before", "after"):
                    if change.get(key) is not None:
                        self._values(change[key], ADDRESSES[address])
                if destroy and change.get("actions") not in (["delete"], ["no-op"]):
                    raise TerraformUnknown("unexpected_destroy_plan")
                if revision is not None:
                    expected_action = "create" if revision == "create" else "update"
                    after = change.get("after", {})
                    if (
                        change.get("actions") != [expected_action]
                        or after.get("content") != self._content(ADDRESSES[address])
                        or after.get("ttl") != 60
                        or after.get("comment") != self.run_prefix
                    ):
                        raise TerraformUnknown("unexpected_revision_plan")
            if revision is not None and seen - {DATA_ADDRESS} != set(ADDRESSES):
                raise TerraformUnknown("incomplete_revision_plan")
            return code, path, directory
        except BaseException:
            directory.cleanup()
            raise

    def _effect(self, path: Path) -> None:
        failed = False
        try:
            self._run(["apply", "-input=false", "-no-color", "-lock-timeout=0s", str(path)])
        except CompletedFailure:
            failed = True
        # Pull/checkpoint even for a completed partial failure. A failed pull,
        # generation read or checkpoint is unknown, not cleanup authorization.
        try:
            _, raw = self._run(["state", "pull", "-no-color"], capture=True)
            generation = self._generation()
            if not isinstance(generation, str) or not generation:
                raise TerraformUnknown("invalid_state_generation")
            with tempfile.TemporaryFile(mode="w+t") as quiet:
                with redirect_stdout(quiet), redirect_stderr(quiet):
                    self._checkpoint(raw, generation)
            self._state(raw)
        except Exception:
            raise TerraformUnknown("effect_checkpoint_unconfirmed") from None
        if failed:
            # Process exit does not prove a timed-out provider request stopped
            # at Cloudflare. Preserve the checkpoint, but do not authorize
            # cleanup or takeover solely from a nonzero native apply result.
            raise TerraformUnknown("terraform_effect_outcome_unconfirmed")

    def apply(self, revision: Revision) -> None:
        self._ready()
        if self._qualification:
            raise TerraformUnknown("qualification_is_plan_only")
        if revision not in ("create", "update"):
            raise ValueError("invalid_canary_revision")
        self._revision = revision
        _, path, directory = self._plan(revision=revision)
        try:
            self._effect(path)
        finally:
            directory.cleanup()
        _, raw = self._run(["output", "-json", "records"], capture=True)
        output = _json(raw)
        if set(output) != {"txt", "cname"}:
            raise TerraformUnknown("unexpected_outputs")
        records = {}
        for label, value in output.items():
            self._values(value, label)
            if (
                not isinstance(value.get("id"), str)
                or re.fullmatch(r"[0-9a-f]{32}", value["id"]) is None
            ):
                raise TerraformUnknown("invalid_output_id")
            records[label] = ExpectedRecord(
                value["id"], value["name"], value["type"], self._content(label)
            )
        self._records = records

    def _content(self, label: str) -> str:
        return (
            f"canary_{self._revision}"
            if label == "txt"
            else ("example.com" if self._revision == "create" else "example.org")
        )

    def _expectations(self, revision: Revision) -> list[ExpectedRecord]:
        if revision != self._revision or set(self._records) != {"txt", "cname"}:
            raise TerraformUnknown("missing_record_evidence")
        return list(self._records.values())

    def verify_api(self, revision: Revision) -> None:
        try:
            for expected in self._expectations(revision):
                self.dns.verify_record(expected)
        except DNSValidationError:
            raise CompletedFailure("api_validation_failed") from None

    def verify_dns(self, revision: Revision) -> None:
        try:
            for expected in self._expectations(revision):
                verify_public_dns(
                    expected,
                    run_prefix=self.run_prefix,
                    resolver=self.resolver,
                    max_attempts=37,
                    deadline_seconds=180,
                    interval_seconds=5,
                )
        except DNSValidationError:
            raise CompletedFailure("public_dns_validation_failed") from None

    def drift(self) -> bool:
        self._ready()
        code, _, directory = self._plan()
        directory.cleanup()
        return code == 2

    def has_state(self) -> bool:
        self._ready()
        self._state()
        return True

    def destroy(self) -> None:
        self._ready()
        if self._qualification:
            raise TerraformUnknown("qualification_is_plan_only")
        self._state()
        _, path, directory = self._plan(destroy=True)
        try:
            self._effect(path)
        finally:
            directory.cleanup()

    def verify_absence(self) -> None:
        self._ready()
        _, state, count = self._state()
        if count or any(r.get("instances") for r in state["resources"]):
            raise CompletedFailure("remote_state_not_empty")
        for label in ("txt", "cname"):
            self.dns.verify_absent(record_name(self.run_prefix, label))


def qualify_native_lock(
    driver: TerraformDriver, holder: LockHolder, *, qualification_prefix: str
) -> str:
    """Prove native lock refusal then success on a disposable qualification key.

    Never call with the run's production backend/root. The caller provisions a
    separate initialized driver under its approved qualification prefix; this
    helper plans only, never applies. Uncertain outcomes retain the exact key.
    An injected holder must implement real conditional S3 creation/read/release;
    a boolean 'lock held' assertion is not evidence.
    """
    driver._ready()
    if (
        not qualification_prefix.endswith("/qualification/")
        or not driver.backend.key.startswith(qualification_prefix)
        or re.fullmatch(
            r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}/terraform\.tfstate",
            driver.backend.key.removeprefix(qualification_prefix),
        )
        is None
    ):
        raise TerraformUnknown("disposable_lock_backend_required")
    key = driver.backend.key + ".tflock"
    lock_id = str(uuid.uuid4())
    body = json.dumps(
        {
            "ID": lock_id,
            "Operation": "OperationTypePlan",
            "Info": "canary lock qualification",
            "Who": "canary-qualification",
            "Version": "1.13.5",
            "Created": "2026-01-01T00:00:00Z",
            "Path": f"{driver.backend.bucket}/{driver.backend.key}",
        },
        sort_keys=True,
    ).encode()
    try:
        evidence = holder.create_lock(key, body)
        if (
            not isinstance(evidence, LockEvidence)
            or evidence.key != key
            or not isinstance(evidence.version, str)
            or not evidence.version
            or evidence.body != body
            or holder.read_lock(key) != evidence
        ):
            raise TerraformUnknown("qualification_lock_unconfirmed")
        code, diagnostic = driver._run(
            ["plan", "-input=false", "-no-color", "-lock-timeout=0s", "-detailed-exitcode"],
            (0, 1, 2),
            capture=True,
            diagnostic=True,
        )
        if (
            code != 1
            or b"Error acquiring the state lock" not in diagnostic
            or lock_id.encode() not in diagnostic
            or not any(
                marker in diagnostic
                for marker in (b"PreconditionFailed", b"ConditionalCheckFailed", b"StatusCode: 412")
            )
        ):
            raise TerraformUnknown("native_lock_refusal_not_observed")
        if holder.read_lock(key) != evidence:
            raise TerraformUnknown("qualification_lock_ownership_lost")
        holder.release_lock(key, evidence.version)
        if holder.read_lock(key) is not None:
            raise TerraformUnknown("qualification_lock_release_unconfirmed")
        code, _, directory = driver._plan()
        directory.cleanup()
        if code != 0:
            raise TerraformUnknown("qualification_plan_not_empty")
    except Exception:
        raise TerraformUnknown("native_lock_qualification_unconfirmed") from None
    return key
