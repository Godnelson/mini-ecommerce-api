from __future__ import annotations
import json
import redis
from app.core.config import settings

_redis = None

def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis

def cache_get_json(key: str):
    r = get_redis()
    raw = r.get(key)
    if raw is None:
        return None
    return json.loads(raw)

def cache_set_json(key: str, value, ttl_seconds: int):
    r = get_redis()
    r.setex(key, ttl_seconds, json.dumps(value))

def cache_del(*keys: str):
    if not keys:
        return
    r = get_redis()
    r.delete(*keys)
