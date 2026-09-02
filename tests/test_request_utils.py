import requests

from quant.data.request_utils import (
    DEFAULT_TIMEOUT,
    TimeoutSession,
    create_resilient_session,
    resilient_get,
)


def test_timeout_session_uses_default_timeout(monkeypatch):
    session = TimeoutSession()

    captured = {}

    def fake_request(self, method, url, **kwargs):
        captured["timeout"] = kwargs.get("timeout")
        return None

    monkeypatch.setattr(requests.Session, "request", fake_request)

    session.get("https://example.com")

    assert captured["timeout"] == DEFAULT_TIMEOUT


def test_timeout_session_allows_explicit_timeout(monkeypatch):
    session = TimeoutSession()

    captured = {}

    def fake_request(self, method, url, **kwargs):
        captured["timeout"] = kwargs.get("timeout")
        return None

    monkeypatch.setattr(requests.Session, "request", fake_request)

    explicit_timeout = (10, 60)

    session.get(
        "https://example.com",
        timeout=explicit_timeout,
    )

    assert captured["timeout"] == explicit_timeout


def test_create_resilient_session_uses_timeout_session():
    session = create_resilient_session()

    assert isinstance(session, TimeoutSession)
    assert session.timeout == DEFAULT_TIMEOUT


from quant.data.request_utils import (
    DEFAULT_TIMEOUT,
    TimeoutSession,
    create_resilient_session,
)


def test_timeout_session_uses_default_timeout(monkeypatch):
    session = TimeoutSession()

    captured = {}

    def fake_request(self, method, url, **kwargs):
        captured["timeout"] = kwargs.get("timeout")
        return None

    monkeypatch.setattr(
        requests.Session,
        "request",
        fake_request,
    )

    session.get("https://example.com")

    assert captured["timeout"] == DEFAULT_TIMEOUT


def test_timeout_session_allows_explicit_timeout(monkeypatch):
    session = TimeoutSession()

    captured = {}

    def fake_request(self, method, url, **kwargs):
        captured["timeout"] = kwargs.get("timeout")
        return None

    monkeypatch.setattr(
        requests.Session,
        "request",
        fake_request,
    )

    explicit_timeout = (10, 60)

    session.get(
        "https://example.com",
        timeout=explicit_timeout,
    )

    assert captured["timeout"] == explicit_timeout


def test_create_resilient_session_uses_timeout_session():
    session = create_resilient_session()

    assert isinstance(session, TimeoutSession)
    assert session.timeout == DEFAULT_TIMEOUT

from quant.data.request_utils import retry_call


def test_retry_call_retries_after_request_exception(monkeypatch):
    calls = 0

    def fake_function():
        nonlocal calls
        calls += 1

        if calls < 3:
            raise requests.exceptions.ReadTimeout()

        return "success"

    monkeypatch.setattr(
        "quant.data.request_utils.time.sleep",
        lambda _: None,
    )

    result = retry_call(
        fake_function,
        attempts=4,
        initial_delay=1.0,
    )

    assert result == "success"
    assert calls == 3


def test_retry_call_raises_after_all_attempts(monkeypatch):
    calls = 0

    def fake_function():
        nonlocal calls
        calls += 1
        raise requests.exceptions.ReadTimeout()

    monkeypatch.setattr(
        "quant.data.request_utils.time.sleep",
        lambda _: None,
    )

    try:
        retry_call(
            fake_function,
            attempts=4,
            initial_delay=1.0,
        )
    except requests.exceptions.ReadTimeout:
        pass
    else:
        raise AssertionError(
            "retry_call() should raise after all attempts fail"
        )

    assert calls == 4


def test_retry_call_uses_exponential_backoff(monkeypatch):
    delays = []

    def fake_sleep(delay):
        delays.append(delay)

    monkeypatch.setattr(
        "quant.data.request_utils.time.sleep",
        fake_sleep,
    )

    calls = 0

    def fake_function():
        nonlocal calls
        calls += 1
        raise requests.exceptions.ConnectionError()

    try:
        retry_call(
            fake_function,
            attempts=4,
            initial_delay=1.0,
        )
    except requests.exceptions.ConnectionError:
        pass

    assert delays == [1.0, 2.0, 4.0]

def test_resilient_get_retries_after_connection_error(monkeypatch):
    calls = 0

    def fake_get(url, **kwargs):
        nonlocal calls
        calls += 1

        if calls < 3:
            raise requests.exceptions.ConnectionError(
                "temporary connection failure"
            )

        return "success"

    monkeypatch.setattr(
        "quant.data.request_utils.time.sleep",
        lambda _: None,
    )

    session = requests.Session()
    monkeypatch.setattr(session, "get", fake_get)

    result = resilient_get(
        session,
        "https://example.com",
        attempts=4,
    )

    assert result == "success"
    assert calls == 3

def test_resilient_get_retries_after_read_timeout(monkeypatch):
    calls = 0

    def fake_get(url, **kwargs):
        nonlocal calls
        calls += 1

        if calls < 3:
            raise requests.exceptions.ReadTimeout(
                "read timed out"
            )

        return "success"

    monkeypatch.setattr(
        "quant.data.request_utils.time.sleep",
        lambda _: None,
    )

    session = requests.Session()
    monkeypatch.setattr(session, "get", fake_get)

    result = resilient_get(
        session,
        "https://example.com",
        attempts=4,
    )

    assert result == "success"
    assert calls == 3


def test_resilient_get_raises_after_all_attempts(monkeypatch):
    calls = 0

    def fake_get(url, **kwargs):
        nonlocal calls
        calls += 1
        raise requests.exceptions.ConnectionError(
            "permanent failure"
        )

    monkeypatch.setattr(
        "quant.data.request_utils.time.sleep",
        lambda _: None,
    )

    session = requests.Session()
    monkeypatch.setattr(session, "get", fake_get)

    try:
        resilient_get(
            session,
            "https://example.com",
            attempts=4,
        )
    except requests.exceptions.ConnectionError:
        pass
    else:
        raise AssertionError(
            "resilient_get() should raise after all attempts fail"
        )

    assert calls == 4