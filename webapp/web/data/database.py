"""
This file contains all sorts of database interactions.

We provide the option of using sqllite, mysql or redis. Ideally,
image (and any other blob) storage is on sqllite/mysql. Redis is
used exclusively for user info and asset forests.

Image handles are stored on redis and are keys that are used for
quick search in mysql.
"""

from csv import Error
from typing import Any, List, Optional, override
from abc import ABC, abstractmethod
from unittest import result
import redis
import sqlite3

import logging


logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("pollux")


class Database(ABC):

    @abstractmethod
    def get(self, serialized_id: str) -> Optional[str]:
        """
        Get a record from the database.
        """
        pass

    @abstractmethod
    def set(self, serialized_id: str, serialized_data: str) -> bool:
        """
        Set a record in the database.
        Returns True if set was successful, False otherwise.
        """
        pass

    @abstractmethod
    def delete(self, serialized_id: str) -> bool:
        """
        Delete a record from the database.
        Returns True if deletion was successful, False otherwise.
        """
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
                """
                    SELECT 
                        image_handle, 
                        img 
                    FROM 
                        image_store 
                    WHERE 
                image_handle = ?
                """.strip()
            )
            cursor.execute(select_sql, (image_handle,))
            image_data: List[Any] = cursor.fetchall()
            if self.verbose:
                print(f"Found {len(image_data)} image(s) for handle: {image_handle}")
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
            return None

    @override
    def set(self, image_handle: str, image_data: str) -> bool:
        try:
            connection: sqlite3.Connection = sqlite3.connect("images.db")
            if self.verbose:
                print("writing to Image Store...")
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
            if self.verbose:
                print("Write Successful!")
            return True
        except sqlite3.Error as e:
            if self.verbose:
                print("Write Failed!")
            LOGGER.error(f"Error writing image to Image Store: {e}")
        finally:
            if connection:
                connection.close()
            return False

    @override
    def delete(self, image_handle: str) -> bool:
        try:
            connection: sqlite3.Connection = sqlite3.connect("images.db")
            cursor: sqlite3.Cursor = connection.cursor()
            if self.verbose:
                print("Deleting from Image Store...")
            delete_query: str = "DELETE FROM image_store WHERE image_handle = ?"
            cursor.execute(delete_query, (image_handle,))
            connection.commit()
            cursor.close()
            return True
        except sqlite3.Error as e:
            LOGGER.error(f"Error deleting image from Image Store: {e}")
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
            print(f"Reading UDB for {hash} ...")
        user_id: Any = UserDB.RDB.get(hash)
        if self.verbose:
            if user_id is None:
                print(f"No user found for hash {hash}")
            else:
                assert isinstance(user_id, str)
                print(f"Found user {user_id} for hash {hash}")
        return user_id

    @override
    def set(self, hash: str, user_id: str) -> bool:
        if self.verbose:
            print(f"writing to UDB for {hash} ...")
        ret: Any = UserDB.RDB.set(hash, user_id)
        assert isinstance(ret, bool)
        if self.verbose:
            result: str = "Successful" if ret else "Failed"
            print(f"Write {result}!")
        return ret

    @override
    def delete(self, hash: str) -> bool:
        if self.verbose:
            print("Deleting from UDB...")
        ret: Any = UserDB.RDB.delete(hash)
        assert isinstance(ret, int)
        return ret > 0  # Returns number of keys deleted, should be 1 if successful


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
    def get(self, serialized_id: str) -> Optional[str]:
        if self.verbose:
            print(f"Reading NDB for ID {serialized_id} ...")
        serialized_data: Any = NodeDB.RDB.get(serialized_id)
        if self.verbose:
            if serialized_data is None:
                print(f"No data found for ID {serialized_id}")
            else:
                assert isinstance(serialized_data, str)
                print(f"Found data for ID {serialized_id}")
        return serialized_data

    @override
    def set(self, serialized_id: str, serialized_data: str) -> bool:
        if self.verbose:
            print(f"writing to NDB for ID {serialized_id} ...")
        ret: Any = NodeDB.RDB.set(serialized_id, serialized_data)
        assert isinstance(ret, bool)
        if self.verbose:
            result: str = "Successful" if ret else "Failed"
            print(f"Write {result}!")
        return ret

    @override
    def delete(self, serialized_id: str) -> bool:
        if self.verbose:
            print(f"Deleting from NDB for ID {serialized_id} ...")
        ret: Any = NodeDB.RDB.delete(serialized_id)
        assert isinstance(ret, int)
        return ret > 0  # Returns number of keys deleted, should be 1 if successful
