import pymongo

from licenta_code.mongodb.common import (
    mongodb_connect,
    MONGODB_DATABASE_NAME,
    MONGODB_SCRAPPED_COLLECTION_NAME,
)
from licenta_code.redis.common import redis_connect
from licenta_code.celery_searcher.common import get_cfg


class WorkerState:
    def __init__(self) -> None:
        self.cfg = get_cfg()

        self.mongodb_client = mongodb_connect(self.cfg.mongodb)
        self.mongodb_db = self.mongodb_client[MONGODB_DATABASE_NAME]
        self.redis_client = redis_connect(self.cfg.redis)

    def mongodb_connect_to_collection(self) -> pymongo.collection.Collection:
        return self.mongodb_db[MONGODB_SCRAPPED_COLLECTION_NAME]
