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
        pass

    @abstractmethod
    def describe_image(self, image_path: str) -> str:
        pass

    @abstractmethod
    def find_bucket(self, buckets: List[str], asset_name: str) -> str:
        pass

    @abstractmethod
    def suggest_bucket(self, buckets: List[str], asset_name: str) -> str:
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
                    "neither. Only say one word which is the answer. "
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
    def suggest_bucket(self, buckets, asset_name):
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
        return resp.content


def initialize_engine(llm_engine_type: LlmEngineType):
    if llm_engine_type == LlmEngineType.OPENAI:
        return OpenAILLM()
    else:
        raise NotImplementedError("Provided LLM engine type not yet supported")


LLM_ENGINE: LLM = initialize_engine(LlmEngineType.OPENAI)
