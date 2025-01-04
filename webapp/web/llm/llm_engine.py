#!/usr/bin/env python3
# pyre-strict

import base64
import os
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pyre_extensions import override

ENV_VARIABLES: Dict[str, str] = {
    "LANGCHAIN_TRACING_V2": "true",
    "LANGCHAIN_ENDPOINT": "https://api.smith.langchain.com",
    "LANGCHAIN_API_KEY": "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",
    "LANGCHAIN_PROJECT": "pollux",
}

for env_var, value in ENV_VARIABLES.items():
    os.environ[env_var] = value


class LlmEngineType(Enum):
    OPENAI = 1
    LLAMA = 2


class LLM(ABC):
    EMPTY_BUCKET_STRING = "neither"

    def __init__(self, engine_type: LlmEngineType) -> None:
        self.engine_type: LlmEngineType = engine_type

    @abstractmethod
    def get_response(self, prompt: str) -> str:
        """
        Generic method to get response from the LLM engine
        """
        pass

    @abstractmethod
    def describe_image(self, image_path: str) -> str:
        """
        Ask LLM to extract objects from the image
        """
        pass

    @abstractmethod
    def find_bucket(self, buckets: List[str], asset_name: str) -> str:
        """
        Ask LLM to find which of the buckets (Descriptor) the asset belongs to.
        Usually it has to pick the most-fitting bucket or return "neither"
        """
        pass

    @abstractmethod
    def suggest_bucket(self, buckets: List[str], asset_name: str) -> str:
        """
        Ask LLM to suggest a new bucket (not among the ones provided) that
        is better suited for the asset.
        """
        pass

    @abstractmethod
    def find_sub_buckets(self, buckets: List[str], target_bucket: str) -> str:
        """
        Ask LLM to find which of the provided buckets are sub-buckets of the target bucket.
        """
        pass

    @abstractmethod
    def expand_bucket(self, buckets: List[str], target_bucket: str) -> List[str]:
        """
        Ask LLM to expand a the target bucket into more granular buckets such that
        none of them are within the provided buckets.
        """
        pass

    @abstractmethod
    def merge_buckets(self, buckets: List[str]) -> str:
        """
        Ask LLM to merge the provided granualr buckets into a single broad bucket.
        """
        pass


class OpenAILLM(LLM):
    OPENAI_API_KEY = "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"  # noqa

    def __init__(
        self, model_type: str = "gpt-4o-mini", api_key: Optional[str] = None
    ) -> None:
        super().__init__(LlmEngineType.OPENAI)
        os.environ["OPENAI_API_KEY"] = api_key or self.OPENAI_API_KEY
        self.model_type: str = model_type
        self.model = ChatOpenAI(model=self.model_type)

    @override
    def get_response(self, prompt: str) -> str:
        messages: List[BaseMessage] = [
            SystemMessage("Translate the following from English into Spanish"),
            HumanMessage(prompt),
        ]
        resp: BaseMessage = self.model.invoke(messages)
        assert isinstance(resp.content, str)
        return resp.content

    @override
    def describe_image(self, image_path: str) -> str:
        with open(image_path, "rb") as img:
            image_data = base64.b64encode(img.read()).decode("utf-8")

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "What are the objects in this image? Please only "
                    "list out the objects, without any other "
                    "details.",
                ),
                (
                    "user",
                    [
                        {
                            "type": "image_url",
                            "image_url": {"url": "data:image/jpeg;base64,{image_data}"},
                        }
                    ],
                ),
            ]
        )
        chain = prompt | self.model
        resp: BaseMessage = chain.invoke({"image_data": image_data})
        assert isinstance(resp.content, str)
        return resp.content

    @override
    def find_bucket(self, buckets: List[str], asset_name: str) -> str:
        buckets_str: str = ",".join(buckets)
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Which of these buckets should the given object"
                    "belong? If you think it's neither, please reply with "
                    f"{self.EMPTY_BUCKET_STRING}. Only say one word which is the answer. "
                    f"\n buckets: {buckets_str}",
                ),
                (
                    "user",
                    "Object: {asset_name}",
                ),
            ]
        )
        chain = prompt | self.model
        resp: BaseMessage = chain.invoke({"asset_name": asset_name})
        assert isinstance(resp.content, str)
        return resp.content

    @override
    def suggest_bucket(self, buckets: List[str], asset_name: str) -> str:
        buckets_str: str = ",".join(buckets)
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Suggest a new bucket which is better suited for the given object. "  # noqa
                    "Only reply with the new suggested bucket name please. "
                    "Bucket names can have multiple words, if they do they are "  # noqa
                    "space separated, for example 'Gardening Tools'"
                    f"\n buckets: {buckets_str}",
                ),
                (
                    "user",
                    "Object: {asset_name}",
                ),
            ]
        )
        chain = prompt | self.model
        resp: BaseMessage = chain.invoke({"asset_name": asset_name})
        assert isinstance(resp.content, str)
        return resp.content

    @override
    def find_sub_buckets(self, buckets: List[str], target_bucket: str) -> str:
        buckets_str: str = ",".join(buckets)
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Which of these categories are sub-categories of the provided base category? "
                    "A sub-category is a category that is more granular than the base category. "
                    "A sub-category and category have an is-a relationship. "
                    "For example, 'Gardening Tools' is a sub-category of 'Tools'. "
                    "However, 'Tools' is not a sub-category of 'Gardening Tools'. "
                    f"If none of the potential sub-categories are applicable, please reply with '{self.EMPTY_BUCKET_STRING}'. "
                    "Only reply with the category names as a comma separated list. "
                    f"\n Base Category: {target_bucket} \n Potential Sub-Categories: {buckets_str}",
                )
            ]
        )
        chain = prompt | self.model
        resp: BaseMessage = chain.invoke({})
        assert isinstance(resp.content, str)
        return resp.content

    @override
    def expand_bucket(self, buckets: List[str], target_bucket: str) -> str:
        buckets_str: str = ",".join(buckets)
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Expand the provided base category into upto 3 granular categories. "
                    "None of these new categories should be present in the provided category list. "
                    "A granular category is a category that is more specific than the base category. "
                    "For example, 'Power Tools' & 'Gardening Tools' are granular categories of 'Tools'. "
                    "Only reply with the category names as a comma separated list. "
                    "Categories can have multiple words, if they do they are space separated, "
                    "for example 'Gardening Tools'."
                    f"\n Base Category: {target_bucket} \n Provided Categories: {buckets_str}",
                )
            ]
        )
        chain = prompt | self.model
        resp: BaseMessage = chain.invoke({})
        assert isinstance(resp.content, str)
        return resp.content

    @override
    def merge_buckets(self, buckets: List[str]) -> str:
        buckets_str: str = ",".join(buckets)
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Merge the provided granular categories into a single broader category. "
                    "A broader category is a category that encompasses the provided granular categories. "
                    "Each of the provided categories should be a sub-category of the merged category. "
                    "Only reply with the merged category name. "
                    "Category names can have multiple words, if they do then they are space separated, "
                    "for example 'Gardening Tools'."
                    f"\n Provided Categories: {buckets_str}",
                )
            ]
        )
        chain = prompt | self.model
        resp: BaseMessage = chain.invoke({})
        assert isinstance(resp.content, str)
        return resp.content


def initialize_engine(llm_engine_type: LlmEngineType):
    if llm_engine_type == LlmEngineType.OPENAI:
        return OpenAILLM()
    else:
        raise NotImplementedError("Provided LLM engine type not yet supported")


LLM_ENGINE: LLM = initialize_engine(LlmEngineType.OPENAI)
