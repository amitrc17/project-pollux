#!/usr/bin/env python3
from turtle import mode
from typing import Dict, Any, override
from webapp.web.llm.llm_engine import LLM_ENGINE as llm

from ..mutators.mutator import Mutator, MutatorResult, MutatorInput
from ..data.node import Node
from ..data.pid import PID


class DeleteMutator(Mutator):
    """
    A mutator that deletes nodes from an Asset Tree.

    Does not support Inputs with only asset tree provided.
    If the deleted node is:
    - A Descriptor: All its children become children of its parent
    - An Asset: It is simply removed
    - A User: Not supported yet
    - An Image: Will simply be deleted
    When a node is deleted it is also removed from the DB (UserDB, ImageStore, NodeDB etc.)
    """

    def __init__(self):
        super().__init__("DeleteMutator")

    @override
    def mutate(self, input: MutatorInput) -> MutatorResult:
        self.validate(input)
        # For the given node, delete it and its children
        assert (
            input.nodes is not None
        ), "DeleteMutator requires specific nodes to delete."
        for node in input.nodes:
            assert (
                input.asset_tree is not None
            ), "DeleteMutator requires an AssetTree to operate on."
            try:
                input.asset_tree.DFS(
                    self.operation,
                    context={"node_id": node.id, "parents": {}},
                )
            except Exception as e:
                return MutatorResult(
                    success=False,
                    message=f"Failed to delete node {node.id.serialize()}: {str(e)}",
                )

        return MutatorResult(
            success=True,
            message=f"Successfully deleted {len(input.nodes)} nodes.",
            modified_nodes=[],
            created_nodes=[],
            deleted_node_ids=[node.id for node in input.nodes],
            metadata={},
        )

    def operation(self, node: Node, context: Dict[str, Any]) -> None:
        node_id_to_delete = context.get("node_id")
        assert node_id_to_delete is not None and isinstance(
            node_id_to_delete, PID
        ), "Node ID to delete must be provided in context."
        # Assign parents to the context for deletion logic
        parents: Any = context.get("parents")
        assert parents is not None and isinstance(
            parents, Dict
        ), "Parents must be provided in context."
        for child_id in node.edges:
            parents[child_id] = node.id  # Store parent-child relationship

        if node.id != node_id_to_delete:
            return

        # Assign all children to the parent
        parent_node = parents.get(node.id)
        assert parent_node is not None and isinstance(
            parent_node, Node
        ), "Parent node must be found in context."
        for child_id in node.edges:
            # Move child to parent, no need to commit till later
            parent_node.add_edge(child_id, True)
        # Remove the node from the parent, now we can commit
        parent_node.remove_edge(node.id, False)

        # Perform the deletion logic here
        Node.delete(node.id)
        context["early_exit"] = True  # Stop further processing

    def validate(self, input: MutatorInput) -> bool:
        assert (
            input.nodes is not None and len(input.nodes) > 0
        ), "DeleteMutator requires specific nodes to delete."
        assert (
            input.asset_tree is not None
        ), "DeleteMutator requires an AssetTree to operate on."
        assert not any(
            node.id.ptype == "User" or node.id.ptype == "Image" for node in input.nodes
        ), "DeleteMutator does not support deleting Users or Images yet."
        return super().validate(input)
