from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func

from app.core.ca import issue_certificate as ca_issue, verify_certificate_pem
from app.db.database import get_db
from app.db.models import Certificate, UserKey
from app.dependencies.auth import get_current_user

router = APIRouter()

# ---------- Request / Response Schemas ----------

class IssueRequest(BaseModel):
    subject_name: str
    validity_days: Optional[int] = 365


class IssueResponse(BaseModel):
    id: int
    subject: str
    issuer: str
    valid_from: datetime
    valid_to: datetime
    fingerprint: str


class CertificateItem(BaseModel):
    id: int
    subject: str
    issuer: str
    serial_number: str
    valid_from: datetime
    valid_to: datetime
    revoked: bool
    created_at: datetime


class CertificateListResponse(BaseModel):
    items: list[CertificateItem]
    total: int


class CertificateDetailResponse(BaseModel):
    id: int
    subject: str
    public_key: str
    issuer: str
    valid_from: datetime
    valid_to: datetime
    revoked: bool


class RevokeRequest(BaseModel):
    reason: Optional[str] = None


class RevokeResponse(BaseModel):
    message: str
    revoked_at: datetime


class VerifyRequest(BaseModel):
    certificate_pem: str
    document_hash: Optional[str] = None
    signature: Optional[str] = None


class VerifyResponse(BaseModel):
    valid: bool
    reason: str
    expires_in_days: Optional[int] = None


class CheckResponse(BaseModel):
    valid: bool
    status: str


class MessageResponse(BaseModel):
    message: str


# ---------- Endpoints ----------

@router.post("/issue", response_model=IssueResponse, status_code=status.HTTP_201_CREATED)
async def issue(
    body: IssueRequest,
    current_user: "User" = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserKey).where(UserKey.user_id == current_user.id).order_by(UserKey.created_at.desc())
    )
    user_key = result.scalar_one_or_none()
    if user_key is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must generate a key pair before issuing a certificate. Use POST /crypto/keys/generate",
        )

    cert_data = ca_issue(
        subject_name=body.subject_name,
        public_key_pem=user_key.public_key,
        validity_days=body.validity_days or 365,
    )

    certificate = Certificate(
        user_id=current_user.id,
        subject_name=cert_data["subject"],
        public_key=user_key.public_key,
        issuer=cert_data["issuer"],
        serial_number=cert_data["serial_number"],
        valid_from=cert_data["valid_from"],
        valid_to=cert_data["valid_to"],
    )
    db.add(certificate)
    await db.commit()
    await db.refresh(certificate)

    return IssueResponse(
        id=certificate.id,
        subject=certificate.subject_name,
        issuer=certificate.issuer,
        valid_from=certificate.valid_from,
        valid_to=certificate.valid_to,
        fingerprint=cert_data["fingerprint"],
    )


@router.get("", response_model=CertificateListResponse)
async def list_certificates(
    revoked: Optional[bool] = Query(None),
    current_user: "User" = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Certificate).where(Certificate.user_id == current_user.id)
    count_query = select(func.count()).select_from(Certificate).where(Certificate.user_id == current_user.id)

    if revoked is not None:
        query = query.where(Certificate.revoked == revoked)
        count_query = count_query.where(Certificate.revoked == revoked)

    query = query.order_by(Certificate.created_at.desc())

    result = await db.execute(query)
    certs = result.scalars().all()

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    return CertificateListResponse(
        items=[
            CertificateItem(
                id=c.id,
                subject=c.subject_name,
                issuer=c.issuer,
                serial_number=c.serial_number,
                valid_from=c.valid_from,
                valid_to=c.valid_to,
                revoked=c.revoked,
                created_at=c.created_at,
            )
            for c in certs
        ],
        total=total or 0,
    )


@router.get("/{cert_id}", response_model=CertificateDetailResponse)
async def get_certificate(
    cert_id: int,
    current_user: "User" = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Certificate).where(Certificate.id == cert_id, Certificate.user_id == current_user.id)
    )
    cert = result.scalar_one_or_none()
    if cert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found",
        )

    return CertificateDetailResponse(
        id=cert.id,
        subject=cert.subject_name,
        public_key=cert.public_key,
        issuer=cert.issuer,
        valid_from=cert.valid_from,
        valid_to=cert.valid_to,
        revoked=cert.revoked,
    )


@router.post("/{cert_id}/revoke", response_model=RevokeResponse)
async def revoke_certificate(
    cert_id: int,
    body: RevokeRequest,
    current_user: "User" = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Certificate).where(Certificate.id == cert_id, Certificate.user_id == current_user.id)
    )
    cert = result.scalar_one_or_none()
    if cert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found",
        )

    if cert.revoked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Certificate is already revoked",
        )

    now = datetime.now(timezone.utc)
    cert.revoked = True
    cert.revoked_at = now
    cert.revocation_reason = body.reason
    db.add(cert)
    await db.commit()

    return RevokeResponse(
        message="Certificate revoked successfully",
        revoked_at=now,
    )


@router.post("/verify", response_model=VerifyResponse)
async def verify(
    body: VerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    result = verify_certificate_pem(body.certificate_pem)
    if not result["valid"]:
        return VerifyResponse(valid=False, reason=result["reason"], expires_in_days=None)

    return VerifyResponse(
        valid=True,
        reason="Certificate is valid",
        expires_in_days=result.get("expires_in_days"),
    )


@router.get("/check/{cert_id}", response_model=CheckResponse)
async def check_certificate(
    cert_id: int,
    current_user: "User" = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Certificate).where(Certificate.id == cert_id, Certificate.user_id == current_user.id)
    )
    cert = result.scalar_one_or_none()
    if cert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found",
        )

    now = datetime.now(timezone.utc)

    if cert.revoked:
        return CheckResponse(valid=False, status="revoked")

    if now < cert.valid_from:
        return CheckResponse(valid=False, status="not_yet_valid")

    if now > cert.valid_to:
        return CheckResponse(valid=False, status="expired")

    return CheckResponse(valid=True, status="active")
