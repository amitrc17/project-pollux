# !/usr/bin/env python3
# pyre-strict
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Union, Optional
import json

from .database import NodeDB, UserDB
from .pid import PID
from .factories.factory import Factory

"""
    A pollux entity. The base class for all objects within the Pollux
    universe. All Nodes have a unique ID (PID), a creation time, an update time
    and are connected to other nodes via edges.

    For now, edges themselves are logical constructs and don't have
    an explicit representation. Nodes store connections as a raw list of
    PIDs that they are connected to.
    
    Edges are not bidirectional, i.e if Node A has an edge to Node B,
    Node B does not have an edge to Node A. This is a design choice to
    simplify the edge management logic. This is not enforced at the node level,
    so it is up to you to ensure that this assumption holds true.
"""


class Node(ABC):

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

    def remove_edge(self, node_id: PID, disable_commit: bool = False) -> None:
        self.edges.remove(node_id)
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
    def deserialize(cls, seralized: str, factory: Factory) -> "Node":
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
        if id.ptype not in factory.SUPPORTED_TYPES:
            raise NotImplementedError(
                f"The deserialized ptype is not supported: {id.ptype}"
            )
        n: object = factory.gen(id, data)
        if not isinstance(n, Node):
            raise TypeError(
                f"Factory did not return a Node instance, got {type(n)} instead"
            )
        n.creation_time = data["creation_time"]  # type: ignore
        n.update_time = data["update_time"]  # type: ignore
        n.id = id
        n.edges = edges
        return n

    @classmethod
    def from_id(cls, node_id: Union[PID, str], factory: Factory) -> "Node":
        ndb = NodeDB()
        if isinstance(node_id, str):
            node_id = PID.deserialize(node_id)
        assert isinstance(node_id, PID)
        serialized_result: Optional[str] = ndb.get(node_id.serialize())
        if serialized_result is None:
            raise ValueError(f"Node with id {node_id.serialize()} not found in NDB")
        return Node.deserialize(serialized_result, factory)

    @classmethod
    def delete(cls, node_id: Union[PID, str]) -> bool:
        ndb = NodeDB()
        if isinstance(node_id, str):
            node_id = PID.deserialize(node_id)
        assert isinstance(node_id, PID)
        if node_id.ptype == "User" or node_id.ptype == "Image":
            raise NotImplementedError("Cannot delete User or Image nodes directly yet")
        return ndb.delete(node_id.serialize())
