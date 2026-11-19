import uuid
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.api.exceptions import NotFoundError
from src.db.session import get_db
from src.models.practice_problem import PracticeProblem
from src.models.user import User
from src.services.task_service import TaskNotFoundError, TaskService

router = APIRouter(tags=["practice"])


class PracticeProblemResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    problem_number: int
    problem_type: str
    problem_statement: str
    learning_objective: str | None
    hints: list[Any] | None
    model_solution: str | None
    expected_output: str | None


class TaskPracticeResponse(BaseModel):
    task_id: str
    status: str
    problems: list[PracticeProblemResponse]


def _to_response(problem: PracticeProblem) -> PracticeProblemResponse:
    return PracticeProblemResponse(
        problem_number=problem.problem_number,
        problem_type=problem.problem_type,
        problem_statement=problem.problem_statement,
        learning_objective=problem.learning_objective,
        hints=problem.hints,
        model_solution=problem.model_solution,
        expected_output=problem.expected_output,
    )


async def _get_owned_problems(
    task_id: uuid.UUID, user: User, session: AsyncSession
) -> list[PracticeProblem]:
    try:
        task = await TaskService(session).get(user_id=user.id, task_id=task_id)
    except TaskNotFoundError as exc:
        raise NotFoundError("Task not found") from exc

    result = await session.execute(
        select(PracticeProblem)
        .where(PracticeProblem.task_id == task.id)
        .order_by(PracticeProblem.problem_number.asc())
    )
    return list(result.scalars().all())


@router.get("/tasks/{task_id}/practice")
async def get_practice_problems(
    task_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TaskPracticeResponse:
    problems = await _get_owned_problems(task_id, user, session)
    return TaskPracticeResponse(
        task_id=str(task_id),
        status="completed" if problems else "pending",
        problems=[_to_response(p) for p in problems],
    )


@router.get("/tasks/{task_id}/practice/{problem_number}")
async def get_practice_problem(
    task_id: uuid.UUID,
    problem_number: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PracticeProblemResponse:
    problems = await _get_owned_problems(task_id, user, session)
    for problem in problems:
        if problem.problem_number == problem_number:
            return _to_response(problem)
    raise NotFoundError("Practice problem not found")
