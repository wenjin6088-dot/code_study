import pytest

from src.services.ai.gemini_client import (
    GeminiAPIError,
    GeminiConfigurationError,
    GeminiResponseError,
)
from src.services.ai.prompts import PRACTICE_PROBLEM_TYPES, CodeFileInput
from src.services.practice.practice_generation_service import (
    InvalidPracticeStructureError,
    PracticeGenerationService,
)


def _valid_problems() -> dict:
    return {
        "problems": [
            {
                "problem_number": number,
                "problem_type": problem_type,
                "problem_statement": f"Statement {number}",
                "learning_objective": f"Objective {number}",
                "hints": ["Hint 1", "Hint 2"],
                "model_solution": f"Solution {number}",
                "expected_output": f"Output {number}",
            }
            for number, problem_type in enumerate(PRACTICE_PROBLEM_TYPES, 1)
        ]
    }


def _files() -> list[CodeFileInput]:
    return [CodeFileInput(path="main.py", content="print('hi')")]


class FakeGeminiClient:
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
    service = PracticeGenerationService(client, sleep=sleep, **kwargs)
    return service, client, sleep


def _retryable_error(status_code: int = 503) -> GeminiAPIError:
    return GeminiAPIError("server error", status_code=status_code, retryable=True)


def _non_retryable_error(status_code: int = 400) -> GeminiAPIError:
    return GeminiAPIError("bad request", status_code=status_code, retryable=False)


class TestSuccessfulGeneration:
    async def test_returns_five_problems_in_order_on_first_success(self):
        service, client, sleep = make_service([_valid_problems()])
        result = await service.generate_problems(
            _files(), detected_language="python", complexity_level="beginner"
        )
        assert len(result) == 5
        assert [p["problem_number"] for p in result] == [1, 2, 3, 4, 5]
        assert [p["problem_type"] for p in result] == list(PRACTICE_PROBLEM_TYPES)
        assert len(client.calls) == 1
        assert sleep.delays == []

    async def test_sends_built_prompt_to_gemini(self):
        service, client, _ = make_service([_valid_problems()])
        await service.generate_problems(
            _files(), detected_language="python", complexity_level="beginner"
        )
        call = client.calls[0]
        assert "print('hi')" in call["prompt"]
        assert call["system_instruction"]


class TestRetryOnTransientFailure:
    async def test_retries_retryable_api_error_and_succeeds(self):
        service, client, sleep = make_service(
            [_retryable_error(), _valid_problems()]
        )
        result = await service.generate_problems(
            _files(), detected_language="python", complexity_level="beginner"
        )
        assert len(result) == 5
        assert len(client.calls) == 2
        assert sleep.delays == [1.0]

    async def test_retries_invalid_json_response_error(self):
        service, client, sleep = make_service(
            [GeminiResponseError("bad json"), _valid_problems()]
        )
        result = await service.generate_problems(
            _files(), detected_language="python", complexity_level="beginner"
        )
        assert len(result) == 5
        assert len(client.calls) == 2

    async def test_retries_wrong_problem_count(self):
        incomplete = {"problems": _valid_problems()["problems"][:4]}
        service, client, sleep = make_service([incomplete, _valid_problems()])
        result = await service.generate_problems(
            _files(), detected_language="python", complexity_level="beginner"
        )
        assert len(result) == 5
        assert len(client.calls) == 2

    async def test_retries_invalid_problem_type(self):
        bad = _valid_problems()
        bad["problems"][0]["problem_type"] = "not_a_real_type"
        service, client, sleep = make_service([bad, _valid_problems()])
        result = await service.generate_problems(
            _files(), detected_language="python", complexity_level="beginner"
        )
        assert len(result) == 5
        assert len(client.calls) == 2

    async def test_retries_duplicate_or_missing_problem_numbers(self):
        bad = _valid_problems()
        bad["problems"][1]["problem_number"] = 1  # duplicate, 5 missing
        service, client, sleep = make_service([bad, _valid_problems()])
        result = await service.generate_problems(
            _files(), detected_language="python", complexity_level="beginner"
        )
        assert len(result) == 5
        assert len(client.calls) == 2

    async def test_uses_exponential_backoff_delays(self):
        service, client, sleep = make_service(
            [_retryable_error(), _retryable_error(), _valid_problems()]
        )
        await service.generate_problems(
            _files(), detected_language="python", complexity_level="beginner"
        )
        assert sleep.delays == [1.0, 2.0]

    async def test_stops_after_max_retries_and_raises_last_error(self):
        error = _retryable_error()
        service, client, sleep = make_service(
            [error, error, error, error], max_retries=3
        )
        with pytest.raises(GeminiAPIError):
            await service.generate_problems(
                _files(), detected_language="python", complexity_level="beginner"
            )
        assert len(client.calls) == 4
        assert sleep.delays == [1.0, 2.0, 4.0]

    async def test_default_max_retries_is_three(self):
        error = _retryable_error()
        service, client, sleep = make_service([error, error, error, error])
        with pytest.raises(GeminiAPIError):
            await service.generate_problems(
                _files(), detected_language="python", complexity_level="beginner"
            )
        assert len(client.calls) == 4


class TestNonRetryableFailures:
    async def test_raises_immediately_on_non_retryable_api_error(self):
        service, client, sleep = make_service([_non_retryable_error()])
        with pytest.raises(GeminiAPIError) as exc_info:
            await service.generate_problems(
                _files(), detected_language="python", complexity_level="beginner"
            )
        assert exc_info.value.retryable is False
        assert len(client.calls) == 1
        assert sleep.delays == []

    async def test_propagates_configuration_error_without_retry(self):
        service, client, sleep = make_service([GeminiConfigurationError("no key")])
        with pytest.raises(GeminiConfigurationError):
            await service.generate_problems(
                _files(), detected_language="python", complexity_level="beginner"
            )
        assert len(client.calls) == 1
        assert sleep.delays == []

    async def test_raises_invalid_structure_after_exhausting_retries(self):
        incomplete = {"problems": _valid_problems()["problems"][:4]}
        service, client, sleep = make_service([incomplete, incomplete], max_retries=1)
        with pytest.raises(InvalidPracticeStructureError):
            await service.generate_problems(
                _files(), detected_language="python", complexity_level="beginner"
            )
        assert len(client.calls) == 2


class TestInputValidation:
    async def test_rejects_empty_file_list(self):
        service, client, _ = make_service([_valid_problems()])
        with pytest.raises(ValueError):
            await service.generate_problems(
                [], detected_language="python", complexity_level="beginner"
            )
        assert client.calls == []
