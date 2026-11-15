"""Offline HTTP/resolver contracts. Network access is forbidden in this suite."""

import importlib.util
import json
import socket
import sys
import traceback
from dataclasses import asdict, replace
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "canary_dns_test_package",
    ROOT / "src/main/__init__.py",
    submodule_search_locations=[str(ROOT / "src/main")],
)
package = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = package
from canary_dns_test_package import canary_dns as dns

PREFIX = "gha-1794700000-123-1"
ZONE = "a" * 32
RECORD_ID = "b" * 32
NAME = f"{PREFIX}.txt.ci.solomonhd.ai"
SENTINEL = "synthetic-secret-do-not-disclose"
EXPECTED = dns.ExpectedRecord(RECORD_ID, NAME, "TXT", "canary-marker")


def doh_payload(kind="TXT", value='"canary-marker"'):
    name = f"{PREFIX}.{kind.lower()}.ci.solomonhd.ai"
    code = {"TXT": 16, "CNAME": 5}[kind]
    return {
        "Status": 0,
        "TC": False,
        "Question": [{"name": name, "type": code}],
        "Answer": [{"name": name + ".", "type": code, "TTL": 60, "data": value}],
    }


@pytest.mark.parametrize(
    "kind,value,expected",
    [
        ("TXT", '"canary-marker"', "canary-marker"),
        ("CNAME", "example.com.", "example.com."),
        ("CNAME", "example.org.", "example.org."),
    ],
)
def test_real_doh_contract_without_network(kind, value, expected):
    calls = []

    def transport(url, headers, timeout, max_bytes):
        calls.append((url, headers, timeout, max_bytes))
        return response(doh_payload(kind, value))

    resolver = dns.CloudflareDoHResolver(PREFIX, transport=transport)
    name = f"{PREFIX}.{kind.lower()}.ci.solomonhd.ai"
    assert resolver(name, kind, 1) == [expected]
    url, headers, timeout, bound = calls[0]
    assert urlsplit(url).scheme == "https"
    assert urlsplit(url).netloc == "cloudflare-dns.com"
    assert urlsplit(url).path == "/dns-query"
    assert parse_qs(urlsplit(url).query) == {"name": [name], "type": [kind]}
    assert headers == {"Accept": "application/dns-json"}
    assert timeout == 1 and bound == dns.MAX_RESPONSE_BYTES


@pytest.mark.parametrize(
    "changes",
    [
        {"Status": 3},
        {"Status": False},
        {"TC": True},
        {"Question": []},
        {"Question": [{"name": "other.example", "type": 16}]},
        {"Question": [{"name": NAME, "type": 5}]},
        {"Answer": {}},
        {"Answer": [{"name": NAME, "type": 16, "data": '"bad\\032encoding"'}]},
        {"Answer": [{"name": NAME, "type": 16, "data": '"chunk1" "chunk2"'}]},
    ],
)
def test_doh_rejects_wrong_question_status_and_encoding(changes):
    payload = doh_payload()
    payload.update(changes)
    resolver = dns.CloudflareDoHResolver(PREFIX, transport=lambda *_: response(payload))
    with pytest.raises(dns.DNSValidationError):
        resolver(NAME, "TXT", 1)


def test_doh_unrelated_answers_cannot_satisfy_query():
    payload = doh_payload()
    payload["Answer"][0]["name"] = "elsewhere.example."
    resolver = dns.CloudflareDoHResolver(PREFIX, transport=lambda *_: response(payload))
    assert resolver(NAME, "TXT", 1) == []


def test_doh_deadline_bounds_even_blocked_transport():
    import threading

    gate = threading.Event()
    try:
        resolver = dns.CloudflareDoHResolver(PREFIX, transport=lambda *_: gate.wait(2))
        with pytest.raises(dns.DNSValidationError, match="dns_deadline_exceeded"):
            resolver(NAME, "TXT", 0.01)
    finally:
        gate.set()


@pytest.mark.parametrize("target", ["example.com", "example.org", f"{PREFIX}.txt.ci.solomonhd.ai"])
def test_cname_target_allowlist_accepts_only_reviewed_targets(target):
    expected = dns.ExpectedRecord(RECORD_ID, f"{PREFIX}.cname.ci.solomonhd.ai", "CNAME", target)
    dns.verify_public_dns(expected, run_prefix=PREFIX, resolver=lambda *_: [target])


