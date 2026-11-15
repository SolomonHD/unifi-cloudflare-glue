"""Small execution contracts shared by Terraform orchestration and verification."""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    import dagger


class PhaseFailure(RuntimeError):
    """A completed command failed; its container remains available for state capture."""

    def __init__(self, phase: str, exit_code: int):
        self.exit_code = exit_code
        super().__init__(f"{phase} failed (exit code {exit_code})")


def validate_run_label(label: str) -> None:
    """A transitional label is metadata, never executable syntax or freshness."""
    if not isinstance(label, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{0,80}", label):
        raise ValueError(
            "run label must contain at most 80 letters, digits, dots, underscores or hyphens"
        )


def selected_root(unifi_only: bool, cloudflare_only: bool, state_scope: str) -> str:
    """Resolve a previously qualified state/root selection before backend access."""
    if unifi_only and cloudflare_only:
        raise ValueError("Cannot use both --unifi-only and --cloudflare-only")
    scope = "unifi" if unifi_only else "cloudflare" if cloudflare_only else "full"
    if state_scope != scope:
        raise ValueError(
            "Selected scope is incompatible with state-scope; use the existing state's root"
        )
    return {"full": "glue", "unifi": "unifi-dns", "cloudflare": "cloudflare-tunnel"}[scope]


def validate_unifi_auth(api_key, username, password) -> None:
    if (username is None) != (password is None):
        raise ValueError("UniFi username and password must both be supplied")
    if api_key is not None and username is not None:
        raise ValueError("Cannot use both API key and username/password")


def terraform_runtime(dag, image: str):
    """Frozen parser tooling is built before any backend Secret is mounted."""
    try:
        from .offline import UV_IMAGE
        from .toolchains import PYTHON_IMAGE
    except ImportError:
        from offline import UV_IMAGE  # type: ignore[no-redef,import-not-found]
        from toolchains import PYTHON_IMAGE  # type: ignore[no-redef,import-not-found]
    return (
        dag.container()
        .from_(PYTHON_IMAGE)
        .with_file("/usr/local/bin/terraform", dag.container().from_(image).file("/bin/terraform"))
        .with_file("/usr/local/bin/uv", dag.container().from_(UV_IMAGE).file("/usr/local/bin/uv"))
        .with_directory(
            "/tooling",
            dag.current_module().source(),
            include=["pyproject.toml", "uv.lock", "sdk/**", "clients/core/**", "src/**"],
            exclude=["**/__pycache__/**", "**/.venv/**"],
        )
        .with_workdir("/tooling")
        .with_env_variable("UV_PYTHON_DOWNLOADS", "never")
        .with_exec(["uv", "sync", "--frozen", "--no-dev", "--no-install-project"])
        .with_env_variable("PATH", "/tooling/.venv/bin:/usr/local/bin:/usr/bin:/bin")
        .with_env_variable("TF_IN_AUTOMATION", "true")
        .with_env_variable("TF_INPUT", "false")
    )


def prepare_root(dag, image: str, root: str, backend_type: str):
    """Retain sibling paths and one selected root for plan/apply/destroy."""
    if root not in {"glue", "unifi-dns", "cloudflare-tunnel"}:
        raise ValueError("Invalid Terraform root")
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,31}", backend_type):
        raise ValueError("Invalid backend type")
    workdir = "/module/" + root
    container = (
        terraform_runtime(dag, image)
        .with_directory("/module", dag.current_module().source().directory("terraform/modules"))
        .with_workdir(workdir)
    )
    if backend_type != "local":
        container = container.with_new_file(
            workdir + "/backend.tf", 'terraform {\n  backend "' + backend_type + '" {}\n}\n'
        )
    if root == "unifi-dns":
        container = container.with_new_file(workdir + "/provider.tf", 'provider "unifi" {}\n')
    return container, workdir


def live_exec(container: dagger.Container, argv: list[str], **options) -> dagger.Container:
    """Freshen an exec, retaining its input snapshot and using direct argv."""
    # Backend parsers can print a single field from a multiline Secret. Exact
    # Secret masking alone cannot redact that derived value in engine traces.
    if (
        len(argv) > 1
        and argv[0] == "terraform"
        and argv[1] in {"init", "apply", "destroy", "plan", "show", "output"}
    ):
        options.setdefault("redirect_stdout", "/root/.terraform-exec.stdout")
        options.setdefault("redirect_stderr", "/root/.terraform-exec.stderr")
    return container.with_env_variable("EXECUTION_NONCE", str(uuid4())).with_exec(argv, **options)


def plan_counts(plan: object) -> dict[str, int]:
    """Extract only action counts; never retain resource values or output contents."""
    if not isinstance(plan, dict) or not isinstance(plan.get("resource_changes", []), list):
        raise ValueError("Terraform plan has invalid resource_changes")
    counts = {"add": 0, "change": 0, "destroy": 0, "replace": 0}
    valid = {
        ("no-op",),
        ("read",),
        ("create",),
        ("update",),
        ("delete",),
        ("delete", "create"),
        ("create", "delete"),
    }
    for resource in plan.get("resource_changes", []):
        if not isinstance(resource, dict) or not isinstance(resource.get("change"), dict):
            raise ValueError("Terraform plan has invalid resource change")
        actions = resource["change"].get("actions")
        if (
            not isinstance(actions, list)
            or not all(isinstance(action, str) for action in actions)
            or tuple(actions) not in valid
        ):
            raise ValueError("Terraform plan has invalid action array")
        counts["add"] += "create" in actions
        counts["change"] += "update" in actions
        counts["destroy"] += "delete" in actions
        counts["replace"] += "create" in actions and "delete" in actions
    return counts


