from pathlib import Path

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".html",
        ".css",
        ".java",
        ".cpp",
        ".c",
        ".txt",
        ".md",
    }
)

MAX_TOTAL_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10MB total per task (FR-014)

_BINARY_SNIFF_SIZE = 8192


class FileValidationError(ValueError):
    """Raised when an uploaded file fails extension, size, or binary validation."""


def get_file_extension(file_name: str) -> str:
    return Path(file_name).suffix.lower()


def validate_extension(file_name: str) -> None:
    extension = get_file_extension(file_name)
    if extension not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise FileValidationError(
            f"지원하지 않는 파일 형식입니다: {file_name} (지원 형식: {supported})"
        )


def validate_total_size(total_size_bytes: int) -> None:
    if total_size_bytes > MAX_TOTAL_UPLOAD_SIZE_BYTES:
        raise FileValidationError(
            "업로드 용량이 10MB를 초과했습니다 "
            f"({total_size_bytes} bytes > {MAX_TOTAL_UPLOAD_SIZE_BYTES} bytes)"
        )


def is_binary_content(content: bytes) -> bool:
    chunk = content[:_BINARY_SNIFF_SIZE]
    if b"\x00" in chunk:
        return True
    try:
        chunk.decode("utf-8")
    except UnicodeDecodeError:
        return True
    return False


def validate_not_binary(file_name: str, content: bytes) -> None:
    if is_binary_content(content):
        raise FileValidationError(f"바이너리 파일은 업로드할 수 없습니다: {file_name}")
