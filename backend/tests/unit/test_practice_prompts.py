import json

import pytest

from src.services.ai.prompts import (
    PRACTICE_PROBLEM_TYPES,
    PRACTICE_SYSTEM_INSTRUCTION,
    CodeFileInput,
    build_practice_prompt,
)

PY_FILE = CodeFileInput(path="main.py", content="def add(a, b):\n    return a + b\n")


class TestPracticeProblemTypes:
    def test_has_exactly_five_types_in_difficulty_order(self):
        assert PRACTICE_PROBLEM_TYPES == (
            "follow_along",
            "fill_blanks",
            "modify",
            "debug",
            "create",
        )


class TestPracticeSystemInstruction:
    def test_targets_complete_beginners(self):
        text = PRACTICE_SYSTEM_INSTRUCTION.lower()
        assert "beginner" in text

    def test_requires_json_only_output(self):
        assert "JSON" in PRACTICE_SYSTEM_INSTRUCTION


class TestBuildPracticePrompt:
    def _build(self, **overrides):
        params = dict(
            files=[PY_FILE], detected_language="python", complexity_level="beginner"
        )
        params.update(overrides)
        return build_practice_prompt(**params)

    def test_returns_bundle_with_system_instruction(self):
        bundle = self._build()
        assert bundle.system_instruction == PRACTICE_SYSTEM_INSTRUCTION
        assert isinstance(bundle.user_prompt, str)

    def test_prompt_contains_source_code(self):
        prompt = self._build().user_prompt
        assert "main.py" in prompt
        assert "return a + b" in prompt

    def test_prompt_mentions_every_problem_type(self):
        prompt = self._build().user_prompt
        for problem_type in PRACTICE_PROBLEM_TYPES:
            assert f'"{problem_type}"' in prompt

    def test_prompt_states_exactly_five_problems(self):
        prompt = self._build().user_prompt
        assert "5" in prompt
        assert "exactly 5" in prompt.lower()

    def test_prompt_requires_text_only_no_execution(self):
        prompt = self._build().user_prompt
        assert "no in-browser" in prompt.lower() or "text-only" in prompt.lower()

    def test_prompt_defaults_to_korean_output(self):
        assert "Korean" in self._build().user_prompt

    def test_output_language_can_be_overridden(self):
        prompt = self._build(output_language="English").user_prompt
        assert "English" in prompt
        assert "Korean" not in prompt

    def test_prompt_includes_detected_language_and_complexity(self):
        prompt = self._build(
            detected_language="javascript", complexity_level="advanced"
        ).user_prompt
        assert "javascript" in prompt
        assert "advanced" in prompt

    def test_prompt_lists_required_problem_fields(self):
        prompt = self._build().user_prompt
        for field in (
            "problem_number",
            "problem_type",
            "problem_statement",
            "learning_objective",
            "hints",
            "model_solution",
            "expected_output",
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
        assert "problems" in parsed
        assert len(parsed["problems"]) == 5

    def test_empty_file_list_is_rejected(self):
        with pytest.raises(ValueError):
            self._build(files=[])

    def test_blank_only_files_are_rejected(self):
        with pytest.raises(ValueError):
            self._build(files=[CodeFileInput(path="a.py", content="   \n")])
