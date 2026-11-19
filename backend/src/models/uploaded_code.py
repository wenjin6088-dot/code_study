import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class UploadedCode(Base):
    __tablename__ = "uploaded_code"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    detected_language: Mapped[str | None] = mapped_column(String(50), nullable=True)
    complexity_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    total_lines: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_files: Mapped[int | None] = mapped_column(Integer, nullable=True)
    upload_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
