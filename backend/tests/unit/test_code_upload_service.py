import pytest

from src.services.code_analysis.code_upload_service import (
    CodeUploadError,
    CodeUploadService,
    UploadedFileInput,
)

service = CodeUploadService(session=None)


def _file(name: str, content: bytes = b"print(1)\n") -> UploadedFileInput:
    return UploadedFileInput(filename=name, content=content)


class TestValidateFilesExclusion:
    def test_silently_drops_git_directory_files(self):
        files = [_file("src/app.py"), _file(".git/config")]

        result = service.validate_files(files)

        assert [f.filename for f in result] == ["src/app.py"]

    def test_silently_drops_node_modules_and_pycache_and_ds_store(self):
        files = [
            _file("main.py"),
            _file("node_modules/pkg/index.js"),
            _file("__pycache__/main.cpython-311.pyc"),
            _file(".DS_Store"),
        ]

        result = service.validate_files(files)

        assert [f.filename for f in result] == ["main.py"]


class TestValidateFilesPathTraversal:
    def test_rejects_parent_directory_segment(self):
        with pytest.raises(CodeUploadError):
            service.validate_files([_file("../../etc/passwd")])

    def test_rejects_absolute_path(self):
        with pytest.raises(CodeUploadError):
            service.validate_files([_file("/etc/passwd")])


class TestValidateFilesCount:
    def test_rejects_zero_files_after_exclusion(self):
        with pytest.raises(CodeUploadError):
            service.validate_files([_file(".git/config")])

    def test_rejects_more_than_twenty_files(self):
        files = [_file(f"file{i}.py") for i in range(21)]

        with pytest.raises(CodeUploadError):
            service.validate_files(files)

    def test_accepts_exactly_twenty_files(self):
        files = [_file(f"file{i}.py") for i in range(20)]

        result = service.validate_files(files)

        assert len(result) == 20


class TestValidateFilesContent:
    def test_rejects_unsupported_extension(self):
        with pytest.raises(CodeUploadError):
            service.validate_files([_file("archive.zip", b"PK\x03\x04")])

    def test_rejects_binary_content(self):
        with pytest.raises(CodeUploadError):
            service.validate_files([_file("image.py", b"\x89PNG\x00\x01\x02")])

    def test_rejects_total_size_over_limit(self):
        huge = b"a" * (10 * 1024 * 1024 + 1)

        with pytest.raises(CodeUploadError):
            service.validate_files([_file("big.txt", huge)])

    def test_accepts_valid_single_file(self):
        result = service.validate_files([_file("main.py")])

        assert len(result) == 1
        assert result[0].filename == "main.py"

    def test_folder_upload_preserves_relative_path_in_result(self):
        result = service.validate_files([_file("src/app.py")])

        assert result[0].filename == "src/app.py"
