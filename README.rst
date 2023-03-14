Redis extending lock
====================

Lock that prolongs itself from time to time and cancels current task if used
as async context manager.

.. image:: https://coveralls.io/repos/github/alvassin/redis-extending-lock/badge.svg?branch=master
   :target: https://coveralls.io/github/alvassin/redis-extending-lock?branch=master
   :alt: Coveralls

.. image:: https://github.com/alvassin/redis-extending-lock/workflows/tests/badge.svg
   :target: https://github.com/alvassin/redis-extending-lock/actions?query=workflow%3Atests
   :alt: Actions

.. image:: https://img.shields.io/pypi/v/redis-extending-lock.svg
   :target: https://pypi.python.org/pypi/redis-extending-lock.svg/
   :alt: Latest Version

.. image:: https://img.shields.io/pypi/wheel/redis-extending-lock.svg
   :target: https://pypi.python.org/pypi/redis-extending-lock/

.. image:: https://img.shields.io/pypi/pyversions/redis-extending-lock.svg
   :target: https://pypi.python.org/pypi/redis-extending-lock/

.. image:: https://img.shields.io/pypi/l/redis-extending-lock.svg
   :target: https://pypi.python.org/pypi/redis-extending-lock/


Usage
~~~~~

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


How to develop
~~~~~~~~~~~~~~

- ``make devenv`` - configure the development environment
- ``poetry shell`` or `source .venv/bin/activate` - activate virtualenv
- ``make lint`` - syntax & code style check
- ``make codestyle`` - reformat code
- ``make test`` - test this project
- ``make build`` - build this project


Versioning
~~~~~~~~~~

This software follows `Semantic Versioning`_.

Version is represented using MAJOR.MINOR.PATCH numbers, increment the:

* MAJOR version when you make incompatible API changes
* MINOR version when you add functionality in a backwards compatible manner
* PATCH version when you make backwards compatible bug fixes
* Additional labels for pre-release and build metadata are available as
  extensions to the MAJOR.MINOR.PATCH format.

In this case, the package version is assigned automatically with poem-plugins_,
it using on the tag in the repository as a major and minor and the counter,
which takes the number of commits between tag to the head of branch.

.. _Semantic Versioning: http://semver.org/
.. _poem-plugins: https://pypi.org/project/poem-plugins
