import pydantic

from licenta_code.utils.common import get_settings_path
from licenta_code.mongodb.common import MongoDB
from licenta_code.celery.common import CeleryConfig
from licenta_code.scrapper.model import SiteConfig


class Config(pydantic.BaseModel):
    mongodb: MongoDB
    celery: CeleryConfig
    site: list[SiteConfig]


def get_cfg(file_path: str = None) -> Config:
    settings_path = get_settings_path(file_path)

    cfg = Config.parse_file(settings_path)

    return cfg