@pytest.mark.parametrize(
    "target", ["evil.example", "example.net", "example.com.", "EXAMPLE.COM", "https://example.com"]
)
def test_cname_target_allowlist_rejects_arbitrary_external_input(target):
    expected = dns.ExpectedRecord(RECORD_ID, f"{PREFIX}.cname.ci.solomonhd.ai", "CNAME", target)
    with pytest.raises(dns.DNSValidationError, match="invalid_cname_target"):
        dns.verify_public_dns(expected, run_prefix=PREFIX, resolver=lambda *_: [target])


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    def denied(*args, **kwargs):
        pytest.fail("Tests must never open a network connection")

    monkeypatch.setattr(socket, "create_connection", denied)
    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket, "getaddrinfo", denied)


def envelope(result, **extra):
    return {"success": True, "errors": [], "result": result, **extra}


def response(payload, status=200):
    return dns.HTTPResponse(status, json.dumps(payload).encode())


def zone(**changes):
    return envelope({"id": ZONE, "name": "solomonhd.ai", **changes})


def record(**changes):
    return {
        "id": RECORD_ID,
        "name": NAME,
        "type": "TXT",
        "content": EXPECTED.content,
        "proxied": False,
        **changes,
    }


def page(records, **changes):
    return envelope(
        records,
        result_info={
            "page": 1,
            "per_page": 100,
            "count": len(records),
            "total_count": len(records),
            "total_pages": 1,
            **changes,
        },
    )


class Transport:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, url, headers, timeout, max_bytes):
        self.calls.append((url, headers, timeout, max_bytes))
        value = self.responses.pop(0)
        if isinstance(value, BaseException):
            raise value
        return value


def client(transport, **options):
    return dns.CloudflareDNSClient(
        ZONE, PREFIX, transport=transport, token_provider=lambda: SENTINEL, **options
    )


class Clock:
    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


def test_zone_and_exact_record_success_return_metadata_only(capsys):
    transport = Transport(response(zone(token=SENTINEL)), response(page([record(secret=SENTINEL)])))
    result = client(transport).verify_record(EXPECTED)
    assert asdict(result) == {
        "record_id": RECORD_ID,
        "name": NAME,
        "record_type": "TXT",
        "proxied": False,
    }
    assert EXPECTED.content not in repr(result)
    assert SENTINEL not in repr(result)
    assert len(transport.calls) == 2
    first, second = transport.calls
    assert first[0] == f"{dns.API_ROOT}/zones/{ZONE}"
    parsed = urlsplit(second[0])
    assert parsed.path == f"/client/v4/zones/{ZONE}/dns_records"
    assert parse_qs(parsed.query) == {
        "name": [NAME],
        "match": ["all"],
        "page": ["1"],
        "per_page": ["100"],
    }
    for url, headers, timeout, max_bytes in transport.calls:
        assert "/accounts/" not in url and "tunnel" not in url and SENTINEL not in url
        assert headers == {"Authorization": f"Bearer {SENTINEL}", "Accept": "application/json"}
        assert 0 < timeout <= 5 and max_bytes == 65536
    assert capsys.readouterr() == ("", "")


def test_credentials_are_read_only_at_request_time(monkeypatch):
    monkeypatch.delenv("CLOUDFLARE_API_TOKEN", raising=False)
    transport = Transport(response(zone()))
    api = dns.CloudflareDNSClient(ZONE, PREFIX, transport=transport)
    assert transport.calls == []
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", SENTINEL)
    assert asdict(api.verify_zone()) == {"zone_id": ZONE, "name": "solomonhd.ai"}


@pytest.mark.parametrize("status", [201, 204, 301, 400, 401, 403, 404, 429, 500, True, "200"])
def test_non_200_status_rejected_without_body_disclosure(status):
    transport = Transport(response({"errors": [{"message": SENTINEL}]}, status))
    with pytest.raises(dns.DNSValidationError, match="^api_http_status$") as error:
        client(transport).verify_zone()
    assert SENTINEL not in "".join(traceback.format_exception(error.value))


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        {},
        {"success": 1, "errors": [], "result": {}},
        {"success": False, "errors": [{"message": SENTINEL}], "result": {}},
        {"success": True, "result": {}},
        {"success": True, "errors": [], "data": {}},
        {"success": True, "errors": [SENTINEL], "result": {}},
    ],
)
def test_strict_success_envelope(payload):
    with pytest.raises(dns.DNSValidationError, match="^api_response_shape$"):
        client(Transport(response(payload))).verify_zone()


