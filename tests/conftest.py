import os

import pytest
from redis.asyncio import Redis


@pytest.fixture
def redis_url():
    return os.getenv('CI_REDIS_URL', 'redis://:hackme@localhost:6379/0')


@pytest.fixture
async def redis(redis_url):
    client = Redis.from_url(redis_url)
    await client.flushdb(False)  # Clean current database
    return client
