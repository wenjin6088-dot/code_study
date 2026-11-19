from fastapi import APIRouter

from src.api.auth import router as auth_router
from src.api.documents import router as documents_router
from src.api.projects import router as projects_router
from src.api.tasks import router as tasks_router
from src.api.trash import router as trash_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(tasks_router)
api_router.include_router(documents_router)
api_router.include_router(trash_router)


@api_router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
