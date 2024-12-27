#!/usr/bin/env python3
# pyre-strict

from llm.llm_engine import OpenAILLM
from data.asset_forest import User, Descriptor, Asset, Node

from data.database import NodeDB


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
    result: str = llm.describe_image("./data/sample.jpeg")
    print(f"LLM Response-> ./data/sample.jpeg: {result}")


def test_find_bucket():
    print("Loading LLM...")
    llm = OpenAILLM()
    print("LLM Loaded.")
    result = llm.find_bucket(
        ["indoor appliance", "outdoor appliance"], "garden chair"
    )  # noqa
    print(f"LLM Response-> bucket: {result}")


def test_asset_ingestion():
    print("Creating User...")
    user = User("amitrc")
    print("Building forest...")
    appliance_category = Descriptor("appliance")
    indoor_category = Descriptor("indoor appliance")
    outdoor_category = Descriptor("outdoor appliance")
    appliance_category.add_edge(indoor_category.id)
    appliance_category.add_edge(outdoor_category.id)
    user.add_edge(appliance_category.id)
    washing_machine = Asset("Lawnmower")
    user.consume(washing_machine)

    print(f"Serialized tree: {user.serialize_forest()}")


def test_database_get_put():
    print("Creating User...")
    user = User("amitrc")
    print("Building forest...")
    appliance_category = Descriptor("appliance")
    furniture_category = Descriptor("furniture")
    user.add_edge(appliance_category.id)
    user.add_edge(furniture_category.id)

    print("Performing DB operations...")
    ndb = NodeDB()
    ndb.set(user)
    res = ndb.get(user.id)
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


if __name__ == "__main__":
    test_database_get_put()
