"""Opt-in background revalidation, independent of the mobile session."""
import asyncio
import logging
import os
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


def refresh_enabled():
    return os.getenv('GOOGLE_PLAY_REFRESH_ENABLED', '').strip().lower() == 'true'


def _create_lifecycle():
    from app.billing.subscription_lifecycle import create_subscription_lifecycle
    return create_subscription_lifecycle()


async def run_refresh_loop(stop, *, factory=None, interval=10, batch_limit=1):
    """Process bounded batches off the event loop; never log purchase details."""
    if interval <= 0 or not 1 <= batch_limit <= 100:
        raise ValueError('Invalid refresh runtime configuration.')
    factory = factory or _create_lifecycle
    lifecycle = None
    while not stop.is_set():
        try:
            if lifecycle is None:
                lifecycle = await asyncio.to_thread(factory)
            if stop.is_set():
                break
            await asyncio.to_thread(lifecycle.run_batch, batch_limit)
        except Exception:
            logger.warning('Subscription refresh cycle unavailable.')
        try:
            await asyncio.wait_for(stop.wait(), timeout=interval)
        except asyncio.TimeoutError:
            pass


@asynccontextmanager
async def subscription_refresh_lifespan(app, *, base_lifespan=None, enabled=None,
                                        factory=None, interval=10):
    """Compose with the existing lifespan, without replacing its services."""
    if base_lifespan is None:
        from app.application_fastapi_lifecycle import application_lifespan
        base_lifespan = application_lifespan
    async with base_lifespan(app) as state:
        active = refresh_enabled() if enabled is None else enabled
        if not active:
            yield state
            return
        stop = asyncio.Event()
        worker = asyncio.create_task(run_refresh_loop(stop, factory=factory, interval=interval))
        try:
            yield state
        finally:
            # Do not cancel an in-flight database transaction in a worker thread.
            stop.set()
            await worker
