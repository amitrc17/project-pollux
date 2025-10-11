#!/usr/bin/env python3
# pyre-strict
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
import logging

from ..data.node import Node
from ..data.pid import PID
from ..data.nodes.user import User
from ..data.nodes.descriptor import Descriptor
from ..data.nodes.asset import Asset
from ..data.asset_tree import AssetTree
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO)


@dataclass
class MutatorResult:
    """
    Standard result object for mutator operations.
    Contains success status, processed nodes, and any relevant metadata.
    """

    success: bool
    message: str = ""
    modified_nodes: List[Node] = field(default_factory=list)
    created_nodes: List[Node] = field(default_factory=list)
    deleted_node_ids: List[PID] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_all_affected_nodes(self) -> List[Node]:
        """Get all nodes that were affected by the mutator operation."""
        return self.modified_nodes + self.created_nodes


@dataclass
class MutatorInput:
    """
    Input data for mutator operations.
    Contains either an AssetTree or a specific set of nodes to operate on.
    If both are provided, the AssetTree will be used to derive the nodes.
    Have to provide at least one of the two
    """

    asset_tree: Optional[AssetTree] = None
    nodes: Optional[List[Node]] = None
    data: Optional[Dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self):
        if not self.asset_tree and not self.nodes:
            raise ValueError("MutatorInput must contain either an AssetTree or nodes")


class Mutator(ABC):
    """
    Abstract base class for all mutators that operate on Asset Trees and Nodes.

    Mutators can operate on:
    1. A complete Asset Tree (for tree-wide operations)
    2. A specific set of nodes (for targeted operations)

    """

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"pollux.mutator.{name}")

    @abstractmethod
    def mutate(self, input: MutatorInput) -> MutatorResult:
        """
        Execute the mutator on an entire Asset Tree.

        Args:
            input: MutatorInput containing either an AssetTree or a specific set of nodes

        Returns:
            MutatorResult with operation details and affected nodes
        """
        raise NotImplementedError("Mutators must implement mutate method")

    def validate(self, input: MutatorInput) -> bool:
        """
        Validate that the provided nodes are suitable for this mutator.
        Override this method to add mutator-specific validation.

        Args:
            input: MutatorInput containing either an AssetTree or a specific set of nodes

        Returns:
            True if nodes are valid for this mutator
        """
        return True

    def log(self, operation: str, details: str = "") -> None:
        """
        Log a mutator operation.

        Args:
            operation: Description of the operation
            details: Additional details about the operation
        """
        message = f"[{self.name}] {operation}"
        if details:
            message += f" - {details}"
        self.logger.info(message)
