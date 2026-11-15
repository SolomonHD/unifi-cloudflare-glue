"""Bounded Wasabi transport. Qualification is explicit and never qualifies other writers.

The runtime caller must instantiate the default client inside its Dagger container,
after injecting credentials there. No credential discovery, recovery, retry, or
production endpoint selection is performed here. Unknown writes require operator
reconciliation; immutable versions are never permanently deleted.
"""

import json
import math
import os
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit

from . import canary_store as store


def _in_dagger() -> bool:
    # Diagnostic execution guard created by the reviewed Dagger graph before
    # secret injection, not proof of authorization or writer exclusion.
    return Path("/run/canary/runtime-marker").is_file()


@dataclass(frozen=True)
class StoredBlob:
    data: bytes = field(repr=False)
    version: str


@dataclass(frozen=True)
class S3QualificationEvidence:
    binding: store.StoreBinding
    key: str
    versions: tuple[str, str]
    cleanup_version: str
    # Deliberately not a store.Qualification: no locking/access/exclusion claims.


def _token(version: object, etag: object) -> str:
    if (
        not isinstance(version, str)
        or not version
        or version == "null"
        or len(version) > 768
        or not version.isascii()
        or not version.isprintable()
        or not isinstance(etag, str)
        or re.fullmatch(r'"[A-Za-z0-9-]{1,128}"', etag) is None
    ):
        raise store.StoreError("S3 durable version metadata invalid")
    token = json.dumps([version, etag], separators=(",", ":"))
    if len(token) > 1024:
        raise store.StoreError("S3 durable version metadata invalid")
    return token


def _untoken(token: str) -> tuple[str, str]:
    try:
        if not isinstance(token, str) or len(token) > 1024:
            raise ValueError
        values = json.loads(token)
        if not isinstance(values, list) or len(values) != 2:
            raise ValueError
        if _token(*values) != token:
            raise ValueError
        return values[0], values[1]
    except Exception:
        raise store.StoreError("S3 opaque version invalid") from None


