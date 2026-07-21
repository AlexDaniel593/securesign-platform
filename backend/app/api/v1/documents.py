from datetime import datetime
from typing import Optional

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


class DocumentListResponse(BaseModel):
    items: list[DocumentItem]
    total: int
    page: int
    limit: int


class MessageResponse(BaseModel):
    message: str


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


class SignaturesResponse(BaseModel):
    signatures: list[SignatureItem]


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
        items=[
            DocumentItem(
                id=doc.id,
                filename=doc.filename,
                file_size=doc.file_size,
                sha256_hash=doc.sha256_hash,
                uploaded_at=doc.uploaded_at,
            )
            for doc in items
        ],
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
    return DocumentItem(
        id=doc.id,
        filename=doc.filename,
        file_size=doc.file_size,
        sha256_hash=doc.sha256_hash,
        uploaded_at=doc.uploaded_at,
    )


@router.get("/{doc_id}/download")
async def download_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content, filename = await document_service.get_document_bytes(db, current_user.id, doc_id)
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
    return SignaturesResponse(
        signatures=[
            SignatureItem(
                id=s.id,
                certificate_id=s.certificate_id,
                signature_blob=s.signature_blob,
                signed_at=s.signed_at,
                is_valid=s.is_valid,
            )
            for s in sigs
        ]
    )
