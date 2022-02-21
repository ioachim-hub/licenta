import pydantic

from code.utils.common import get_settings_path
from code.predicter.utils import dbHandler
from code.celery.common import CeleryConfig
from code.scrapper.model import SiteConfig


class Config(pydantic.BaseModel):
    mongodb: dbHandler
    celery: CeleryConfig
    site: list[SiteConfig]


def get_cfg(file_path: str = None) -> Config:
    settings_path = get_settings_path(file_path)

    cfg = Config.parse_file(settings_path)

    return cfg
