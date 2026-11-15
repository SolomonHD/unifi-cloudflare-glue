"""Offline fake-client contract tests, never live Wasabi acceptance."""

import hashlib
import importlib.util
import io
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from botocore.exceptions import ClientError

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "canary_s3_test_package",
    ROOT / "src/main/__init__.py",
    submodule_search_locations=[str(ROOT / "src/main")],
)
package = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = package
from canary_s3_test_package import canary_s3 as s3
from canary_s3_test_package import canary_store as store

BINDING = store.StoreBinding(
    "https://s3.us-east-1.wasabisys.com", "us-east-1", "synthetic-canary", "canary/test/", "test"
)
KEY = BINDING.prefix + "checkpoint"
SENTINEL = "private-content-canary"


def error(status, code):
    return ClientError(
        {
            "ResponseMetadata": {"HTTPStatusCode": status},
            "Error": {"Code": code, "Message": SENTINEL},
        },
        "synthetic",
    )


class FakeClient:
    def __init__(self):
        self.calls = []
        self.objects = {}
        self.versions = {}
        self.serial = 0
        self.versioning = "Enabled"
        self.encryption = "AES256"
        self.enforce_create = True
        self.enforce_update = True
        self.failure = None
        self.response_mutation = None
        self.bodies = []

    def _call(self, method, params):
        self.calls.append((method, params))
        assert params["Bucket"] == BINDING.bucket
        if self.failure == method:
            raise error(503, "ServiceUnavailable")

    def get_bucket_versioning(self, **params):
        self._call("get_bucket_versioning", params)
        return {"Status": self.versioning}

    def put_object(self, **params):
        self._call("put_object", params)
        key = params["Key"]
        old = self.objects.get(key)
        if params.get("IfNoneMatch") == "*" and old and self.enforce_create:
            raise error(412, "PreconditionFailed")
        if "IfMatch" in params and self.enforce_update:
            if old is None or old[2] != params["IfMatch"]:
                raise error(412, "PreconditionFailed")
        assert params["ContentLength"] == len(params["Body"])
        assert params["ServerSideEncryption"] == "AES256"
        self.serial += 1
        version = f"opaque-{self.serial}"
        etag = '"' + hashlib.md5(params["Body"]).hexdigest() + '"'
        obj = (params["Body"], version, etag)
        self.objects[key] = obj
        self.versions[key, version] = obj
        response = {"VersionId": version, "ETag": etag, "ServerSideEncryption": self.encryption}
        if self.response_mutation:
            self.response_mutation("put", response)
        return response

    def get_object(self, **params):
        self._call("get_object", params)
        key = params["Key"]
        obj = (
            self.versions.get((key, params["VersionId"]))
            if "VersionId" in params
            else self.objects.get(key)
        )
        if obj is None:
            raise error(404, "NoSuchKey")
        data, version, etag = obj
        if "IfMatch" in params and params["IfMatch"] != etag:
            raise error(412, "PreconditionFailed")
        body = io.BytesIO(data)
        self.bodies.append(body)
        response = {
            "Body": body,
            "ContentLength": len(data),
            "VersionId": version,
            "ETag": etag,
            "ServerSideEncryption": self.encryption,
        }
        if self.response_mutation:
            self.response_mutation("get", response)
        return response

    def delete_object(self, **params):
        self._call("delete_object", params)
        assert set(params) in ({"Bucket", "Key"}, {"Bucket", "Key", "IfMatch"})
        assert "VersionId" not in params, "No permanent version deletion"
        old = self.objects.get(params["Key"])
        if "IfMatch" in params and (old is None or old[2] != params["IfMatch"]):
            raise error(412, "PreconditionFailed")
        self.objects.pop(params["Key"], None)
        self.serial += 1
        return {"DeleteMarker": True, "VersionId": f"marker-{self.serial}"}


