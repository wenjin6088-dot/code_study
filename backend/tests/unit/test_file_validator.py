import pytest

from src.utils.file_validator import (
    MAX_TOTAL_UPLOAD_SIZE_BYTES,
    SUPPORTED_EXTENSIONS,
    FileValidationError,
    get_file_extension,
    is_binary_content,
    validate_extension,
    validate_not_binary,
    validate_total_size,
)


class TestGetFileExtension:
    def test_returns_lowercase_extension(self):
        assert get_file_extension("App.JSX") == ".jsx"

    def test_returns_extension_for_dotted_filename(self):
        assert get_file_extension("my.module.py") == ".py"

    def test_returns_empty_string_when_no_extension(self):
        assert get_file_extension("Makefile") == ""


class TestValidateExtension:
    @pytest.mark.parametrize("extension", sorted(SUPPORTED_EXTENSIONS))
    def test_accepts_all_supported_extensions(self, extension):
        validate_extension(f"file{extension}")  # should not raise

    def test_rejects_unsupported_extension(self):
        with pytest.raises(FileValidationError):
            validate_extension("archive.zip")

    def test_rejects_executable_extension(self):
        with pytest.raises(FileValidationError):
            validate_extension("malware.exe")


class TestValidateTotalSize:
    def test_accepts_size_at_exactly_the_limit(self):
        validate_total_size(MAX_TOTAL_UPLOAD_SIZE_BYTES)  # should not raise

    def test_accepts_size_under_the_limit(self):
        validate_total_size(1024)  # should not raise

    def test_rejects_size_over_the_limit(self):
        with pytest.raises(FileValidationError):
            validate_total_size(MAX_TOTAL_UPLOAD_SIZE_BYTES + 1)


class TestIsBinaryContent:
    def test_plain_utf8_text_is_not_binary(self):
        assert is_binary_content(b"def hello():\n    print('hi')\n") is False

    def test_korean_utf8_text_is_not_binary(self):
        assert is_binary_content("# 한글 주석입니다\n".encode()) is False

    def test_null_byte_content_is_binary(self):
        assert is_binary_content(b"\x00\x01\x02PNG\x0d\x0a") is True

    def test_null_byte_plus_invalid_utf8_is_binary(self):
        assert is_binary_content(bytes([0xFF, 0xFE, 0x00, 0x01])) is True

    def test_invalid_utf8_without_null_byte_is_binary(self):
        assert is_binary_content(bytes([0xFF, 0xFE, 0xFD])) is True

    def test_empty_content_is_not_binary(self):
        assert is_binary_content(b"") is False


class TestValidateNotBinary:
    def test_accepts_text_content(self):
        validate_not_binary("main.py", b"print('ok')")  # should not raise

    def test_rejects_binary_content(self):
        with pytest.raises(FileValidationError):
            validate_not_binary("image.png", b"\x89PNG\x00\x01\x02")
