#!/usr/bin/env python3


"""
    An Asset Forest is a representation of the possessions of a user
    as tracked by Pollux. The entire forest belongs to 1 user. Every
    Tree in the forest is rooted at a relatively high level category. We
    cannot predict all categories, so they are always dynamically created.

    All non-leaf nodes in the forest are Descriptors, however some Descriptors
    might be leaf nodes. Descriptors that are leaf nodes indicate the User does
    not possess any Asset fitting that Description. Descriptors may describe:
    Location, Usage, Physical Attributes, Compositional Attributes, and any
    other categorical information. Descriptors are tailored to the single
    owner User, i.e 2 users may have the same Descriptor that has different
    paths from the User to that particular Descriptor. 
    We will eventually use domain knowledge, user input
    and ML to split and splice Descriptors.

    Assets are leaf nodes. These represent the User's possessions. These likely
    came from User inputs: image, text, chat.
"""

import base64
from hashlib import sha256
from io import BufferedReader
import time
import uuid
from abc import ABC, abstractmethod
from collections import deque
from random import randint
from typing import Any, List, Dict, Optional, Union
import uuid
from openai import images
from pyre_extensions import override
from llm.llm_engine import LLM_ENGINE as llm
import logging
import json

from .database import NodeDB, UserDB, ImageStore

# logging.root.setLevel(logging.NOTSET)
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("pollux")


class PID(int):
    """
    Universal Pollux ID. All Nodes & Edges have PIDs.

    A randomized integer between 1 and 2**32.

    If the constructor is passed an integer then the ID
    is set to that integer, otherwise a random number is
    chosen between 1 and 2**32.

    TODO: Change this to Integer value of SHA hash
    """

    ptype: str

    def __new__(cls, *args, **kwargs) -> "PID":
        if len(args) == 1:
            self: PID = super().__new__(cls, randint(1, 2**32))
        else:
            self: PID = super().__new__(cls, args[1])
        self.ptype = type(args[0]).__name__
        return self

    def serialize(self) -> str:
        return f"{self.ptype}:{self}"

    @override
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, PID):
            return NotImplemented
        if self.serialize() == value.serialize():
            return True
        return False

    @override
    def __hash__(self) -> int:
        return hash(self.serialize())

    @classmethod
    def deserialize(cls, *args, **kwargs) -> "PID":
        assert len(args) >= 1, "We need serialized string to be present"
        serialized_str: str = args[0]

        split_string: List[str] = serialized_str.split(":")
        assert (
            len(split_string) == 2
        ), f"Serialized PID should be of format <ptype>:<ID>, got string {serialized_str}"  # noqa

        ptype, id = tuple(split_string)
        ret: PID = PID(id, id)  # Yes, that first id is a dummy
        ret.ptype = ptype
        return ret


