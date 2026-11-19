import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from src.services.ai.gemini_client import (
    GeminiAPIError,
    GeminiClient,
    GeminiResponseError,
)
from src.services.ai.prompts import CHAPTER_KEYS, CodeFileInput, build_document_prompt

# FR-090: retry failed AI requests up to 3 times with exponential backoff.
DEFAULT_MAX_RETRIES = 3
DEFAULT_INITIAL_DELAY_SECONDS = 1.0
DEFAULT_BACKOFF_MULTIPLIER = 2.0

SleepFn = Callable[[float], Awaitable[None]]


class DocumentGenerationError(Exception):
    """Base class for document generation failures."""


class InvalidDocumentStructureError(DocumentGenerationError):
    """Raised when Gemini's response is missing required chapters."""


class DocumentGenerationService:
    """Generates the 7-chapter learning document for a task's code, retrying
    transient Gemini failures with exponential backoff (FR-090)."""

    def __init__(
        self,
        gemini_client: GeminiClient,
        *,
        max_retries: int = DEFAULT_MAX_RETRIES,
        initial_delay_seconds: float = DEFAULT_INITIAL_DELAY_SECONDS,
        backoff_multiplier: float = DEFAULT_BACKOFF_MULTIPLIER,
        sleep: SleepFn = asyncio.sleep,
    ):
        self.gemini_client = gemini_client
        self.max_retries = max_retries
        self.initial_delay_seconds = initial_delay_seconds
        self.backoff_multiplier = backoff_multiplier
        self._sleep = sleep

    async def generate_document(
        self,
        files: list[CodeFileInput],
        *,
        detected_language: str,
        complexity_level: str,
    ) -> dict[str, Any]:
        prompt = build_document_prompt(
            files,
            detected_language=detected_language,
            complexity_level=complexity_level,
        )

        attempt = 0
        while True:
            try:
                content = await self.gemini_client.generate_json(
                    prompt.user_prompt, system_instruction=prompt.system_instruction
                )
                _validate_document_structure(content)
                return content
            except (
                GeminiAPIError,
                GeminiResponseError,
                InvalidDocumentStructureError,
            ) as exc:
                if isinstance(exc, GeminiAPIError) and not exc.retryable:
                    raise
                if attempt >= self.max_retries:
                    raise
                delay = self.initial_delay_seconds * (
                    self.backoff_multiplier**attempt
                )
                await self._sleep(delay)
                attempt += 1


def _validate_document_structure(content: dict[str, Any]) -> None:
    missing = [key for key in CHAPTER_KEYS if key not in content]
    if missing:
        raise InvalidDocumentStructureError(
            f"Generated document is missing required chapters: {', '.join(missing)}"
        )
