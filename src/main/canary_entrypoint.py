"""One uncached Dagger execution boundary, never a plaintext credential reader."""

import asyncio
import json
import re
import time

import dagger

from .canary_identity import build_run_prefix
from .canary_policy import TRUSTED_REPOSITORY, require_trusted_context
from .execution import live_exec, terraform_runtime
from .toolchains import TERRAFORM_IMAGE

BUCKET = "sandbox-ghe-actions-ci"
REGION = "us-east-1"
ENDPOINT = "https://s3.us-east-1.wasabisys.com"
PREFIX = "cloudflare-live-ci/v1/"
RUNTIME_ID = (
    "cli:d8a5c186090f92062fe773508f3b4d609ea75658802d5f5b75d6f627f2f2a075;"
    "engine:ad121f720ed9bfb8e740f99dd783fa8472965a5e262fc64ff3ef2634cea1e6dd;"
    "sdk:9394f7454139f1ee2ca35be20e585b1e54f06cc2;"
    "terraform:1.13.5;boto3:1.44.3;cloudflare:5.16.0"
)


def config_for(
    *,
    operation: str = "normal",
    bucket: str,
    revision: str,
    run_id: str,
    attempt: str,
    repository: str,
    ref: str,
    event_name: str,
    acceptance_sha: str,
    acceptance_branch: str,
    policy_reviewed: str,
) -> dict:
    local_qualification = (
        operation == "qualify"
        and event_name == "local_qualification"
        and repository == TRUSTED_REPOSITORY
        and ref == "refs/heads/change/add-cloudflare-live-ci-canary"
        and acceptance_branch == "change/add-cloudflare-live-ci-canary"
        and revision == acceptance_sha
        and re.fullmatch(r"[0-9a-f]{40}", revision)
    )
    if not local_qualification:
        require_trusted_context(
            {
                "repository": repository,
                "ref": ref,
                "event_name": event_name,
                "ref_type": "branch",
                "sha": revision,
            },
            acceptance_sha=acceptance_sha,
            acceptance_branch=acceptance_branch,
        )
    if (
        operation not in {"normal", "qualify"}
        or bucket != BUCKET
        or policy_reviewed != "true"
        or not re.fullmatch(r"[0-9a-f]{40}", revision)
    ):
        raise ValueError("Canary sandbox identity or operator policy review is missing")
    return {
        "bucket": BUCKET,
        "region": REGION,
        "endpoint": ENDPOINT,
        "prefix": PREFIX,
        "runtime_identity": RUNTIME_ID,
        "revision": revision,
        "run_prefix": build_run_prefix(str(int(time.time())), run_id, attempt),
        "policy_reviewed": True,
        "fixture": "/canary/fixture",
        "operation": operation,
    }


def checked_report(raw: str, config: dict, exit_code: int) -> str:
    try:
        report = json.loads(raw)
        required = {
            "run_prefix",
            "revision",
            "phase",
            "primary",
            "cleanup",
            "qualified",
            "operation",
        }
        if not isinstance(report, dict) or set(report) != required:
            raise ValueError()
        if report["operation"] != config["operation"]:
            raise ValueError()
        if report["run_prefix"] != config["run_prefix"] or report["revision"] != config["revision"]:
            raise ValueError()
        if (
            report["phase"]
            not in {
                "preflight",
                "qualification",
                "prepare",
                "initialize",
                "create",
                "create_api",
                "create_dns",
                "update",
                "update_api",
                "update_dns",
                "plan",
                "cleanup_state",
                "destroy",
                "absence",
            }
            or any(
                report[k] not in {"verified", "failed", "unknown", "not_attempted"}
                for k in ("primary", "cleanup")
            )
            or type(report["qualified"]) is not bool
        ):
            raise ValueError()
        safe = json.dumps(report, sort_keys=True)
    except Exception:
        raise RuntimeError("Canary outcome unknown; retain run " + config["run_prefix"]) from None
    if (
        exit_code != 0
        or report["primary"] != "verified"
        or report["cleanup"] != "verified"
        or report["qualified"] is not True
    ):
        raise RuntimeError("Canary did not verify: " + safe)
    return safe


def runtime_container(cloudflare_api_token, wasabi_access_key, wasabi_secret_key):
    return (
        terraform_runtime(dagger.dag, TERRAFORM_IMAGE)
        .with_directory(
            "/canary/fixture",
            dagger.dag.current_module().source().directory("terraform/cloudflare-canary"),
        )
        .with_new_file("/run/canary/runtime-marker", "dagger-canary-v1", permissions=0o600)
        .with_env_variable("PYTHONPATH", "/tooling/src")
        .with_secret_variable("CLOUDFLARE_API_TOKEN", cloudflare_api_token)
        .with_secret_variable("AWS_ACCESS_KEY_ID", wasabi_access_key)
        .with_secret_variable("AWS_SECRET_ACCESS_KEY", wasabi_secret_key)
    )


