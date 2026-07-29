from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.db.database import get_db
from app.db.models import AuditLog, User
from app.dependencies.auth import get_current_admin_user, get_current_user

router = APIRouter()


class AuditLogItem(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Optional[str] = None
    created_at: datetime


class AuditLogsResponse(BaseModel):
    items: list[AuditLogItem]
    total: int
    page: int
    limit: int


class AuditMetricsResponse(BaseModel):
    total_users: int
    total_documents: int
    total_signatures: int
    failed_logins: int


@router.get("/logs", response_model=AuditLogsResponse)
async def list_own_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * limit

    count_result = await db.execute(
        select(func.count()).select_from(AuditLog).where(
            AuditLog.user_id == current_user.id
        )
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.user_id == current_user.id)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    logs = list(result.scalars().all())

    return AuditLogsResponse(
        items=[
            AuditLogItem(
                id=log.id,
                user_id=log.user_id,
                user_email=current_user.email,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                details=log.details,
                created_at=log.created_at,
            )
            for log in logs
        ],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/logs/all", response_model=AuditLogsResponse)
async def list_all_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * limit

    count_result = await db.execute(select(func.count()).select_from(AuditLog))
    total = count_result.scalar() or 0

    result = await db.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
    )
    logs = list(result.scalars().all())

    user_ids = {log.user_id for log in logs if log.user_id is not None}
    user_map: dict[int, str] = {}
    if user_ids:
        user_result = await db.execute(
            select(User.id, User.email).where(User.id.in_(user_ids))
        )
        for row in user_result.all():
            user_map[row[0]] = row[1]

    return AuditLogsResponse(
        items=[
            AuditLogItem(
                id=log.id,
                user_id=log.user_id,
                user_email=user_map.get(log.user_id) if log.user_id else None,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                details=log.details,
                created_at=log.created_at,
            )
            for log in logs
        ],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/metrics", response_model=AuditMetricsResponse)
async def get_metrics(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    from app.db.models import Document, Signature

    users_result = await db.execute(select(func.count()).select_from(User))
    total_users = users_result.scalar() or 0

    docs_result = await db.execute(select(func.count()).select_from(Document))
    total_documents = docs_result.scalar() or 0

    sigs_result = await db.execute(select(func.count()).select_from(Signature))
    total_signatures = sigs_result.scalar() or 0

    failed_result = await db.execute(
        select(func.count()).select_from(AuditLog).where(
            AuditLog.action == "LOGIN_FAILED"
        )
    )
    failed_logins = failed_result.scalar() or 0

    return AuditMetricsResponse(
        total_users=total_users,
        total_documents=total_documents,
        total_signatures=total_signatures,
        failed_logins=failed_logins,
    )