@pytest.fixture
def qualified():
    client = FakeClient()
    transport = s3.Boto3S3Transport(BINDING, client=client)
    transport.qualify_backend()
    client.calls.clear()
    return transport, client


def test_qualification_exact_conditions_and_retained_versions():
    client = FakeClient()
    transport = s3.Boto3S3Transport(BINDING, client=client)
    evidence = transport.qualify_backend()
    assert evidence.binding == BINDING
    assert evidence.key.startswith(BINDING.prefix + ".qualification/")
    assert transport.qualification_key == evidence.key
    assert len(evidence.versions) == 2
    assert len(client.versions) == 2
    assert not client.objects
    assert not isinstance(evidence, store.Qualification)
    assert not hasattr(evidence, "writer_exclusion")
    puts = [p for method, p in client.calls if method == "put_object"]
    assert len(puts) == 4
    assert puts[0] == {
        "Bucket": BINDING.bucket,
        "Key": evidence.key,
        "Body": b"qualification-create",
        "ContentLength": 20,
        "ServerSideEncryption": "AES256",
        "IfNoneMatch": "*",
    }
    assert puts[1]["IfNoneMatch"] == "*"
    assert puts[2]["IfMatch"] == puts[3]["IfMatch"]
    assert all(p["ServerSideEncryption"] == "AES256" for p in puts)
    assert all(p.get("Key", evidence.key) == evidence.key for _, p in client.calls)
    assert all("VersionId" not in p for method, p in client.calls if method == "delete_object")
    assert all(body.closed for body in client.bodies)


@pytest.mark.parametrize("versioning", [None, "Suspended", "Disabled", ""])
def test_unqualified_versioning_failclosed(versioning):
    client = FakeClient()
    client.versioning = versioning
    transport = s3.Boto3S3Transport(BINDING, client=client)
    with pytest.raises(store.StoreError):
        transport.qualify_backend()
    assert [m for m, _ in client.calls] == ["get_bucket_versioning"]
    with pytest.raises(store.StoreError, match="blocked"):
        transport.create_blob(BINDING, KEY, b"no")


@pytest.mark.parametrize("setting", ["enforce_create", "enforce_update"])
def test_preconditions_not_enforced_blocks_and_retains(setting):
    client = FakeClient()
    setattr(client, setting, False)
    transport = s3.Boto3S3Transport(BINDING, client=client)
    with pytest.raises(store.StoreError, match="qualification failed"):
        transport.qualify_backend()
    assert transport.evidence is None
    assert transport.qualification_key
    assert client.versions
    assert not any(m == "delete_object" for m, _ in client.calls)


@pytest.mark.parametrize("encryption", [None, "aws:kms", ""])
def test_encryption_missing_blocks(encryption):
    client = FakeClient()
    client.encryption = encryption
    transport = s3.Boto3S3Transport(BINDING, client=client)
    with pytest.raises(store.StoreError):
        transport.qualify_backend()
    assert transport.evidence is None


def test_normal_operations_require_qualification():
    client = FakeClient()
    transport = s3.Boto3S3Transport(BINDING, client=client)
    with pytest.raises(store.StoreError, match="qualification required"):
        transport.get_blob(BINDING, KEY)
    assert not client.calls


def test_blob_create_get_update_exact_metadata(qualified):
    transport, client = qualified
    first = transport.create_blob(BINDING, KEY, SENTINEL.encode())
    assert SENTINEL not in repr(first)
    assert first.data == SENTINEL.encode()
    assert transport.get_blob(BINDING, KEY) == first
    second = transport.update_blob(BINDING, KEY, b"new", first.version)
    assert first.version != second.version
    assert transport.get_blob(BINDING, KEY, version=first.version) == first
    puts = [p for method, p in client.calls if method == "put_object"]
    assert len(puts) == 2
    assert puts[0]["IfNoneMatch"] == "*"
    assert puts[1]["IfMatch"] == s3._untoken(first.version)[1]
    exact_gets = [p for m, p in client.calls if m == "get_object" and "VersionId" in p]
    assert exact_gets[0] == {
        "Bucket": BINDING.bucket,
        "Key": KEY,
        "VersionId": s3._untoken(first.version)[0],
        "IfMatch": s3._untoken(first.version)[1],
    }


