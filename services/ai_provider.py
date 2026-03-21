"""
AI Provider Abstraction

Provides abstraction layer for multiple AI providers (OpenAI, Anthropic).
Copied from control_tower for Level 5 autonomy.
Default model: claude-sonnet-4-20250514 (cost-effective for MVP generation).
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import os


class AIProviderInterface(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    def generate_code(self, prompt: str, **kwargs) -> str:
        pass

    @abstractmethod
    def validate_configuration(self) -> bool:
        pass


class OpenAIProvider(AIProviderInterface):
    """OpenAI GPT-4 provider implementation."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4-turbo-preview"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        if not self.api_key:
            raise ValueError("OpenAI API key not provided and OPENAI_API_KEY env var not set")

    def generate_code(self, prompt: str, temperature: float = 0.2, max_tokens: int = 20480) -> str:
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert Python programmer. Generate clean, well-documented code."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except ImportError:
            raise RuntimeError("openai package not installed. Install with: pip install openai")
        except Exception as e:
            raise RuntimeError(f"OpenAI API call failed: {str(e)}")

    def validate_configuration(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 0)


class AnthropicProvider(AIProviderInterface):
    """Anthropic Claude provider implementation."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514"
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        if not self.api_key:
            raise ValueError("Anthropic API key not provided and ANTHROPIC_API_KEY env var not set")

    def generate_code(self, prompt: str, max_tokens: int = 20480) -> str:
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            message = client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
                timeout=600.0
            )
            if message.stop_reason == "max_tokens":
                import logging
                logging.getLogger(__name__).warning(
                    f"Response truncated at max_tokens={max_tokens}"
                )
            return message.content[0].text
        except ImportError:
            raise RuntimeError("anthropic package not installed. Install with: pip install anthropic")
        except Exception as e:
            raise RuntimeError(f"Anthropic API call failed: {str(e)}")

    def validate_configuration(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 0)


class AIProviderFactory:
    """Factory for creating AI provider instances."""

    _providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
    }

    @classmethod
    def create_provider(cls, provider_type: str, **kwargs) -> AIProviderInterface:
        if provider_type not in cls._providers:
            raise ValueError(
                f"Unsupported provider type: {provider_type}. "
                f"Supported types: {', '.join(cls._providers.keys())}"
            )
        return cls._providers[provider_type](**kwargs)

    @classmethod
    def get_supported_providers(cls) -> List[str]:
        return list(cls._providers.keys())