@pytest.mark.parametrize("body", [b"not-json", b"\xff", b"x" * 65537])
def test_invalid_and_oversized_bodies(body):
    with pytest.raises(dns.DNSValidationError):
        client(Transport(dns.HTTPResponse(200, body))).verify_zone()


def test_duplicate_json_keys_are_not_silently_overwritten():
    body = b'{"success":false,"success":true,"errors":[],"result":{}}'
    with pytest.raises(dns.DNSValidationError, match="^api_response_shape$"):
        client(Transport(dns.HTTPResponse(200, body))).verify_zone()


@pytest.mark.parametrize(
    "changes",
    [{"id": "c" * 32}, {"name": "sghd.io"}, {"name": "SolomonHD.ai"}, {"name": "solomonhd.ai."}],
)
def test_zone_identity_exact_and_checked_before_dns_queries(changes):
    transport = Transport(response(zone(**changes)))
    with pytest.raises(dns.DNSValidationError, match="^zone_identity_mismatch$"):
        client(transport).verify_record(EXPECTED)
    assert len(transport.calls) == 1


@pytest.mark.parametrize(
    "changes",
    [
        {"id": "c" * 32},
        {"id": None},
        {"id": SENTINEL},
        {"name": NAME + ".evil"},
        {"type": "A"},
        {"type": "CNAME"},
        {"content": SENTINEL},
        {"content": None},
        {"content": ""},
        {"proxied": True},
        {"proxied": 0},
        {"proxied": None},
    ],
)
def test_record_identity_type_content_and_proxy_fail_closed(changes):
    with pytest.raises(dns.DNSValidationError) as error:
        client(Transport(response(zone()), response(page([record(**changes)])))).verify_record(
            EXPECTED
        )
    assert SENTINEL not in "".join(traceback.format_exception(error.value))


@pytest.mark.parametrize("records", [[], [record(), record(id="c" * 32)], [record(), record()]])
def test_missing_duplicate_or_multiple_records_never_pass(records):
    with pytest.raises(dns.DNSValidationError):
        client(Transport(response(zone()), response(page(records)))).verify_record(EXPECTED)


@pytest.mark.parametrize("empty_pages", [0, 1])
def test_exact_name_absence(empty_pages):
    transport = Transport(response(zone()), response(page([], total_pages=empty_pages)))
    client(transport).verify_absent(NAME)
    assert parse_qs(urlsplit(transport.calls[-1][0]).query)["name"] == [NAME]


def test_absence_rejects_residual_record_and_incomplete_pages():
    for payload in [page([record()]), page([], total_count=1), envelope([])]:
        with pytest.raises(dns.DNSValidationError):
            client(Transport(response(zone()), response(payload))).verify_absent(NAME)


@pytest.mark.parametrize(
    "changes",
    [
        {"page": 2},
        {"page": True},
        {"per_page": 99},
        {"count": 0},
        {"total_count": -1},
        {"total_count": "1"},
        {"total_pages": -1},
        {"total_pages": 0},
        {"total_pages": 5},
        {"total_pages": True},
    ],
)
def test_pagination_metadata_strict(changes):
    with pytest.raises(dns.DNSValidationError):
        client(Transport(response(zone()), response(page([record()], **changes)))).verify_record(
            EXPECTED
        )


def test_all_pages_read_and_unstable_totals_or_duplicate_ids_rejected():
    first = [record(id=f"{index:032x}") for index in range(100)]
    for last in [
        page([record(id="f" * 32)], page=2, total_count=101, total_pages=2),
        page([record(id="0" * 32)], page=2, total_count=101, total_pages=2),
        page([record()], page=2, total_count=102, total_pages=2),
    ]:
        transport = Transport(
            response(zone()), response(page(first, total_count=101, total_pages=2)), response(last)
        )
        with pytest.raises(dns.DNSValidationError):
            client(transport).verify_absent(NAME)
        assert len(transport.calls) == 3
        assert parse_qs(urlsplit(transport.calls[-1][0]).query)["page"] == ["2"]


