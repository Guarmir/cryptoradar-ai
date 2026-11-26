import asyncio
import threading
from contextlib import asynccontextmanager

import pytest

from app.billing.subscription_lifecycle_runtime import (
    refresh_enabled, run_refresh_loop, subscription_refresh_lifespan,
)


@pytest.mark.parametrize('value,expected', [(None, False), ('false', False), (' TRUE ', True), ('1', False)])
def test_opt_in(monkeypatch, value, expected):
    monkeypatch.delenv('GOOGLE_PLAY_REFRESH_ENABLED', raising=False)
    if value is not None:
        monkeypatch.setenv('GOOGLE_PLAY_REFRESH_ENABLED', value)
    assert refresh_enabled() is expected


def test_disabled_preserves_base_lifespan_and_state():
    events = []
    @asynccontextmanager
    async def base(app):
        events.append('start')
        yield {'original': app}
        events.append('stop')
    def factory():
        pytest.fail('Disabled worker must not start')
    async def scenario():
        async with subscription_refresh_lifespan('app', base_lifespan=base, enabled=False, factory=factory) as state:
            assert state == {'original': 'app'}
    asyncio.run(scenario())
    assert events == ['start', 'stop']


def test_worker_runs_off_event_loop_and_stops():
    async def scenario():
        stop = asyncio.Event()
        loop = asyncio.get_running_loop()
        main_thread = threading.get_ident()
        calls = []
        class Lifecycle:
            def run_batch(self, limit):
                calls.append((limit, threading.get_ident()))
                loop.call_soon_threadsafe(stop.set)
        await asyncio.wait_for(run_refresh_loop(stop, factory=Lifecycle, interval=.01), 2)
        assert len(calls) == 1
        assert calls[0][0] == 1
        assert calls[0][1] != main_thread
    asyncio.run(scenario())


def test_factory_failure_retries_without_logging_secret(caplog):
    async def scenario():
        stop = asyncio.Event()
        loop = asyncio.get_running_loop()
        attempts = []
        class Lifecycle:
            def run_batch(self, limit):
                loop.call_soon_threadsafe(stop.set)
        def factory():
            attempts.append(1)
            if len(attempts) == 1:
                raise RuntimeError('secret-token-example')
            return Lifecycle()
        await asyncio.wait_for(run_refresh_loop(stop, factory=factory, interval=.01), 2)
        assert len(attempts) == 2
    asyncio.run(scenario())
    assert 'secret-token-example' not in caplog.text


def test_batch_failure_does_not_end_loop(caplog):
    async def scenario():
        stop = asyncio.Event()
        loop = asyncio.get_running_loop()
        calls = []
        class Lifecycle:
            def run_batch(self, limit):
                calls.append(limit)
                if len(calls) == 1:
                    raise RuntimeError('private credential')
                loop.call_soon_threadsafe(stop.set)
        await asyncio.wait_for(run_refresh_loop(stop, factory=Lifecycle, interval=.01), 2)
        assert calls == [1, 1]
    asyncio.run(scenario())
    assert 'private credential' not in caplog.text


def test_shutdown_waits_for_current_batch_before_base_shutdown():
    async def scenario():
        entered = asyncio.Event()
        release = threading.Event()
        events = []
        loop = asyncio.get_running_loop()
        @asynccontextmanager
        async def base(app):
            yield
            events.append('base-stop')
        class Lifecycle:
            def run_batch(self, limit):
                loop.call_soon_threadsafe(entered.set)
                assert release.wait(2)
                events.append('batch-done')
        async def session():
            async with subscription_refresh_lifespan(None, base_lifespan=base, enabled=True, factory=Lifecycle, interval=.01):
                await entered.wait()
        task = asyncio.create_task(session())
        await asyncio.wait_for(entered.wait(), 2)
        await asyncio.sleep(.02)
        assert not task.done()
        release.set()
        await asyncio.wait_for(task, 2)
        assert events == ['batch-done', 'base-stop']
    asyncio.run(scenario())


@pytest.mark.parametrize('interval,limit', [(0,1), (1,0), (1,101)])
def test_invalid_runtime_config(interval, limit):
    async def scenario():
        with pytest.raises(ValueError):
            await run_refresh_loop(asyncio.Event(), interval=interval, batch_limit=limit)
    asyncio.run(scenario())
