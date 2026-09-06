import os
import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=1)
    redis_client.ping()
except Exception:
    # Graceful degradation if Redis is not running locally
    redis_client = None

def get_cached_response(key: str):
    if redis_client:
        try:
            return redis_client.get(key)
        except Exception:
            return None
    return None

def set_cached_response(key: str, value: str, expiration_seconds: int = 300):
    if redis_client:
        try:
            redis_client.setex(key, expiration_seconds, value)
        except Exception:
            pass