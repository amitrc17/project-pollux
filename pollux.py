#!/usr/bin/env python3
# pyre-strict

from llm.llm_engine import OpenAILLM


def main():
    print("Loading LLM...")
    llm = OpenAILLM()
    print(f"LLM Loaded.")
    result: str = llm.describe_image("./data/sample.jpeg")
    print(f"LLM Response-> ./data/sample.jpeg: {result}")


if __name__ == "__main__":
    main()