class Node(ABC):
    """
    A pollux entity. The base class for all objects within the Pollux
    universe. All Nodes have a unique ID (PID), a creation time, an update time
    and are connected to other nodes via edges.

    For now, edges themselves are logical constructs and don't have
    an explicit representation. Nodes store connections as a raw list of
    PIDs that they are connected to.
    """

    def __init__(self, name: str, disable_commit: bool = False) -> None:
        self.id: PID = PID(self)
        self.creation_time: float = time.time()
        self.update_time: float = self.creation_time
        self.edges: List[PID] = []
        self.name: str = name
        if not disable_commit:
            self.commit()

    def add_edge(self, node_id: PID, disable_commit: bool = False) -> None:
        self.edge_validation(node_id)
        self.edges.append(node_id)
        self.update_time = time.time()
        if not disable_commit:
            self.commit()

    @abstractmethod
    def edge_validation(self, node_id: PID) -> None:
        """
        Ensures the edge being created is a valid edge, if not valid
        this method should throw an appropriate error
        """
        raise NotImplementedError("Nodes must implement Edge Validation")

    def commit(self) -> bool:
        """
        This method will commit the Node object to NodeDB.
        Make sure every Node child class calls this method in
        their constructor, unless you know what you're doing.

        Returns:
            bool: If the commit was successful
        """
        ndb = NodeDB()
        return ndb.set(self.id.serialize(), self.serialize())

    def serialize(self) -> str:
        data: Dict[str, Union[str, float, List[str]]] = {
            "id": self.id.serialize(),
            "creation_time": self.creation_time,
            "update_time": self.update_time,
            "edges": [x.serialize() for x in self.edges],
            "name": self.name,
        }
        return json.dumps(data)

    @classmethod
    def deserialize(cls, seralized: str) -> "Node":
        """
        For any new Node type, please make sure you add the
        relevant code for deserialization here. In the future,
        this method should just identify the ptype of the ID
        and then call the deserialize method from the Node
        child class.

        Args:
            seralized (str): Serialized node

        Raises:
            NotImplementedError: In case the ptype doesn't have
            a deserialize implementation, we throw.

        Returns:
            Node: Deserialized Node of appropriate ptype
        """
        data: Dict[str, Union[str, float, List[str]]] = json.loads(seralized)
        id: PID = PID.deserialize(data["id"])
        edges: List[PID] = [PID.deserialize(x) for x in data["edges"]]  # type: ignore
        # TODO: This should be calling deserialize from the child class
        if id.ptype == Descriptor.__name__:
            n = Descriptor(str(data["name"]), disable_commit=True)
        elif id.ptype == Asset.__name__:
            n = Asset(str(data["name"]), disable_commit=True)
        elif id.ptype == User.__name__:
            n = User(str(data["name"]), disable_commit=True)
        elif id.ptype == Image.__name__:
            # Special treatment for Image to load image data properly
            n = Image(image_data="placeholder_image_data", disable_commit=True)
            image_data: Optional[str] = ImageStore().get(id.serialize())
            assert (
                image_data is not None
            ), f"Image not found in Image Store for id: {id.serialize()}"
            n.image_data = image_data
        else:
            raise NotImplementedError(
                f"The deserialized ptype is not supported: {id.ptype}"
            )
        n.creation_time = data["creation_time"]  # type: ignore
        n.update_time = data["update_time"]  # type: ignore
        n.id = id
        n.edges = edges
        return n

    @classmethod
    def from_id(cls, node_id: Union[PID, str]) -> "Node":
        ndb = NodeDB()
        if isinstance(node_id, str):
            node_id = PID.deserialize(node_id)
        assert isinstance(node_id, PID)
        serilaized_result: str = ndb.get(node_id.serialize())
        return Node.deserialize(serilaized_result)


class Image(Node):
    """
    Image is a special type of Pollux entity that stores image data
    that users upload. At some point, asset tree nodes and Image nodes
    should be inherting from different base classes i.e we should make
    a base class for all asset tree nodes.
    """

    def __init__(
        self,
        image_path: Optional[str] = None,
        image_data: Optional[str] = None,
        image_file_buffer: Optional[BufferedReader] = None,
        disable_commit: bool = False,
    ) -> None:
        assert (
            image_path is not None
            or image_data is not None
            or image_file_buffer is not None
        ), "Need image data, image path or image file buffer to create Image"
        if image_path is not None:
            with open(image_path, "rb") as img:
                self.image_data: str = base64.b64encode(img.read()).decode("utf-8")
        elif image_data is not None:
            self.image_data: str = image_data
        else:
            self.image_data: str = base64.b64encode(image_file_buffer.read()).decode(  # type: ignore
                "utf-8"
            )
        print("Image data extracted: ", len(self.image_data))
        # Initialize the Node base params, no need to call
        # commit because Node.__init__ will do that for us
        super().__init__(
            "Image:" + str(uuid.uuid1()),
            disable_commit=disable_commit,
        )  # TODO: Figure out a better naming scheme

    @override
    def commit(self) -> bool:
        """
        Images need to be stored in ImageStore, so we do that here.
        We still want to store images to NodeDB because Images are Nodes,
        so we call super().commit() to make sure that happens.
        """
        print("Committing image to Image Store...")
        ims = ImageStore()
        ims.set(self.id.serialize(), self.image_data)
        print(
            f"Committed image of size: {len(self.image_data)} and ID: {self.id.serialize()}"
        )
        return super().commit()

    @override
    def edge_validation(self, node_id: PID) -> None:
        raise RuntimeError("Images cannot have edges, for now")


