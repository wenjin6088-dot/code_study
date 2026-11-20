import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from src.services.ai.gemini_client import (
    GeminiAPIError,
    GeminiClient,
    GeminiResponseError,
)
from src.services.ai.prompts import (
    PRACTICE_PROBLEM_TYPES,
    CodeFileInput,
    build_practice_prompt,
)

# FR-090 applies equally to practice generation: retry transient Gemini
# failures up to 3 times with exponential backoff.
DEFAULT_MAX_RETRIES = 3
DEFAULT_INITIAL_DELAY_SECONDS = 1.0
DEFAULT_BACKOFF_MULTIPLIER = 2.0

SleepFn = Callable[[float], Awaitable[None]]


class PracticeGenerationError(Exception):
    """Base class for practice problem generation failures."""


class InvalidPracticeStructureError(PracticeGenerationError):
    """Raised when Gemini's response doesn't match the 5-problem contract."""


class PracticeGenerationService:
    """Generates the 5 practice problems (FR-048/FR-049) for a task's code,
    retrying transient Gemini failures with exponential backoff (FR-090)."""

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

    async def generate_problems(
        self,
        files: list[CodeFileInput],
        *,
        detected_language: str,
        complexity_level: str,
    ) -> list[dict[str, Any]]:
        prompt = build_practice_prompt(
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
                problems = _validate_practice_structure(content)
                return sorted(problems, key=lambda p: p["problem_number"])
            except (
                GeminiAPIError,
                GeminiResponseError,
                InvalidPracticeStructureError,
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


def _validate_practice_structure(content: dict[str, Any]) -> list[dict[str, Any]]:
    problems = content.get("problems")
    if not isinstance(problems, list) or len(problems) != 5:
        raise InvalidPracticeStructureError(
            "Generated practice content must contain exactly 5 problems"
        )

    numbers = sorted(p.get("problem_number") for p in problems)
    if numbers != [1, 2, 3, 4, 5]:
        raise InvalidPracticeStructureError(
            f"Expected problem_number 1-5 exactly once each, got {numbers}"
        )

    invalid_types = [
        p.get("problem_type")
        for p in problems
        if p.get("problem_type") not in PRACTICE_PROBLEM_TYPES
    ]
    if invalid_types:
        raise InvalidPracticeStructureError(
            f"Invalid problem_type(s): {invalid_types}"
        )

    return problems
