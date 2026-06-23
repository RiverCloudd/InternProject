from __future__ import annotations

import os

from .config import Settings


class BaseLLMClient:
    provider_name = "base"

    def generate(self, prompt: str) -> str:
        raise NotImplementedError


class MockLLMClient(BaseLLMClient):
    provider_name = "mock"

    def generate(self, prompt: str) -> str:
        # Keep the mock deterministic and dependency-free for local review.
        if "regional" in prompt.lower() or "rollout" in prompt.lower():
            return (
                "Use a small, testable rollout slice: one region, one audience, one channel owner, "
                "one likely resistance point, and one feedback loop. Keep the Group narrative consistent, "
                "but localize examples and manager enablement."
            )
        if "ceo" in prompt.lower() or "group dna" in prompt.lower() or "autonomy" in prompt.lower():
            return (
                "Frame the decision around Group non-negotiables versus brand-level adaptation. "
                "The leadership system should improve strategy execution without flattening brand identity."
            )
        return (
            "Start from observable behavior. Use Vision, Entrepreneurship, Passion, and Trust, then define "
            "emerging, proficient, and role-model behaviors before designing 360 feedback or coaching."
        )


class GeminiLLMClient(BaseLLMClient):
    provider_name = "gemini"

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str) -> str:
        try:
            from google import genai
        except ImportError as error:
            raise RuntimeError("google-genai is not installed. Run: pip install -r requirements.txt") from error

        os.environ["GEMINI_API_KEY"] = self.api_key
        client = genai.Client(api_key=self.api_key)

        # Current Gemini quickstart recommends the Interactions API. Keep a fallback
        # for SDK versions that still expose generate_content first.
        if hasattr(client, "interactions"):
            interaction = client.interactions.create(model=self.model, input=prompt)
            return getattr(interaction, "output_text", str(interaction))

        response = client.models.generate_content(model=self.model, contents=prompt)
        return getattr(response, "text", str(response))


def create_llm_client(settings: Settings) -> BaseLLMClient:
    if settings.llm_provider == "gemini":
        if not settings.gemini_api_key or "PASTE_YOUR" in settings.gemini_api_key:
            return MockLLMClient()
        return GeminiLLMClient(api_key=settings.gemini_api_key, model=settings.gemini_model)
    return MockLLMClient()
