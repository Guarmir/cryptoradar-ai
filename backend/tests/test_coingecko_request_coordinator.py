
from types import SimpleNamespace

import pytest

from app.services.coingecko_request_coordinator import (
    CoinGeckoRequestBlocked,
    CoinGeckoRequestCoordinator,
)


def test_successful_request():
    coordinator = CoinGeckoRequestCoordinator(
        min_interval_seconds=0,
    )

    response = SimpleNamespace(
        status_code=200,
        headers={},
    )

    assert coordinator.execute(lambda: response) is response


def test_429_blocks_following_requests():
    now = [100.0]
    calls = [0]

    coordinator = CoinGeckoRequestCoordinator(
        min_interval_seconds=0,
        cooldown_seconds=60,
        clock=lambda: now[0],
    )

    def request():
        calls[0] += 1
        return SimpleNamespace(
            status_code=429,
            headers={},
        )

    with pytest.raises(CoinGeckoRequestBlocked):
        coordinator.execute(request)

    with pytest.raises(CoinGeckoRequestBlocked):
        coordinator.execute(request)

    assert calls[0] == 1

    now[0] += 61

    response = coordinator.execute(
        lambda: SimpleNamespace(
            status_code=200,
            headers={},
        )
    )

    assert response.status_code == 200


def test_respects_retry_after():
    now = [100.0]

    coordinator = CoinGeckoRequestCoordinator(
        min_interval_seconds=0,
        cooldown_seconds=60,
        clock=lambda: now[0],
    )

    with pytest.raises(CoinGeckoRequestBlocked):
        coordinator.execute(
            lambda: SimpleNamespace(
                status_code=429,
                headers={"Retry-After": "120"},
            )
        )

    now[0] += 90

    with pytest.raises(CoinGeckoRequestBlocked):
        coordinator.execute(
            lambda: SimpleNamespace(
                status_code=200,
                headers={},
            )
        )

    now[0] += 31

    assert coordinator.execute(
        lambda: SimpleNamespace(
            status_code=200,
            headers={},
        )
    ).status_code == 200

    
def test_concurrent_requests_respect_minimum_interval():
    import threading
    import time
    from concurrent.futures import ThreadPoolExecutor

    request_times = []
    times_lock = threading.Lock()

    coordinator = CoinGeckoRequestCoordinator(
        min_interval_seconds=0.05,
    )

    def request():
        with times_lock:
            request_times.append(time.monotonic())

        return SimpleNamespace(
            status_code=200,
            headers={},
        )

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(
            executor.map(
                lambda _: coordinator.execute(request),
                range(5),
            )
        )

    assert len(results) == 5
    assert len(request_times) == 5

    intervals = [
        current - previous
        for previous, current in zip(
            request_times,
            request_times[1:],
        )
    ]

    assert all(
        interval >= 0.045
        for interval in intervals
    )

