from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.db.database import get_db
from app.db.models import User
from app.dependencies.auth import get_current_admin_user

router = APIRouter()


class UserItem(BaseModel):
    id: int
    name: str
    email: str
    is_admin: bool
    is_active: bool
    created_at: datetime


class UserListResponse(BaseModel):
    items: list[UserItem]
    total: int
    page: int
    limit: int


class MessageResponse(BaseModel):
    message: str


@router.get("", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * limit

    count_result = await db.execute(select(func.count()).select_from(User))
    total = count_result.scalar() or 0

    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(offset).limit(limit)
    )
    users = list(result.scalars().all())

    return UserListResponse(
        items=[
            UserItem(
                id=u.id,
                name=u.name,
                email=u.email,
                is_admin=u.is_admin,
                is_active=u.is_active,
                created_at=u.created_at,
            )
            for u in users
        ],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{user_id}", response_model=UserItem)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserItem(
        id=user.id,
        name=user.name,
        email=user.email,
        is_admin=user.is_admin,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminar tu propia cuenta",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    await db.delete(user)
    await db.commit()
    return MessageResponse(message="Usuario eliminado correctamente")
