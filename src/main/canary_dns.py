"""Bounded, read-only canary DNS verification; no requests run at import time.

Injected transports/resolvers must honor their supplied timeout. Runtime callers
provide a public resolver; no system resolver with an unbounded timeout is used.
Ownership, writer fencing and deletion authorization belong to the lifecycle.
"""

import json
import math
import os
import queue
import re
import threading
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Protocol
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from .canary_identity import (
    RESOURCE_TYPE,
    ZONE_NAME,
    validate_canary_record,
    validate_record_name,
    validate_run_prefix,
)

API_ROOT = "https://api.cloudflare.com/client/v4"
MAX_RESPONSE_BYTES = 65536
PAGE_SIZE = 100
_ID = re.compile(r"[0-9a-f]{32}")


class DNSValidationError(ValueError):
    """A fixed diagnostic code, never a provider message or supplied value."""


@dataclass(frozen=True)
class HTTPResponse:
    status: int
    body: bytes = field(repr=False)


class HTTPTransport(Protocol):
    def __call__(
        self, url: str, headers: dict[str, str], timeout: float, max_bytes: int
    ) -> HTTPResponse: ...


class PublicResolver(Protocol):
    def __call__(self, name: str, record_type: str, timeout: float) -> Sequence[str]: ...


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


def stdlib_transport(
    url: str, headers: dict[str, str], timeout: float, max_bytes: int
) -> HTTPResponse:
    """One HTTPS GET, no redirects/proxies/retries, with bounded body and I/O wait."""
    failed = False
    response: HTTPResponse | None = None
    try:
        opener = build_opener(ProxyHandler({}), _NoRedirect())
        with opener.open(Request(url, headers=headers, method="GET"), timeout=timeout) as result:
            response = HTTPResponse(result.status, result.read(max_bytes + 1))
    except Exception:
        failed = True
    if failed or response is None:
        raise DNSValidationError("http_transport_failed")
    return response


def _positive_seconds(value: float, maximum: float = 300) -> None:
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 < value <= maximum:
        raise DNSValidationError("invalid_time_bound")


def _valid_id(value: object) -> bool:
    return isinstance(value, str) and _ID.fullmatch(value) is not None


def _runtime_token() -> str:
    return os.environ.get("CLOUDFLARE_API_TOKEN", "")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DNSValidationError("duplicate_json_key")
        result[key] = value
    return result


@dataclass(frozen=True)
class ExpectedRecord:
    record_id: str
    name: str
    record_type: str
    content: str = field(repr=False)
    proxied: bool = False


@dataclass(frozen=True)
class ZoneMetadata:
    zone_id: str
    name: str


@dataclass(frozen=True)
class RecordMetadata:
    record_id: str
    name: str
    record_type: str
    proxied: bool


def _validate_expected(expected: ExpectedRecord, run_prefix: str, zone_id: str) -> None:
    validate_canary_record(
        run_prefix=run_prefix,
        name=expected.name,
        zone_name=ZONE_NAME,
        zone_id=zone_id,
        expected_zone_id=zone_id,
        record_type=expected.record_type,
        proxied=expected.proxied,
        resource_type=RESOURCE_TYPE,
    )
    if (
        not _valid_id(expected.record_id)
        or not isinstance(expected.content, str)
        or not expected.content
        or len(expected.content) > 2048
        or any(ord(char) < 32 or ord(char) > 126 for char in expected.content)
    ):
        raise DNSValidationError("invalid_record_expectation")
    if expected.record_type == "CNAME":
        if expected.content not in {
            "example.com",
            "example.org",
            f"{run_prefix}.txt.ci.solomonhd.ai",
        }:
            raise DNSValidationError("invalid_cname_target")


