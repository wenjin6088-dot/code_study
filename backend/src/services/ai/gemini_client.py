import json
import os
from typing import Any

from google import genai
from google.genai import errors, types

DEFAULT_MODEL = "gemini-3-flash-preview"
# Preview models are only served on v1beta; the SDK default (v1) returns 404 for them.
API_VERSION = "v1beta"
API_KEY_ENV_VAR = "GOOGLE_API_KEY"
JSON_MIME_TYPE = "application/json"

# Timeouts, rate limits and upstream outages are worth retrying; other 4xx are not.
_RETRYABLE_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})


class GeminiError(Exception):
    """Base class for Gemini client errors."""


class GeminiConfigurationError(GeminiError):
    pass


class GeminiResponseError(GeminiError):
    pass


class GeminiAPIError(GeminiError):
    def __init__(self, message: str, *, status_code: int | None, retryable: bool):
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable


class GeminiClient:
    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = DEFAULT_MODEL,
        client: Any | None = None,
    ):
        if client is None:
            resolved_key = api_key or os.environ.get(API_KEY_ENV_VAR)
            if not resolved_key:
                raise GeminiConfigurationError(
                    f"Gemini API key missing: pass api_key or set {API_KEY_ENV_VAR}"
                )
            client = genai.Client(
                api_key=resolved_key,
                http_options=types.HttpOptions(api_version=API_VERSION),
            )
        self._client = client
        self.model_name = model_name

    async def generate_text(
        self,
        prompt: str,
        *,
        system_instruction: str | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
    ) -> str:
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        return await self._generate(prompt, config)

    async def generate_json(
        self,
        prompt: str,
        *,
        system_instruction: str | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
    ) -> dict[str, Any]:
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            response_mime_type=JSON_MIME_TYPE,
        )
        text = await self._generate(prompt, config)
        return _parse_json_object(text)

    async def _generate(self, prompt: str, config: types.GenerateContentConfig) -> str:
        try:
            response = await self._client.aio.models.generate_content(
                model=self.model_name, contents=prompt, config=config
            )
        except errors.APIError as exc:
            raise GeminiAPIError(
                exc.message or str(exc),
                status_code=exc.code,
                retryable=exc.code in _RETRYABLE_STATUS_CODES,
            ) from exc

        text = getattr(response, "text", None)
        if not text:
            raise GeminiResponseError("Gemini returned an empty response")
        return text


def _strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        first_newline = stripped.find("\n")
        stripped = stripped[first_newline + 1 :] if first_newline != -1 else ""
    if stripped.endswith("```"):
        stripped = stripped[: -len("```")]
    return stripped.strip()


def _parse_json_object(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(_strip_code_fences(text))
    except json.JSONDecodeError as exc:
        raise GeminiResponseError(f"Gemini returned invalid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise GeminiResponseError(
            f"Gemini returned JSON {type(parsed).__name__}, expected an object"
        )
    return parsed
