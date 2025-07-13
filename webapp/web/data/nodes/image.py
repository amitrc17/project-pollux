# !/usr/bin/env python3
# pyre-strict
"""
Image is a special type of Pollux entity that stores image data
that users upload. At some point, asset tree nodes and Image nodes
should be inherting from different base classes i.e we should make
a base class for all asset tree nodes.
"""
import base64
from io import BufferedReader
import uuid
from typing import Optional
import uuid
from pyre_extensions import override

from ..node import Node
from ..pid import PID
from ..database import ImageStore


class Image(Node):
    def __init__(
        self,
        image_path: Optional[str] = None,
        image_data: Optional[str] = None,
        image_file_buffer: Optional[BufferedReader] = None,
        disable_commit: bool = False,
    ) -> None:
        assert (
            image_path is not None
            or image_data is not None
            or image_file_buffer is not None
        ), "Need image data, image path or image file buffer to create Image"
        if image_path is not None:
            with open(image_path, "rb") as img:
                self.image_data: str = base64.b64encode(img.read()).decode("utf-8")
        elif image_data is not None:
            self.image_data: str = image_data
        else:
            self.image_data: str = base64.b64encode(image_file_buffer.read()).decode(  # type: ignore
                "utf-8"
            )
        print("Image data extracted: ", len(self.image_data))
        # Initialize the Node base params, no need to call
        # commit because Node.__init__ will do that for us
        super().__init__(
            "Image:" + str(uuid.uuid1()),
            disable_commit=disable_commit,
        )  # TODO: Figure out a better naming scheme

    @override
    def commit(self) -> bool:
        """
        Images need to be stored in ImageStore, so we do that here.
        We still want to store images to NodeDB because Images are Nodes,
        so we call super().commit() to make sure that happens.
        """
        print("Committing image to Image Store...")
        ims = ImageStore()
        ims.set(self.id.serialize(), self.image_data)
        print(
            f"Committed image of size: {len(self.image_data)} and ID: {self.id.serialize()}"
        )
        return super().commit()

    @override
    def edge_validation(self, node_id: PID) -> None:
        raise RuntimeError("Images cannot have edges, for now")
