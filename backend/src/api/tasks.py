import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.api.exceptions import AppException, NotFoundError
from src.db.session import get_db
from src.models.task import Task
from src.models.user import User
from src.services.code_analysis import file_storage
from src.services.code_analysis.code_upload_service import (
    CodeUploadError,
    CodeUploadService,
    UploadedFileInput,
    UploadResult,
)
from src.services.document.document_queue_service import DocumentQueueService
from src.services.project_service import ProjectNotFoundError
from src.services.task_service import (
    InvalidTaskDescriptionError,
    InvalidTaskTitleError,
    TaskNotFoundError,
    TaskService,
)

router = APIRouter(tags=["tasks"])

VALID_UPLOAD_METHODS = {"file", "folder", "paste"}


class UpdateTaskRequest(BaseModel):
    title: str | None = None
    description: str | None = None


class CodeFileResponse(BaseModel):
    file_name: str
    file_path: str | None
    file_extension: str | None
    file_size_bytes: int | None

    model_config = {"from_attributes": True}


class UploadedCodeResponse(BaseModel):
    detected_language: str | None
    complexity_level: str | None
    total_lines: int | None
    total_files: int | None
    upload_size_bytes: int | None
    files: list[CodeFileResponse]

    model_config = {"from_attributes": True}


class TaskResponse(BaseModel):
    id: str
    project_id: str
    task_number: int
    title: str
    description: str | None
    upload_method: str | None
    deletion_status: str
    created_at: str
    updated_at: str
    uploaded_code: UploadedCodeResponse | None

    model_config = {"from_attributes": True}


class TaskCodeFileResponse(BaseModel):
    file_name: str
    file_path: str | None
    file_extension: str | None
    content: str


class TaskCodeResponse(BaseModel):
    files: list[TaskCodeFileResponse]


def _code_file_response(code_file) -> CodeFileResponse:
    return CodeFileResponse(
        file_name=code_file.file_name,
        file_path=code_file.file_path,
        file_extension=code_file.file_extension,
        file_size_bytes=code_file.file_size_bytes,
    )


def _uploaded_code_response(result: UploadResult) -> UploadedCodeResponse:
    return UploadedCodeResponse(
        detected_language=result.uploaded_code.detected_language,
        complexity_level=result.uploaded_code.complexity_level,
        total_lines=result.uploaded_code.total_lines,
        total_files=result.uploaded_code.total_files,
        upload_size_bytes=result.uploaded_code.upload_size_bytes,
        files=[_code_file_response(f) for f in result.files],
    )


def _task_response(task: Task, upload_result: UploadResult | None) -> TaskResponse:
    return TaskResponse(
        id=str(task.id),
        project_id=str(task.project_id),
        task_number=task.task_number,
        title=task.title,
        description=task.description,
        upload_method=task.upload_method,
        deletion_status=task.deletion_status,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
        uploaded_code=_uploaded_code_response(upload_result) if upload_result else None,
    )


@router.get("/projects/{project_id}/tasks")
async def list_tasks(
    project_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[TaskResponse]:
    task_service = TaskService(session)
    try:
        tasks = await task_service.list_active(user_id=user.id, project_id=project_id)
    except ProjectNotFoundError as exc:
        raise NotFoundError(str(exc)) from exc

    upload_service = CodeUploadService(session)
    responses = []
    for task in tasks:
        upload_result = await upload_service.get_for_task(task.id)
        responses.append(_task_response(task, upload_result))
    return responses


@router.post("/projects/{project_id}/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(
    project_id: uuid.UUID,
    title: str = Form(...),
    description: str | None = Form(None),
    upload_method: str = Form(...),
    files: list[UploadFile] = File(default=[]),
    paste_content: str | None = Form(None),
    paste_filename: str | None = Form(None),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TaskResponse:
    task_service = TaskService(session)
    upload_service = CodeUploadService(session)

    try:
        await task_service.ensure_project_access(user_id=user.id, project_id=project_id)
    except ProjectNotFoundError as exc:
        raise NotFoundError(str(exc)) from exc

    try:
        TaskService.validate_title(title)
        TaskService.validate_description(description)
    except (InvalidTaskTitleError, InvalidTaskDescriptionError) as exc:
        raise AppException(str(exc)) from exc

    if upload_method not in VALID_UPLOAD_METHODS:
        raise AppException(
            f"upload_method must be one of {sorted(VALID_UPLOAD_METHODS)}"
        )

    if upload_method == "paste":
        if not paste_content or not paste_filename:
            raise AppException(
                "paste_content and paste_filename are required for paste uploads"
            )
        file_inputs = [
            UploadedFileInput(
                filename=paste_filename, content=paste_content.encode("utf-8")
            )
        ]
    else:
        if not files:
            raise AppException("files is required for file/folder uploads")
        file_inputs = [
            UploadedFileInput(filename=f.filename or "", content=await f.read())
            for f in files
        ]

    try:
        validated_files = upload_service.validate_files(file_inputs)
    except CodeUploadError as exc:
        raise AppException(str(exc)) from exc

    task = await task_service.create(
        user_id=user.id,
        project_id=project_id,
        title=title,
        description=description,
        upload_method=upload_method,
    )

    upload_result = await upload_service.create_upload(
        user_id=user.id, task_id=task.id, files=validated_files
    )

    # T096: code upload succeeded, so queue AI document generation (T094/T095)
    # right away instead of waiting for the user to open the task.
    await DocumentQueueService(session).enqueue_generation(task.id)

    return _task_response(task, upload_result)


@router.get("/tasks/{task_id}")
async def get_task(
    task_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TaskResponse:
    task_service = TaskService(session)
    try:
        task = await task_service.get(user_id=user.id, task_id=task_id)
    except TaskNotFoundError as exc:
        raise NotFoundError(str(exc)) from exc

    upload_result = await CodeUploadService(session).get_for_task(task.id)
    return _task_response(task, upload_result)


@router.patch("/tasks/{task_id}")
async def update_task(
    task_id: uuid.UUID,
    payload: UpdateTaskRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TaskResponse:
    task_service = TaskService(session)
    try:
        task = await task_service.update(
            user_id=user.id,
            task_id=task_id,
            title=payload.title,
            description=payload.description,
        )
    except TaskNotFoundError as exc:
        raise NotFoundError(str(exc)) from exc
    except (InvalidTaskTitleError, InvalidTaskDescriptionError) as exc:
        raise AppException(str(exc)) from exc

    upload_result = await CodeUploadService(session).get_for_task(task.id)
    return _task_response(task, upload_result)


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TaskResponse:
    task_service = TaskService(session)
    try:
        task = await task_service.soft_delete(user_id=user.id, task_id=task_id)
    except TaskNotFoundError as exc:
        raise NotFoundError(str(exc)) from exc

    upload_result = await CodeUploadService(session).get_for_task(task.id)
    return _task_response(task, upload_result)


@router.get("/tasks/{task_id}/code")
async def get_task_code(
    task_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TaskCodeResponse:
    task_service = TaskService(session)
    try:
        task = await task_service.get(user_id=user.id, task_id=task_id)
    except TaskNotFoundError as exc:
        raise NotFoundError(str(exc)) from exc

    upload_result = await CodeUploadService(session).get_for_task(task.id)
    files = []
    if upload_result is not None:
        for code_file in upload_result.files:
            content = file_storage.read_file(code_file.storage_path).decode("utf-8")
            files.append(
                TaskCodeFileResponse(
                    file_name=code_file.file_name,
                    file_path=code_file.file_path,
                    file_extension=code_file.file_extension,
                    content=content,
                )
            )
    return TaskCodeResponse(files=files)
