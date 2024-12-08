#!/usr/bin/env python3
# pyre-strict

import base64
import os
from abc import ABC
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
    def __init__(self, engine_type: LlmEngineType) -> None:
        self.engine_type: LlmEngineType = engine_type

    def get_response(self, prompt: str) -> str:
        pass


class OpenAILLM(LLM):
    OPENAI_API_KEY = "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"

    def __init__(self, model_type: str = "gpt-4o-mini", api_key: Optional[str] = None) -> None:
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
        return resp.content

    def describe_image(self, image_path: str) -> str:
        with open(image_path, "rb") as img:
            image_data = base64.b64encode(img.read()).decode("utf-8")

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "What are the objects in this image? Please only list out the objects, without any other "
                           "details."),
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
        return resp.content