class Boto3S3Transport:
    def __init__(
        self,
        binding: store.StoreBinding,
        *,
        client: Any = None,
        runtime: bool = False,
        runtime_check: Callable[[], bool] = _in_dagger,
        connect_timeout: float = 3,
        read_timeout: float = 5,
        max_bytes: int = 1048576,
    ) -> None:
        binding.validate()
        url = urlsplit(binding.endpoint)
        hosts = {f"s3.{binding.region}.wasabisys.com"}
        if binding.region == "us-east-1":
            hosts.add("s3.wasabisys.com")
        if (
            re.fullmatch(r"[a-z]{2}-[a-z]+-[1-9][0-9]*", binding.region) is None
            or url.hostname not in hosts
            or url.netloc != url.hostname
            or re.fullmatch(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]", binding.bucket) is None
            or ".." in binding.bucket
            or re.fullmatch(r"[0-9.]+", binding.bucket)
            or re.fullmatch(r"[A-Za-z0-9_/-]+", binding.prefix) is None
        ):
            raise store.StoreError("Exact HTTPS Wasabi binding required")
        if (
            type(max_bytes) is not int
            or not 1 <= max_bytes <= 16777216
            or any(
                type(n) not in (int, float) or not math.isfinite(n) or not 0 < n <= 30
                for n in (connect_timeout, read_timeout)
            )
        ):
            raise store.StoreError("Invalid bounded S3 configuration")
        self.binding = binding
        self.max_bytes = max_bytes
        self._qualified = False
        self._qualifying = False
        self._blocked = False
        self.evidence: S3QualificationEvidence | None = None
        self.qualification_key: str | None = None
        self.qualification_versions: tuple[str, ...] = ()
        if client is None:
            try:
                permitted = runtime is True and runtime_check() is True
            except Exception:
                permitted = False
            if not permitted:
                raise store.StoreError("Default S3 client requires Dagger runtime credentials")
            access = os.environ.get("AWS_ACCESS_KEY_ID")
            secret = os.environ.get("AWS_SECRET_ACCESS_KEY")
            if not access or not secret or os.environ.get("AWS_SESSION_TOKEN"):
                raise store.StoreError("Explicit runtime S3 credentials required")
            try:
                import boto3  # type: ignore[import-untyped]
                from botocore.config import Config  # type: ignore[import-untyped]

                client = boto3.client(
                    "s3",
                    endpoint_url=binding.endpoint,
                    region_name=binding.region,
                    verify=True,
                    aws_access_key_id=access,
                    aws_secret_access_key=secret,
                    config=Config(
                        signature_version="s3v4",
                        connect_timeout=connect_timeout,
                        read_timeout=read_timeout,
                        retries={"total_max_attempts": 1, "mode": "standard"},
                        proxies={},
                        s3={"addressing_style": "path"},
                    ),
                )
            except Exception:
                raise store.StoreError("S3 runtime client configuration failed") from None
        # Real injected boto clients must obey the same binding and I/O policy.
        # A metadata-free client is the explicit offline test transport seam.
        if getattr(client, "meta", None) is not None:
            try:
                config = client.meta.config
                if (
                    client.meta.endpoint_url != binding.endpoint
                    or client.meta.region_name != binding.region
                    or config.signature_version != "s3v4"
                    or config.retries.get("total_max_attempts") != 1
                    or config.connect_timeout != connect_timeout
                    or config.read_timeout != read_timeout
                    or config.proxies != {}
                    or config.s3.get("addressing_style") != "path"
                ):
                    raise ValueError
                client.meta.events.register("before-send.s3", self._check_destination)
            except Exception:
                raise store.StoreError(
                    "Injected S3 client does not match bounded binding"
                ) from None
        self._client = client

    def _check_destination(self, request: Any, **kwargs: Any) -> None:
        url = urlsplit(request.url)
        expected = urlsplit(self.binding.endpoint)
        root = "/" + self.binding.bucket
        if (
            url.scheme != "https"
            or url.netloc != expected.netloc
            or not (url.path == root or url.path.startswith(root + "/" + self.binding.prefix))
        ):
            raise store.StoreError("S3 destination changed; reconciliation required")

    def _gate(self, binding: store.StoreBinding, key: str) -> None:
        if self._blocked:
            raise store.StoreError(
                "S3 transport blocked; explicit operator reconciliation required"
            )
        if binding != self.binding:
            raise store.StoreError("S3 binding mismatch")
        if (
            not isinstance(key, str)
            or not key.startswith(binding.prefix)
            or key == binding.prefix
            or len(key.encode()) > 1024
            or any(part in ("", ".", "..") for part in key.split("/"))
            or re.fullmatch(r"[A-Za-z0-9_./-]+", key) is None
            or (key.startswith(binding.prefix + ".qualification/") and not self._qualifying)
        ):
            raise store.StoreError("S3 key outside exact canary prefix")
        if not self._qualified and not self._qualifying:
            raise store.StoreError("S3 backend qualification required")

    def _call(self, method: str, **params: Any) -> Any:
        try:
            result = getattr(self._client, method)(Bucket=self.binding.bucket, **params)
            if not isinstance(result, dict):
                raise ValueError
            return result
        except Exception as error:
            try:
                response = getattr(error, "response", {})
                status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
                code = response.get("Error", {}).get("Code")
            except Exception:
                status, code = None, None
            if status == 412 and code in ("PreconditionFailed", "412"):
                raise store.PreconditionFailed() from None
            if method == "get_object" and status == 404 and code == "NoSuchKey":
                return None
            self._blocked = True
            raise store.StoreError(
                "S3 operation uncertain or rejected; retain recovery identity"
            ) from None

    def _versioning(self) -> None:
        response = self._call("get_bucket_versioning")
        if response.get("Status") != "Enabled":
            self._blocked = True
            raise store.StoreError("S3 bucket versioning must be Enabled")

    def get_blob(
        self, binding: store.StoreBinding, key: str, *, version: str | None = None
    ) -> StoredBlob | None:
        self._gate(binding, key)
        params: dict[str, Any] = {"Key": key}
        if version is not None:
            params["VersionId"], params["IfMatch"] = _untoken(version)
        response = self._call("get_object", **params)
        if response is None:
            return None
        body = response.get("Body")
        try:
            length = response.get("ContentLength")
            if (
                type(length) is not int
                or not 0 <= length <= self.max_bytes
                or response.get("ServerSideEncryption") != "AES256"
            ):
                raise ValueError
            actual = _token(response.get("VersionId"), response.get("ETag"))
            if version is not None and actual != version:
                raise ValueError
            data = body.read(self.max_bytes + 1)
            if not isinstance(data, bytes) or len(data) != length or len(data) > self.max_bytes:
                raise ValueError
            return StoredBlob(data, actual)
        except Exception:
            self._blocked = True
            raise store.StoreError("S3 bounded encrypted readback invalid") from None
        finally:
            if body is not None:
                try:
                    body.close()
                except Exception:
                    self._blocked = True
                    raise store.StoreError("S3 response close failed") from None

    def _put(
        self, binding: store.StoreBinding, key: str, data: bytes, version: str | None
    ) -> StoredBlob:
        self._gate(binding, key)
        if not isinstance(data, bytes) or len(data) > self.max_bytes:
            raise store.StoreError("S3 payload exceeds bounded bytes")
        self._versioning()
        params: dict[str, Any] = {
            "Key": key,
            "Body": data,
            "ContentLength": len(data),
            "ServerSideEncryption": "AES256",
        }
        if version is None:
            params["IfNoneMatch"] = "*"
        else:
            old_id, params["IfMatch"] = _untoken(version)
            current = self.get_blob(binding, key)
            if current is None or current.version != version:
                raise store.PreconditionFailed()
        response = self._call("put_object", **params)
        try:
            if response.get("ServerSideEncryption") != "AES256":
                raise ValueError
            token = _token(response.get("VersionId"), response.get("ETag"))
            if version is not None and (token == version or _untoken(token)[0] == old_id):
                raise ValueError
            expected = StoredBlob(data, token)
            if self.get_blob(binding, key, version=token) != expected:
                raise ValueError
            if self.get_blob(binding, key) != expected:
                raise ValueError
            return expected
        except Exception:
            self._blocked = True
            raise store.StoreError(
                "S3 durable write confirmation invalid; retain recovery identity"
            ) from None

    def create_blob(self, binding: store.StoreBinding, key: str, data: bytes) -> StoredBlob:
        return self._put(binding, key, data, None)

    def update_blob(
        self, binding: store.StoreBinding, key: str, data: bytes, expected_version: str
    ) -> StoredBlob:
        return self._put(binding, key, data, expected_version)

    def delete_blob(self, binding: store.StoreBinding, key: str, expected_version: str) -> None:
        """Hide only an owned disposable native-lock probe, retaining every version."""
        self._gate(binding, key)
        if not key.startswith(binding.prefix + "qualification/") or not key.endswith(
            "/terraform.tfstate.tflock"
        ):
            raise store.StoreError("Only disposable qualification lock cleanup permitted")
        old_id, etag = _untoken(expected_version)
        self._versioning()
        current = self.get_blob(binding, key)
        if current is None or current.version != expected_version:
            raise store.PreconditionFailed()
        response = self._call("delete_object", Key=key, IfMatch=etag)
        try:
            marker = response.get("VersionId")
            _token(marker, etag)
            if (
                response.get("DeleteMarker") is not True
                or marker == old_id
                or self.get_blob(binding, key) is not None
                or self.get_blob(binding, key, version=expected_version) != current
            ):
                raise ValueError
        except Exception:
            self._blocked = True
            raise store.StoreError(
                "S3 lock cleanup unconfirmed; retain recovery identity"
            ) from None

    def get(self, binding: store.StoreBinding, key: str) -> store.StoredLedger | None:
        blob = self.get_blob(binding, key)
        return (
            None
            if blob is None
            else store.StoredLedger(store.decode_ledger(blob.data), blob.version)
        )

    def create_if_absent(
        self, binding: store.StoreBinding, key: str, ledger: store.Ledger
    ) -> store.StoredLedger:
        blob = self.create_blob(binding, key, store.encode_ledger(ledger))
        return store.StoredLedger(store.decode_ledger(blob.data), blob.version)

    def update_if_version(
        self, binding: store.StoreBinding, key: str, ledger: store.Ledger, expected_version: str
    ) -> store.StoredLedger:
        blob = self.update_blob(binding, key, store.encode_ledger(ledger), expected_version)
        return store.StoredLedger(store.decode_ledger(blob.data), blob.version)

    def get_archive(self, binding: store.StoreBinding, key: str) -> store.StoredArchive | None:
        blob = self.get_blob(binding, key)
        return (
            None
            if blob is None
            else store.StoredArchive(store.decode_archive(blob.data), blob.version)
        )

    def create_archive(
        self, binding: store.StoreBinding, key: str, receipt: store.CompletedReceipt
    ) -> store.StoredArchive:
        blob = self.create_blob(binding, key, store.encode_archive(receipt))
        return store.StoredArchive(store.decode_archive(blob.data), blob.version)

    def qualify_backend(self) -> S3QualificationEvidence:
        if self._blocked or self._qualified or self._qualifying:
            raise store.StoreError("S3 qualification unavailable; retain existing evidence")
        key = self.binding.prefix + ".qualification/" + uuid.uuid4().hex + "/probe"
        self.qualification_key = key
        self._qualifying = True
        try:
            self._versioning()
            first = self.create_blob(self.binding, key, b"qualification-create")
            self.qualification_versions = (first.version,)
            try:
                self.create_blob(self.binding, key, b"competing-create")
            except store.PreconditionFailed:
                pass
            else:
                raise store.StoreError("S3 conditional create not enforced")
            second = self.update_blob(self.binding, key, b"qualification-update", first.version)
            self.qualification_versions = (first.version, second.version)
            # Direct stale PUT proves server-side rejection, not our local version check.
            try:
                self._call(
                    "put_object",
                    Key=key,
                    Body=b"stale-update",
                    ContentLength=12,
                    IfMatch=_untoken(first.version)[1],
                    ServerSideEncryption="AES256",
                )
            except store.PreconditionFailed:
                pass
            else:
                raise store.StoreError("S3 conditional update not enforced")
            if self.get_blob(self.binding, key) != second:
                raise store.StoreError("S3 qualification readback changed")
            if self.get_blob(self.binding, key, version=first.version) != first:
                raise store.StoreError("S3 historical version unavailable")
            # A delete marker hides only this disposable key. All versions remain.
            deleted = self._call("delete_object", Key=key)
            marker = deleted.get("VersionId")
            if (
                deleted.get("DeleteMarker") is not True
                or not isinstance(marker, str)
                or marker in ("", "null")
            ):
                raise store.StoreError("S3 qualification cleanup unconfirmed")
            if (
                self.get_blob(self.binding, key) is not None
                or self.get_blob(self.binding, key, version=first.version) != first
                or self.get_blob(self.binding, key, version=second.version) != second
            ):
                raise store.StoreError("S3 qualification retention unconfirmed")
            self.evidence = S3QualificationEvidence(
                self.binding, key, (first.version, second.version), marker
            )
            self._qualified = True
            return self.evidence
        except Exception:
            self._blocked = True
            raise store.StoreError(
                "S3 qualification failed; retain qualification prefix for reconciliation"
            ) from None
        finally:
            self._qualifying = False
