import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def create_resilient_session(
    *,
    user_agent: str | None = None,
    total_retries: int = 4,
    backoff_factor: float = 1.0,
) -> requests.Session:
    """
    Create a requests.Session with automatic retries and
    exponential backoff.

    Retries are performed for transient connection failures
    and common temporary HTTP errors.
    """

    session = requests.Session()

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

    session.mount(
        "https://",
        adapter,
    )

    session.mount(
        "http://",
        adapter,
    )

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