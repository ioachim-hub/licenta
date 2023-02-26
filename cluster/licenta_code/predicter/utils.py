from typing import Tuple
import pymongo
import pymongo.database


def get_db_handle(
    db_name: str, host: str, port: int, username: str, password: str
) -> Tuple[pymongo.database.Database, pymongo.MongoClient]:
    client: pymongo.MongoClient = pymongo.MongoClient(
        host=host, port=port, username=username, password=password
    )
    db_handle = client[db_name]
    return db_handle, client


def singleton(class_):
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return getinstance


@singleton
class dbHandler:
    def __init__(
        self, db_name: str, host: str, port: int, username: str, password: str
    ) -> None:
        self.client: pymongo.MongoClient = pymongo.MongoClient(
            host=host, port=port, username=username, password=password
        )
        self.db_handle = self.client[db_name]

    def get_db_handle(self) -> pymongo.database.Database:
        return self.db_handle

    def get_client(self) -> pymongo.MongoClient:
        return self.client
