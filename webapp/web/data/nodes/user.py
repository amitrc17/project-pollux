#!/usr/bin/env python3
from hashlib import sha256
from io import BufferedReader
from collections import deque
from typing import List, Dict, Optional, Set, Tuple, Union, override
from webapp.web.llm.llm_engine import LLM_ENGINE as llm
import logging


from ..node import Node
from ..pid import PID
from ..database import UserDB
from ..factories.node_factory import NodeFactory
from .image import Image
from .asset import Asset
from .descriptor import Descriptor

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("pollux")


class User(Node):
    def __init__(self, name: str, disable_commit: bool = False) -> None:
        super().__init__(name, disable_commit=disable_commit)
        if not disable_commit:
            self.commit()

    @override
    def edge_validation(self, node_id: PID) -> None:
        # TODO: Instead of hardcoding ptypes here, we should have an enum
        # and have that enum exist outside of any of these classes
        assert node_id.ptype in [
            "Descriptor",
            "Image",
        ], f"Users must only have edges to Descriptors or Images, for now Users cannot directly link to Assets, given ptype: {node_id.ptype}"  # noqa
        assert node_id not in self.edges, "User cannot have duplicate edges"

    @classmethod
    def login(cls, user_name: str, password: str) -> "User":
        # Check if user exists in DB
        udb: UserDB = UserDB()
        user_id: Optional[str] = udb.get(
            sha256((user_name + password).encode()).hexdigest()
        )
        assert user_id is not None, "user not found"

        # pull user from Node DB
        # TODO: Understand the implications of using Node DB over UserDB
        user: Node = Node.from_id(user_id, NodeFactory())
        assert isinstance(user, User)
        return user

    @classmethod
    def register(cls, user_name: str, password: str) -> "User":
        udb: UserDB = UserDB()
        hashed_password: str = sha256((user_name + password).encode()).hexdigest()

        # check if user already exists
        existing_user_id: Optional[str] = udb.get(hashed_password)
        if existing_user_id is not None:
            raise RuntimeError("User already exists, please login")
        user: User = User(user_name)
        udb.set(hashed_password, user.id.serialize())
        return user

    def attach_image(
        self,
        image_path: Optional[str] = None,
        image_data: Optional[str] = None,
        image_file_buffer: Optional[BufferedReader] = None,
        image: Optional[Image] = None,
    ) -> Image:
        """
        Attaches an image to the User making them the owner of the provided image.
        Many ways to provide the image, check args below to see what you need.

        Args:
            image_path (Optional[str], optional): Path to raw image file. Defaults to None.
            image_data (Optional[str], optional): Image read as binary file decoded to string.
            Defaults to None.
            image_file_buffer (Optional[BufferedReader], optional): Image binary data opened
            as bufferedreader object. Defaults to None.
            image (Optional[Image], optional): An instance of Image class. Defaults to None.

        Raises:
            RuntimeError: In case none of the supported image sources are provided

        Returns:
            image: If the image is successfully attached, then we return the image object
        """
        assert (
            image_path is not None
            or image_data is not None
            or image_file_buffer is not None
            or image is not None
        ), "Need image data, image path, image file buffer or Image object to attach image"
        image_obj: Image
        if image_path is not None:
            image_obj = Image(image_path=image_path)
        elif image_file_buffer is not None:
            image_obj = Image(image_file_buffer=image_file_buffer)
        elif image_data is not None:
            image_obj = Image(image_data=image_data)
        elif image is not None:
            image_obj = image
        else:
            raise RuntimeError("No valid image source provided")

        self.add_edge(image_obj.id)
        asset_names: List[str] = llm.describe_image(
            image_data=image_obj.image_data
        ).split(",")
        for asset_name in asset_names:
            asset: Asset = Asset(asset_name)
            self.consume(asset)

        return image_obj

    def get_images(self) -> List[Image]:
        """
        Get all images attached to User
        Returns:
            List[Image]: A possibly empty list of Image objects
        """
        images: List[Image] = []
        for node_id in self.edges:
            if node_id.ptype == Image.__name__:
                node: Node = Node.from_id(node_id, NodeFactory())
                assert isinstance(node, Image)  # This should always be true
                images.append(node)

        return images

    def _level_order_traversal(
        self,
    ) -> Tuple[List[List[PID]], Dict[PID, PID], List[PID]]:
        q = deque([(self.id, 1)])
        vis = {self.id}
        levels: List[List[PID]] = []
        parents: Dict[PID, PID] = {}
        leaves: List[PID] = []

        while len(q) > 0:
            node_id, cur_level = q.pop()
            node: Node = Node.from_id(node_id, NodeFactory())
            if len(levels) < cur_level:
                levels.append([])

            levels[-1].append(node.id)
            has_children: bool = False
            for next_node_id in node.edges:
                # We don't want to visit Images
                if next_node_id not in vis and next_node_id.ptype != Image.__name__:
                    has_children = True
                    parents[next_node_id] = node_id
                    vis.add(next_node_id)
                    q.appendleft((next_node_id, cur_level + 1))

            if not has_children:
                leaves.append(node_id)
        return levels, parents, leaves

    def _dfs(self, cur: Node, node: Node) -> None:
        if isinstance(cur, Asset):
            raise RuntimeError(
                "We seem to have traversed down to an existing Asset while consuming this Asset"  # noqa
            )

        buckets: List[str] = []
        name_to_id_mapping: Dict[str, PID] = {}
        for child_id in cur.edges:
            # no need to visit Images
            if child_id.ptype in [Image.__name__]:
                continue

            # no need to visit Assets when we are consuming an Asset
            if child_id.ptype in [Asset.__name__]:
                if node.id.ptype == Asset.__name__:
                    continue

            child: Node = Node.from_id(child_id, NodeFactory())
            child_str: str = child.name
            buckets.append(child_str)
            name_to_id_mapping[child_str.lower().strip()] = child_id

        # TODO: We should make this more robust!
        if node.name.lower().strip() in name_to_id_mapping:
            # If the Asset already exists in the tree, we don't need to do anything
            # and can just return
            return

        response: str = ""
        if len(buckets) == 0:
            # No edges to any descriptors
            LOGGER.warning(f"No edges to any descriptors! cur: {cur.name}")  # noqa
            cur.add_edge(node.id)
            return
        response = llm.find_bucket(buckets=buckets, asset_name=node.name)  # noqa
        LOGGER.info(f"Found bucket: {response}")
        if response.lower().strip() in name_to_id_mapping:
            # In case llm responds with an existing bucket
            # continue DFS into child
            return self._dfs(
                Node.from_id(
                    name_to_id_mapping[response.lower().strip()], NodeFactory()
                ),
                node,
            )
        elif response.lower() == llm.EMPTY_BUCKET_STRING.lower():
            assert (
                len(buckets) > 0
            ), "buckets has to have elements at this point"  # noqa
            if node.id.ptype == Asset.__name__:
                new_bucket_name: str = llm.suggest_bucket(
                    buckets=buckets, asset_name=node.name
                )
                LOGGER.info(f"Suggest creating bucket: {new_bucket_name}")
                if new_bucket_name.lower().strip() in name_to_id_mapping:
                    # The suggested bucket already exists, so we can just
                    # add the asset to that bucket
                    return self._dfs(
                        Node.from_id(
                            name_to_id_mapping[response.lower().strip()], NodeFactory()
                        ),
                        node,
                    )
                # create a new descriptor (i.e a bucket)
                new_node = Descriptor(new_bucket_name)
                # Add edge from parent to new descriptor
                cur.add_edge(new_node.id)
                # Add an edge from new descriptor to Asset being added to tree
                new_node.add_edge(node.id)
                return
            else:  # Node is a Descriptor
                sub_buckets: List[str] = llm.find_sub_buckets(
                    buckets=buckets, target_bucket=node.name
                ).split(",")

                if len(sub_buckets) == 0:
                    # An error occurred, since LLM should at least return "neither"
                    raise RuntimeError(
                        f"LLM returned no sub buckets for bucket:{node.name}, sub buckets:{buckets}"  # noqa
                    )
                elif (
                    len(sub_buckets) == 1
                    and sub_buckets[0].lower() == llm.EMPTY_BUCKET_STRING.lower()
                ):
                    # None of the sub buckets match the bucket so the bucket
                    # can be a direct child of current node
                    LOGGER.info("No sub buckets found, adding directly to parent")
                    cur.add_edge(node.id)
                    return
                else:
                    # LLM returned some sub buckets, so we need to add the
                    # descriptor as a child of the current node and then add
                    # the sub buckets as children of the descriptor
                    LOGGER.info(
                        f"Found sub buckets: {sub_buckets} matching bucket: {node.name}"
                    )  # noqa
                    cur.add_edge(node.id)
                    for sub_bucket in sub_buckets:
                        assert (
                            sub_bucket.lower().strip() in name_to_id_mapping
                        ), f"Sub bucket {sub_bucket} not found in buckets {buckets}!"  # noqa
                        # remember to remove the edge from the parent
                        # TODO: We can probably reduce DB operations by not commiting everytime
                        # and instead only commit once at the end of the _dfs operation
                        cur.remove_edge(name_to_id_mapping[sub_bucket.lower().strip()])
                        node.add_edge(name_to_id_mapping[sub_bucket.lower().strip()])
                    return
        else:
            raise RuntimeError(
                f"LLM returned an unsupported bucket name:{response}"
            )  # noqa

    @override
    def serialize(self) -> str:
        return super().serialize()

    def consume(self, node: Node) -> None:
        LOGGER.info("Begin traversal...")
        assert node.id.ptype not in [
            User.__name__,
            Image.__name__,
        ], "Cannot consume User or Image nodes"  # noqa
        self._dfs(self, node)

    def serialize_forest(self) -> str:
        # Since level order traversal returns both the levels and the parents
        # we only use the levels and pull out the names from the concrete Node
        # objects.
        levels_pid: List[List[PID]] = self._level_order_traversal()[0]
        levels: List[List[str]] = []
        for level in levels_pid:
            levels.append([Node.from_id(x, NodeFactory()).name for x in level])
        ret: str = ""
        for level_str in levels:
            ret += "\n" + "\t".join(level_str)

        return ret

    def get_asset_tree_info_for_visualization(
        self,
    ) -> List[Dict[str, Union[str, int]]]:
        """
        A utility function to get all nodes of the asset tree in level order as well
        as edge mapping (as a parent-child mapping) of the tree. This is useful for
        visualizing the tree.
        """
        levels, parents, leaves = self._level_order_traversal()
        nodes_info: List[Dict[str, Union[str, int]]] = []
        cur_level: int = len(levels)
        h_levels: Dict[PID, int] = {}

        # Assign h_level to leaves first.
        # All leaves are incrementally assigned h_levels
        # This dictates the total width of the tree. All non-leaf nodes will have
        # h_levels assigned based on the average of their children's h_levels
        for idx, leaf in enumerate(leaves):
            h_levels[leaf] = idx + 1
        leaves_set: Set[PID] = set(leaves)

        # We go level-wise from bottom to top to make sure all children of a node
        # are processed before the node itself.
        for level in levels[::-1]:
            for node_id in level:
                node: Node = Node.from_id(node_id, NodeFactory())

                # All nodes being processed at this point should have h_level assigned
                assert (
                    h_levels.get(node_id, -1) != -1
                ), f"Horizontal level not found for node: {node_id.serialize()} during processing!!"

                # For non-leaf nodes, assign the average of their children's h_levels.
                # The sum of h_levels of all children is already assigned to the current node.
                # We must process the current node before sending the h_level to the parent.
                if node_id not in leaves_set:
                    h_levels[node_id] = h_levels[node_id] // len(node.edges)

                node_info: Dict[str, Union[str, int]] = {
                    "id": node_id.serialize(),
                    "label": node.name,
                    "horizontal_level": h_levels[node_id],
                    "vertical_level": cur_level,
                    "type": node.id.ptype,
                }
                # Add to the h_level of the parent node to maintain the sum of children
                if parents.get(node_id) is not None:
                    h_levels[parents[node_id]] = (
                        h_levels.get(parents[node_id], 0) + h_levels[node_id]
                    )
                    # Root node will not have a parent so we place this assignment here
                    node_info["parent"] = parents[node_id].serialize()
                nodes_info.append(node_info)
            cur_level -= 1
        return nodes_info
