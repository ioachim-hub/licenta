import pydantic
import pymongo

MONGODB_DATABASE_NAME = "news"
MONGODB_SCRAPPED_COLLECTION_NAME = "scrapped"


class MongoDB(pydantic.BaseModel):
    host: str
    port: int
    username: str
    password: str


def mongodb_connect(cfg: MongoDB) -> pymongo.MongoClient:
    return pymongo.MongoClient(
        host=cfg.host, port=cfg.port, username=cfg.username, password=cfg.password
    )
