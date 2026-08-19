"""Fallback chain for LLM providers.

Tries providers in configured order. If Gemini throws a quota error or
times out, falls through to Groq, then to a local Ollama instance.
If every provider fails (or none are configured), returns None so the
pipeline can degrade gracefully to deterministic explanations.
"""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Final

from app.core.config import settings

logger = logging.getLogger(__name__)

# Retries per provider before moving to the next one in the chain.
MAX_ATTEMPTS_PER_PROVIDER: Final = 2

DETERMINISTIC_PROVIDER: Final = "deterministic"
NO_MODEL: Final = "none"


class LLMError(RuntimeError):
    """Base class for provider failures."""


class LLMConfigurationError(LLMError):
    """Provider cannot work as configured. Never worth retrying."""


class LLMTransientError(LLMError):
    """Timeout, rate limit or transient server error. Worth one more attempt."""


class AllProvidersFailed(LLMError):
    """Every provider in the chain was skipped or failed."""

    def __init__(self, attempts: list[ProviderAttempt]) -> None:
        self.attempts = attempts
        summary = ", ".join(f"{a.provider} ({a.reason})" for a in attempts) or "no providers configured"
        super().__init__(f"All LLM providers failed ({summary})")


@dataclass(frozen=True, slots=True)
class ProviderAttempt:
    """What happened with one provider, for logging and the audit trail."""

    provider: str
    succeeded: bool
    reason: str
    duration_ms: int


@dataclass(frozen=True, slots=True)
class LLMResponse:
    """A successful generation and its provenance."""

    text: str
    provider: str
    model: str
    attempts: list[ProviderAttempt] = field(default_factory=list)

    def as_json(self) -> dict[str, Any]:
        """Parse the response as a JSON object.

        Models sometimes wrap JSON in prose or a fenced code block even when
        asked not to, so the outermost brace span is extracted before parsing.
        """
        raw = (self.text or "").strip()
        if not raw:
            return {}

        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            start = raw.find("{")
            end = raw.rfind("}")
            if start == -1 or end <= start:
                return {}
            try:
                parsed = json.loads(raw[start : end + 1])
                return parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                return {}


# -----------------------------------------------------------------------------
# Providers
# -----------------------------------------------------------------------------


class LLMProvider(ABC):
    """One backend capable of returning a JSON object for a prompt."""

    name: str
    # Free tiers are commonly funded by training on submitted data. Providers
    # that make no such guarantee must only ever receive redacted text.
    trusted_with_pii: bool = False

    @abstractmethod
    def is_configured(self) -> bool:
        """True when this provider has everything it needs to be attempted."""

    @property
    @abstractmethod
    def model(self) -> str:
        """Model identifier, recorded for provenance."""

    @abstractmethod
    def generate_json(self, *, system_prompt: str, user_prompt: str) -> str:
        """Return raw response text, or raise an 'LLMError' subclass."""

    def _classify(self, exc: Exception) -> LLMError:
        """Map a provider SDK exception onto retry-worthy or not.

        SDKs differ, so this inspects the message rather than depending on each
        library's exception hierarchy.
        """
        message = str(exc).lower()

        permanent_markers = (
            "api_key",
            "api key",
            "unauthorized",
            "permission denied",
            "quota exceeded",
            "not found",
            "unsupported",
            "invalid argument",
        )
        if any(marker in message for marker in permanent_markers):
            return LLMConfigurationError(str(exc))

        return LLMTransientError(str(exc))


class GeminiProvider(LLMProvider):
    """Google Gemini via the 'google-genai' SDK."""

    name = "gemini"

    def is_configured(self) -> bool:
        return settings.GEMINI_API_KEY is not None

    @property
    def model(self) -> str:
        return settings.GEMINI_MODEL

    def generate_json(self, *, system_prompt: str, user_prompt: str) -> str:
        if settings.GEMINI_API_KEY is None:
            raise LLMConfigurationError("GEMINI_API_KEY is not set")

        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise LLMConfigurationError("google-genai is not installed") from exc

        api_key = settings.GEMINI_API_KEY.get_secret_value()
        timeout_ms = int(settings.AI_PROVIDER_TIMEOUT_SECONDS * 1000)

        try:
            client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(timeout=timeout_ms),
            )
        except TypeError:
            # Older SDK builds do not accept http_options on the constructor.
            client = genai.Client(api_key=api_key)

        try:
            response = client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config={
                    "system_instruction": system_prompt,
                    "response_mime_type": "application/json",
                    "temperature": 0.2,
                },
            )
        except Exception as exc:
            raise self._classify(exc) from exc

        return response.text or ""


class GroqProvider(LLMProvider):
    """Groq-hosted open-weight models. Fast, used to conserve Gemini quota."""

    name = "groq"

    def is_configured(self) -> bool:
        return settings.GROQ_API_KEY is not None

    @property
    def model(self) -> str:
        return settings.GROQ_MODEL

    def generate_json(self, *, system_prompt: str, user_prompt: str) -> str:
        if settings.GROQ_API_KEY is None:
            raise LLMConfigurationError("GROQ_API_KEY is not set")

        try:
            from groq import Groq
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise LLMConfigurationError("groq is not installed") from exc

        client = Groq(
            api_key=settings.GROQ_API_KEY.get_secret_value(),
            timeout=settings.AI_PROVIDER_TIMEOUT_SECONDS,
        )

        try:
            completion = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
        except Exception as exc:
            raise self._classify(exc) from exc

        return completion.choices[0].message.content or ""


