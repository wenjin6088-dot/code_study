from types import SimpleNamespace

import pytest
from google.genai import errors

from src.services.ai.gemini_client import (
    API_KEY_ENV_VAR,
    API_VERSION,
    DEFAULT_MODEL,
    GeminiAPIError,
    GeminiClient,
    GeminiConfigurationError,
    GeminiResponseError,
)

_SDK_CLIENT_PATH = "src.services.ai.gemini_client.genai.Client"


class FakeModels:
    def __init__(self, text: str | None = "ok", error: Exception | None = None):
        self.text = text
        self.error = error
        self.calls: list[dict] = []

    async def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return SimpleNamespace(text=self.text)


class FakeSDKClient:
    def __init__(self, text: str | None = "ok", error: Exception | None = None):
        self.aio = SimpleNamespace(models=FakeModels(text=text, error=error))

    @property
    def calls(self) -> list[dict]:
        return self.aio.models.calls


def make_client(text: str | None = "ok", error: Exception | None = None):
    sdk = FakeSDKClient(text=text, error=error)
    return GeminiClient(client=sdk), sdk


class TestInitialization:
    def test_raises_when_no_api_key_available(self, monkeypatch):
        monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
        with pytest.raises(GeminiConfigurationError):
            GeminiClient()

    def test_uses_explicit_api_key(self, monkeypatch):
        captured = {}

        def fake_sdk_client(*, api_key, **_):
            captured["api_key"] = api_key
            return FakeSDKClient()

        monkeypatch.setattr(_SDK_CLIENT_PATH, fake_sdk_client)
        GeminiClient(api_key="explicit-key")
        assert captured["api_key"] == "explicit-key"

    def test_pins_v1beta_api_version_for_preview_models(self, monkeypatch):
        captured = {}

        def fake_sdk_client(*, api_key, http_options):
            captured["api_version"] = http_options.api_version
            return FakeSDKClient()

        monkeypatch.setattr(_SDK_CLIENT_PATH, fake_sdk_client)
        GeminiClient(api_key="k")
        assert API_VERSION == "v1beta"
        assert captured["api_version"] == "v1beta"

    def test_falls_back_to_environment_api_key(self, monkeypatch):
        captured = {}

        def fake_sdk_client(*, api_key, **_):
            captured["api_key"] = api_key
            return FakeSDKClient()

        monkeypatch.setattr(_SDK_CLIENT_PATH, fake_sdk_client)
        monkeypatch.setenv(API_KEY_ENV_VAR, "env-key")
        GeminiClient()
        assert captured["api_key"] == "env-key"

    def test_default_model_is_gemini_3_flash_preview(self):
        client, _ = make_client()
        assert DEFAULT_MODEL == "gemini-3-flash-preview"
        assert client.model_name == DEFAULT_MODEL

    def test_model_name_can_be_overridden(self):
        client = GeminiClient(client=FakeSDKClient(), model_name="custom-model")
        assert client.model_name == "custom-model"


class TestGenerateText:
    async def test_returns_response_text(self):
        client, _ = make_client(text="hello world")
        assert await client.generate_text("say hi") == "hello world"

    async def test_sends_prompt_to_configured_model(self):
        client, sdk = make_client()
        await client.generate_text("explain this")
        call = sdk.calls[0]
        assert call["model"] == DEFAULT_MODEL
        assert call["contents"] == "explain this"

    async def test_passes_generation_options_in_config(self):
        client, sdk = make_client()
        await client.generate_text(
            "p",
            system_instruction="You are a teacher",
            temperature=0.2,
            max_output_tokens=512,
        )
        config = sdk.calls[0]["config"]
        assert config.system_instruction == "You are a teacher"
        assert config.temperature == 0.2
        assert config.max_output_tokens == 512
        assert config.response_mime_type is None

    async def test_empty_text_raises_response_error(self):
        client, _ = make_client(text="")
        with pytest.raises(GeminiResponseError):
            await client.generate_text("p")

    async def test_missing_text_raises_response_error(self):
        client, _ = make_client(text=None)
        with pytest.raises(GeminiResponseError):
            await client.generate_text("p")


class TestGenerateJson:
    async def test_parses_json_object_response(self):
        client, _ = make_client(text='{"chapter1": {"title": "Intro"}}')
        assert await client.generate_json("p") == {"chapter1": {"title": "Intro"}}

    async def test_requests_json_mime_type(self):
        client, sdk = make_client(text="{}")
        await client.generate_json("p", system_instruction="sys")
        config = sdk.calls[0]["config"]
        assert config.response_mime_type == "application/json"
        assert config.system_instruction == "sys"

    async def test_strips_markdown_code_fences(self):
        client, _ = make_client(text='```json\n{"a": 1}\n```')
        assert await client.generate_json("p") == {"a": 1}

    async def test_invalid_json_raises_response_error(self):
        client, _ = make_client(text="not json at all")
        with pytest.raises(GeminiResponseError):
            await client.generate_json("p")

    async def test_non_object_json_raises_response_error(self):
        client, _ = make_client(text="[1, 2, 3]")
        with pytest.raises(GeminiResponseError):
            await client.generate_json("p")


def _server_error(code: int) -> errors.ServerError:
    return errors.ServerError(code, {"error": {"message": f"server {code}"}})


def _client_error(code: int) -> errors.ClientError:
    return errors.ClientError(code, {"error": {"message": f"client {code}"}})


class TestErrorTranslation:
    async def test_server_error_is_retryable_api_error(self):
        client, _ = make_client(error=_server_error(503))
        with pytest.raises(GeminiAPIError) as exc_info:
            await client.generate_text("p")
        assert exc_info.value.status_code == 503
        assert exc_info.value.retryable is True

    async def test_rate_limit_is_retryable(self):
        client, _ = make_client(error=_client_error(429))
        with pytest.raises(GeminiAPIError) as exc_info:
            await client.generate_text("p")
        assert exc_info.value.retryable is True

    async def test_bad_request_is_not_retryable(self):
        client, _ = make_client(error=_client_error(400))
        with pytest.raises(GeminiAPIError) as exc_info:
            await client.generate_text("p")
        assert exc_info.value.status_code == 400
        assert exc_info.value.retryable is False

    async def test_preserves_message_and_cause(self):
        original = _client_error(403)
        client, _ = make_client(error=original)
        with pytest.raises(GeminiAPIError) as exc_info:
            await client.generate_json("p")
        assert "client 403" in str(exc_info.value)
        assert exc_info.value.__cause__ is original

    async def test_api_error_is_gemini_error_subclass(self):
        from src.services.ai.gemini_client import GeminiError

        assert issubclass(GeminiAPIError, GeminiError)
        assert issubclass(GeminiResponseError, GeminiError)
        assert issubclass(GeminiConfigurationError, GeminiError)
