from licenta_code.mongodb.common import (
    mongodb_connect,
    MONGODB_DATABASE_NAME,
)
from licenta_code.redis.common import redis_connect
from licenta_code.celery_scrapper.common import get_cfg


class WorkerState:
    def __init__(self) -> None:
        self.cfg = get_cfg()

        self.mongodb_client = mongodb_connect(self.cfg.mongodb)
        self.mongodb_db = self.mongodb_client[MONGODB_DATABASE_NAME]
        self.redis_client = redis_connect(self.cfg.redis)
