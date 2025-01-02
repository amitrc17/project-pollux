"""
This file contains all sorts of database interactions.

We provide the option of using sqllite, mysql or redis. Ideally,
image (and any other blob) storage is on sqllite/mysql. Redis is
used exclusively for user info and asset forests.

Image handles are stored on redis and are keys that are used for
quick search in mysql.
"""

from csv import Error
from typing import Any, List, Optional
from abc import ABC, abstractmethod
import redis
import sqlite3

from pyre_extensions import override
import logging

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("pollux")


class Database(ABC):

    @abstractmethod
    def get(self, serialized_id: str) -> Optional[str]:
        pass

    @abstractmethod
    def set(self, serialized_data: str) -> bool:
        pass


class ImageStore(Database):
    """
    ImageStore is the primary storage of images.
    We use sqlite for storing images as blobs.

    This db requires storage of large blobs and
    is likely not going to have many reads & writes.
    We also expect many more reads than writes and no updates to
    entries. We prefer using sqlite for this over redis because
    of these reasons.
    """

    def __init__(self, verbose: bool = False) -> None:
        super().__init__()
        self.verbose: bool = verbose

    @override
    def get(self, image_handle: str) -> Optional[str]:
        try:
            connection: sqlite3.Connection = sqlite3.connect("images.db")
            if self.verbose:
                print("Reading db...")
            cursor: sqlite3.Cursor = connection.cursor()
            select_sql: str = (
                "SELECT image_handle, img FROM image_store WHERE image_handle = ?"
            )
            cursor.execute(select_sql, (image_handle,))
            image_data: List[Any] = cursor.fetchall()
            print(f"Length image data:::: {len(image_data)}")
            assert (
                len(image_data) <= 1
            ), f"There shouldn't be 2 or more images for given handle: {image_handle}. Found: {len(image_data)}"

            if len(image_data) == 0:
                return None
            cursor.close()
            connection.close()
            return image_data[0][1].decode("utf-8")
        except sqlite3.Error as e:
            LOGGER.error(f"Error fetching image from Image Store: {e}")
        finally:
            if connection:
                connection.close()

    @override
    def set(self, image_handle: str, image_data: str) -> bool:
        try:
            connection: sqlite3.Connection = sqlite3.connect("images.db")
            if self.verbose:
                print("writing to db...")
            cursor: sqlite3.Cursor = connection.cursor()
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS image_store (image_handle TEXT PRIMARY KEY, img BLOB NOT NULL)"
            )
            image_data_blob: bytes = image_data.encode("utf-8")
            insert_query: str = (
                f"INSERT OR REPLACE INTO image_store (image_handle, img) VALUES (?, ?)"
            )
            cursor.execute(
                insert_query,
                (
                    image_handle,
                    image_data_blob,
                ),
            )
            connection.commit()
            cursor.close()
            return True
        except sqlite3.Error as e:
            LOGGER.error(f"Error writing image to Image Store: {e}")
        finally:
            if connection:
                connection.close()
            return False


class UserDB(Database):
    """
    UserDB is the primary storage of User Credentials.
    Purpose is for logins and registration of users.
    It is a simple key-value store where the key is
    the hash (username + password) and value is the
    userid (Serialized PID format)

    This db requires a lot of reads but not many writes
    and practically no updates. We prefer redis for this.
    """

    RDB = redis.Redis(host="localhost", port=6379, decode_responses=True)  # noqa

    def __init__(self, verbose: bool = False) -> None:
        super().__init__()
        self.verbose: bool = verbose

    @override
    def get(self, hash: str) -> Optional[str]:
        if self.verbose:
            print("Reading db...")
        user_id: Any = UserDB.RDB.get(hash)
        return user_id

    @override
    def set(self, hash: str, user_id: str) -> bool:
        if self.verbose:
            print("writing to db...")
        if self.verbose:
            print(f"DB Payload: {user_id}")
            print(f"DB Key: {hash}")
        ret: Any = NodeDB.RDB.set(hash, user_id)
        assert isinstance(ret, bool)
        return ret


class NodeDB(Database):
    """
    NodeDB is the primary storage for asset trees.
    Nodes within the asset tree (User, Descriptor, Assets) are
    serialized and stored as strings in the db.
    Since this db requires a lot of read/writes of small objects,
    we use redis.

    Serialization & Deserialization are the responsibility of
    the Node class/sub-classes.

    NOTE: Remember to always update the DB when Nodes are updated.
    The Node class should already have these updates implemented but
    if you subclass Node then it is your responsibility to ensure
    the DB is consistent for your class.
    """

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
