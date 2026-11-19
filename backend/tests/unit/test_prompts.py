import json

import pytest

from src.services.ai.prompts import (
    CHAPTER_KEYS,
    DOCUMENT_SYSTEM_INSTRUCTION,
    CodeFileInput,
    PromptBundle,
    build_document_prompt,
    format_code_files,
)

PY_FILE = CodeFileInput(path="main.py", content="def add(a, b):\n    return a + b\n")
JS_FILE = CodeFileInput(path="src/util.js", content="export const x = 1;\n")


class TestChapterKeys:
    def test_has_exactly_seven_ordered_chapter_keys(self):
        assert CHAPTER_KEYS == tuple(f"chapter{i}" for i in range(1, 8))


class TestSystemInstruction:
    def test_targets_complete_beginners(self):
        text = DOCUMENT_SYSTEM_INSTRUCTION.lower()
        assert "beginner" in text
        assert "zero programming knowledge" in text

    def test_requires_json_only_output(self):
        assert "JSON" in DOCUMENT_SYSTEM_INSTRUCTION


class TestFormatCodeFiles:
    def test_includes_file_path_and_fenced_content(self):
        rendered = format_code_files([PY_FILE])
        assert "main.py" in rendered
        assert "```python" in rendered
        assert "return a + b" in rendered

    def test_numbers_each_line_starting_at_one(self):
        rendered = format_code_files([PY_FILE])
        assert "1: def add(a, b):" in rendered
        assert "2:     return a + b" in rendered

    def test_renders_multiple_files_in_given_order(self):
        rendered = format_code_files([PY_FILE, JS_FILE])
        assert rendered.index("main.py") < rendered.index("src/util.js")
        assert "```javascript" in rendered

    def test_unknown_extension_uses_plain_fence(self):
        rendered = format_code_files([CodeFileInput(path="notes.xyz", content="hi")])
        assert "```\n1: hi" in rendered


class TestBuildDocumentPrompt:
    def _build(self, **overrides) -> PromptBundle:
        params = dict(
            files=[PY_FILE],
            detected_language="python",
            complexity_level="beginner",
        )
        params.update(overrides)
        return build_document_prompt(**params)

    def test_returns_bundle_with_system_instruction(self):
        bundle = self._build()
        assert bundle.system_instruction == DOCUMENT_SYSTEM_INSTRUCTION
        assert isinstance(bundle.user_prompt, str)

    def test_prompt_contains_source_code(self):
        prompt = self._build().user_prompt
        assert "main.py" in prompt
        assert "return a + b" in prompt

    def test_prompt_mentions_every_chapter_key(self):
        prompt = self._build().user_prompt
        for key in CHAPTER_KEYS:
            assert f'"{key}"' in prompt

    def test_prompt_includes_detected_language_and_complexity(self):
        prompt = self._build(
            detected_language="javascript", complexity_level="advanced"
        ).user_prompt
        assert "javascript" in prompt
        assert "advanced" in prompt

    def test_prompt_defaults_to_korean_output(self):
        assert "Korean" in self._build().user_prompt

    def test_output_language_can_be_overridden(self):
        prompt = self._build(output_language="English").user_prompt
        assert "English" in prompt
        assert "Korean" not in prompt

    def test_prompt_states_chapter2_concept_limit(self):
        prompt = self._build().user_prompt
        assert "at most 5" in prompt

    def test_prompt_states_chapter7_mistake_range(self):
        prompt = self._build().user_prompt
        assert "3 to 5" in prompt

    def test_prompt_lists_required_chapter_fields(self):
        prompt = self._build().user_prompt
        for field in (
            "summary",
            "concepts",
            "analogy",
            "use_cases",
            "flowchart",
            "file_breakdown",
            "explanations",
            "syntax_breakdown",
            "steps",
            "mistakes",
        ):
            assert f'"{field}"' in prompt

    def test_prompt_embeds_valid_json_schema_example(self):
        prompt = self._build().user_prompt
        start = prompt.index("{", prompt.index("JSON structure"))
        depth = 0
        for offset, char in enumerate(prompt[start:]):
            depth += {"{": 1, "}": -1}.get(char, 0)
            if depth == 0:
                end = start + offset + 1
                break
        parsed = json.loads(prompt[start:end])
        assert tuple(parsed.keys()) == CHAPTER_KEYS

    def test_empty_file_list_is_rejected(self):
        with pytest.raises(ValueError):
            self._build(files=[])

    def test_blank_only_files_are_rejected(self):
        with pytest.raises(ValueError):
            self._build(files=[CodeFileInput(path="a.py", content="   \n")])
