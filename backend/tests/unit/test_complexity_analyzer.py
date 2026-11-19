from src.services.code_analysis.complexity_analyzer import (
    ComplexityMetrics,
    analyze_complexity,
    analyze_complexity_for_files,
    analyze_metrics,
    classify_complexity,
    count_functions,
    count_lines,
    max_nesting_depth,
)


class TestCountLines:
    def test_counts_non_blank_lines(self):
        content = "line1\nline2\n\nline3\n"
        assert count_lines(content) == 3

    def test_empty_content_has_zero_lines(self):
        assert count_lines("") == 0

    def test_whitespace_only_lines_are_not_counted(self):
        content = "line1\n   \n\t\nline2\n"
        assert count_lines(content) == 2


class TestMaxNestingDepth:
    def test_flat_code_has_zero_depth(self):
        content = "x = 1\ny = 2\n"
        assert max_nesting_depth(content) == 0

    def test_single_level_indent_is_depth_one(self):
        content = "if True:\n    x = 1\n"
        assert max_nesting_depth(content) == 1

    def test_deeply_nested_indent_is_counted(self):
        content = (
            "def outer():\n"
            "    if True:\n"
            "        for i in range(1):\n"
            "            print(i)\n"
        )
        assert max_nesting_depth(content) == 3

    def test_tabs_count_as_one_level_each(self):
        content = "if True:\n\tif True:\n\t\tx = 1\n"
        assert max_nesting_depth(content) == 2

    def test_blank_lines_do_not_affect_depth(self):
        content = "if True:\n    x = 1\n\n\n"
        assert max_nesting_depth(content) == 1


class TestCountFunctions:
    def test_counts_python_function_definitions(self):
        content = "def foo():\n    pass\n\ndef bar():\n    pass\n"
        assert count_functions(content) == 2

    def test_counts_async_python_function(self):
        content = "async def fetch():\n    pass\n"
        assert count_functions(content) == 1

    def test_counts_javascript_function_declaration(self):
        content = "function greet() {\n  console.log('hi');\n}\n"
        assert count_functions(content) == 1

    def test_counts_java_style_method(self):
        content = "public static void main(String[] args) {\n    return;\n}\n"
        assert count_functions(content) == 1

    def test_returns_zero_for_code_without_functions(self):
        content = "x = 1\ny = x + 1\nprint(y)\n"
        assert count_functions(content) == 0


class TestClassifyComplexity:
    def test_classifies_small_simple_code_as_beginner(self):
        metrics = ComplexityMetrics(line_count=10, nesting_depth=0, function_count=1)
        assert classify_complexity(metrics) == "beginner"

    def test_classifies_at_beginner_boundary(self):
        metrics = ComplexityMetrics(line_count=50, nesting_depth=1, function_count=3)
        assert classify_complexity(metrics) == "beginner"

    def test_classifies_just_past_beginner_boundary_as_intermediate(self):
        metrics = ComplexityMetrics(line_count=51, nesting_depth=1, function_count=3)
        assert classify_complexity(metrics) == "intermediate"

    def test_classifies_moderate_code_as_intermediate(self):
        metrics = ComplexityMetrics(line_count=120, nesting_depth=2, function_count=6)
        assert classify_complexity(metrics) == "intermediate"

    def test_classifies_large_deeply_nested_code_as_advanced(self):
        metrics = ComplexityMetrics(line_count=400, nesting_depth=4, function_count=20)
        assert classify_complexity(metrics) == "advanced"

    def test_high_nesting_alone_can_push_to_advanced(self):
        metrics = ComplexityMetrics(line_count=30, nesting_depth=5, function_count=2)
        assert classify_complexity(metrics) == "advanced"

    def test_high_lines_and_functions_push_to_advanced_without_deep_nesting(self):
        metrics = ComplexityMetrics(line_count=300, nesting_depth=0, function_count=50)
        assert classify_complexity(metrics) == "advanced"


class TestAnalyzeMetricsAndComplexity:
    def test_analyze_metrics_combines_all_three_measures(self):
        content = "def foo():\n    if True:\n        return 1\n"
        metrics = analyze_metrics(content)
        assert metrics == ComplexityMetrics(
            line_count=3, nesting_depth=2, function_count=1
        )

    def test_analyze_complexity_returns_valid_level_for_simple_snippet(self):
        content = "x = 1\nprint(x)\n"
        assert analyze_complexity(content) == "beginner"

    def test_analyze_complexity_returns_valid_level_for_empty_content(self):
        assert analyze_complexity("") == "beginner"


class TestAnalyzeComplexityForFiles:
    def test_sums_lines_and_functions_across_files(self):
        file_a = "def a():\n    pass\n"
        file_b = "def b():\n    pass\n"
        assert analyze_complexity_for_files([file_a, file_b]) == "beginner"

    def test_uses_worst_case_nesting_depth_across_files(self):
        shallow = "x = 1\n"
        deep = (
            "def outer():\n"
            "    if True:\n"
            "        for i in range(1):\n"
            "            print(i)\n"
        )
        assert analyze_complexity_for_files([shallow, deep]) == analyze_complexity(deep)

    def test_empty_file_list_is_beginner(self):
        assert analyze_complexity_for_files([]) == "beginner"
