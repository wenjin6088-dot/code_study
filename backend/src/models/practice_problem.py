import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class PracticeProblem(Base):
    __tablename__ = "practice_problems"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
    )
    problem_number: Mapped[int] = mapped_column(Integer, nullable=False)
    problem_type: Mapped[str] = mapped_column(String(20), nullable=False)
    problem_statement: Mapped[str] = mapped_column(Text, nullable=False)
    learning_objective: Mapped[str | None] = mapped_column(Text, nullable=True)
    hints: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    model_solution: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
