#!/usr/bin/env python3
# pyre-strict

from llm.llm_engine import OpenAILLM
from data.asset_forest import User, Descriptor, Asset


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


if __name__ == "__main__":
    test_asset_ingestion()
