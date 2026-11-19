import pytest

from src.services.ai.gemini_client import (
    GeminiAPIError,
    GeminiConfigurationError,
    GeminiResponseError,
)
from src.services.ai.prompts import CHAPTER_KEYS, CodeFileInput
from src.services.document.document_generation_service import (
    DocumentGenerationService,
    InvalidDocumentStructureError,
)

VALID_DOCUMENT = {key: {"title": key} for key in CHAPTER_KEYS}


def _files() -> list[CodeFileInput]:
    return [CodeFileInput(path="main.py", content="print('hi')")]


class FakeGeminiClient:
    """Returns/raises each item of ``responses`` in order, one per call."""

    def __init__(self, responses: list):
        self._responses = list(responses)
        self.calls: list[dict] = []

    async def generate_json(self, prompt, *, system_instruction=None, **kwargs):
        self.calls.append({"prompt": prompt, "system_instruction": system_instruction})
        if not self._responses:
            raise AssertionError("generate_json called more times than expected")
        outcome = self._responses.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class FakeSleep:
    def __init__(self):
        self.delays: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.delays.append(seconds)


def make_service(responses: list, **kwargs):
    client = FakeGeminiClient(responses)
    sleep = FakeSleep()
    service = DocumentGenerationService(client, sleep=sleep, **kwargs)
    return service, client, sleep


def _retryable_error(status_code: int = 503) -> GeminiAPIError:
    return GeminiAPIError("server error", status_code=status_code, retryable=True)


def _non_retryable_error(status_code: int = 400) -> GeminiAPIError:
    return GeminiAPIError("bad request", status_code=status_code, retryable=False)


class TestSuccessfulGeneration:
    async def test_returns_validated_document_on_first_success(self):
        service, client, sleep = make_service([VALID_DOCUMENT])
        result = await service.generate_document(
            _files(), detected_language="python", complexity_level="beginner"
        )
        assert result == VALID_DOCUMENT
        assert len(client.calls) == 1
        assert sleep.delays == []

    async def test_sends_built_prompt_to_gemini(self):
        service, client, _ = make_service([VALID_DOCUMENT])
        await service.generate_document(
            _files(), detected_language="python", complexity_level="beginner"
        )
        call = client.calls[0]
        assert "print('hi')" in call["prompt"]
        assert call["system_instruction"]


class TestRetryOnTransientFailure:
    async def test_retries_retryable_api_error_and_succeeds(self):
        service, client, sleep = make_service([_retryable_error(), VALID_DOCUMENT])
        result = await service.generate_document(
            _files(), detected_language="python", complexity_level="beginner"
        )
        assert result == VALID_DOCUMENT
        assert len(client.calls) == 2
        assert sleep.delays == [1.0]

    async def test_retries_invalid_json_response_error(self):
        service, client, sleep = make_service(
            [GeminiResponseError("bad json"), VALID_DOCUMENT]
        )
        result = await service.generate_document(
            _files(), detected_language="python", complexity_level="beginner"
        )
        assert result == VALID_DOCUMENT
        assert len(client.calls) == 2

    async def test_retries_missing_chapters_in_response(self):
        incomplete = {k: v for k, v in VALID_DOCUMENT.items() if k != "chapter7"}
        service, client, sleep = make_service([incomplete, VALID_DOCUMENT])
        result = await service.generate_document(
            _files(), detected_language="python", complexity_level="beginner"
        )
        assert result == VALID_DOCUMENT
        assert len(client.calls) == 2

    async def test_uses_exponential_backoff_delays(self):
        service, client, sleep = make_service(
            [_retryable_error(), _retryable_error(), VALID_DOCUMENT]
        )
        await service.generate_document(
            _files(), detected_language="python", complexity_level="beginner"
        )
        assert sleep.delays == [1.0, 2.0]

    async def test_stops_after_max_retries_and_raises_last_error(self):
        error = _retryable_error()
        service, client, sleep = make_service(
            [error, error, error, error], max_retries=3
        )
        with pytest.raises(GeminiAPIError):
            await service.generate_document(
                _files(), detected_language="python", complexity_level="beginner"
            )
        assert len(client.calls) == 4  # initial attempt + 3 retries
        assert sleep.delays == [1.0, 2.0, 4.0]

    async def test_default_max_retries_is_three(self):
        error = _retryable_error()
        service, client, sleep = make_service([error, error, error, error])
        with pytest.raises(GeminiAPIError):
            await service.generate_document(
                _files(), detected_language="python", complexity_level="beginner"
            )
        assert len(client.calls) == 4

    async def test_custom_retry_configuration(self):
        error = _retryable_error()
        service, client, sleep = make_service(
            [error, VALID_DOCUMENT],
            max_retries=1,
            initial_delay_seconds=0.5,
            backoff_multiplier=3.0,
        )
        result = await service.generate_document(
            _files(), detected_language="python", complexity_level="beginner"
        )
        assert result == VALID_DOCUMENT
        assert sleep.delays == [0.5]


class TestNonRetryableFailures:
    async def test_raises_immediately_on_non_retryable_api_error(self):
        service, client, sleep = make_service([_non_retryable_error()])
        with pytest.raises(GeminiAPIError) as exc_info:
            await service.generate_document(
                _files(), detected_language="python", complexity_level="beginner"
            )
        assert exc_info.value.retryable is False
        assert len(client.calls) == 1
        assert sleep.delays == []

    async def test_propagates_configuration_error_without_retry(self):
        service, client, sleep = make_service([GeminiConfigurationError("no key")])
        with pytest.raises(GeminiConfigurationError):
            await service.generate_document(
                _files(), detected_language="python", complexity_level="beginner"
            )
        assert len(client.calls) == 1
        assert sleep.delays == []

    async def test_raises_invalid_document_structure_after_exhausting_retries(self):
        incomplete = {k: v for k, v in VALID_DOCUMENT.items() if k != "chapter1"}
        service, client, sleep = make_service([incomplete, incomplete], max_retries=1)
        with pytest.raises(InvalidDocumentStructureError):
            await service.generate_document(
                _files(), detected_language="python", complexity_level="beginner"
            )
        assert len(client.calls) == 2


class TestInputValidation:
    async def test_rejects_empty_file_list(self):
        service, client, _ = make_service([VALID_DOCUMENT])
        with pytest.raises(ValueError):
            await service.generate_document(
                [], detected_language="python", complexity_level="beginner"
            )
        assert client.calls == []
