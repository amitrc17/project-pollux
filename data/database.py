"""
This file contains all sorts of database interactions.

We provide the option of using sqllite, mysql or redis. Ideally,
image (and any other blob) storage is on sqllite/mysql. Redis is
used exclusively for user info and asset forests.

Image handles are stored on redis and are keys that are used for
quick search in mysql.
"""

from .asset_forest import PID, Node
from abc import ABC, abstractmethod
import redis

from pyre_extensions import override
import json


class Database(ABC):

    @abstractmethod
    def get(self, pid: PID) -> Node:
        pass

    @abstractmethod
    def set(self, node: Node) -> bool:
        pass


class ImageStore(Database):
    pass


class NodeDB(Database):

    def __init__(self):
        super().__init__()
        self.r = redis.Redis(host="localhost", port=6379, decode_responses=True)  # noqa

    @override
    def get(self, pid: PID) -> Node:
        print("Reading db...")
        serialized_data = self.r.get(pid.serialize())
        return Node.deserialize(serialized_data)

    @override
    def set(self, node: Node) -> bool:
        print("writing to db...")
        data = node.serialize()
        print(f"DB Payload: {data}")
        return self.r.set(node.id.serialize(), data)
