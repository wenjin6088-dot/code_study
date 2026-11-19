import pytest

from src.services.code_analysis.language_detector import (
    LanguageDetectionError,
    detect_dominant_language,
    detect_language,
)


class TestDetectLanguage:
    @pytest.mark.parametrize(
        "file_name,expected_language",
        [
            ("main.py", "python"),
            ("app.js", "javascript"),
            ("app.ts", "typescript"),
            ("App.jsx", "javascript"),
            ("App.tsx", "typescript"),
            ("index.html", "html"),
            ("style.css", "css"),
            ("Main.java", "java"),
            ("main.cpp", "cpp"),
            ("main.c", "c"),
            ("notes.txt", "text"),
            ("README.md", "markdown"),
        ],
    )
    def test_detects_language_for_each_supported_extension(
        self, file_name, expected_language
    ):
        assert detect_language(file_name) == expected_language

    def test_detection_is_case_insensitive_for_extension(self):
        assert detect_language("App.PY") == "python"

    def test_raises_for_unsupported_extension(self):
        with pytest.raises(LanguageDetectionError):
            detect_language("archive.zip")

    def test_raises_for_extensionless_file(self):
        with pytest.raises(LanguageDetectionError):
            detect_language("Makefile")


class TestDetectDominantLanguage:
    def test_returns_language_shared_by_all_files(self):
        files = ["main.py", "utils.py", "models.py"]
        assert detect_dominant_language(files) == "python"

    def test_returns_most_frequent_language_among_mixed_files(self):
        files = ["index.html", "style.css", "app.js", "helpers.js", "main.js"]
        assert detect_dominant_language(files) == "javascript"

    def test_ignores_documentation_files_when_picking_dominant_language(self):
        files = ["README.md", "notes.txt", "main.py"]
        assert detect_dominant_language(files) == "python"

    def test_breaks_ties_alphabetically_for_determinism(self):
        files = ["a.py", "b.js"]
        assert detect_dominant_language(files) == "javascript"

    def test_raises_when_no_code_language_can_be_determined(self):
        with pytest.raises(LanguageDetectionError):
            detect_dominant_language(["README.md", "notes.txt"])

    def test_raises_for_empty_file_list(self):
        with pytest.raises(LanguageDetectionError):
            detect_dominant_language([])

    def test_skips_individually_undetectable_files_without_failing(self):
        files = ["main.py", "archive.zip"]
        assert detect_dominant_language(files) == "python"