class Asset(Node):
    def __init__(self, name: str, disable_commit: bool = False):
        # This will initialize the ID
        super().__init__(name, disable_commit=disable_commit)
        if not disable_commit:
            self.commit()

    @override
    def edge_validation(self, node_id: PID) -> None:
        assert node_id.ptype in [Descriptor.__name__], "All assets must be"
        " leaf nodes in the forest so can only have edges coming"
        " from Descriptors"

    @override
    def serialize(self) -> str:
        return super().serialize()


class Descriptor(Node):
    def __init__(self, name: str, disable_commit: bool = False) -> None:
        """
        disable_commit: If set to True, the commit method will not be called,
        useful for creating dummy objects
        """
        # This will initialize the ID
        super().__init__(name, disable_commit=disable_commit)
        if not disable_commit:
            self.commit()

    @override
    def edge_validation(self, node_id: PID) -> None:
        assert node_id.ptype in [
            Descriptor.__name__,
            Asset.__name__,
            User.__name__,
        ], f"Descriptors are internal nodes and can have edges to Descriptors, Assets or Users only. Found ptype: {node_id.ptype}"  # noqa

    @override
    def serialize(self) -> str:
        return super().serialize()


class User(Node):
    def __init__(self, name: str, disable_commit: bool = False) -> None:
        super().__init__(name, disable_commit=disable_commit)
        if not disable_commit:
            self.commit()

    @override
    def edge_validation(self, node_id: PID) -> None:
        assert node_id.ptype in [
            Descriptor.__name__,
            Image.__name__,
        ], f"Users must only have edges to Descriptors or Images, for now Users cannot directly link to Assets, given ptype: {node_id.ptype}"  # noqa
        assert node_id not in self.edges, "User cannot have duplicate edges"

    @classmethod
    def login(cls, user_name: str, password: str) -> "User":
        # Check if user exists in DB
        udb: UserDB = UserDB()
        user_id: Optional[str] = udb.get(
            sha256((user_name + password).encode()).hexdigest()
        )
        assert user_id is not None, "user not found"

        # pull user from Node DB
        user: Node = Node.from_id(user_id)
        assert isinstance(user, User)
        return user

    @classmethod
    def register(cls, user_name: str, password: str) -> "User":
        udb: UserDB = UserDB()
        hashed_password: str = sha256((user_name + password).encode()).hexdigest()

        # check if user already exists
        existing_user_id: Optional[str] = udb.get(hashed_password)
        if existing_user_id is not None:
            raise RuntimeError("User already exists, please login")
        user: User = User(user_name)
        udb.set(hashed_password, user.id.serialize())
        return user

    def attach_image(
        self,
        image_path: Optional[str] = None,
        image_data: Optional[str] = None,
        image_file_buffer: Optional[BufferedReader] = None,
        image: Optional[Image] = None,
    ) -> Image:
        """
        Attaches an image to the User making them the owner of the provided image.
        Many ways to provide the image, check args below to see what you need.

        Args:
            image_path (Optional[str], optional): Path to raw image file. Defaults to None.
            image_data (Optional[str], optional): Image read as binary file decoded to string.
            Defaults to None.
            image_file_buffer (Optional[BufferedReader], optional): Image binary data opened
            as bufferedreader object. Defaults to None.
            image (Optional[Image], optional): An instance of Image class. Defaults to None.

        Raises:
            RuntimeError: In case none of the supported image sources are provided

        Returns:
            image: If the image is successfully attached, then we return the image object
        """
        assert (
            image_path is not None
            or image_data is not None
            or image_file_buffer is not None
            or image is not None
        ), "Need image data, image path, image file buffer or Image object to attach image"
        if image_path is not None:
            image_obj: Image = Image(image_path=image_path)
        elif image_file_buffer is not None:
            image_obj: Image = Image(image_file_buffer=image_file_buffer)
        elif image_data is not None:
            image_obj: Image = Image(image_data=image_data)
        elif image is not None:
            image_obj: Image = image
        else:
            raise RuntimeError("No valid image source provided")

        self.add_edge(image_obj.id)

        return image_obj

    def get_images(self) -> List[Image]:
        """
        Get all images attached to User
        Returns:
            List[Image]: A possibly empty list of Image objects
        """
        images: List[Image] = []
        for node_id in self.edges:
            if node_id.ptype == Image.__name__:
                node: Node = Node.from_id(node_id)
                assert isinstance(node, Image)  # This should always be true
                images.append(node)

        return images

    def _level_order_traversal(self) -> List[List[str]]:
        q = deque([(self.id, 1)])
        vis = {self.id}
        levels: List[List[str]] = []

        while len(q) > 0:
            node_id, cur_level = q.pop()
            node: Node = Node.from_id(node_id)
            if len(levels) < cur_level:
                levels.append([])

            levels[-1].append(node.name)
            for next_node_id in node.edges:
                # We don't want to visit Images
                if next_node_id not in vis and next_node_id.ptype != Image.__name__:
                    vis.add(next_node_id)
                    q.appendleft((next_node_id, cur_level + 1))
        return levels

    def _dfs(self, cur: Node, asset: Node) -> None:
        if isinstance(cur, Asset):
            raise RuntimeError(
                "We seem to have traversed down to an existing Asset while consuming this Asset"  # noqa
            )

        buckets: List[str] = []
        name_to_id_mapping: Dict[str, PID] = {}
        for child_id in cur.edges:
            if child_id.ptype in [Asset.__name__, Image.__name__]:
                # no need to visit Asset nodes or Images
                continue

            child: Node = Node.from_id(child_id)
            child_str: str = child.name
            buckets.append(child_str)
            name_to_id_mapping[child_str] = child_id

        response: str = ""
        if len(buckets) == 0:
            # No edges to any descriptors
            LOGGER.warning(f"No edges to any descriptors! cur: {cur.name}")  # noqa
            cur.add_edge(asset.id)
            return
        response = llm.find_bucket(buckets=buckets, asset_name=asset.name)  # noqa
        LOGGER.info(f"Found bucket: {response}")
        if response in name_to_id_mapping:
            # In case llm responds with an existing bucket
            # continue DFS into child
            self._dfs(Node.from_id(name_to_id_mapping[response]), asset)
        elif response.lower() == llm.EMPTY_BUCKET_STRING.lower():
            assert (
                len(buckets) > 0
            ), "buckets has to have elements at this point"  # noqa
            new_bucket_name: str = llm.suggest_bucket(
                buckets=buckets, asset_name=asset.name
            )
            LOGGER.info(f"Suggest creating bucket: {new_bucket_name}")
            # create a new descriptor (i.e a bucket)
            new_node = Descriptor(new_bucket_name)
            # Add edge from parent to new descriptor
            cur.add_edge(new_node.id)
            # Add an edge from new descriptor to Asset being added to tree
            new_node.add_edge(asset.id)
            return
        else:
            raise RuntimeError(
                f"LLM returned an unsupported bucket name:{response}"
            )  # noqa

    @override
    def serialize(self) -> str:
        return super().serialize()

    def consume(self, asset: Asset) -> None:
        LOGGER.info("Begin traversal...")
        self._dfs(self, asset)

    def serialize_forest(self) -> str:
        levels: List[List[str]] = self._level_order_traversal()
        ret: str = ""
        for level in levels:
            ret += "\n" + "\t".join(level)

        return ret
