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

import time
from abc import ABC, abstractmethod
from collections import deque
from random import randint
from typing import List, Dict, Union
from pyre_extensions import override
from llm.llm_engine import LLM_ENGINE as llm
import logging
import json

# logging.root.setLevel(logging.NOTSET)
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("pollux")

# TODO: Turn this into a fast key-value db storage
__GLOBAL_STORE__ = dict()


class PID(int):
    """
    Universal Pollux ID. All Nodes & Edges have PIDs.

    A randomized integer between 1 and 2**32.

    If the constructor is passed an integer then the ID
    is set to that integer, otherwise a random number is
    chosen between 1 and 2**32.

    TODO: Change this to Integer value of SHA hash
    """

    def __new__(cls, *args, **kwargs) -> "PID":
        if len(args) == 1:
            self: PID = super().__new__(cls, randint(1, 2**32))
        else:
            self: PID = super().__new__(cls, args[1])
        self.ptype = type(args[0]).__name__
        return self

    def serialize(self) -> str:
        return f"{self.ptype}:{self}"

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
    A Node within the forest. Can be any sort of concept: Asset or Descriptor.
    """

    def __init__(self, name) -> None:
        self.id: PID = PID(self)
        self.creation_time: float = time.time()
        self.update_time: float = self.creation_time
        self.edges: List[PID] = []
        self.name: str = name

        # Important!! This will add all nodes (users, descriptors, assets)
        # to an in memory cache for fast lookup and graph traversal.
        global __GLOBAL_STORE__
        __GLOBAL_STORE__[self.id] = self

    def add_edge(self, node_id: PID) -> None:
        self.edge_validation(node_id)
        self.edges.append(node_id)
        self.update_time = time.time()

    @abstractmethod
    def edge_validation(self, node_id: PID) -> None:
        """
        Ensures the edge being created is a valid edge, if not valid
        this method should throw an appropriate error
        """
        raise NotImplementedError("Nodes must implement Edge Validation")

    def serialize(self) -> str:
        data: Dict[str, Union[str, List[str]]] = {
            "id": self.id.serialize(),
            "creation_time": self.creation_time,
            "update_time": self.update_time,
            "edges": [x.serialize() for x in self.edges],
            "name": self.name,
        }
        return json.dumps(data)

    @classmethod
    def deserialize(cls, seralized: str) -> "Node":
        data: Dict[str, Union[str, List[str]]] = json.loads(seralized)
        id: PID = PID.deserialize(data["id"])
        edges: List[PID] = [PID.deserialize(x) for x in data["edges"]]
        if id.ptype == Descriptor.__name__:
            n = Descriptor(data["name"])
        elif id.ptype == Asset.__name__:
            n = Asset(data["name"])
        elif id.ptype == User.__name__:
            n = User(data["name"])
        else:
            raise NotImplementedError(
                f"The deserialized ptype is not supported: {id.ptype}"
            )
        n.creation_time = data["creation_time"]
        n.update_time = data["update_time"]
        n.id = id
        n.edges = edges
        return n


class Edge:
    def __init__(self, left: Node, right: Node) -> None:
        self.left: PID = left.id
        self.right: PID = right.id
        self.id: PID = PID(self)
        left.add_edge(self.right)
        right.add_edge(self.left)


class Asset(Node):
    def __init__(self, name: str):
        # This will initialize the ID
        super().__init__(name)

    @override
    def edge_validation(self, node_id: PID) -> None:
        assert node_id.ptype in [Descriptor.__name__], "All assets must be"
        " leaf nodes in the forest so can only have edges coming"
        " from Descriptors"

    @override
    def serialize(self) -> str:
        return super().serialize()


class Descriptor(Node):
    def __init__(self, name: str):
        # This will initialize the ID
        super().__init__(name)

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
    def __init__(self, name: str) -> None:
        super().__init__(name)

    @override
    def edge_validation(self, node_id: PID) -> None:
        assert node_id.ptype in [
            Descriptor.__name__
        ], "Users must only have edges to Descriptors, for now Users cannot directly link to Assets"  # noqa

    def _level_order_traversal(self) -> List[List[str]]:
        global __GLOBAL_STORE__

        q = deque([(self.id, 1)])
        vis = {self.id}
        levels: List[List[str]] = []

        while len(q) > 0:
            node_id, cur_level = q.pop()
            node: Node = __GLOBAL_STORE__[node_id]
            if len(levels) < cur_level:
                levels.append([])

            levels[-1].append(node.serialize())
            for next_node_id in node.edges:
                if next_node_id not in vis:
                    vis.add(next_node_id)
                    q.appendleft((next_node_id, cur_level + 1))
        return levels

    def _dfs(self, cur: Node, asset: Node) -> None:
        if isinstance(cur, Asset):
            raise RuntimeError(
                "We seem to have traversed down to an existing Asset while consuming this Asset"  # noqa
            )

        global __GLOBAL_STORE__
        buckets = []
        name_to_id_mapping: Dict[str, PID] = {}
        for child_id in cur.edges:
            if child_id.ptype in [Asset.__name__]:
                # no need to visit Asset nodes
                continue

            child: Node = __GLOBAL_STORE__[child_id]
            child_str: str = child.serialize()
            buckets.append(child_str)
            name_to_id_mapping[child_str] = child_id

        response: str = ""
        if len(buckets) == 0:
            # No edges to any descriptors
            LOGGER.warning(
                f"No edges to any descriptors! cur: {cur.serialize()}"
            )  # noqa
            cur.add_edge(asset.id)
            return
        response = llm.find_bucket(
            buckets=buckets, asset_name=asset.serialize()
        )  # noqa
        LOGGER.info(f"Found bucket: {response}")
        if response in name_to_id_mapping:
            # In case llm responds with an existing bucket
            # continue DFS into child
            self._dfs(__GLOBAL_STORE__[name_to_id_mapping[response]], asset)
        elif response.lower() == llm.EMPTY_BUCKET_STRING.lower():
            assert (
                len(buckets) > 0
            ), "buckets has to have elements at this point"  # noqa
            new_bucket_name: str = llm.suggest_bucket(
                buckets=buckets, asset_name=asset.serialize()
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
        ret = ""
        for level in levels:
            ret += "\n" + "\t".join(level)

        return ret
