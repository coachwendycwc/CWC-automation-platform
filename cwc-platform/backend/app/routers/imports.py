from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.import_job import ImportJob
from app.models.user import User
from app.services.auth_service import require_admin
from app.services.import_service import (
    PRESETS,
    run_preview,
    run_commit,
    run_undo,
)

router = APIRouter(prefix="/imports", tags=["Imports"])


class ImportRequest(BaseModel):
    entity_type: str
    csv_text: str
    mapping: dict[str, str] | None = None
    dedupe_strategy: str = "skip"


class ImportJobResponse(BaseModel):
    id: str
    source: str
    entity_type: str
    status: str
    total_rows: int
    created_count: int
    skipped_count: int
    updated_count: int
    error_count: int
    row_errors: list
    created_at: datetime | None

    model_config = {"from_attributes": True}


@router.get("/presets")
async def list_presets(current_user: User = Depends(require_admin)):
    """Importable-platform presets: name, entity type, and column mapping."""
    return [
        {
            "name": name,
            "entity_type": preset["entity_type"],
            "header_signature": preset["header_signature"],
            "mapping": preset["mapping"],
        }
        for name, preset in PRESETS.items()
    ]


@router.post("/preview")
async def preview_import(
    request: ImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Dry-run: parse, map, validate and dedupe-check. Writes nothing."""
    try:
        return await run_preview(
            db,
            request.entity_type,
            request.csv_text,
            mapping=request.mapping,
            dedupe_strategy=request.dedupe_strategy,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/commit", response_model=ImportJobResponse, status_code=201)
async def commit_import(
    request: ImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Run the import in one transaction and record an undoable ImportJob."""
    try:
        job = await run_commit(
            db,
            request.entity_type,
            request.csv_text,
            mapping=request.mapping,
            dedupe_strategy=request.dedupe_strategy,
            user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return ImportJobResponse.model_validate(job)


@router.get("", response_model=list[ImportJobResponse])
async def list_imports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Import history, newest first."""
    result = await db.execute(
        select(ImportJob).order_by(ImportJob.created_at.desc())
    )
    return [ImportJobResponse.model_validate(j) for j in result.scalars().all()]


@router.post("/{job_id}/undo")
async def undo_import(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete the records this import created (skips ones referenced since)."""
    try:
        return await run_undo(db, job_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
