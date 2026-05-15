from __future__ import annotations

import logging
from typing import Any

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from config import settings

logger = logging.getLogger(__name__)


class AIClientError(Exception):
    pass


class AIClient:

    def __init__(self) -> None:
        self._openai: AsyncOpenAI | None = None
        self._anthropic: AsyncAnthropic | None = None
        self._custom: AsyncOpenAI | None = None
        self._init_clients()

    def _init_clients(self) -> None:
        if settings.OPENAI_API_KEY:
            self._openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info("OpenAI client initialised")
        if settings.ANTHROPIC_API_KEY:
            self._anthropic = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            logger.info("Anthropic client initialised")
        if settings.OPENAI_API_KEY and settings.AI_CUSTOM_BASE_URL:
            self._custom = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.AI_CUSTOM_BASE_URL,
            )
            logger.info("Custom OpenAI-compatible client initialised: %s", settings.AI_CUSTOM_BASE_URL)

    @property
    def openai(self) -> AsyncOpenAI:
        if self._openai is None:
            raise AIClientError("OpenAI API key not configured")
        return self._openai

    @property
    def anthropic(self) -> AsyncAnthropic:
        if self._anthropic is None:
            raise AIClientError("Anthropic API key not configured")
        return self._anthropic

    @property
    def custom(self) -> AsyncOpenAI:
        if self._custom is None:
            raise AIClientError("Custom provider not configured (set OPENAI_API_KEY + AI_CUSTOM_BASE_URL)")
        return self._custom

    async def generate(
        self,
        prompt: str,
        *,
        provider: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        provider = provider or settings.AI_DEFAULT_PROVIDER
        model = model or settings.AI_DEFAULT_MODEL
        temperature = temperature if temperature is not None else settings.AI_TEMPERATURE
        max_tokens = max_tokens or settings.AI_MAX_TOKENS

        if provider == "openai":
            return await self._call_openai(prompt, model, temperature, max_tokens, system_prompt)
        elif provider == "anthropic":
            return await self._call_anthropic(prompt, model, temperature, max_tokens, system_prompt)
        elif provider == "custom":
            return await self._call_custom(prompt, model, temperature, max_tokens, system_prompt)
        else:
            raise AIClientError(f"Unsupported provider: {provider}")

    async def list_models(self, provider: str | None = None) -> list[str]:
        provider = provider or settings.AI_DEFAULT_PROVIDER
        if provider == "openai":
            resp = await self.openai.models.list()
            return [m.id for m in resp.data]
        elif provider == "custom":
            resp = await self.custom.models.list()
            return [m.id for m in resp.data]
        elif provider == "anthropic":
            return [
                "claude-sonnet-4-20250514",
                "claude-3-5-sonnet-20241022",
                "claude-3-5-haiku-20241022",
                "claude-3-opus-20240229",
            ]
        else:
            raise AIClientError(f"Unsupported provider: {provider}")

    async def _call_openai(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        system_prompt: str | None,
    ) -> dict[str, Any]:
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.openai.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as exc:
            raise AIClientError(f"OpenAI call failed: {exc}") from exc

        choice = response.choices[0]
        return {
            "content": choice.message.content or "",
            "provider": "openai",
            "model": model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            },
        }

    async def _call_custom(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        system_prompt: str | None,
    ) -> dict[str, Any]:
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.custom.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as exc:
            raise AIClientError(f"Custom provider call failed ({settings.AI_CUSTOM_BASE_URL}): {exc}") from exc

        choice = response.choices[0]
        return {
            "content": choice.message.content or "",
            "provider": "custom",
            "model": model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            },
        }

    async def _call_anthropic(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        system_prompt: str | None,
    ) -> dict[str, Any]:
        try:
            kwargs: dict[str, Any] = dict(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            if system_prompt:
                kwargs["system"] = system_prompt

            response = await self.anthropic.messages.create(**kwargs)
        except Exception as exc:
            raise AIClientError(f"Anthropic call failed: {exc}") from exc

        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text

        return {
            "content": content,
            "provider": "anthropic",
            "model": model,
            "usage": {
                "input_tokens": response.usage.input_tokens if response.usage else 0,
                "output_tokens": response.usage.output_tokens if response.usage else 0,
            },
        }


ai_client = AIClient()
