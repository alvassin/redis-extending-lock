import asyncio
import time

import pytest
from redis.asyncio import Redis
from redis.exceptions import LockError

from redis_extending_lock import ExtendingLock


class CountedExtendingLock(ExtendingLock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reacquire_called = 0

    async def reacquire(self):
        self.reacquire_called += 1
        return await super().reacquire()


async def test_reacquiring_lock(redis: Redis):
    lock_name = 'example'
    timeout = 0.1

    lock = CountedExtendingLock(
        redis, lock_name,
        blocking_timeout=0,
        timeout=timeout
    )
    await lock.acquire()

    # Sleep 2x timeout times
    await asyncio.sleep(timeout * 2)
    assert await lock.locked()
    await lock.release()

    # reacquire should be called x2 times then often + 0.5 timeout delay
    assert lock.reacquire_called == 3
    assert not await lock.locked()


class ExtendingLockFailingOnReacquire(ExtendingLock):
    async def do_reacquire(self) -> bool:
        raise LockError


async def test_cxt_task_is_cancelled_if_lock_is_lost(redis: Redis):
    """
    If lock is used as async context manager, we expect it would cancel task
    where it was called.

    In this example it should be test_cxt_task_is_cancelled_if_lock_is_lost
    coroutine.
    """
    future: asyncio.Future = asyncio.Future()

    lock = ExtendingLockFailingOnReacquire(
        redis, 'example',
        timeout=.2,  # reacquiring timeout would be .1
        blocking_timeout=0,
    )

    async with lock:
        with pytest.raises(asyncio.CancelledError):
            await future

    assert future.cancelled()


async def test_gathered_tasks_cancelled_if_lock_is_lost(redis: Redis):
    """
    Gather itself does not cancel all gathered coroutines, if one is cancelled.

    But in case we are not able to reacquire lock, all gathered coroutines in
    current context task would be cancelled.
    """
    fut1: asyncio.Future = asyncio.Future()
    fut2: asyncio.Future = asyncio.Future()

    lock = ExtendingLockFailingOnReacquire(
        redis, 'example',
        timeout=0.2,
        blocking_timeout=0,
    )

    async with lock:
        with pytest.raises(asyncio.CancelledError):
            await asyncio.gather(fut1, fut2)

    assert fut1.cancelled()
    assert fut2.cancelled()


async def test_lock_is_not_lost_on_lock_conn_disconnect(redis: Redis):
    lock = redis.lock(
        name='example',
        timeout=5,
        blocking_timeout=0,
    )
    assert not await lock.locked()
    await lock.acquire()
    assert await lock.locked()
    assert await lock.owned()

    await redis.connection_pool.disconnect()

    assert await lock.locked()
    assert await lock.owned()
    await lock.release()


class TimedExtendingLock(ExtendingLock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reacquire_calls = []

    async def reacquire(self):
        self.reacquire_calls.append(time.monotonic())
        return await super().reacquire()


async def test_lock_is_reacquired_without_loop_blocking_offset(redis: Redis):
    """
    Imagine lock was acquired, backgroung re-acquiring task was started, but
    then event loop was blocked.

    If event loop was blocked less then reacquire interval, we expect reacquire
    must happen correctly. (E.g. reacquire_interval is 2 seconds, event loop is
    blocked for 1 second, reacquire must happen in 2 seconds after start, not
    in 3).
    """
    lock = TimedExtendingLock(
        redis, 'example',
        blocking_timeout=0,
        timeout=.2
    )
    assert not await lock.locked()
    assert not lock.reacquire_calls

    time_started = time.monotonic()
    await lock.acquire()
    assert await lock.owned()
    assert not lock.reacquire_calls
    time.sleep(.1)
    await asyncio.sleep(.01)

    assert lock.reacquire_calls
    assert round(lock.reacquire_calls[0] - time_started, 1) == 0.1
    await lock.release()
