import pytest

from src.services.task_service import (
    InvalidTaskDescriptionError,
    InvalidTaskTitleError,
    TaskService,
)


class TestValidateTitle:
    def test_accepts_title_with_five_characters(self):
        TaskService.validate_title("Title")  # should not raise

    def test_rejects_title_shorter_than_five_characters(self):
        with pytest.raises(InvalidTaskTitleError):
            TaskService.validate_title("Hi")

    def test_rejects_empty_title(self):
        with pytest.raises(InvalidTaskTitleError):
            TaskService.validate_title("")

    def test_rejects_whitespace_only_title(self):
        with pytest.raises(InvalidTaskTitleError):
            TaskService.validate_title("      ")


class TestValidateDescription:
    def test_accepts_none_description(self):
        TaskService.validate_description(None)  # should not raise

    def test_accepts_description_at_exactly_the_limit(self):
        TaskService.validate_description("a" * 500)  # should not raise

    def test_rejects_description_over_the_limit(self):
        with pytest.raises(InvalidTaskDescriptionError):
            TaskService.validate_description("a" * 501)
