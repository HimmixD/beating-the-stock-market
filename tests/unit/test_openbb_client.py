from unittest.mock import Mock

from openbb_core.app.model.abstract.error import OpenBBError

from quant.data.request_utils import retry_call


def test_retry_call_can_retry_openbb_error(monkeypatch):
    calls = 0

    def fake_function():
        nonlocal calls
        calls += 1

        if calls < 3:
            raise OpenBBError("temporary OpenBB failure")

        return "success"

    monkeypatch.setattr(
        "quant.data.request_utils.time.sleep",
        lambda _: None,
    )

    result = retry_call(
        fake_function,
        attempts=4,
        initial_delay=1.0,
        exceptions=(OpenBBError,),
    )

    assert result == "success"
    assert calls == 3