def test_stale_version_does_not_put(qualified):
    transport, client = qualified
    first = transport.create_blob(BINDING, KEY, b"first")
    transport.update_blob(BINDING, KEY, b"second", first.version)
    client.calls.clear()
    with pytest.raises(store.PreconditionFailed):
        transport.update_blob(BINDING, KEY, b"stale", first.version)
    assert not any(m == "put_object" for m, _ in client.calls)


def test_missing_key_only_authoritative_nosuchkey(qualified):
    transport, client = qualified
    assert transport.get_blob(BINDING, KEY) is None
    client.failure = "get_object"
    with pytest.raises(store.StoreError) as caught:
        transport.get_blob(BINDING, KEY)
    assert SENTINEL not in str(caught.value)
    assert caught.value.__suppress_context__


@pytest.mark.parametrize(
    "field,value",
    [
        ("endpoint", "http://s3.us-east-1.wasabisys.com"),
        ("endpoint", "https://s3.us-east-1.wasabisys.com.evil.test"),
        ("endpoint", "https://s3.us-east-1.wasabisys.com:443"),
        ("endpoint", "https://s3.eu-central-1.wasabisys.com"),
        ("endpoint", "https://user@s3.us-east-1.wasabisys.com"),
        ("endpoint", "https://s3.us-east-1.wasabisys.com/path"),
        ("endpoint", "https://s3.us-east-1.wasabisys.com?redirect=yes"),
        ("region", "us-east-2"),
        ("bucket", "127.0.0.1"),
        ("bucket", "a..b"),
        ("prefix", "canary/../test/"),
        ("prefix", "canary/%2F/"),
    ],
)
def test_invalid_bindings_do_not_connect(field, value):
    with pytest.raises(store.StoreError):
        s3.Boto3S3Transport(replace(BINDING, **{field: value}), client=FakeClient())


@pytest.mark.parametrize(
    "key",
    [
        "other/checkpoint",
        "canary/test/../x",
        KEY + "?query",
        BINDING.prefix,
        BINDING.prefix + ".qualification/x",
    ],
)
def test_out_of_scope_keys_never_call(qualified, key):
    transport, client = qualified
    with pytest.raises(store.StoreError):
        transport.get_blob(BINDING, key)
    assert not client.calls


def test_binding_identity_cannot_change(qualified):
    transport, client = qualified
    with pytest.raises(store.StoreError, match="binding mismatch"):
        transport.get_blob(replace(BINDING, runtime_identity="other"), KEY)
    assert not client.calls


@pytest.mark.parametrize(
    "field,value",
    [("VersionId", None), ("VersionId", "null"), ("ETag", None), ("ServerSideEncryption", None)],
)
def test_missing_put_metadata_blocks_without_retry(qualified, field, value):
    transport, client = qualified
    client.response_mutation = lambda kind, r: r.update({field: value}) if kind == "put" else None
    with pytest.raises(store.StoreError):
        transport.create_blob(BINDING, KEY, b"test")
    assert sum(m == "put_object" for m, _ in client.calls) == 1
    with pytest.raises(store.StoreError, match="blocked"):
        transport.create_blob(BINDING, KEY, b"test")


@pytest.mark.parametrize(
    "field,value",
    [
        ("ContentLength", 99999999),
        ("ContentLength", 0),
        ("ContentLength", True),
        ("VersionId", "null"),
        ("ServerSideEncryption", "aws:kms"),
    ],
)
def test_bounded_read_rejects_invalid_metadata(qualified, field, value):
    transport, client = qualified
    transport.create_blob(BINDING, KEY, b"payload")
    client.response_mutation = lambda kind, r: r.update({field: value}) if kind == "get" else None
    with pytest.raises(store.StoreError):
        transport.get_blob(BINDING, KEY)
    assert client.bodies[-1].closed


