import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.exceptions import register_exception_handlers
from src.api.router import api_router

app = FastAPI(title="AI Code Learning Platform API")

register_exception_handlers(app)

allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "AI Code Learning Platform API"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router)