async def invoke(config: dict, cloudflare_api_token, wasabi_access_key, wasabi_secret_key) -> str:
    container = runtime_container(
        cloudflare_api_token, wasabi_access_key, wasabi_secret_key
    ).with_new_file("/canary/config.json", json.dumps(config), permissions=0o600)
    container = live_exec(
        container,
        ["python", "-m", "main.canary_runtime", "/canary/config.json"],
        expect=dagger.ReturnType.ANY,
        redirect_stdout="/canary/result.json",
        redirect_stderr="/canary/errors.private",
    )
    try:
        exit_code = await asyncio.wait_for(container.exit_code(), timeout=1500)
        raw = await asyncio.wait_for(container.file("/canary/result.json").contents(), timeout=30)
    except Exception:
        raise RuntimeError(
            "Canary execution unknown; reconcile run " + config["run_prefix"]
        ) from None
    return checked_report(raw, config, exit_code)


async def observe(
    run_prefix: str, cloudflare_api_token, wasabi_access_key, wasabi_secret_key
) -> str:
    from .canary_identity import validate_run_prefix

    validate_run_prefix(run_prefix)
    container = runtime_container(cloudflare_api_token, wasabi_access_key, wasabi_secret_key)
    container = live_exec(
        container,
        ["python", "-m", "main.canary_observation", run_prefix],
        expect=dagger.ReturnType.ANY,
        redirect_stdout="/canary/observation.json",
        redirect_stderr="/canary/observation.private",
    )
    try:
        code = await asyncio.wait_for(container.exit_code(), timeout=240)
        if code != 0:
            raise ValueError()
        raw = await container.file("/canary/observation.json").contents()
        report = json.loads(raw)
        if (
            report.get("operation") != "read_only_observation"
            or report.get("run_prefix") != run_prefix
        ):
            raise ValueError()
    except Exception:
        raise RuntimeError("Read-only observation unconfirmed for " + run_prefix) from None
    return json.dumps(report, sort_keys=True)


async def reconcile(
    config: dict, cloudflare_api_token, wasabi_access_key, wasabi_secret_key
) -> str:
    from .canary_identity import validate_run_prefix

    validate_run_prefix(config["run_prefix"])
    if (
        config.get("exclusive_writer") is not True
        or config.get("prior_writer_terminated") is not True
        or any(
            not isinstance(config.get(key), str)
            or not 1 <= len(config[key]) <= 768
            or not config[key].isascii()
            or not config[key].isprintable()
            for key in ("expected_claim_version_id", "expected_state_version_id")
        )
    ):
        raise ValueError("Explicit version-bound termination/exclusivity authorization required")
    container = runtime_container(
        cloudflare_api_token, wasabi_access_key, wasabi_secret_key
    ).with_new_file("/canary/recovery.json", json.dumps(config), permissions=0o600)
    container = live_exec(
        container,
        ["python", "-m", "main.canary_recovery", "/canary/recovery.json"],
        expect=dagger.ReturnType.ANY,
        redirect_stdout="/canary/recovery-result.json",
        redirect_stderr="/canary/recovery.private",
    )
    try:
        code = await asyncio.wait_for(container.exit_code(), timeout=600)
        raw = await container.file("/canary/recovery-result.json").contents()
        report = json.loads(raw)
        if (
            code != 0
            or report.get("operation") != "reconcile"
            or report.get("run_prefix") != config["run_prefix"]
            or report.get("cleanup") != "verified"
            or report.get("ownership_transferred") is not True
            or report.get("original_outcome") not in {"unknown", "failed"}
        ):
            raise ValueError()
    except Exception:
        raise RuntimeError("Reconciliation unconfirmed; retain " + config["run_prefix"]) from None
    return json.dumps(report, sort_keys=True)


async def reporting(
    config: dict, cloudflare_api_token, wasabi_access_key, wasabi_secret_key
) -> str:
    from .canary_identity import validate_run_prefix

    if config.get("operation") not in {"janitor", "metrics"}:
        raise ValueError("Unsupported reporting operation")
    if config["operation"] == "metrics":
        validate_run_prefix(config["run_prefix"])
        if re.fullmatch(r"[0-9a-f]{40}", config.get("revision", "")) is None:
            raise ValueError("Exact measurement revision required")
    container = runtime_container(cloudflare_api_token, wasabi_access_key, wasabi_secret_key)
    container = live_exec(
        container,
        ["python", "-m", "main.canary_reporting", json.dumps(config)],
        expect=dagger.ReturnType.ANY,
        redirect_stdout="/canary/report.json",
        redirect_stderr="/canary/report.private",
    )
    try:
        code = await asyncio.wait_for(container.exit_code(), timeout=240)
        if code != 0:
            raise ValueError()
        value = json.loads(await container.file("/canary/report.json").contents())
        expected = "janitor_inventory" if config["operation"] == "janitor" else "phase_measurements"
        if not isinstance(value, dict) or value.get("operation") != expected:
            raise ValueError()
    except Exception:
        raise RuntimeError("Read-only canary report unconfirmed") from None
    return json.dumps(value, sort_keys=True)
