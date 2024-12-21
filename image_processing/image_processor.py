#!/usr/bin/env python3
# pyre-strict


class Image:
    """
    An Image is essentially a photo that can be a raw camera output or an
    upload from disk. This class also has methods for loading and mild
    processing of images.
    """

    def __init__(self) -> None:
        pass

    @staticmethod
    def load() -> "Image":
        return Image()
