import time
from openbb_core.app.model.abstract.error import OpenBBError

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


DEFAULT_TIMEOUT = (5, 20)

OPENBB_RETRY_EXCEPTIONS = (
    OpenBBError,
    requests.exceptions.RequestException,
    TimeoutError,
)


class TimeoutSession(requests.Session):
    def __init__(
        self,
        *,
        timeout: tuple[float, float] = DEFAULT_TIMEOUT,
    ):
        super().__init__()
        self.timeout = timeout

    def request(self, method, url, **kwargs):
        kwargs.setdefault("timeout", self.timeout)
        return super().request(method, url, **kwargs)


def create_resilient_session(
    *,
    user_agent: str | None = None,
    total_retries: int = 4,
    backoff_factor: float = 1.0,
) -> requests.Session:
    """
    Create a requests.Session with automatic retries,
    exponential backoff, and a default timeout.

    Retries are performed for transient connection failures
    and common temporary HTTP errors.
    """

    session = TimeoutSession()

    retry = Retry(
        total=total_retries,
        connect=total_retries,
        read=total_retries,
        status=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist={
            429,
            500,
            502,
            503,
            504,
        },
        allowed_methods={
            "GET",
        },
        respect_retry_after_header=True,
        raise_on_status=False,
    )

    adapter = HTTPAdapter(
        max_retries=retry,
    )

    session.mount("https://", adapter)
    session.mount("http://", adapter)

    if user_agent:
        session.headers.update({
            "User-Agent": user_agent,
        })

    return session


def retry_call(
    function,
    *,
    attempts: int = 4,
    initial_delay: float = 1.0,
    exceptions: tuple[type[BaseException], ...] = (
        requests.exceptions.RequestException,
        TimeoutError,
    ),
):
    """
    Retry an arbitrary function call.

    Intended for APIs where the underlying HTTP session cannot
    be configured directly, such as OpenBB.
    """

    last_exception = None

    for attempt in range(attempts):
        try:
            return function()

        except exceptions as exc:
            last_exception = exc

            if attempt == attempts - 1:
                raise

            delay = initial_delay * (2 ** attempt)
            time.sleep(delay)

    raise last_exception

def resilient_get(
    session: requests.Session,
    url: str,
    *,
    attempts: int = 4,
    initial_delay: float = 1.0,
    **kwargs,
):
    """
    Perform a GET request with retries around the complete
    request/response lifecycle.

    This catches connection and read failures that may occur
    while requests is loading response.content.
    """

    return retry_call(
        lambda: session.get(url, **kwargs),
        attempts=attempts,
        initial_delay=initial_delay,
        exceptions=(
            requests.exceptions.RequestException,
            TimeoutError,
        ),
    )