class CloudflareDoHResolver:
    """Bounded DNS JSON reads at one fixed HTTPS resolver, without credentials."""

    def __init__(
        self,
        run_prefix: str,
        *,
        transport: HTTPTransport = stdlib_transport,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.run_prefix = validate_run_prefix(run_prefix)
        self._transport = transport
        self._clock = clock

    def __call__(self, name: str, record_type: str, timeout: float) -> Sequence[str]:
        validate_record_name(name, self.run_prefix)
        if record_type not in ("TXT", "CNAME") or name.split(".")[1] != record_type.lower():
            raise DNSValidationError("invalid_dns_query")
        _positive_seconds(timeout, 30)
        deadline = self._clock() + timeout
        responses: queue.Queue[HTTPResponse | None] = queue.Queue(maxsize=1)

        def request() -> None:
            response = None
            try:
                response = self._transport(
                    "https://cloudflare-dns.com/dns-query?"
                    + urlencode({"name": name, "type": record_type}),
                    {"Accept": "application/dns-json"},
                    timeout,
                    MAX_RESPONSE_BYTES,
                )
            except Exception:
                pass
            responses.put_nowait(response)

        # urllib's socket timeout does not bound getaddrinfo or a slow trickle.
        # Bound the caller's total wait too. A timed-out read-only worker may
        # finish later, but never publishes anything or blocks process exit.
        threading.Thread(target=request, daemon=True).start()
        try:
            response = responses.get(timeout=timeout)
        except queue.Empty:
            raise DNSValidationError("dns_deadline_exceeded") from None
        if self._clock() >= deadline:
            raise DNSValidationError("dns_deadline_exceeded")
        if (
            not isinstance(response, HTTPResponse)
            or response.status != 200
            or len(response.body) > MAX_RESPONSE_BYTES
        ):
            raise DNSValidationError("dns_response_failed")
        payload = None
        try:
            payload = json.loads(response.body, object_pairs_hook=_unique_object)
        except Exception:
            pass
        code = {"TXT": 16, "CNAME": 5}[record_type]
        if (
            not isinstance(payload, dict)
            or type(payload.get("Status")) is not int
            or payload["Status"] != 0
            or payload.get("TC") is not False
            or payload.get("Question") != [{"name": name, "type": code}]
            or not isinstance(payload.get("Answer", []), list)
        ):
            raise DNSValidationError("dns_response_shape")
        answers = []
        for answer in payload.get("Answer", []):
            if not isinstance(answer, dict) or not isinstance(answer.get("name"), str):
                raise DNSValidationError("dns_answer_shape")
            # CNAME responses may include the target's address records. Never use
            # those records as evidence for the queried name/type.
            if answer["name"].removesuffix(".").lower() != name or answer.get("type") != code:
                continue
            data = answer.get("data")
            if not isinstance(data, str) or len(data) > 2048:
                raise DNSValidationError("dns_answer_shape")
            if record_type == "TXT":
                # The fixture is a single ASCII chunk; reject DNS escape syntax
                # rather than interpreting an ambiguous representation.
                if re.fullmatch(r'"[A-Za-z0-9_-]{1,128}"', data) is None:
                    raise DNSValidationError("dns_txt_encoding")
                data = data[1:-1]
            answers.append(data)
        return answers


class CloudflareDNSClient:
    """Exact-zone/exact-name reads only. Credentials are resolved only at request time."""

    def __init__(
        self,
        zone_id: str,
        run_prefix: str,
        *,
        transport: HTTPTransport = stdlib_transport,
        token_provider: Callable[[], str] = _runtime_token,
        timeout_seconds: float = 5,
        deadline_seconds: float = 30,
        max_pages: int = 4,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if not _valid_id(zone_id):
            raise DNSValidationError("invalid_zone_identity")
        validate_run_prefix(run_prefix)
        _positive_seconds(timeout_seconds, 30)
        _positive_seconds(deadline_seconds)
        if type(max_pages) is not int or not 1 <= max_pages <= 20:
            raise DNSValidationError("invalid_page_bound")
        self.zone_id = zone_id
        self.run_prefix = run_prefix
        self._transport = transport
        self._token_provider = token_provider
        self._timeout = timeout_seconds
        self._deadline = deadline_seconds
        self._max_pages = max_pages
        self._clock = clock

    def _get(self, suffix: str, deadline: float) -> dict[str, object]:
        remaining = deadline - self._clock()
        if remaining <= 0:
            raise DNSValidationError("api_deadline_exceeded")
        failed = False
        response: HTTPResponse | None = None
        try:
            token = self._token_provider()
            if not isinstance(token, str) or not token or re.fullmatch(r"[!-~]+", token) is None:
                failed = True
            else:
                response = self._transport(
                    f"{API_ROOT}/zones/{self.zone_id}{suffix}",
                    {"Authorization": f"Bearer {token}", "Accept": "application/json"},
                    min(self._timeout, remaining),
                    MAX_RESPONSE_BYTES,
                )
        except Exception:
            failed = True
        if failed or not isinstance(response, HTTPResponse):
            raise DNSValidationError("api_request_failed")
        if self._clock() >= deadline:
            raise DNSValidationError("api_deadline_exceeded")
        if type(response.status) is not int or response.status != 200:
            raise DNSValidationError("api_http_status")
        if not isinstance(response.body, bytes) or len(response.body) > MAX_RESPONSE_BYTES:
            raise DNSValidationError("api_response_size")
        payload: object = None
        try:
            payload = json.loads(response.body, object_pairs_hook=_unique_object)
        except Exception:
            pass
        if (
            not isinstance(payload, dict)
            or payload.get("success") is not True
            or payload.get("errors") != []
            or "result" not in payload
        ):
            raise DNSValidationError("api_response_shape")
        return payload

    def _zone(self, deadline: float) -> ZoneMetadata:
        zone = self._get("", deadline)["result"]
        if (
            not isinstance(zone, dict)
            or zone.get("id") != self.zone_id
            or zone.get("name") != ZONE_NAME
        ):
            raise DNSValidationError("zone_identity_mismatch")
        return ZoneMetadata(self.zone_id, ZONE_NAME)

    def verify_zone(self) -> ZoneMetadata:
        return self._zone(self._clock() + self._deadline)

    def _records(self, name: str, deadline: float) -> list[dict[str, object]]:
        validate_record_name(name, self.run_prefix)
        self._zone(deadline)
        records: list[dict[str, object]] = []
        total: int | None = None
        pages: int | None = None
        seen: set[str] = set()
        for page in range(1, self._max_pages + 1):
            query = urlencode({"name": name, "match": "all", "page": page, "per_page": PAGE_SIZE})
            payload = self._get(f"/dns_records?{query}", deadline)
            result, info = payload["result"], payload.get("result_info")
            if not isinstance(result, list) or not isinstance(info, dict):
                raise DNSValidationError("record_page_shape")
            if any(
                type(info.get(key)) is not int
                for key in ("page", "per_page", "count", "total_count", "total_pages")
            ):
                raise DNSValidationError("record_pagination_shape")
            count, page_total = info["total_count"], info["total_pages"]
            if (
                info["page"] != page
                or info["per_page"] != PAGE_SIZE
                or info["count"] != len(result)
                or len(result) > PAGE_SIZE
                or count < 0
                or page_total < 0
                or page_total > self._max_pages
                or (
                    page_total != (count + PAGE_SIZE - 1) // PAGE_SIZE
                    # Cloudflare may report one empty page rather than zero.
                    and not (count == 0 and page_total == 1)
                )
                or (total is not None and (total != count or pages != page_total))
            ):
                raise DNSValidationError("record_pagination_mismatch")
            total, pages = count, page_total
            for record in result:
                if not isinstance(record, dict):
                    raise DNSValidationError("record_shape")
                record_id = record.get("id")
                if (
                    not isinstance(record_id, str)
                    or not _valid_id(record_id)
                    or record_id in seen
                    or record.get("name") != name
                    or record.get("type") not in ("TXT", "CNAME")
                    or not isinstance(record.get("content"), str)
                    or not record["content"]
                    or record.get("proxied") is not False
                ):
                    raise DNSValidationError("record_shape")
                seen.add(record_id)
                records.append(record)
            if page >= page_total:
                if len(records) != count:
                    raise DNSValidationError("record_count_mismatch")
                return records
        raise DNSValidationError("record_page_bound_exceeded")

    def verify_record(self, expected: ExpectedRecord) -> RecordMetadata:
        _validate_expected(expected, self.run_prefix, self.zone_id)
        records = self._records(expected.name, self._clock() + self._deadline)
        if len(records) != 1:
            raise DNSValidationError("record_not_unique")
        record = records[0]
        if any(
            record[key] != value
            for key, value in (
                ("id", expected.record_id),
                ("name", expected.name),
                ("type", expected.record_type),
                ("content", expected.content),
                ("proxied", expected.proxied),
            )
        ):
            raise DNSValidationError("record_identity_mismatch")
        return RecordMetadata(expected.record_id, expected.name, expected.record_type, False)

    def verify_absent(self, name: str) -> None:
        """API absence is authoritative; recursive cache expiry is not required."""
        if self._records(name, self._clock() + self._deadline):
            raise DNSValidationError("record_still_present")


@dataclass(frozen=True)
class PublicDNSMetadata:
    name: str
    record_type: str
    attempts: int


def verify_public_dns(
    expected: ExpectedRecord,
    *,
    run_prefix: str,
    resolver: PublicResolver,
    max_attempts: int = 5,
    timeout_seconds: float = 5,
    deadline_seconds: float = 30,
    interval_seconds: float = 1,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> PublicDNSMetadata:
    """Resolver returns decoded TXT strings or CNAME targets, never raw packets.

    CNAME targets are compared case-insensitively with one optional terminal dot;
    TXT content is exact (the resolver must join chunks within each TXT RR).
    """
    _validate_expected(expected, run_prefix, "0" * 32)
    _positive_seconds(timeout_seconds, 30)
    _positive_seconds(deadline_seconds)
    if type(max_attempts) is not int or not 1 <= max_attempts <= 100:
        raise DNSValidationError("invalid_attempt_bound")
    if (
        type(interval_seconds) not in (int, float)
        or not math.isfinite(interval_seconds)
        or not 0 <= interval_seconds <= 30
    ):
        raise DNSValidationError("invalid_interval_bound")
    deadline = clock() + deadline_seconds
    for attempt in range(1, max_attempts + 1):
        remaining = deadline - clock()
        if remaining <= 0:
            break
        answers: object = None
        try:
            answers = resolver(expected.name, expected.record_type, min(timeout_seconds, remaining))
        except Exception:
            pass
        if clock() >= deadline:
            break
        if (
            isinstance(answers, (list, tuple))
            and len(answers) == 1
            and isinstance(answers[0], str)
            and (
                answers[0] == expected.content
                if expected.record_type == "TXT"
                else answers[0].removesuffix(".").lower() == expected.content.lower()
            )
        ):
            return PublicDNSMetadata(expected.name, expected.record_type, attempt)
        if attempt < max_attempts:
            remaining = deadline - clock()
            if remaining <= 0:
                break
            failed = False
            try:
                sleep(min(interval_seconds, remaining))
            except Exception:
                failed = True
            if failed:
                raise DNSValidationError("public_dns_wait_failed")
    raise DNSValidationError("public_dns_not_observed")
