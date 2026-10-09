from typing import Any, Callable, Optional

import requests

from app.services.coingecko_request_runtime import (
    coingecko_request_coordinator,
)


def coingecko_controlled_get(
    url: str,
    *,
    request_get: Optional[Callable[..., Any]] = None,
    **kwargs: Any,
) -> Any:
    getter = request_get or requests.get

    return coingecko_request_coordinator.execute(
        lambda: getter(url, **kwargs)
    )