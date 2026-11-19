import asyncio
import logging

logger = logging.getLogger(__name__)

class SyncScheduler:
    """A minimal placeholder scheduler.
    The original project expects a background sync manager with async start/shutdown.
    For demonstration purposes we provide no‑op implementations that satisfy the import
    and lifecycle hooks without performing any work.
    """

    def __init__(self, app):
        self.app = app
        self._task = None
        logger.info("SyncScheduler initialized (no‑op).")

    async def _run(self):
        # Placeholder loop – sleeps forever until cancelled.
        logger.info("SyncScheduler background task started.")
        try:
            while True:
                await asyncio.sleep(3600)  # sleep 1 hour intervals
        except asyncio.CancelledError:
            logger.info("SyncScheduler background task cancelled.")
            raise

    async def start(self):
        """Start the background scheduler (no‑op)."""
        if self._task is None:
            self._task = asyncio.create_task(self._run())
            logger.info("SyncScheduler.start() called.")
        else:
            logger.info("SyncScheduler already running.")

    async def shutdown(self):
        """Gracefully stop the scheduler (no‑op)."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                logger.info("SyncScheduler shutdown completed.")
            self._task = None
        else:
            logger.info("SyncScheduler.shutdown() called but no task was running.")

