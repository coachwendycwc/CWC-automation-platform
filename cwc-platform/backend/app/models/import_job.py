import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Integer, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ImportJob(Base):
    """Audit record of one migration-importer commit.

    created_ids remembers exactly what was written so the import can be
    undone; row_errors preserves per-row failures for the admin to review.
    """

    __tablename__ = "import_jobs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="custom")
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="committed"
    )  # committed, undone
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_ids: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    row_errors: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