def api_result(payload: object, provider: str) -> list[dict]:
    """Validate supported HTTP API envelopes; an error/null is never absence."""
    if provider == "unifi-v2" and isinstance(payload, list):
        if not all(isinstance(item, dict) for item in payload):
            raise ValueError("UniFi v2 response must contain objects")
        return payload
    if not isinstance(payload, dict):
        raise ValueError("API response must be an object")
    if provider == "cloudflare":
        if payload.get("success") is not True or payload.get("errors") != []:
            raise ValueError("Cloudflare API reported failure or missing success envelope")
        result = payload.get("result")
    elif provider in {"unifi", "unifi-v2"}:
        meta = payload.get("meta")
        if not isinstance(meta, dict) or meta.get("rc") != "ok":
            raise ValueError("UniFi API reported failure or missing success envelope")
        result = payload.get("data")
    else:
        raise ValueError("Unsupported API response provider")
    if not isinstance(result, list) or not all(isinstance(item, dict) for item in result):
        raise ValueError("API response result must be an array of objects")
    return result


def parse_api_response(body: str, status: int, provider: str) -> list[dict]:
    if type(status) is not int or not 200 <= status < 300:
        raise ValueError("API HTTP status is unsuccessful")
    try:
        payload = json.loads(body)
    except (TypeError, ValueError):
        raise ValueError("API response is not valid JSON") from None
    return api_result(payload, provider)


CLOUDFLARE_QUERY = r"""
import json, os, sys
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from execution import parse_api_response

def query(path, params):
    request = Request(
        "https://api.cloudflare.com/client/v4/" + path + "?" + urlencode(params),
        headers={"Authorization": "Bearer " + os.environ["CLOUDFLARE_API_TOKEN"]},
    )
    with urlopen(request, timeout=20) as response:
        body = response.read(8 * 1024 * 1024 + 1)
        if len(body) > 8 * 1024 * 1024:
            raise ValueError("API response exceeded limit")
        result = parse_api_response(body, response.status, "cloudflare")
        # A paged partial result cannot establish an exact count or absence.
        info = json.loads(body).get("result_info")
        if info is not None:
            if (not isinstance(info, dict)
                or type(info.get("total_pages")) is not int
                or info["total_pages"] not in (0, 1)
                or type(info.get("total_count")) is not int
                or info["total_count"] != len(result)):
                raise ValueError("API result is paginated or malformed")
        return result

try:
    account, zone, tunnel, hostname = sys.argv[1:]
    tunnels = query("accounts/" + quote(account, safe="") + "/cfd_tunnel", {"name": tunnel, "is_deleted": "false"})
    if not all(isinstance(item.get("id"), str) and item.get("name") == tunnel for item in tunnels):
        raise ValueError("Invalid tunnel shape")
    zones = query("zones", {"name": zone})
    if len(zones) != 1 or not isinstance(zones[0].get("id"), str) or zones[0].get("name") != zone:
        raise ValueError("Zone identity not uniquely resolved")
    records = query("zones/" + quote(zones[0]["id"], safe="") + "/dns_records", {"name": hostname})
    if not all(isinstance(item.get("id"), str) and item.get("name") == hostname for item in records):
        raise ValueError("Invalid DNS record shape")
    print(json.dumps([len(tunnels), len(records)]))
except Exception:
    sys.stderr.write("Cloudflare verification failed: HTTP, envelope or response shape invalid\n")
    sys.exit(1)
"""

UNIFI_PREFIX_QUERY = r"""
import json, os, ssl, sys
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen
from execution import parse_api_response

try:
    base, site, prefix, insecure, match_mode = sys.argv[1:]
    if urlsplit(base).scheme not in {"http", "https"} or not prefix:
        raise ValueError("Invalid endpoint or prefix")
    context = ssl._create_unverified_context() if insecure == "true" else ssl.create_default_context()
    request = Request(base.rstrip("/") + "/proxy/network/v2/api/site/" + quote(site, safe="") + "/static-dns",
        headers={"X-API-KEY": os.environ["UNIFI_API_KEY"]})
    with urlopen(request, context=context, timeout=20) as response:
        body = response.read(8 * 1024 * 1024 + 1)
        if len(body) > 8 * 1024 * 1024:
            raise ValueError("API response exceeded limit")
        records = parse_api_response(body, response.status, "unifi-v2")
    names = [item.get("key", item.get("name")) for item in records]
    if not all(isinstance(name, str) for name in names):
        raise ValueError("Invalid DNS record shape")
    print(sum(name == prefix if match_mode == "exact" else prefix in name for name in names))
except Exception:
    sys.stderr.write("UniFi verification failed: HTTP, envelope or response shape invalid\n")
    sys.exit(1)
"""
