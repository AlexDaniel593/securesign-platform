from datetime import datetime
from typing import Optional, Literal

from fastapi import APIRouter, Body, Depends, File, Query, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import User
from app.dependencies.auth import get_current_user
from app.services import document_service

router = APIRouter()

# ---------------------------------------------------------------------------
# Schemas (inline, following certificates.py and crypto.py convention)
# ---------------------------------------------------------------------------


class UploadResponse(BaseModel):
    id: int
    filename: str
    sha256_hash: str
    file_size: int
    uploaded_at: datetime


class DocumentItem(BaseModel):
    id: int
    filename: str
    file_size: int
    sha256_hash: str
    uploaded_at: datetime
    signature_count: int = 0


class DocumentListResponse(BaseModel):
    items: list[DocumentItem]
    total: int
    page: int
    limit: int


class MessageResponse(BaseModel):
    message: str


class VerifyFileSignatureItem(BaseModel):
    id: int
    signed_at: datetime
    is_valid: bool
    verified_at: datetime
    signer_name: str
    signer_email: str
    certificate_status: Literal["valid", "revoked", "expired", "not_found"]


class VerifyFileResponse(BaseModel):
    sha256_hash: str
    signatures: list[VerifyFileSignatureItem]


# ---------------------------------------------------------------------------
# Schemas — PR #2 (mutating + sign + signatures)
# ---------------------------------------------------------------------------


class RenameRequest(BaseModel):
    filename: str = Field(..., min_length=1)


class RenameResponse(BaseModel):
    id: int
    filename: str


class SignRequest(BaseModel):
    certificate_id: Optional[int] = None


class SignResponse(BaseModel):
    signature_id: int
    signature: str
    signed_at: datetime
    certificate_id: Optional[int] = None


class SignatureItem(BaseModel):
    id: int
    certificate_id: Optional[int] = None
    signature_blob: str
    signed_at: datetime
    is_valid: Optional[bool] = None
    verified_at: Optional[datetime] = None
    signer_name: str = ""
    signer_email: str = ""


class SignaturesResponse(BaseModel):
    signatures: list[SignatureItem]


class VerificationResult(BaseModel):
    is_valid: bool
    verified_at: datetime
    signer_name: str
    signer_email: str
    certificate_status: Literal["valid", "revoked", "expired", "not_found"]


# ---------------------------------------------------------------------------
# Endpoints — PR #1 scope
# ---------------------------------------------------------------------------


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doc = await document_service.upload_document(db, current_user.id, file)
    return UploadResponse(
        id=doc.id,
        filename=doc.filename,
        sha256_hash=doc.sha256_hash,
        file_size=doc.file_size,
        uploaded_at=doc.uploaded_at,
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await document_service.list_documents(db, current_user.id, page, limit)
    return DocumentListResponse(
        items=[DocumentItem(**doc) for doc in items],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{doc_id}", response_model=DocumentItem)
async def get_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doc = await document_service.get_document(db, current_user.id, doc_id)

    # Compute signature_count for this document across all copies
    from sqlmodel import select, func
    from app.db.models import Signature

    count_result = await db.execute(
        select(func.count()).select_from(Signature).where(
            Signature.sha256_hash == doc.sha256_hash
        )
    )
    sig_count = count_result.scalar() or 0

    return DocumentItem(
        id=doc.id,
        filename=doc.filename,
        file_size=doc.file_size,
        sha256_hash=doc.sha256_hash,
        uploaded_at=doc.uploaded_at,
        signature_count=sig_count,
    )


@router.get("/{doc_id}/download")
async def download_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content, filename, sha256_hash = await document_service.get_document_bytes(
        db, current_user.id, doc_id
    )

    from sqlmodel import select, func
    from app.db.models import Signature

    sig_result = await db.execute(
        select(func.count()).select_from(Signature).where(
            Signature.sha256_hash == sha256_hash
        )
    )
    sig_count = sig_result.scalar() or 0

    if sig_count > 0:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "pdf")
        filename = f"{name}-signed.{ext}"

    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# Endpoints — PR #2 (mutating + sign + signatures)
# ---------------------------------------------------------------------------


@router.delete("/{doc_id}", response_model=MessageResponse)
async def delete_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await document_service.delete_document(db, current_user.id, doc_id)
    return MessageResponse(message="Document deleted successfully")


@router.put("/{doc_id}", response_model=RenameResponse)
async def rename_document(
    doc_id: int,
    body: RenameRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doc = await document_service.rename_document(db, current_user.id, doc_id, body.filename)
    return RenameResponse(id=doc.id, filename=doc.filename)


@router.post("/{doc_id}/sign", response_model=SignResponse, status_code=status.HTTP_201_CREATED)
async def sign_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    body: SignRequest = Body(default_factory=SignRequest),
):
    sig = await document_service.sign_document(
        db, current_user.id, doc_id, body.certificate_id
    )
    return SignResponse(
        signature_id=sig.id,
        signature=sig.signature_blob,
        signed_at=sig.signed_at,
        certificate_id=sig.certificate_id,
    )


@router.get("/{doc_id}/signatures", response_model=SignaturesResponse)
async def list_signatures(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sigs = await document_service.list_signatures(db, current_user.id, doc_id)

    # Fetch signer names/emails (user table) for each signature
    from sqlmodel import select
    from app.db.models import User as UserModel

    user_ids = {s.user_id for s in sigs}
    signer_map: dict[int, tuple[str, str]] = {}
    if user_ids:
        result = await db.execute(
            select(UserModel.id, UserModel.name, UserModel.email).where(
                UserModel.id.in_(user_ids)
            )
        )
        for row in result.all():
            signer_map[row[0]] = (row[1], row[2])

    return SignaturesResponse(
        signatures=[
            SignatureItem(
                id=s.id,
                certificate_id=s.certificate_id,
                signature_blob=s.signature_blob,
                signed_at=s.signed_at,
                is_valid=s.is_valid,
                verified_at=s.verified_at,
                signer_name=signer_map.get(s.user_id, ("Unknown", ""))[0],
                signer_email=signer_map.get(s.user_id, ("", "unknown@unknown"))[1],
            )
            for s in sigs
        ]
    )


@router.post("/{doc_id}/verify/{sig_id}", response_model=VerificationResult)
async def verify_signature(
    doc_id: int,
    sig_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify a document signature — RSA check + certificate validity.

    Returns VerificationResult with is_valid, verified_at, signer identity
    and certificate_status. Persists verified_at + is_valid on the Signature row.
    """
    result = await document_service.verify_document_signature(
        db, current_user.id, doc_id, sig_id
    )
    return VerificationResult(**result)


@router.post("/verify-file", response_model=VerifyFileResponse)
async def verify_uploaded_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a PDF, compute its hash, look up signatures by hash, and verify each.

    Read-only — nothing is persisted (no Document row, no Signature mutation).
    """
    content = await file.read()
    sha256_hash = document_service.hash_content(content)
    sigs = await document_service.verify_document_by_hash(db, sha256_hash)
    return VerifyFileResponse(sha256_hash=sha256_hash, signatures=sigs)
