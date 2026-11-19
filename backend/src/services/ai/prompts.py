import json
from dataclasses import dataclass
from pathlib import PurePosixPath

CHAPTER_KEYS: tuple[str, ...] = tuple(f"chapter{i}" for i in range(1, 8))

MAX_PREREQUISITE_CONCEPTS = 5
MIN_COMMON_MISTAKES = 3
MAX_COMMON_MISTAKES = 5

DOCUMENT_SYSTEM_INSTRUCTION = (
    "You are an expert teacher explaining code to complete beginners with zero "
    "programming knowledge. Every technical term must be introduced with everyday "
    "language and a real-life analogy before it is used. Never assume prior "
    "knowledge. Respond with a single JSON object only: no markdown, no prose "
    "outside the JSON."
)

_FENCE_LANGUAGES = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".kt": "kotlin",
    ".swift": "swift",
    ".html": "html",
    ".css": "css",
    ".sql": "sql",
    ".sh": "bash",
}

_DOCUMENT_SCHEMA_EXAMPLE = {
    "chapter1": {
        "title": "What This Code Does",
        "summary": "One plain-language sentence, no jargon.",
    },
    "chapter2": {
        "title": "Prerequisites Knowledge",
        "concepts": [
            {
                "name": "Concept name",
                "explanation": "Simple explanation in everyday words.",
                "analogy": "Real-life analogy.",
                "example": "Short code example.",
                "use_cases": "Where this is commonly used.",
            }
        ],
    },
    "chapter3": {
        "title": "Code Structure Overview",
        "flowchart": "Mermaid flowchart (flowchart TD ...) of the execution flow.",
        "file_breakdown": {"path/to/file": "What this file is responsible for."},
    },
    "chapter4": {
        "title": "Line-by-Line Explanation",
        "explanations": [
            {
                "file": "path/to/file",
                "line_start": 1,
                "line_end": 1,
                "code": "The exact source line(s).",
                "what_it_does": "What this line does.",
                "syntax_breakdown": "Each token/symbol explained.",
                "analogy": "Real-life analogy.",
                "alternative_example": "Another way to write or use this.",
                "notes": "Important caveats or tips.",
            }
        ],
    },
    "chapter5": {
        "title": "Execution Flow Simulation",
        "steps": [
            {
                "step": 1,
                "description": "What happens at this step.",
                "data_state": "Values of the relevant variables after this step.",
            }
        ],
    },
    "chapter6": {
        "title": "Core Concepts Summary",
        "concepts": [
            {
                "name": "Concept name",
                "what_it_is": "Definition in plain words.",
                "why_used": "Why programmers use it.",
                "where_applied": "Where it shows up in real programs.",
            }
        ],
    },
    "chapter7": {
        "title": "Common Mistakes",
        "mistakes": [
            {
                "wrong": "Incorrect code example.",
                "right": "Corrected code example.",
                "why": "Why this matters.",
                "fix": "How to fix or avoid it.",
            }
        ],
    },
}

_CHAPTER_RULES = f"""\
Chapter rules:
- "chapter1": exactly one sentence in plain language with no technical jargon.
- "chapter2": at most {MAX_PREREQUISITE_CONCEPTS} prerequisite concepts, each with \
"explanation", "analogy", "example" and "use_cases". Pick only what a beginner must \
know to read this code.
- "chapter3": "flowchart" must be a Mermaid diagram showing the execution flow; \
"file_breakdown" must have one entry per source file.
- "chapter4": cover the source in order from top to bottom. Each entry must give \
"what_it_does", "syntax_breakdown", "analogy", "alternative_example" and "notes". \
"line_start"/"line_end" must match the numbered lines provided.
- "chapter5": simulate one realistic run step by step, showing how data changes.
- "chapter6": for each core concept give "what_it_is", "why_used" and "where_applied".
- "chapter7": {MIN_COMMON_MISTAKES} to {MAX_COMMON_MISTAKES} common mistakes, each \
with "wrong", "right", "why" and "fix".
- Every chapter must include a "title"."""


@dataclass(frozen=True)
class CodeFileInput:
    path: str
    content: str


@dataclass(frozen=True)
class PromptBundle:
    system_instruction: str
    user_prompt: str


def _fence_language(path: str) -> str:
    return _FENCE_LANGUAGES.get(PurePosixPath(path).suffix.lower(), "")


def _number_lines(content: str) -> str:
    return "\n".join(
        f"{number}: {line}" for number, line in enumerate(content.splitlines(), 1)
    )


def _format_code_file(file: CodeFileInput) -> str:
    fence = _fence_language(file.path)
    return f"### {file.path}\n```{fence}\n{_number_lines(file.content)}\n```"


def format_code_files(files: list[CodeFileInput]) -> str:
    return "\n\n".join(_format_code_file(file) for file in files)


def build_document_prompt(
    files: list[CodeFileInput],
    *,
    detected_language: str,
    complexity_level: str,
    output_language: str = "Korean",
) -> PromptBundle:
    if not any(file.content.strip() for file in files):
        raise ValueError("At least one non-empty code file is required")

    schema = json.dumps(_DOCUMENT_SCHEMA_EXAMPLE, indent=2, ensure_ascii=False)
    user_prompt = f"""\
Create a 7-chapter textbook-style learning document for the code below.

Context:
- Programming language: {detected_language}
- Complexity level: {complexity_level}
- Write all explanations in {output_language}. Keep code, identifiers and JSON keys \
exactly as they are.
- Line numbers are shown as "N: " prefixes; they are not part of the code.

Source code:
{format_code_files(files)}

{_CHAPTER_RULES}

Return exactly this JSON structure (same keys, same nesting; the string values are \
placeholders describing what to write):
{schema}"""
    return PromptBundle(
        system_instruction=DOCUMENT_SYSTEM_INSTRUCTION, user_prompt=user_prompt
    )
