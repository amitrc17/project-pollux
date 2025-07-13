# !/usr/bin/env python3
# pyre-strict
from abc import ABC, abstractmethod
from ..pid import PID

"""
    An abstract factory class for creating data objects.
    This class defines the interface for creating various data objects
    (nodes, images, descriptors, users, and PIDs) based on the provided PID.
"""


class Factory(ABC):
    SUPPORTED_TYPES: set[str] = set()

    @abstractmethod
    def gen(self, id: PID, data: dict) -> object:
        """
        Generate a data object based on the provided data.

        :param id: PID of the object to be generated.
        :param data: A dictionary containing the data required to create the object.
        :return: An instance of User, Node, Image, Descriptor etc.
        """
        pass
