import redis


def get_redis_client(host="localhost", port=6379, db=0) -> redis.Redis:
    """Initialize and return a Redis client."""
    return redis.StrictRedis(host=host, port=port, db=db)