def test_unknown_write_sanitized_never_retried(qualified):
    transport, client = qualified
    client.failure = "put_object"
    with pytest.raises(store.StoreError) as caught:
        transport.create_blob(BINDING, KEY, b"payload")
    assert SENTINEL not in str(caught.value)
    assert sum(m == "put_object" for m, _ in client.calls) == 1
    with pytest.raises(store.StoreError, match="blocked"):
        transport.get_blob(BINDING, KEY)


def test_qualification_cleanup_failure_retains_version_evidence():
    client = FakeClient()
    client.failure = "delete_object"
    transport = s3.Boto3S3Transport(BINDING, client=client)
    with pytest.raises(store.StoreError) as caught:
        transport.qualify_backend()
    assert SENTINEL not in str(caught.value)
    assert len(transport.qualification_versions) == 2
    assert len(client.versions) == 2
    assert transport.qualification_key in client.objects
    assert sum(m == "delete_object" for m, _ in client.calls) == 1
    with pytest.raises(store.StoreError):
        transport.qualify_backend()


def test_read_size_bounded_even_if_stream_exceeds_content_length(qualified):
    transport, client = qualified
    transport.create_blob(BINDING, KEY, b"payload")
    amounts = []

    class Stream:
        closed = False

        def read(self, amount):
            amounts.append(amount)
            return b"x" * amount

        def close(self):
            self.closed = True

    stream = Stream()
    client.response_mutation = lambda kind, row: row.update(Body=stream) if kind == "get" else None
    with pytest.raises(store.StoreError):
        transport.get_blob(BINDING, KEY)
    assert amounts == [transport.max_bytes + 1]
    assert stream.closed


def test_access_denied_is_not_absence(qualified, monkeypatch):
    transport, client = qualified

    def denied(**kwargs):
        raise error(403, "AccessDenied")

    monkeypatch.setattr(client, "get_object", denied)
    with pytest.raises(store.StoreError):
        transport.get_blob(BINDING, KEY)


def test_oversize_payload_rejected_before_network(qualified):
    transport, client = qualified
    with pytest.raises(store.StoreError, match="payload"):
        transport.create_blob(BINDING, KEY, b"x" * (transport.max_bytes + 1))
    assert not client.calls


def test_create_conflict_definitive_no_retry(qualified):
    transport, client = qualified
    transport.create_blob(BINDING, KEY, b"first")
    client.calls.clear()
    with pytest.raises(store.PreconditionFailed):
        transport.create_blob(BINDING, KEY, b"second")
    assert sum(m == "put_object" for m, _ in client.calls) == 1


def test_versioning_suspended_after_qualification_blocks_write(qualified):
    transport, client = qualified
    client.versioning = "Suspended"
    with pytest.raises(store.StoreError, match="versioning"):
        transport.create_blob(BINDING, KEY, b"first")
    assert not any(m == "put_object" for m, _ in client.calls)


def test_disposable_native_lock_cleanup_preserves_versions(qualified):
    transport, client = qualified
    key = BINDING.prefix + "qualification/owned/terraform.tfstate.tflock"
    holder = transport.create_blob(BINDING, key, b"synthetic-lock")
    client.calls.clear()
    assert transport.delete_blob(BINDING, key, holder.version) is None
    deleted = [p for m, p in client.calls if m == "delete_object"]
    assert deleted == [
        {"Bucket": BINDING.bucket, "Key": key, "IfMatch": s3._untoken(holder.version)[1]}
    ]
    assert (key, s3._untoken(holder.version)[0]) in client.versions
    assert key not in client.objects


