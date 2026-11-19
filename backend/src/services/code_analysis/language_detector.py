from collections import Counter
from pathlib import Path

from pygments.lexers import get_lexer_for_filename
from pygments.util import ClassNotFound

# Pygments has no filename-based lexer for these extensions in the pinned
# version; both are JS/TS with embedded JSX syntax, so they inherit the
# base language rather than being treated as undetectable.
_EXTENSION_OVERRIDES: dict[str, str] = {
    ".jsx": "javascript",
    ".tsx": "typescript",
}

_LEXER_NAME_TO_LANGUAGE: dict[str, str] = {
    "python": "python",
    "javascript": "javascript",
    "typescript": "typescript",
    "html": "html",
    "css": "css",
    "java": "java",
    "c++": "cpp",
    "c": "c",
    "text only": "text",
    "markdown": "markdown",
}

# Documentation-only formats are ignored when picking the dominant language
# of an upload, since they don't represent the project's programming language.
_NON_CODE_LANGUAGES = frozenset({"text", "markdown"})


class LanguageDetectionError(ValueError):
    """Raised when a programming language cannot be determined for a file."""


def detect_language(file_name: str) -> str:
    path = Path(file_name)
    extension = path.suffix.lower()
    override = _EXTENSION_OVERRIDES.get(extension)
    if override is not None:
        return override

    # Pygments matches filename glob patterns case-sensitively, so normalize
    # the extension before lookup (callers may pass "App.PY", "Main.JAVA", etc.)
    normalized_name = path.stem + extension
    try:
        lexer = get_lexer_for_filename(normalized_name)
    except ClassNotFound as exc:
        raise LanguageDetectionError(
            f"프로그래밍 언어를 감지할 수 없습니다: {file_name}"
        ) from exc

    language = _LEXER_NAME_TO_LANGUAGE.get(lexer.name.lower())
    if language is None:
        raise LanguageDetectionError(
            f"지원하지 않는 언어가 감지되었습니다: {file_name} ({lexer.name})"
        )
    return language


def detect_dominant_language(file_names: list[str]) -> str:
    counts: Counter[str] = Counter()
    for file_name in file_names:
        try:
            language = detect_language(file_name)
        except LanguageDetectionError:
            continue
        if language in _NON_CODE_LANGUAGES:
            continue
        counts[language] += 1

    if not counts:
        raise LanguageDetectionError(
            "업로드된 파일에서 프로그래밍 언어를 감지할 수 없습니다."
        )

    top_count = counts.most_common(1)[0][1]
    top_languages = [
        language for language, count in counts.items() if count == top_count
    ]
    return min(top_languages)
