from typing import Any, Callable, List, Dict, Optional, Set
from ..data.node import Node
from ..data.pid import PID
from ..data.nodes.user import User
from ..data.nodes.descriptor import Descriptor
from ..data.nodes.asset import Asset
from ..data.factories.node_factory import NodeFactory


"""
An encapsulation of an entire Asset Tree for a specific user.
This class provides utilities for traversing and manipulating the tree structure,
and allows for operations on the tree as a whole or on specific nodes.
"""


class AssetTree:
    """
    Represents an Asset Forest/Tree for a specific user.
    Provides utilities for traversing and manipulating the tree structure.

    TODO: Provide 2 methods which allow for ordered node-wise operations,
    by BFS and DFS.
    """

    def __init__(self, user: User):
        self.user: User = user
        # TODO: This cache is not being invalidated upon deletion, need to implement cache invalidation
        self._node_cache: Dict[PID, Node] = {}

    def get_all_nodes(self) -> List[Node]:
        """Get all nodes in the asset tree using BFS traversal."""
        visited: Set[PID] = set()
        nodes: List[Node] = []
        queue: List[PID] = [self.user.id]

        while queue:
            current_id = queue.pop(0)
            if current_id in visited:
                continue

            visited.add(current_id)
            node = self._get_node(current_id)
            nodes.append(node)

            # Add all connected nodes to queue
            for edge_id in node.edges:
                if edge_id not in visited:
                    queue.append(edge_id)

        return nodes

    def get_nodes_by_type(self, node_type: type) -> List[Node]:
        """Get all nodes of a specific type (Asset, Descriptor, User)."""
        all_nodes = self.get_all_nodes()
        return [node for node in all_nodes if isinstance(node, node_type)]

    def get_descriptors(self) -> List[Descriptor]:
        """Get all descriptor nodes in the tree."""
        all_nodes = self.get_all_nodes()
        return [node for node in all_nodes if isinstance(node, Descriptor)]

    def get_assets(self) -> List[Asset]:
        """Get all asset nodes in the tree."""
        all_nodes = self.get_all_nodes()
        return [node for node in all_nodes if isinstance(node, Asset)]

    def get_leaf_nodes(self) -> List[Node]:
        """Get all leaf nodes (nodes with no outgoing edges)."""
        all_nodes = self.get_all_nodes()
        return [node for node in all_nodes if len(node.edges) == 0]

    def get_node_depth(self, node_id: PID) -> int:
        """Get the depth of a node from the user root (0-indexed)."""
        visited: Set[PID] = set()
        queue: List[tuple[PID, int]] = [(self.user.id, 0)]

        while queue:
            current_id, depth = queue.pop(0)
            if current_id == node_id:
                return depth

            if current_id in visited:
                continue

            visited.add(current_id)
            node = self._get_node(current_id)

            for edge_id in node.edges:
                if edge_id not in visited:
                    queue.append((edge_id, depth + 1))

        return -1  # Node not found

    def _get_node(self, node_id: PID) -> Node:
        """Get a node by ID, using cache for performance."""
        if node_id not in self._node_cache:
            self._node_cache[node_id] = Node.from_id(node_id, NodeFactory())
        return self._node_cache[node_id]

    def BFS(
        self,
        operation: Callable[[Node, Dict[str, Any]], None],
        context: Dict[str, Any],
        start_node: Optional[Node] = None,
    ) -> List[Node]:
        """Perform a breadth-first search starting from a given node."""
        visited: Set[PID] = set()
        if start_node is None:
            start_node = self.user
        queue: List[Node] = [start_node]
        result: List[Node] = []

        while queue:
            current_node = queue.pop(0)
            if current_node.id in visited:
                continue

            visited.add(current_node.id)
            operation(current_node, context)
            result.append(current_node)

            for edge_id in current_node.edges:
                next_node = self._get_node(edge_id)
                if next_node.id not in visited:
                    queue.append(next_node)

        return result

    def DFS(
        self,
        operation: Callable[[Node, Dict[str, Any]], None],
        context: Dict[str, Any],
        start_node: Optional[Node] = None,
    ) -> List[Node]:
        """Perform a depth-first search starting from a given node."""
        visited: Set[PID] = set()
        if start_node is None:
            start_node = self.user
        result: List[Node] = []

        # recursive DFS function
        def dfs(node: Node):
            if node.id in visited:
                return
            visited.add(node.id)

            for edge_id in node.edges:
                next_node = self._get_node(edge_id)
                dfs(next_node)

            operation(node, context)
            if context.get("early_exit", False):
                return
            result.append(node)

        dfs(start_node)

        return result
