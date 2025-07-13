#!/usr/bin/env python3
from typing import Dict, Optional
from pyre_extensions import override

from ..database import ImageStore
from ..node import Node
from ..pid import PID
from .factory import Factory


class NodeFactory(Factory):
    """
    A factory class for creating Node objects based on the provided PID.
    This class implements the Factory interface and provides a method to generate Node objects.
    """

    # TODO: Instead of hardcoding ptypes here, we should have an enum
    # and have that enum exist outside of any of these classes
    SUPPORTED_TYPES: set[str] = {
        "Descriptor",
        "Asset",
        "User",
        "Image",
    }

    @override
    def gen(self, id: PID, data: Dict[str, str]) -> Node:
        """
        Generate a Node object based on the provided PID.

        :param id: PID of the node to be generated.
        :return: An instance of Node.
        """
        assert (
            id.ptype in self.SUPPORTED_TYPES
        ), f"The ptype {id.ptype} is not supported by this factory."

        # Create a Node instance based on the ptype
        if id.ptype == "Descriptor":
            from ..nodes.descriptor import Descriptor

            n = Descriptor(str(data["name"]), disable_commit=True)
        elif id.ptype == "Asset":
            from ..nodes.asset import Asset

            n = Asset(str(data["name"]), disable_commit=True)
        elif id.ptype == "User":
            from ..nodes.user import User

            n = User(str(data["name"]), disable_commit=True)
        elif id.ptype == "Image":
            from ..nodes.image import Image

            # Special treatment for Image to load image data properly
            n = Image(image_data="placeholder_image_data", disable_commit=True)
            image_data: Optional[str] = ImageStore().get(id.serialize())
            assert (
                image_data is not None
            ), f"Image not found in Image Store for id: {id.serialize()}"
            n.image_data = image_data
        else:
            raise NotImplementedError(
                f"The deserialized ptype is not supported: {id.ptype}"
            )
        assert isinstance(
            n, Node
        ), f"Factory did not return a Node instance, got {type(n)} instead"
        return n
