#!/usr/bin/env python3
from typing_extensions import override
from webapp.web.llm.llm_engine import LLM_ENGINE as llm

from ..mutators.mutator import Mutator, MutatorResult, MutatorInput


class DedupeMutator(Mutator):
    """
    A mutator that removes duplicate nodes based on similarity.
    Uses LLM to determine if two nodes are duplicates.

    The duplicate nodes found lower in depth in the tree will be deleted,
    i.e only the first node found in level order will be kept
    """

    def __init__(self):
        super().__init__("DedupeMutator")

    @override
    def mutate(self, input: MutatorInput) -> MutatorResult:
        # For the given node, find all nodes that are similar to it
        # (should be 1 LLM call)
        # and then call DeleteMutator on those nodes
        return MutatorResult(
            success=False,
            message="Not implemented yet",
        )
