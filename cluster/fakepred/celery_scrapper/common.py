import pydantic

from fakepred.utils.common import get_settings_path
from fakepred.mongodb.common import MongoDB
from fakepred.celery.common import CeleryConfig
from fakepred.redis.common import RedisConfig


class Config(pydantic.BaseModel):
    mongodb: MongoDB
    celery: CeleryConfig
    redis: RedisConfig


def get_cfg(file_path: str = None) -> Config:
    settings_path = get_settings_path(file_path)

    cfg: Config = Config.parse_file(settings_path)

    return cfg
