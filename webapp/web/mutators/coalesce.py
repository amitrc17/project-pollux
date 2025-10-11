#!/usr/bin/env python3
from pyre_extensions import override
from webapp.web.llm.llm_engine import LLM_ENGINE as llm

from ..mutators.mutator import Mutator, MutatorResult, MutatorInput


class CoalesceMutator(Mutator):
    """
    A mutator that coalesces multiple nodes into a single node.
    All the children of the constituent nodes will become the children
    of the new node.

    All nodes must be Descriptors.
    """

    def __init__(self):
        super().__init__("CoalesceMutator")

    @override
    def mutate(self, input: MutatorInput) -> MutatorResult:
        self.validate(input)
        
        return MutatorResult(
            success=False,
            message="Not implemented yet",
        )

    def validate(self, input: MutatorInput) -> bool:
        if input.asset_tree and (not input.nodes or len(input.nodes) == 0):
            raise ValueError(
                "CoalesceMutator requires a specific set of nodes to coalesce, not just an AssetTree."
            )
        if input.nodes and any(node.id.ptype != "Descriptor" for node in input.nodes):
            raise ValueError("CoalesceMutator can only operate on Descriptor nodes.")
        return super().validate(input)
