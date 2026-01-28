"""ICF Coaching Hours Tracker router."""
from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
import csv
import io

from app.database import get_db
from app.services.auth_service import get_current_user
from app.models.user import User
from app.models.coaching_session import CoachingSession
from app.models.contact import Contact
from app.models.icf_certification import ICFCertificationProgress
from app.schemas.coaching_session import (
    CoachingSessionCreate,
    CoachingSessionUpdate,
    CoachingSessionResponse,
    CoachingSessionListResponse,
    ICFSummary,
    ClientHoursSummary,
    BulkImportRequest,
    BulkImportResponse,
)
from app.schemas.icf_certification import (
    ICFCertificationProgressUpdate,
    ICFCertificationProgressResponse,
    ICFCertificationDashboard,
    ICFRequirements,
)

router = APIRouter(prefix="/api/icf-tracker", tags=["ICF Tracker"])


def session_to_response(session: CoachingSession) -> CoachingSessionResponse:
    """Convert coaching session model to response."""
    contact_name = None
    if session.contact:
        contact_name = f"{session.contact.first_name} {session.contact.last_name or ''}".strip()

    return CoachingSessionResponse(
        id=session.id,
        contact_id=session.contact_id,
        client_name=session.client_name,
        client_email=session.client_email,
        session_date=session.session_date,
        start_time=session.start_time,
        end_time=session.end_time,
        duration_hours=session.duration_hours,
        session_type=session.session_type,
        group_size=session.group_size,
        payment_type=session.payment_type,
        source=session.source,
        external_id=session.external_id,
        meeting_title=session.meeting_title,
        notes=session.notes,
        is_verified=session.is_verified,
        created_at=session.created_at,
        updated_at=session.updated_at,
        contact_name=contact_name,
    )


@router.get("/summary", response_model=ICFSummary)
async def get_icf_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get ICF hours summary statistics."""
    query = select(CoachingSession)

    if start_date:
        query = query.where(CoachingSession.session_date >= start_date)
    if end_date:
        query = query.where(CoachingSession.session_date <= end_date)

    result = await db.execute(query)
    sessions = result.scalars().all()

    total_hours = sum(s.duration_hours for s in sessions)
    paid_hours = sum(s.duration_hours for s in sessions if s.payment_type == "paid")
    pro_bono_hours = sum(s.duration_hours for s in sessions if s.payment_type == "pro_bono")
    individual_hours = sum(s.duration_hours for s in sessions if s.session_type == "individual")
    group_hours = sum(s.duration_hours for s in sessions if s.session_type == "group")
    verified_hours = sum(s.duration_hours for s in sessions if s.is_verified)
    unverified_hours = sum(s.duration_hours for s in sessions if not s.is_verified)

    # Count unique clients
    unique_clients = len(set(s.client_name.lower() for s in sessions))

    return ICFSummary(
        total_hours=round(total_hours, 2),
        paid_hours=round(paid_hours, 2),
        pro_bono_hours=round(pro_bono_hours, 2),
        individual_hours=round(individual_hours, 2),
        group_hours=round(group_hours, 2),
        total_sessions=len(sessions),
        total_clients=unique_clients,
        verified_hours=round(verified_hours, 2),
        unverified_hours=round(unverified_hours, 2),
    )


@router.get("/by-client", response_model=list[ClientHoursSummary])
async def get_hours_by_client(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get coaching hours summarized by client."""
    query = select(CoachingSession)

    if start_date:
        query = query.where(CoachingSession.session_date >= start_date)
    if end_date:
        query = query.where(CoachingSession.session_date <= end_date)

    query = query.order_by(CoachingSession.client_name, CoachingSession.session_date)
    result = await db.execute(query)
    sessions = result.scalars().all()

    # Group by client (case-insensitive)
    client_data = {}
    for s in sessions:
        key = s.client_name.lower()
        if key not in client_data:
            client_data[key] = {
                "client_name": s.client_name,
                "contact_id": s.contact_id,
                "sessions": [],
            }
        client_data[key]["sessions"].append(s)

    # Build summaries
    summaries = []
    for key, data in sorted(client_data.items(), key=lambda x: sum(s.duration_hours for s in x[1]["sessions"]), reverse=True):
        sessions_list = data["sessions"]
        summaries.append(ClientHoursSummary(
            client_name=data["client_name"],
            contact_id=data["contact_id"],
            total_sessions=len(sessions_list),
            total_hours=round(sum(s.duration_hours for s in sessions_list), 2),
            paid_hours=round(sum(s.duration_hours for s in sessions_list if s.payment_type == "paid"), 2),
            pro_bono_hours=round(sum(s.duration_hours for s in sessions_list if s.payment_type == "pro_bono"), 2),
            individual_hours=round(sum(s.duration_hours for s in sessions_list if s.session_type == "individual"), 2),
            group_hours=round(sum(s.duration_hours for s in sessions_list if s.session_type == "group"), 2),
            first_session=min(s.session_date for s in sessions_list),
            last_session=max(s.session_date for s in sessions_list),
        ))

    return summaries


