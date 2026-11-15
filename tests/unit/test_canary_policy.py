"""Offline checks for admission before credential/environment acquisition."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src/main"))

from canary_policy import require_trusted_context


def context(**changes):
    return {
        "repository": "SolomonHD/unifi-cloudflare-glue",
        "ref": "refs/heads/main",
        "ref_type": "branch",
        "event_name": "workflow_dispatch",
        **changes,
    }


@pytest.mark.parametrize("event", ["push", "schedule", "workflow_dispatch"])
def test_trusted_events(event):
    require_trusted_context(context(event_name=event))


@pytest.mark.parametrize(
    "changes",
    [
        {"event_name": "pull_request"},
        {"event_name": "pull_request_target"},
        {"event_name": "workflow_run"},
        {"event_name": "repository_dispatch"},
        {"repository": "fork/unifi-cloudflare-glue"},
        {"ref": "refs/heads/feature"},
        {"ref": "refs/tags/main"},
        {"ref": "refs/pull/1/merge"},
        {"ref_type": "tag"},
        {"ref": "refs/heads/main\n"},
        {"event_name": []},
        {"event_name": None},
    ],
)
def test_rejection_precedes_credentials(changes):
    acquired = []
    with pytest.raises(ValueError, match="context is not trusted"):
        require_trusted_context(context(**changes))
        acquired.append("credentials")
    assert acquired == []


@pytest.mark.parametrize("key", ["repository", "ref", "ref_type", "event_name"])
def test_missing_claim_fails_closed(key):
    claims = context()
    del claims[key]
    with pytest.raises(ValueError):
        require_trusted_context(claims)


def test_rejection_does_not_echo_untrusted_input():
    with pytest.raises(ValueError) as error:
        require_trusted_context(context(ref="synthetic-confidential-marker"))
    assert "synthetic-confidential-marker" not in str(error.value)
