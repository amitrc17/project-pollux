#!/usr/bin/env python3
from typing import override
from webapp.web.llm.llm_engine import LLM_ENGINE as llm

from ..mutators.mutator import Mutator, MutatorResult, MutatorInput


class ExplodeNodeMutator(Mutator):
    """
    A mutator that explodes a single Descriptor node into multiple Asset nodes.
    This is useful for transforming a single Descriptor to something more granular.

    Input nodes must be Descriptors.
    """

    def __init__(self):
        super().__init__("ExplodeNodeMutator")

    @override
    def mutate(self, input: MutatorInput) -> MutatorResult:
        return MutatorResult(
            success=False,
            message="Not implemented yet",
        )

    def validate(self, input: MutatorInput) -> bool:
        if input.asset_tree and (not input.nodes or len(input.nodes) == 0):
            raise ValueError(
                "DeleteMutator requires a specific set of nodes to explode, not just an AssetTree."
            )
        if input.nodes and any(node.id.ptype != "Descriptor" for node in input.nodes):
            raise ValueError("ExplodeNodeMutator can only operate on Descriptor nodes.")
        return super().validate(input)