def test_lock_cleanup_wrong_version_never_deletes(qualified):
    transport, client = qualified
    key = BINDING.prefix + "qualification/owned/terraform.tfstate.tflock"
    first = transport.create_blob(BINDING, key, b"first")
    transport.update_blob(BINDING, key, b"second", first.version)
    client.calls.clear()
    with pytest.raises(store.PreconditionFailed):
        transport.delete_blob(BINDING, key, first.version)
    assert not any(m == "delete_object" for m, _ in client.calls)


@pytest.mark.parametrize(
    "key",
    [KEY, BINDING.prefix + "maintenance.json", BINDING.prefix + "qualification/owned/checkpoint"],
)
def test_no_ledger_or_checkpoint_deletion(qualified, key):
    transport, client = qualified
    with pytest.raises(store.StoreError, match="disposable"):
        transport.delete_blob(BINDING, key, s3._token("v1", '"etag"'))
    assert not client.calls


def test_lock_cleanup_unknown_blocks_no_retry(qualified):
    transport, client = qualified
    key = BINDING.prefix + "qualification/owned/terraform.tfstate.tflock"
    holder = transport.create_blob(BINDING, key, b"lock")
    client.calls.clear()
    client.failure = "delete_object"
    with pytest.raises(store.StoreError) as caught:
        transport.delete_blob(BINDING, key, holder.version)
    assert SENTINEL not in str(caught.value)
    assert sum(m == "delete_object" for m, _ in client.calls) == 1
    with pytest.raises(store.StoreError, match="blocked"):
        transport.get_blob(BINDING, key)


def test_strict_ledger_helpers_roundtrip_and_reject_unknown_schema(qualified):
    transport, client = qualified
    prefix = "gha-1794700000-123-1"
    run = store.RunIdentity(
        prefix,
        "a" * 40,
        "b" * 32,
        "solomonhd.ai",
        (
            (f"{prefix}.txt.ci.solomonhd.ai", "TXT"),
            (f"{prefix}.cname.ci.solomonhd.ai", "CNAME"),
        ),
    )
    ledger = store.Ledger(run, "owner", 0, "empty")
    key = BINDING.prefix + "maintenance.json"
    stored = transport.create_if_absent(BINDING, key, ledger)
    assert stored.ledger == ledger
    assert transport.get(BINDING, key) == stored
    next_ledger = replace(ledger, generation=1, receipts=(store.Receipt("create", "empty"),))
    updated = transport.update_if_version(BINDING, key, next_ledger, stored.version)
    assert updated.ledger == next_ledger
    transport.create_blob(BINDING, KEY, b'{"schema":999,"kind":"ledger","body":{}}')
    with pytest.raises(store.StoreError):
        transport.get(BINDING, KEY)


def test_archive_immutable_strict_helpers(qualified):
    transport, client = qualified
    prefix = "gha-1794700000-123-1"
    run = store.RunIdentity(
        prefix,
        "a" * 40,
        "b" * 32,
        "solomonhd.ai",
        (
            (f"{prefix}.txt.ci.solomonhd.ai", "TXT"),
            (f"{prefix}.cname.ci.solomonhd.ai", "CNAME"),
        ),
    )
    ledger = store.Ledger(
        run,
        "owner",
        4,
        "empty",
        (
            store.Receipt("destroy", "empty", "succeeded", "empty"),
            store.Receipt("absence", "empty", "succeeded", "empty"),
        ),
    )
    receipt = store.CompletedReceipt(ledger, "claim-version")
    key = BINDING.prefix + f"runs/{prefix}/completed.json"
    stored = transport.create_archive(BINDING, key, receipt)
    assert stored.receipt == receipt
    assert transport.get_archive(BINDING, key) == stored
    with pytest.raises(store.PreconditionFailed):
        transport.create_archive(BINDING, key, receipt)
    assert not any(m == "delete_object" for m, _ in client.calls)


