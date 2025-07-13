from random import randint
from typing import List
from pyre_extensions import override

"""
    Universal Pollux ID. All Nodes & Edges have PIDs.

    A randomized integer between 1 and 2**32.

    If the constructor is passed an integer then the ID
    is set to that integer, otherwise a random number is
    chosen between 1 and 2**32.

    TODO: Change this to Integer value of SHA hash
"""


class PID(int):
    ptype: str

    def __new__(cls, *args, **kwargs) -> "PID":
        if len(args) == 1:
            self: PID = super().__new__(cls, randint(1, 2**32))
        else:
            self: PID = super().__new__(cls, args[1])
        self.ptype = type(args[0]).__name__
        return self

    def serialize(self) -> str:
        return f"{self.ptype}:{self}"

    @override
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, PID):
            return NotImplemented
        if self.serialize() == value.serialize():
            return True
        return False

    @override
    def __hash__(self) -> int:
        return hash(self.serialize())

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