@pytest.mark.parametrize(
    "name", ["*", "ci.solomonhd.ai", NAME + ".", NAME + "&name=evil", SENTINEL]
)
def test_no_invalid_name_can_reach_transport(name):
    transport = Transport()
    api = client(transport)
    with pytest.raises(ValueError):
        api.verify_absent(name)
    with pytest.raises(ValueError):
        api.verify_record(replace(EXPECTED, name=name))
    assert transport.calls == []


@pytest.mark.parametrize(
    "options",
    [
        {"timeout_seconds": 0},
        {"timeout_seconds": float("nan")},
        {"deadline_seconds": float("inf")},
        {"deadline_seconds": -1},
        {"max_pages": 0},
        {"max_pages": 21},
        {"max_pages": True},
    ],
)
def test_invalid_bounds_fail_before_network(options):
    transport = Transport()
    with pytest.raises(dns.DNSValidationError):
        client(transport, **options)
    assert not transport.calls


def test_api_deadline_covers_zone_and_record_requests():
    clock = Clock()
    calls = []

    def transport(url, headers, timeout, max_bytes):
        calls.append(timeout)
        clock.now += 2
        return response(zone()) if len(calls) == 1 else response(page([record()]))

    with pytest.raises(dns.DNSValidationError, match="^api_deadline_exceeded$"):
        client(transport, deadline_seconds=3, clock=clock).verify_record(EXPECTED)
    assert calls == [3, 1]


def test_transport_and_token_failures_are_sanitized(capsys):
    for transport in [Transport(RuntimeError(SENTINEL)), Transport(None)]:
        with pytest.raises(dns.DNSValidationError) as error:
            client(transport).verify_zone()
        assert SENTINEL not in "".join(traceback.format_exception(error.value))
        assert error.value.__context__ is None

    def bad_token():
        raise RuntimeError(SENTINEL)

    transport = Transport()
    for supplier in [bad_token, lambda: "", lambda: SENTINEL + "\r\nheader"]:
        with pytest.raises(dns.DNSValidationError) as error:
            dns.CloudflareDNSClient(
                ZONE, PREFIX, transport=transport, token_provider=supplier
            ).verify_zone()
        assert SENTINEL not in repr(error.value)
    assert not transport.calls
    assert capsys.readouterr() == ("", "")


def test_stdlib_adapter_never_follows_redirects_or_uses_environment_proxy(monkeypatch):
    captured = []

    class Result:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self, maximum):
            captured.append(maximum)
            return b"{}"

    class Opener:
        def open(self, request, timeout):
            assert request.get_method() == "GET"
            assert timeout == 2
            return Result()

    def opener(*handlers):
        assert handlers[0].proxies == {}
        assert isinstance(handlers[1], dns._NoRedirect)
        assert handlers[1].redirect_request(None, None, 302, None, None, "https://evil") is None
        return Opener()

    monkeypatch.setattr(dns, "build_opener", opener)
    assert dns.stdlib_transport("https://example.invalid", {}, 2, 100).body == b"{}"
    assert captured == [101]


def test_public_txt_success_retry_and_metadata(capsys):
    clock = Clock()
    calls = []

    def resolver(name, kind, timeout):
        calls.append((name, kind, timeout))
        if len(calls) == 1:
            raise RuntimeError(SENTINEL)
        return [EXPECTED.content]

    result = dns.verify_public_dns(
        EXPECTED, run_prefix=PREFIX, resolver=resolver, clock=clock, sleep=clock.sleep
    )
    assert asdict(result) == {"name": NAME, "record_type": "TXT", "attempts": 2}
    assert calls == [(NAME, "TXT", 5), (NAME, "TXT", 5)]
    assert clock.sleeps == [1]
    assert capsys.readouterr() == ("", "")


