#!/usr/bin/env python3
from pyre_extensions import override

from ..node import Node
from ..pid import PID


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
        # TODO: Instead of hardcoding ptypes here, we should have an enum
        # and have that enum exist outside of any of these classes
        assert node_id.ptype in [
            "Descriptor",
            "Asset",
            "User",
        ], f"Descriptors are internal nodes and can have edges to Descriptors, Assets or Users only. Found ptype: {node_id.ptype}"  # noqa

    @override
    def serialize(self) -> str:
        return super().serialize()
