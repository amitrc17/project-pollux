#!/usr/bin/env python3
# pyre-strict

from typing import Dict, List, Union
from llm.llm_engine import OpenAILLM
from data.asset_forest import PID, User, Descriptor, Asset, Node, Image

from data.database import NodeDB, ImageStore


def test_serialize_tree():
    user = User("amitrc")
    washing_machine = Asset("washing machine")
    hair_dryer = Asset("hair dryer")
    appliance_category = Descriptor("appliance")
    indoor_category = Descriptor("indoor appliance")
    outdoor_category = Descriptor("outdoor appliance")
    appliance_category.add_edge(indoor_category.id)
    appliance_category.add_edge(outdoor_category.id)
    indoor_category.add_edge(washing_machine.id)
    indoor_category.add_edge(hair_dryer.id)
    user.add_edge(appliance_category.id)

    print(f"Serialized tree: {user.serialize_forest()}")


def test_describe_image():
    print("Loading LLM...")
    llm = OpenAILLM()
    print("LLM Loaded.")
    result: str = llm.describe_image(image_path="./data/sample.jpeg")
    print(f"LLM Response-> ./data/sample.jpeg: {result}")


def test_find_bucket():
    print("Loading LLM...")
    llm = OpenAILLM()
    print("LLM Loaded.")
    result = llm.find_bucket(
        # ["indoor appliance", "outdoor appliance"], "appliances"
        ["car", "vehicle"],
        "motorcycle",
    )  # noqa
    print(f"LLM Response-> bucket: {result}")


def test_find_sub_buckets():
    print("Loading LLM...")
    llm = OpenAILLM()
    print("LLM Loaded.")
    result = llm.find_sub_buckets(
        ["appliance", "vehicle", "chairs", "tables"], "furniture"
    )
    print(f"LLM Response-> sub buckets: {result}")
    result = llm.find_sub_buckets(["appliance", "vehicle", "chairs", "tables"], "car")
    print(f"LLM Response-> sub buckets: {result}")


def test_expand_bucket():
    print("Loading LLM...")
    llm = OpenAILLM()
    print("LLM Loaded.")
    result = llm.expand_bucket(["appliance"], "furniture")
    print(f"LLM Response-> expanded bucket: {result}")
    result = llm.expand_bucket(
        ["chair", "table", "pot", "pan", "cookware", "fan"], "furniture"
    )
    print(f"LLM Response-> expanded bucket: {result}")


def test_merge_buckets():
    print("Loading LLM...")
    llm = OpenAILLM()
    print("LLM Loaded.")
    result = llm.merge_buckets(["chair", "table", "pot", "pan", "cookware", "sofa"])
    print(f"LLM Response-> merged bucket: {result}")
    result = llm.merge_buckets(["motorcycle", "car"])
    print(f"LLM Response-> merged bucket: {result}")


def test_asset_ingestion():
    print("Logging in User...")
    user: User = User.login("amitrc", "password12")
    print("Building As...")
    appliance_category = Descriptor("appliance")
    indoor_category = Descriptor("indoor appliance")
    outdoor_category = Descriptor("outdoor appliance")
    appliance_category.add_edge(indoor_category.id)
    appliance_category.add_edge(outdoor_category.id)
    washing_machine = Asset("washing machine")
    hair_dryer = Asset("hair dryer")
    indoor_category.add_edge(hair_dryer.id)
    user.add_edge(appliance_category.id)
    print(f"Serialized tree: {user.serialize_forest()}")
    user.consume(washing_machine)

    print(f"Serialized tree after: {user.serialize_forest()}")
    print(f"Serialized user: {user.serialize()}")


def test_descriptor_ingestion():
    print("Logging in User...")
    user: User = User.login("amitrc", "password9")
    print("Making descriptor...")
    wooden_furniture_category = Descriptor("Wooden furniture")
    print(f"Serialized tree: {user.serialize_forest()}")
    user.consume(wooden_furniture_category)

    print(f"Serialized tree after: {user.serialize_forest()}")
    print(f"Serialized user: {user.serialize()}")