@router.get("", response_model=CoachingSessionListResponse)
async def list_sessions(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    client_name: Optional[str] = None,
    contact_id: Optional[str] = None,
    session_type: Optional[str] = None,
    payment_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    is_verified: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List coaching sessions with filters."""
    query = select(CoachingSession).options(selectinload(CoachingSession.contact))
    count_query = select(func.count(CoachingSession.id))

    # Apply filters
    conditions = []
    if client_name:
        conditions.append(CoachingSession.client_name.ilike(f"%{client_name}%"))
    if contact_id:
        conditions.append(CoachingSession.contact_id == contact_id)
    if session_type:
        conditions.append(CoachingSession.session_type == session_type)
    if payment_type:
        conditions.append(CoachingSession.payment_type == payment_type)
    if start_date:
        conditions.append(CoachingSession.session_date >= start_date)
    if end_date:
        conditions.append(CoachingSession.session_date <= end_date)
    if is_verified is not None:
        conditions.append(CoachingSession.is_verified == is_verified)

    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))

    total = await db.scalar(count_query) or 0

    query = query.offset((page - 1) * size).limit(size).order_by(
        CoachingSession.session_date.desc()
    )
    result = await db.execute(query)
    sessions = result.scalars().all()

    return CoachingSessionListResponse(
        items=[session_to_response(s) for s in sessions],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{session_id}", response_model=CoachingSessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single coaching session."""
    result = await db.execute(
        select(CoachingSession)
        .options(selectinload(CoachingSession.contact))
        .where(CoachingSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    return session_to_response(session)


@router.post("", response_model=CoachingSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: CoachingSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new coaching session."""
    # Validate contact if provided
    if data.contact_id:
        contact_result = await db.execute(
            select(Contact).where(Contact.id == data.contact_id)
        )
        if not contact_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contact not found",
            )

    session = CoachingSession(
        contact_id=data.contact_id,
        client_name=data.client_name,
        client_email=data.client_email,
        session_date=data.session_date,
        start_time=data.start_time,
        end_time=data.end_time,
        duration_hours=data.duration_hours,
        session_type=data.session_type,
        group_size=data.group_size,
        payment_type=data.payment_type,
        source=data.source,
        external_id=data.external_id,
        meeting_title=data.meeting_title,
        notes=data.notes,
        is_verified=data.is_verified,
    )
    db.add(session)
    await db.commit()

    # Reload with relationships
    result = await db.execute(
        select(CoachingSession)
        .options(selectinload(CoachingSession.contact))
        .where(CoachingSession.id == session.id)
    )
    session = result.scalar_one()

    return session_to_response(session)


@router.put("/{session_id}", response_model=CoachingSessionResponse)
async def update_session(
    session_id: str,
    data: CoachingSessionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a coaching session."""
    result = await db.execute(
        select(CoachingSession)
        .options(selectinload(CoachingSession.contact))
        .where(CoachingSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    # Update fields
    update_fields = [
        "contact_id", "client_name", "client_email", "session_date",
        "start_time", "end_time", "duration_hours", "session_type",
        "group_size", "payment_type", "meeting_title", "notes", "is_verified"
    ]

    for field in update_fields:
        value = getattr(data, field, None)
        if value is not None:
            setattr(session, field, value)

    await db.commit()
    await db.refresh(session)

    return session_to_response(session)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a coaching session."""
    result = await db.execute(
        select(CoachingSession).where(CoachingSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    await db.delete(session)
    await db.commit()


@router.post("/bulk-import", response_model=BulkImportResponse)
async def bulk_import_sessions(
    data: BulkImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bulk import coaching sessions."""
    imported = 0
    skipped = 0
    errors = []

    for i, session_data in enumerate(data.sessions):
        try:
            # Check for duplicate (same client, date, duration)
            existing = await db.execute(
                select(CoachingSession).where(
                    and_(
                        func.lower(CoachingSession.client_name) == session_data.client_name.lower(),
                        CoachingSession.session_date == session_data.session_date,
                        CoachingSession.duration_hours == session_data.duration_hours,
                    )
                )
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue

            session = CoachingSession(
                contact_id=session_data.contact_id,
                client_name=session_data.client_name,
                client_email=session_data.client_email,
                session_date=session_data.session_date,
                start_time=session_data.start_time,
                end_time=session_data.end_time,
                duration_hours=session_data.duration_hours,
                session_type=session_data.session_type,
                group_size=session_data.group_size,
                payment_type=session_data.payment_type,
                source=session_data.source,
                external_id=session_data.external_id,
                meeting_title=session_data.meeting_title,
                notes=session_data.notes,
                is_verified=session_data.is_verified,
            )
            db.add(session)
            imported += 1
        except Exception as e:
            errors.append(f"Row {i + 1}: {str(e)}")

    await db.commit()

    return BulkImportResponse(
        imported=imported,
        skipped=skipped,
        errors=errors,
    )


@router.post("/verify-all")
async def verify_all_sessions(
    client_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark all sessions (optionally filtered by client) as verified."""
    query = select(CoachingSession).where(CoachingSession.is_verified == False)

    if client_name:
        query = query.where(CoachingSession.client_name.ilike(f"%{client_name}%"))

    result = await db.execute(query)
    sessions = result.scalars().all()

    for session in sessions:
        session.is_verified = True

    await db.commit()

    return {"verified": len(sessions)}


@router.get("/export/csv")
async def export_csv(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export coaching sessions as CSV in ICF format."""
    query = select(CoachingSession).order_by(
        CoachingSession.client_name,
        CoachingSession.session_date,
    )

    if start_date:
        query = query.where(CoachingSession.session_date >= start_date)
    if end_date:
        query = query.where(CoachingSession.session_date <= end_date)

    result = await db.execute(query)
    sessions = result.scalars().all()

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "#", "Client Name", "Contact Information", "Individual/Group",
        "Number in Group", "Start Date", "Duration of coaching call",
        "End Date", "Paid hours", "Pro-bono hours"
    ])

    # Group sessions by client
    client_sessions = {}
    for s in sessions:
        key = s.client_name.lower()
        if key not in client_sessions:
            client_sessions[key] = {
                "name": s.client_name,
                "email": s.client_email or "",
                "sessions": [],
            }
        client_sessions[key]["sessions"].append(s)

    client_num = 0
    for key in sorted(client_sessions.keys()):
        data = client_sessions[key]
        client_num += 1
        sessions_list = sorted(data["sessions"], key=lambda x: x.session_date)

        total_hours = sum(s.duration_hours for s in sessions_list)
        first_date = min(s.session_date for s in sessions_list)
        last_date = max(s.session_date for s in sessions_list)
        is_group = sessions_list[0].session_type == "group"
        paid_total = sum(s.duration_hours for s in sessions_list if s.payment_type == "paid")
        probono_total = sum(s.duration_hours for s in sessions_list if s.payment_type == "pro_bono")

        # Client header row
        writer.writerow([
            client_num,
            data["name"],
            data["email"],
            "Group" if is_group else "Individual",
            sessions_list[0].group_size if is_group else "",
            first_date.isoformat(),
            total_hours,
            last_date.isoformat(),
            paid_total,
            probono_total,
        ])

        # Individual session rows
        for s in sessions_list:
            paid = s.duration_hours if s.payment_type == "paid" else ""
            probono = s.duration_hours if s.payment_type == "pro_bono" else ""
            writer.writerow([
                "",
                "",
                "",
                "",
                "",
                s.session_date.isoformat(),
                s.duration_hours,
                "",
                paid,
                probono,
            ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=icf_coaching_log.csv"},
    )


@router.post("/match-contacts")
async def match_contacts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Auto-match unlinked sessions to contacts by name."""
    # Get sessions without contact_id
    sessions_result = await db.execute(
        select(CoachingSession).where(CoachingSession.contact_id == None)
    )
    sessions = sessions_result.scalars().all()

    # Get all contacts
    contacts_result = await db.execute(select(Contact))
    contacts = contacts_result.scalars().all()

    # Build contact name lookup
    contact_lookup = {}
    for c in contacts:
        full_name = f"{c.first_name} {c.last_name or ''}".strip().lower()
        contact_lookup[full_name] = c.id
        # Also add first name only
        contact_lookup[c.first_name.lower()] = c.id

    matched = 0
    for session in sessions:
        client_lower = session.client_name.lower()
        if client_lower in contact_lookup:
            session.contact_id = contact_lookup[client_lower]
            matched += 1

    await db.commit()

    return {"matched": matched, "total_unlinked": len(sessions)}


# ============ ICF Certification Progress Endpoints ============


@router.get("/certification/dashboard", response_model=ICFCertificationDashboard)
async def get_certification_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full ICF certification dashboard with progress toward ACC and PCC."""
    # Get coaching stats
    result = await db.execute(select(CoachingSession))
    sessions = result.scalars().all()

    total_hours = sum(s.duration_hours for s in sessions)
    paid_hours = sum(s.duration_hours for s in sessions if s.payment_type == "paid")
    pro_bono_hours = sum(s.duration_hours for s in sessions if s.payment_type == "pro_bono")
    total_clients = len(set(s.client_name.lower() for s in sessions))

    # Get certification progress record (create if doesn't exist)
    progress_result = await db.execute(select(ICFCertificationProgress))
    progress = progress_result.scalar_one_or_none()

    if not progress:
        progress = ICFCertificationProgress()
        db.add(progress)
        await db.commit()
        await db.refresh(progress)

    # Define requirements
    requirements = ICFRequirements()

    # Calculate ACC progress percentages
    acc_training_pct = min(100, (progress.acc_training_hours / requirements.acc_training_required) * 100)
    acc_coaching_pct = min(100, (total_hours / requirements.acc_coaching_hours_required) * 100)
    acc_paid_pct = min(100, (paid_hours / requirements.acc_paid_hours_required) * 100)
    acc_clients_pct = min(100, (total_clients / requirements.acc_clients_required) * 100)
    acc_mentor_pct = min(100, (progress.acc_mentor_hours / requirements.acc_mentor_hours_required) * 100)

    acc_ready = (
        progress.acc_training_hours >= requirements.acc_training_required and
        total_hours >= requirements.acc_coaching_hours_required and
        paid_hours >= requirements.acc_paid_hours_required and
        total_clients >= requirements.acc_clients_required and
        progress.acc_mentor_hours >= requirements.acc_mentor_hours_required and
        progress.acc_exam_passed
    )

    # Calculate PCC progress percentages
    total_training = progress.acc_training_hours + progress.pcc_training_hours
    pcc_training_pct = min(100, (total_training / requirements.pcc_training_required) * 100)
    pcc_coaching_pct = min(100, (total_hours / requirements.pcc_coaching_hours_required) * 100)
    pcc_paid_pct = min(100, (paid_hours / requirements.pcc_paid_hours_required) * 100)
    pcc_clients_pct = min(100, (total_clients / requirements.pcc_clients_required) * 100)
    pcc_mentor_pct = min(100, (progress.pcc_mentor_hours / requirements.pcc_mentor_hours_required) * 100)

    pcc_ready = (
        total_training >= requirements.pcc_training_required and
        total_hours >= requirements.pcc_coaching_hours_required and
        paid_hours >= requirements.pcc_paid_hours_required and
        total_clients >= requirements.pcc_clients_required and
        progress.pcc_mentor_hours >= requirements.pcc_mentor_hours_required and
        progress.pcc_exam_passed
    )

    # Calculate MCC progress percentages
    total_all_training = progress.acc_training_hours + progress.pcc_training_hours + (progress.mcc_training_hours or 0)
    mcc_training_pct = min(100, (total_all_training / requirements.mcc_training_required) * 100)
    mcc_coaching_pct = min(100, (total_hours / requirements.mcc_coaching_hours_required) * 100)
    mcc_paid_pct = min(100, (paid_hours / requirements.mcc_paid_hours_required) * 100)
    mcc_clients_pct = min(100, (total_clients / requirements.mcc_clients_required) * 100)
    mcc_mentor_pct = min(100, ((progress.mcc_mentor_hours or 0) / requirements.mcc_mentor_hours_required) * 100)

    mcc_ready = (
        total_all_training >= requirements.mcc_training_required and
        total_hours >= requirements.mcc_coaching_hours_required and
        paid_hours >= requirements.mcc_paid_hours_required and
        total_clients >= requirements.mcc_clients_required and
        (progress.mcc_mentor_hours or 0) >= requirements.mcc_mentor_hours_required and
        (progress.mcc_exam_passed or False)
    )

    return ICFCertificationDashboard(
        total_coaching_hours=round(total_hours, 2),
        paid_coaching_hours=round(paid_hours, 2),
        pro_bono_hours=round(pro_bono_hours, 2),
        total_clients=total_clients,
        requirements=requirements,
        acc_training_progress=round(acc_training_pct, 1),
        acc_coaching_progress=round(acc_coaching_pct, 1),
        acc_paid_progress=round(acc_paid_pct, 1),
        acc_clients_progress=round(acc_clients_pct, 1),
        acc_mentor_progress=round(acc_mentor_pct, 1),
        acc_ready=acc_ready,
        pcc_training_progress=round(pcc_training_pct, 1),
        pcc_coaching_progress=round(pcc_coaching_pct, 1),
        pcc_paid_progress=round(pcc_paid_pct, 1),
        pcc_clients_progress=round(pcc_clients_pct, 1),
        pcc_mentor_progress=round(pcc_mentor_pct, 1),
        pcc_ready=pcc_ready,
        mcc_training_progress=round(mcc_training_pct, 1),
        mcc_coaching_progress=round(mcc_coaching_pct, 1),
        mcc_paid_progress=round(mcc_paid_pct, 1),
        mcc_clients_progress=round(mcc_clients_pct, 1),
        mcc_mentor_progress=round(mcc_mentor_pct, 1),
        mcc_ready=mcc_ready,
        progress=ICFCertificationProgressResponse(
            id=progress.id,
            acc_training_hours=progress.acc_training_hours or 0,
            acc_training_provider=progress.acc_training_provider,
            acc_training_completed=progress.acc_training_completed or False,
            acc_training_completion_date=progress.acc_training_completion_date,
            acc_training_certificate_url=progress.acc_training_certificate_url,
            pcc_training_hours=progress.pcc_training_hours or 0,
            pcc_training_provider=progress.pcc_training_provider,
            pcc_training_completed=progress.pcc_training_completed or False,
            pcc_training_completion_date=progress.pcc_training_completion_date,
            pcc_training_certificate_url=progress.pcc_training_certificate_url,
            acc_mentor_hours=progress.acc_mentor_hours or 0,
            acc_mentor_individual_hours=progress.acc_mentor_individual_hours or 0,
            acc_mentor_group_hours=progress.acc_mentor_group_hours or 0,
            acc_mentor_name=progress.acc_mentor_name,
            acc_mentor_credential=progress.acc_mentor_credential,
            acc_mentor_completed=progress.acc_mentor_completed or False,
            pcc_mentor_hours=progress.pcc_mentor_hours or 0,
            pcc_mentor_individual_hours=progress.pcc_mentor_individual_hours or 0,
            pcc_mentor_group_hours=progress.pcc_mentor_group_hours or 0,
            pcc_mentor_name=progress.pcc_mentor_name,
            pcc_mentor_credential=progress.pcc_mentor_credential,
            pcc_mentor_completed=progress.pcc_mentor_completed or False,
            acc_exam_passed=progress.acc_exam_passed or False,
            acc_exam_date=progress.acc_exam_date,
            acc_exam_score=progress.acc_exam_score,
            pcc_exam_passed=progress.pcc_exam_passed or False,
            pcc_exam_date=progress.pcc_exam_date,
            pcc_exam_score=progress.pcc_exam_score,
            acc_applied=progress.acc_applied or False,
            acc_application_date=progress.acc_application_date,
            acc_credential_received=progress.acc_credential_received or False,
            acc_credential_date=progress.acc_credential_date,
            acc_credential_number=progress.acc_credential_number,
            acc_expiration_date=progress.acc_expiration_date,
            pcc_applied=progress.pcc_applied or False,
            pcc_application_date=progress.pcc_application_date,
            pcc_credential_received=progress.pcc_credential_received or False,
            pcc_credential_date=progress.pcc_credential_date,
            pcc_credential_number=progress.pcc_credential_number,
            pcc_expiration_date=progress.pcc_expiration_date,
            mcc_training_hours=progress.mcc_training_hours or 0,
            mcc_training_provider=progress.mcc_training_provider,
            mcc_training_completed=progress.mcc_training_completed or False,
            mcc_training_completion_date=progress.mcc_training_completion_date,
            mcc_training_certificate_url=progress.mcc_training_certificate_url,
            mcc_mentor_hours=progress.mcc_mentor_hours or 0,
            mcc_mentor_individual_hours=progress.mcc_mentor_individual_hours or 0,
            mcc_mentor_group_hours=progress.mcc_mentor_group_hours or 0,
            mcc_mentor_name=progress.mcc_mentor_name,
            mcc_mentor_completed=progress.mcc_mentor_completed or False,
            mcc_exam_passed=progress.mcc_exam_passed or False,
            mcc_exam_date=progress.mcc_exam_date,
            mcc_exam_score=progress.mcc_exam_score,
            mcc_applied=progress.mcc_applied or False,
            mcc_application_date=progress.mcc_application_date,
            mcc_credential_received=progress.mcc_credential_received or False,
            mcc_credential_date=progress.mcc_credential_date,
            mcc_credential_number=progress.mcc_credential_number,
            mcc_expiration_date=progress.mcc_expiration_date,
            notes=progress.notes,
            created_at=progress.created_at,
            updated_at=progress.updated_at,
        ),
    )


@router.get("/certification/progress", response_model=ICFCertificationProgressResponse)
async def get_certification_progress(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get certification progress record."""
    result = await db.execute(select(ICFCertificationProgress))
    progress = result.scalar_one_or_none()

    if not progress:
        progress = ICFCertificationProgress()
        db.add(progress)
        await db.commit()
        await db.refresh(progress)

    return progress


@router.put("/certification/progress", response_model=ICFCertificationProgressResponse)
async def update_certification_progress(
    data: ICFCertificationProgressUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update certification progress."""
    result = await db.execute(select(ICFCertificationProgress))
    progress = result.scalar_one_or_none()

    if not progress:
        progress = ICFCertificationProgress()
        db.add(progress)

    # Update all fields from the request
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(progress, field, value)

    await db.commit()
    await db.refresh(progress)

    return progress
