# !/usr/bin/env python3
# pyre-strict
from pyre_extensions import override

from ..node import Node
from ..pid import PID
from .descriptor import Descriptor


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
