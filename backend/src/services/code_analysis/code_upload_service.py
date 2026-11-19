import uuid
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.code_file import CodeFile
from src.models.uploaded_code import UploadedCode
from src.services.code_analysis import file_storage
from src.services.code_analysis.complexity_analyzer import (
    analyze_complexity_for_files,
    count_lines,
)
from src.services.code_analysis.language_detector import (
    LanguageDetectionError,
    detect_dominant_language,
)
from src.utils.file_validator import (
    FileValidationError,
    get_file_extension,
    validate_extension,
    validate_not_binary,
    validate_total_size,
)

MIN_FILE_COUNT = 1
MAX_FILE_COUNT = 20  # FR-018

_EXCLUDED_PATH_SEGMENTS = frozenset(
    {".git", "node_modules", ".DS_Store", "__pycache__"}
)


class CodeUploadError(ValueError):
    """Raised when an upload fails file-count, path, or content validation."""


@dataclass(frozen=True)
class UploadedFileInput:
    filename: str
    content: bytes


@dataclass(frozen=True)
class UploadResult:
    uploaded_code: UploadedCode
    files: list[CodeFile]


def _segments(filename: str) -> list[str]:
    return filename.replace("\\", "/").split("/")


def _is_excluded(filename: str) -> bool:
    return any(segment in _EXCLUDED_PATH_SEGMENTS for segment in _segments(filename))


def _has_path_traversal(filename: str) -> bool:
    normalized = filename.replace("\\", "/")
    if normalized.startswith("/"):
        return True
    return ".." in _segments(normalized)


class CodeUploadService:
    def __init__(self, session: AsyncSession):
        self.session = session

    def validate_files(
        self, files: list[UploadedFileInput]
    ) -> list[UploadedFileInput]:
        """Run the full upload validation pipeline (FR-017/FR-018 + file_validator)
        and return the surviving files, in order. Raises CodeUploadError."""
        remaining = [f for f in files if not _is_excluded(f.filename)]

        for file in remaining:
            if _has_path_traversal(file.filename):
                raise CodeUploadError(
                    f"허용되지 않는 파일 경로입니다: {file.filename}"
                )

        if not (MIN_FILE_COUNT <= len(remaining) <= MAX_FILE_COUNT):
            raise CodeUploadError(
                f"업로드 파일 개수는 {MIN_FILE_COUNT}~{MAX_FILE_COUNT}개여야 합니다 "
                f"(현재 {len(remaining)}개)"
            )

        try:
            for file in remaining:
                validate_extension(file.filename)
            validate_total_size(sum(len(f.content) for f in remaining))
            for file in remaining:
                validate_not_binary(file.filename, file.content)
        except FileValidationError as exc:
            raise CodeUploadError(str(exc)) from exc

        return remaining

    async def create_upload(
        self,
        user_id: uuid.UUID,
        task_id: uuid.UUID,
        files: list[UploadedFileInput],
    ) -> UploadResult:
        """Persist already-validated files to storage and create the
        UploadedCode + CodeFile rows for ``task_id``."""
        file_names = [f.filename for f in files]
        contents = [f.content.decode("utf-8") for f in files]

        try:
            detected_language = detect_dominant_language(file_names)
        except LanguageDetectionError:
            detected_language = None

        uploaded_code = UploadedCode(
            task_id=task_id,
            detected_language=detected_language,
            complexity_level=analyze_complexity_for_files(contents),
            total_lines=sum(count_lines(content) for content in contents),
            total_files=len(files),
            upload_size_bytes=sum(len(f.content) for f in files),
        )
        self.session.add(uploaded_code)
        await self.session.flush()

        code_files: list[CodeFile] = []
        for file in files:
            storage_path = file_storage.save_file(
                user_id, task_id, file.filename, file.content
            )
            normalized_name = file.filename.replace("\\", "/")
            code_file = CodeFile(
                uploaded_code_id=uploaded_code.id,
                file_name=Path(normalized_name).name,
                file_path=normalized_name if "/" in normalized_name else None,
                file_extension=get_file_extension(file.filename) or None,
                file_size_bytes=len(file.content),
                storage_path=storage_path,
            )
            self.session.add(code_file)
            code_files.append(code_file)

        await self.session.commit()
        await self.session.refresh(uploaded_code)
        for code_file in code_files:
            await self.session.refresh(code_file)

        return UploadResult(uploaded_code=uploaded_code, files=code_files)

    async def get_for_task(self, task_id: uuid.UUID) -> UploadResult | None:
        result = await self.session.execute(
            select(UploadedCode).where(UploadedCode.task_id == task_id)
        )
        uploaded_code = result.scalar_one_or_none()
        if uploaded_code is None:
            return None

        files_result = await self.session.execute(
            select(CodeFile)
            .where(CodeFile.uploaded_code_id == uploaded_code.id)
            .order_by(CodeFile.file_name.asc())
        )
        files = list(files_result.scalars().all())
        return UploadResult(uploaded_code=uploaded_code, files=files)