def test_database_get_put():
    print("Creating User...")
    user = User("amitrc")
    print("Building forest...")
    appliance_category = Descriptor("appliance")
    furniture_category = Descriptor("furniture")
    user.add_edge(appliance_category.id)
    user.add_edge(furniture_category.id)

    print("Performing DB operations...")
    ndb = NodeDB(verbose=True)
    ndb.set(user.id.serialize(), user.serialize())
    res: Node = Node.from_id(user.id)
    print(f"Final result from db: {res.serialize()}")


def test_serialize_deserialize_nodes():
    print("Creating User...")
    user = User("amitrc")
    print("Building forest...")
    appliance_category = Descriptor("appliance")
    furniture_category = Descriptor("furniture")
    asset = Asset("hair dryer")
    appliance_category.add_edge(asset.id)
    user.add_edge(appliance_category.id)
    user.add_edge(furniture_category.id)

    user_serial = user.serialize()
    print(f"Serialized User: {user_serial}")
    print("Deserializing user ...")
    user_deserial = Node.deserialize(user_serial)
    print(f"Final User: {user_deserial.serialize()}")

    descriptor_serial = appliance_category.serialize()
    print(f"Serialized descriptor: {descriptor_serial}")
    print("Deserializing descriptor ...")
    descriptor_deserial = Node.deserialize(descriptor_serial)
    print(f"Final descriptor: {descriptor_deserial.serialize()}")

    asset_serial = asset.serialize()
    print(f"Serialized asset: {asset_serial}")
    print("Deserializing asset ...")
    asset_deserial = Node.deserialize(asset_serial)
    print(f"Final asset: {asset_deserial.serialize()}")


def test_user_load(asset_name: str) -> None:
    assert asset_name != "", "Please provide a valid asset name"
    new_asset: Asset = Asset(asset_name)
    user: Node = Node.from_id("User:2263816597")
    assert isinstance(user, User)
    user.consume(new_asset)
    print(f"Serialized User tree: {user.serialize_forest()}")


def test_user_login(username: str, user_password: str) -> None:
    assert username != "", "Please provide a valid username"
    assert user_password != "", "Please provide a valid password"
    user: User = User.login(username, user_password)
    print(f"Serialized User tree: {user.serialize_forest()}")


def test_user_register(username: str, user_password: str) -> None:
    assert username != "", "Please provide a valid username"
    assert user_password != "", "Please provide a valid password"
    user: User = User.register(username, user_password)
    print(f"Serialized User tree: {user.serialize_forest()}")


def test_image_upload() -> None:
    print("User login...")
    user: User = User.login("amitrc", "password12")
    print("User logged in")
    print("Attach image to User...")
    image: Image = user.attach_image(image_path="./data/sample.jpeg")
    print("Attached image to User")
    all_images: List[Image] = user.get_images()
    print(f"Total images found: {len(all_images)}")
    print(f"Image sizes: {[len(img.image_data) for img in all_images]}")
    print(f"Image IDs: {[img.id.serialize() for img in all_images]}")
    print(f"Serialized User: {user.serialize()}")
    print(f"Attached Image serialized: {image.serialize()}")
    print(f"Serialized tree: {user.serialize_forest()}")


def test_user_asset_tree_visualization() -> None:
    print("User login...")
    user: User = User.login("amitrc", "password12")
    print("User logged in")
    nodes_info: List[Dict[str, Union[str, int]]] = (
        user.get_asset_tree_info_for_visualization()
    )
    print(f"Total nodes found: {len(nodes_info)}")
    for node_info in nodes_info:
        print(f"Node info: {node_info}")


if __name__ == "__main__":
    # test_user_register("amitrc", "password12")
    # test_user_login("amitrc", "password8")
    # test_find_sub_buckets()
    # test_expand_bucket()
    # test_merge_buckets()
    # test_find_bucket()
    # test_asset_ingestion()
    # test_descriptor_ingestion()
    # test_describe_image()
    # test_show_images()
    # image_data: Optional[str] = ImageStore().get("Image:18041440")
    # assert image_data is not None, "Image data not found"
    # print(f"Length of Image data: {len(image_data)}")
    # test_image_upload()
    test_user_asset_tree_visualization()