def test_default_client_runtime_gate_no_ambient_credential_discovery(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", SENTINEL)
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", SENTINEL)
    with pytest.raises(store.StoreError, match="Dagger runtime"):
        s3.Boto3S3Transport(BINDING)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY")
    with pytest.raises(store.StoreError, match="runtime S3 credentials"):
        s3.Boto3S3Transport(BINDING, runtime=True, runtime_check=lambda: True)
    with pytest.raises(store.StoreError, match="Dagger runtime"):
        s3.Boto3S3Transport(BINDING, runtime=True, runtime_check=lambda: False)


def test_default_client_exact_config_no_retries_or_proxies(monkeypatch):
    import boto3

    calls = []
    events = []
    fake = SimpleNamespace(
        meta=SimpleNamespace(events=SimpleNamespace(register=lambda *a: events.append(a)))
    )

    def make_client(*args, **kwargs):
        calls.append((args, kwargs))
        fake.meta.config = kwargs["config"]
        fake.meta.endpoint_url = kwargs["endpoint_url"]
        fake.meta.region_name = kwargs["region_name"]
        return fake

    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "synthetic-access")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", SENTINEL)
    monkeypatch.delenv("AWS_SESSION_TOKEN", raising=False)
    monkeypatch.setattr(boto3, "client", make_client)
    transport = s3.Boto3S3Transport(BINDING, runtime=True, runtime_check=lambda: True)
    args, kwargs = calls[0]
    assert args == ("s3",)
    assert kwargs["endpoint_url"] == BINDING.endpoint
    assert kwargs["region_name"] == BINDING.region
    assert kwargs["verify"] is True
    config = kwargs["config"]
    assert config.retries == {"total_max_attempts": 1, "mode": "standard"}
    assert config.connect_timeout == 3 and config.read_timeout == 5
    assert config.signature_version == "s3v4"
    assert config.s3 == {"addressing_style": "path"}
    assert config.proxies == {}
    assert events[0][0] == "before-send.s3"
    for url in [
        "http://s3.us-east-1.wasabisys.com/x",
        "https://evil.test/x",
        BINDING.endpoint + "/another-bucket/x",
    ]:
        with pytest.raises(store.StoreError):
            transport._check_destination(SimpleNamespace(url=url))


@pytest.mark.parametrize(
    "change", ["endpoint", "region", "retries", "proxy", "addressing", "timeout"]
)
def test_injected_real_client_cannot_change_binding_or_policy(change):
    from botocore.config import Config

    values = {
        "signature_version": "s3v4",
        "connect_timeout": 3,
        "read_timeout": 5,
        "retries": {"total_max_attempts": 1},
        "proxies": {},
        "s3": {"addressing_style": "path"},
    }
    if change == "retries":
        values["retries"] = {"total_max_attempts": 2}
    if change == "proxy":
        values["proxies"] = {"https": "https://untrusted.invalid"}
    if change == "addressing":
        values["s3"] = {"addressing_style": "virtual"}
    if change == "timeout":
        values["read_timeout"] = 60
    fake = SimpleNamespace(
        meta=SimpleNamespace(
            endpoint_url="https://other.invalid" if change == "endpoint" else BINDING.endpoint,
            region_name="us-east-2" if change == "region" else BINDING.region,
            config=Config(**values),
            events=SimpleNamespace(register=lambda *a: None),
        )
    )
    with pytest.raises(store.StoreError, match="Injected S3 client"):
        s3.Boto3S3Transport(BINDING, client=fake)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_bytes": 0},
        {"max_bytes": True},
        {"max_bytes": 16777217},
        {"connect_timeout": 0},
        {"read_timeout": float("inf")},
        {"read_timeout": "bad"},
    ],
)
def test_invalid_limits_failclosed(kwargs):
    with pytest.raises(store.StoreError):
        s3.Boto3S3Transport(BINDING, client=FakeClient(), **kwargs)
