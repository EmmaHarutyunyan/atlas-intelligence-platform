import json
from abc import ABC, abstractmethod

from django.conf import settings


class AIProvider(ABC):
    @abstractmethod
    def extract_json(self, content: str, schema: dict) -> dict:
        raise NotImplementedError


class MockAIProvider(AIProvider):
    def extract_json(self, content: str, schema: dict) -> dict:
        return {key: None for key in schema}


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str):
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)

    def extract_json(self, content: str, schema: dict) -> dict:
        response = self.client.chat.completions.create(
            model=getattr(settings, "OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "Extract only the requested fields. Return valid JSON."},
                {"role": "user", "content": json.dumps({"schema": schema, "content": content[:20000]}, ensure_ascii=False)},
            ],
        )
        return json.loads(response.choices[0].message.content or "{}")


def get_ai_provider() -> AIProvider:
    api_key = getattr(settings, "OPENAI_API_KEY", "")
    return OpenAIProvider(api_key) if api_key else MockAIProvider()
