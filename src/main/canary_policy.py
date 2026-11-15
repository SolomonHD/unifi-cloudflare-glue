"""Credential-free admission policy, evaluated before a live job requests secrets."""

import re
from collections.abc import Mapping

TRUSTED_REPOSITORY = "SolomonHD/unifi-cloudflare-glue"
TRUSTED_REF = "refs/heads/main"
TRUSTED_EVENTS = frozenset({"push", "schedule", "workflow_dispatch"})


def require_trusted_context(
    context: Mapping[str, object],
    *,
    acceptance_sha: str = "",
    acceptance_branch: str = "",
) -> None:
    """Reject missing or unexpected GitHub claims without echoing caller input.

    This is a second admission check, not a substitute for a job-level condition
    before environment selection or verified GitHub environment branch controls.
    Callers must use GitHub-provided claims, never dispatch inputs as claims.
    """
    if (
        context.get("repository") == TRUSTED_REPOSITORY
        and context.get("ref_type") == "branch"
        and context.get("event_name") == "push"
        and acceptance_branch == "change/add-cloudflare-live-ci-canary"
        and re.fullmatch(r"[0-9a-f]{40}", acceptance_sha)
        and context.get("ref") == "refs/heads/" + acceptance_branch
        and context.get("sha") == acceptance_sha
    ):
        return
    if (
        context.get("repository") != TRUSTED_REPOSITORY
        or context.get("ref") != TRUSTED_REF
        or not isinstance(context.get("event_name"), str)
        or context.get("event_name") not in TRUSTED_EVENTS
        or context.get("ref_type") != "branch"
    ):
        raise ValueError("Canary workflow context is not trusted")
