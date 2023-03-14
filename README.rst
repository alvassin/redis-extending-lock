Redis extending lock
====================

Usage
~~~~~
Lock that prolongs itself from time to time and cancels current task if used
as async context manager.

.. code-block:: python

    import asyncio
    import logging

    from redis.asyncio import Redis
    from redis_extending_lock import ExtendingLock


    async def main():
        redis = Redis.from_url('redis://:hackme@localhost:6379/0')
        lock = ExtendingLock(
            redis, 'example',
            timeout=2,
            # optional, if not specified explicitly
            # would be half of timeout
            reacquiring_timeout=1,
            blocking_timeout=0,
        )

        async with lock:
            # your long-running task,
            # would be cancelled if lock would be not able to extend
            # for some reason
            await asyncio.Future()


    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())


Lock can be also used without context manager:

.. code-block:: python

    import asyncio
    import logging

    from redis.asyncio import Redis
    from redis_extending_lock import ExtendingLock


    async def main():
        redis = Redis.from_url('redis://:hackme@localhost:6379/0')
        lock = ExtendingLock(
            redis, 'example', timeout=2, blocking_timeout=0,
        )
        await lock.acquire()
        await asyncio.sleep(5)
        await lock.release()


    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
