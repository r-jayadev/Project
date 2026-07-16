"""
Redis Configuration Module
"""
import json 
import redis
from app.config import settings

#Create redis client using values from the .env file
redis_client=redis.Redis(host=settings.REDIS_HOST,
                         port=settings.REDIS_PORT,
                         db=settings.REDIS_DB,
                         decode_responses=True)

def get_cache(key: str):
    """
    Get data from redis cache

    retruns:
        cached data if exists
        none if not found
    """
    try:
        cached_data = redis_client.get(key)

        if cached_data:
            return json.loads(cached_data)
        
        return None
    
    except Exception as e:
        print(f"Redis GET Error: {e}")
        return None 
    
def set_cache(key: str, value):
    """
    Store data in redis
    """
    try:
        redis_client.setex(name=key, time=settings.CACHE_TTL, value=json.dumps(value))

    except Exception as e:
        print(f"Redis SET Error: {e}")

def delete_cache(key: str):
    """
    Remove cached item from redis
    """
    try:
        redis_client.delete(key)

    except Exception as e:
        print(f"Redis DELETE Error: {e}")

def check_redis_connection():
    """
    Check whether redis is reachable

    Return:
        True if redis is connected
        False if redis is not Connected
    """
    try:
        redis_client.ping()
        return True
    
    except Exception:
        return False
    