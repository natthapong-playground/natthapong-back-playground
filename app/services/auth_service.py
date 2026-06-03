from datetime import datetime, timezone

import redis.asyncio as redis
DENYLIST_PREFIX = "denylist:"


async def revoke_token(r: redis.Redis, jti: str, exp_ts: int) -> None:
    ttl = exp_ts - int(datetime.now(timezone.utc).timestamp())
    if ttl > 0:
        await r.set(f"{DENYLIST_PREFIX}{jti}", "1", ex=ttl)

async def is_token_revoked(r: redis.Redis, jti: str) -> bool:
    return await r.exists(f"{DENYLIST_PREFIX}{jti}") == 1
