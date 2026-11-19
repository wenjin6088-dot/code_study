import uuid

import pytest

from src.services.code_analysis import file_storage


@pytest.fixture(autouse=True)
def _upload_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))
    return tmp_path


class TestSaveFile:
    def test_writes_content_under_user_and_task_directories(self, tmp_path):
        user_id = uuid.uuid4()
        task_id = uuid.uuid4()

        storage_path = file_storage.save_file(user_id, task_id, "main.py", b"print(1)")

        expected_dir = tmp_path / str(user_id) / str(task_id)
        assert expected_dir.is_dir()
        assert storage_path.startswith(str(expected_dir))

    def test_stored_filename_keeps_only_basename_for_nested_paths(self, tmp_path):
        user_id = uuid.uuid4()
        task_id = uuid.uuid4()

        storage_path = file_storage.save_file(
            user_id, task_id, "src/app.py", b"print(2)"
        )

        assert storage_path.endswith("_app.py")
        assert "src" not in storage_path.split(str(task_id))[-1]

    def test_prefixes_filename_with_a_uuid_to_avoid_collisions(self, tmp_path):
        user_id = uuid.uuid4()
        task_id = uuid.uuid4()

        first = file_storage.save_file(user_id, task_id, "main.py", b"a")
        second = file_storage.save_file(user_id, task_id, "main.py", b"b")

        assert first != second
        assert file_storage.read_file(first) == b"a"
        assert file_storage.read_file(second) == b"b"


class TestReadFile:
    def test_round_trips_bytes_written_by_save_file(self, tmp_path):
        user_id = uuid.uuid4()
        task_id = uuid.uuid4()
        content = "한글 코드 주석\nprint('hi')\n".encode()

        storage_path = file_storage.save_file(user_id, task_id, "hello.py", content)

        assert file_storage.read_file(storage_path) == content
