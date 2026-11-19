import re
from dataclasses import dataclass

_INDENT_WIDTH = 4

_FUNCTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\s*(async\s+)?def\s+\w+\s*\("),  # Python
    re.compile(r"^\s*(export\s+)?(default\s+)?(async\s+)?function\s*\w*\s*\("),  # JS/TS
    re.compile(
        r"^\s*(public|private|protected|static|final|\s)*"
        r"[\w<>\[\],]+\s+\w+\s*\([^;{}]*\)\s*\{"
    ),  # Java/C/C++ method definitions
)

# (soft_limit, hard_limit): value <= soft_limit -> 0, <= hard_limit -> 1, else 2
_LINE_COUNT_THRESHOLDS = (50, 200)
_NESTING_DEPTH_THRESHOLDS = (1, 2)
_FUNCTION_COUNT_THRESHOLDS = (3, 10)


@dataclass(frozen=True)
class ComplexityMetrics:
    line_count: int
    nesting_depth: int
    function_count: int


def count_lines(content: str) -> int:
    return len([line for line in content.splitlines() if line.strip()])


def max_nesting_depth(content: str) -> int:
    depth = 0
    for line in content.splitlines():
        if not line.strip():
            continue
        indent = line[: len(line) - len(line.lstrip(" \t"))]
        tabs = indent.count("\t")
        spaces = len(indent) - tabs
        depth = max(depth, tabs + spaces // _INDENT_WIDTH)
    return depth


def count_functions(content: str) -> int:
    return sum(
        1
        for line in content.splitlines()
        if any(pattern.search(line) for pattern in _FUNCTION_PATTERNS)
    )


def analyze_metrics(content: str) -> ComplexityMetrics:
    return ComplexityMetrics(
        line_count=count_lines(content),
        nesting_depth=max_nesting_depth(content),
        function_count=count_functions(content),
    )


def _tier_score(value: int, thresholds: tuple[int, int]) -> int:
    soft_limit, hard_limit = thresholds
    if value <= soft_limit:
        return 0
    if value <= hard_limit:
        return 1
    return 2


def classify_complexity(metrics: ComplexityMetrics) -> str:
    nesting_score = _tier_score(metrics.nesting_depth, _NESTING_DEPTH_THRESHOLDS)
    if nesting_score == 2:
        # Deep nesting alone makes code hard to follow for beginners,
        # regardless of how short or function-light it otherwise is.
        return "advanced"

    total_score = (
        _tier_score(metrics.line_count, _LINE_COUNT_THRESHOLDS)
        + nesting_score
        + _tier_score(metrics.function_count, _FUNCTION_COUNT_THRESHOLDS)
    )
    if total_score == 0:
        return "beginner"
    if total_score <= 3:
        return "intermediate"
    return "advanced"


def analyze_complexity(content: str) -> str:
    return classify_complexity(analyze_metrics(content))


def analyze_complexity_for_files(contents: list[str]) -> str:
    depths = (max_nesting_depth(content) for content in contents)
    combined = ComplexityMetrics(
        line_count=sum(count_lines(content) for content in contents),
        nesting_depth=max(depths, default=0),
        function_count=sum(count_functions(content) for content in contents),
    )
    return classify_complexity(combined)
