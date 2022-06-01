import pydantic
import redis.client  # type: ignore


class RedisConfig(pydantic.BaseModel):
    host: str
    port: int


def redis_connect(cfg: RedisConfig) -> "redis.client.Redis[bytes]":
    return redis.client.Redis(host=cfg.host, port=cfg.port)