def test_cname_api_and_public_dns_check_target_not_address():
    expected = replace(
        EXPECTED, name=f"{PREFIX}.cname.ci.solomonhd.ai", record_type="CNAME", content=NAME
    )
    transport = Transport(
        response(zone()), response(page([record(name=expected.name, type="CNAME", content=NAME)]))
    )
    assert client(transport).verify_record(expected).record_type == "CNAME"
    calls = []

    def resolver(name, kind, timeout):
        calls.append((name, kind))
        return [NAME.upper() + "."]

    assert dns.verify_public_dns(expected, run_prefix=PREFIX, resolver=resolver).attempts == 1
    assert calls == [(expected.name, "CNAME")]


@pytest.mark.parametrize(
    "answers",
    [
        [],
        [SENTINEL],
        [EXPECTED.content, SENTINEL],
        EXPECTED.content,
        [None],
        [EXPECTED.content.upper()],
        ['"canary-marker"'],
    ],
)
def test_public_dns_unexpected_or_ambiguous_answers_fail_sanitized(answers, capsys):
    calls = []
    clock = Clock()

    def resolver(name, kind, timeout):
        calls.append(timeout)
        return answers

    with pytest.raises(dns.DNSValidationError, match="^public_dns_not_observed$") as error:
        dns.verify_public_dns(
            EXPECTED,
            run_prefix=PREFIX,
            resolver=resolver,
            max_attempts=3,
            clock=clock,
            sleep=clock.sleep,
        )
    assert len(calls) == 3
    assert SENTINEL not in "".join(traceback.format_exception(error.value))
    assert capsys.readouterr() == ("", "")


def test_public_deadline_and_attempt_limits_are_independent():
    clock = Clock()
    calls = []

    def resolver(name, kind, timeout):
        calls.append(timeout)
        clock.now += 2
        return []

    with pytest.raises(dns.DNSValidationError):
        dns.verify_public_dns(
            EXPECTED,
            run_prefix=PREFIX,
            resolver=resolver,
            max_attempts=10,
            deadline_seconds=4,
            clock=clock,
            sleep=clock.sleep,
        )
    assert calls == [4, 1]
    assert clock.sleeps == [1]


@pytest.mark.parametrize(
    "options",
    [
        {"max_attempts": 0},
        {"max_attempts": 101},
        {"max_attempts": True},
        {"timeout_seconds": 0},
        {"deadline_seconds": float("nan")},
        {"interval_seconds": -1},
        {"interval_seconds": float("inf")},
    ],
)
def test_invalid_public_bounds_precede_resolution(options):
    def resolver(*args):
        pytest.fail("Invalid options must not call a resolver")

    with pytest.raises(dns.DNSValidationError):
        dns.verify_public_dns(EXPECTED, run_prefix=PREFIX, resolver=resolver, **options)


def test_content_not_in_expected_or_http_response_repr():
    assert SENTINEL not in repr(replace(EXPECTED, content=SENTINEL))
    assert SENTINEL not in repr(dns.HTTPResponse(400, SENTINEL.encode()))


def test_public_resolver_late_success_cannot_pass_deadline():
    clock = Clock()

    def resolver(name, kind, timeout):
        clock.now += timeout
        return [EXPECTED.content]

    with pytest.raises(dns.DNSValidationError, match="^public_dns_not_observed$"):
        dns.verify_public_dns(
            EXPECTED, run_prefix=PREFIX, resolver=resolver, deadline_seconds=1, clock=clock
        )


def test_public_wait_failure_never_discloses_exception():
    def fail_sleep(seconds):
        raise RuntimeError(SENTINEL)

    with pytest.raises(dns.DNSValidationError, match="^public_dns_wait_failed$") as error:
        dns.verify_public_dns(
            EXPECTED, run_prefix=PREFIX, resolver=lambda *args: [], sleep=fail_sleep
        )
    assert SENTINEL not in "".join(traceback.format_exception(error.value))
    assert error.value.__context__ is None


def test_stdlib_transport_sanitizes_raw_http_errors(monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError(SENTINEL)

    monkeypatch.setattr(dns, "build_opener", fail)
    with pytest.raises(dns.DNSValidationError, match="^http_transport_failed$") as error:
        dns.stdlib_transport("https://example.invalid", {}, 1, 100)
    assert SENTINEL not in "".join(traceback.format_exception(error.value))
    assert error.value.__context__ is None