class OllamaProvider(LLMProvider):
    """Locally hosted model over Ollama's HTTP API."""

    name = "ollama"
    trusted_with_pii = True

    def is_configured(self) -> bool:
        return settings.OLLAMA_ENABLED

    @property
    def model(self) -> str:
        return settings.OLLAMA_MODEL

    def generate_json(self, *, system_prompt: str, user_prompt: str) -> str:
        try:
            import httpx
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise LLMConfigurationError("httpx is not installed") from exc

        try:
            response = httpx.post(
                f"{settings.OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": self.model,
                    "format": "json",
                    "stream": False,
                    "options": {"temperature": 0.2},
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                },
                timeout=settings.AI_PROVIDER_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except Exception as exc:
            raise self._classify(exc) from exc

        payload = response.json()
        return payload.get("message", {}).get("content", "") or ""


# -----------------------------------------------------------------------------
# Router
# -----------------------------------------------------------------------------


class LLMRouter:
    """Tries each configured provider in order until one returns."""

    def __init__(self, providers: dict[str, LLMProvider] | None = None) -> None:
        self._providers: dict[str, LLMProvider] = providers or {
            provider.name: provider
            for provider in (GeminiProvider(), GroqProvider(), OllamaProvider())
        }

    @property
    def configured_providers(self) -> list[str]:
        """Names of providers that could currently be attempted."""
        return [
            name
            for name in settings.provider_chain
            if (provider := self._providers.get(name)) and provider.is_configured()
        ]

    @property
    def any_available(self) -> bool:
        return bool(self.configured_providers)

    def generate_json(
        self, *, system_prompt: str, user_prompt: str
    ) -> LLMResponse:
        """Generate a JSON response, walking the fallback chain.

        Raises 'AllProvidersFailed' when nothing in the chain succeeds.
        """
        attempts: list[ProviderAttempt] = []

        for name in settings.provider_chain:
            provider = self._providers.get(name)
            if provider is None:
                attempts.append(
                    ProviderAttempt(name, False, "unknown provider name", 0)
                )
                continue

            if not provider.is_configured():
                attempts.append(
                    ProviderAttempt(name, False, "not configured", 0)
                )
                continue

            response = self._attempt_provider(
                provider, system_prompt, user_prompt, attempts
            )
            if response is not None:
                return LLMResponse(
                    text=response.text,
                    provider=response.provider,
                    model=response.model,
                    attempts=attempts,
                )

        logger.warning(
            "LLM fallback chain exhausted after trying: %s",
            ", ".join(a.provider for a in attempts) or "nothing",
        )
        raise AllProvidersFailed(attempts)

    def _attempt_provider(
        self,
        provider: LLMProvider,
        system_prompt: str,
        user_prompt: str,
        attempts: list[ProviderAttempt],
    ) -> LLMResponse | None:
        """Call one provider with bounded retries. None means give up on it."""
        for attempt_number in range(1, MAX_ATTEMPTS_PER_PROVIDER + 1):
            started = time.perf_counter()
            try:
                text = provider.generate_json(
                    system_prompt=system_prompt, user_prompt=user_prompt
                )
            except LLMConfigurationError as exc:
                duration = int((time.perf_counter() - started) * 1000)
                logger.error(
                    "Provider %s is misconfigured; skipping it: %s",
                    provider.name,
                    exc,
                )
                attempts.append(
                    ProviderAttempt(provider.name, False, f"misconfigured: {exc}", duration)
                )
                return None
            except LLMTransientError as exc:
                duration = int((time.perf_counter() - started) * 1000)
                is_last = attempt_number == MAX_ATTEMPTS_PER_PROVIDER
                logger.warning(
                    "Provider %s attempt %d failed (retry=%s): %s",
                    provider.name,
                    attempt_number,
                    not is_last,
                    exc,
                )
                if is_last:
                    attempts.append(
                        ProviderAttempt(provider.name, False, f"transient: {exc}", duration)
                    )
                    return None
                continue
            except Exception as exc:
                duration = int((time.perf_counter() - started) * 1000)
                logger.exception("Provider %s crashed: %s", provider.name, exc)
                attempts.append(
                    ProviderAttempt(provider.name, False, f"crashed: {exc}", duration)
                )
                return None

            duration = int((time.perf_counter() - started) * 1000)
            if not text.strip():
                logger.warning(
                    "Provider %s returned an empty response (attempt %d)",
                    provider.name,
                    attempt_number,
                )
                if attempt_number == MAX_ATTEMPTS_PER_PROVIDER:
                    attempts.append(
                        ProviderAttempt(provider.name, False, "empty response", duration)
                    )
                    return None
                continue

            attempts.append(ProviderAttempt(provider.name, True, "ok", duration))
            logger.info(
                "LLM call to %s (%s) succeeded in %dms",
                provider.name,
                provider.model,
                duration,
            )
            return LLMResponse(text=text, provider=provider.name, model=provider.model)

        return None


# Shared router instance. Stateless apart from its rate-limit buckets.
router = LLMRouter()