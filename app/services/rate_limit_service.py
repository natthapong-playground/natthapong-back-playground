import redis.asyncio as redis

from app.core.config import settings

LOGIN_FAIL_PREFIX = "login_fail:"
REGISTER_PREFIX = "register_attempt:"
GOOGLE_LOGIN_PREFIX = "google_login_attempt:"

_HIT_SCRIPT = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return count
"""

def _key(prefix: str, identifier: str) -> str:
    return f"{prefix}{identifier}"


async def _count(r: redis.Redis, prefix: str, identifier: str) -> int:
    value = await r.get(_key(prefix, identifier))
    return int(value) if value else 0


async def _hit(r: redis.Redis, prefix: str, identifier: str, window: int) -> int:
    key = _key(prefix, identifier)
    return int(await r.eval(_HIT_SCRIPT, 1, key, window))


async def _retry_after(r: redis.Redis, prefix: str, identifier: str, window: int) -> int:
    ttl = await r.ttl(_key(prefix, identifier))
    return ttl if ttl and ttl > 0 else window


async def _clear(r: redis.Redis, prefix: str, identifier: str) -> None:
    await r.delete(_key(prefix, identifier))


# --- login brute-force guard (counts FAILED attempts; cleared on success) ---- #
async def is_login_blocked(r: redis.Redis, identifier: str) -> bool:
    return await _count(r, LOGIN_FAIL_PREFIX, identifier) >= settings.LOGIN_RATE_LIMIT_MAX_ATTEMPTS


async def record_login_failure(r: redis.Redis, identifier: str) -> int:
    return await _hit(r, LOGIN_FAIL_PREFIX, identifier, settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS)


async def clear_login_failures(r: redis.Redis, identifier: str) -> None:
    await _clear(r, LOGIN_FAIL_PREFIX, identifier)


async def get_retry_after(r: redis.Redis, identifier: str) -> int:
    return await _retry_after(r, LOGIN_FAIL_PREFIX, identifier, settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS)


# --- registration throttle (counts EVERY attempt per source IP) -------------- #
async def is_register_blocked(r: redis.Redis, identifier: str) -> bool:
    return await _count(r, REGISTER_PREFIX, identifier) >= settings.REGISTER_RATE_LIMIT_MAX_ATTEMPTS


async def record_register_attempt(r: redis.Redis, identifier: str) -> int:
    return await _hit(r, REGISTER_PREFIX, identifier, settings.REGISTER_RATE_LIMIT_WINDOW_SECONDS)


async def get_register_retry_after(r: redis.Redis, identifier: str) -> int:
    return await _retry_after(r, REGISTER_PREFIX, identifier, settings.REGISTER_RATE_LIMIT_WINDOW_SECONDS)


# --- Google login throttle (counts EVERY attempt per source IP) --------------- #
async def record_google_login_attempt(r: redis.Redis, identifier: str) -> int:
    return await _hit(
        r,
        GOOGLE_LOGIN_PREFIX,
        identifier,
        settings.GOOGLE_LOGIN_RATE_LIMIT_WINDOW_SECONDS,
    )


async def get_google_login_retry_after(r: redis.Redis, identifier: str) -> int:
    return await _retry_after(
        r,
        GOOGLE_LOGIN_PREFIX,
        identifier,
        settings.GOOGLE_LOGIN_RATE_LIMIT_WINDOW_SECONDS,
    )
