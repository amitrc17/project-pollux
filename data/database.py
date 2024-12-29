"""
This file contains all sorts of database interactions.

We provide the option of using sqllite, mysql or redis. Ideally,
image (and any other blob) storage is on sqllite/mysql. Redis is
used exclusively for user info and asset forests.

Image handles are stored on redis and are keys that are used for
quick search in mysql.
"""

from typing import Any
from abc import ABC, abstractmethod
import redis

from pyre_extensions import override
import logging

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("pollux")


class Database(ABC):

    @abstractmethod
    def get(self, serialized_id: str) -> str:
        pass

    @abstractmethod
    def set(self, serialized_data: str) -> bool:
        pass


class ImageStore(Database):
    pass


class NodeDB(Database):

    RDB = redis.Redis(host="localhost", port=6379, decode_responses=True)  # noqa

    def __init__(self, verbose: bool = False) -> None:
        super().__init__()
        self.verbose: bool = verbose

    @override
    def get(self, serialized_id: str) -> str:
        if self.verbose:
            print("Reading db...")
        serialized_data: Any = NodeDB.RDB.get(serialized_id)
        assert isinstance(serialized_data, str)
        return serialized_data

    @override
    def set(self, serialized_id: str, serialized_data: str) -> bool:
        if self.verbose:
            print("writing to db...")
        if self.verbose:
            print(f"DB Payload: {serialized_data}")
            print(f"DB Key: {serialized_id}")
        ret: Any = NodeDB.RDB.set(serialized_id, serialized_data)
        assert isinstance(ret, bool)
        return ret
