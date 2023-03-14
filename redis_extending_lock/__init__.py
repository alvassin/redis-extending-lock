import asyncio
import logging
from contextlib import suppress
from typing import Optional, Union

from aiomisc import PeriodicCallback
from redis import RedisError
from redis.asyncio import Redis
from redis.asyncio.lock import Lock


log = logging.getLogger(__name__)


class ExtendingLock(Lock):
    def __init__(
        self,
        redis: Union[Redis],
        name: Union[str, bytes, memoryview],
        *,
        timeout: float,
        extend_interval: Optional[Union[int, float]] = None,
        **kwargs
    ):
        if timeout is None:
            raise TypeError('timeout must be specified')

        super().__init__(redis, name, timeout=timeout, **kwargs)

        self._reacquire_interval = (
            extend_interval if extend_interval is not None
            else timeout * 0.5
        )
        self._lock = asyncio.Lock()
        self._reacquire_task = PeriodicCallback(self.reacquire)
        self._current_task: Optional[asyncio.Task] = None

    def __cancel_current_task(self):
        if self._current_task is None:
            return
        if self._current_task.done():
            return
        log.debug('Cancelling ctx manager task')
        self._current_task.cancel()

    async def reacquire(self) -> bool:
        log.debug('Reacquiring lock %r', self.name)
        try:
            result = await super().reacquire()
            if not result:
                log.error('Unable to reacquire lock, cancelling context task')
                self.__cancel_current_task()
            return result
        except RedisError:
            self.__cancel_current_task()
            return False

    async def __aenter__(self):
        self._current_task = asyncio.current_task()
        await super().__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await super().__aexit__(exc_type, exc_val, exc_tb)
        self._current_task = None

    async def acquire(self, *args, **kwargs):
        log.debug('Acquiring lock %r', self.name)
        async with self._lock:
            acquired = await super().acquire(*args, **kwargs)
            if acquired:
                self._reacquire_task.start(
                    self._reacquire_interval, delay=self._reacquire_interval
                )
                log.debug('Acquired lock %r', self.name)
            return acquired

    async def release(self):
        async with self._lock:
            log.debug('Releasing lock %r', self.name)
            with suppress(asyncio.CancelledError, RuntimeError):
                await self._reacquire_task.stop()
            await super().release()
            log.debug('Released lock %r', self.name)
