"""Business logic for document CRUD and file orchestration.

Module-level constant UPLOAD_DIR is monkeypatched by tests to tmp_path.
"""

from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.core.crypto import hash_sha256
from app.db.models import Document, Signature
from app.services import crypto_service
from app.utils import file_handlers

UPLOAD_DIR: Path = Path(".")
MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB


async def upload_document(
    db: AsyncSession, user_id: int, file: UploadFile
) -> Document:
    """Validate, persist, and store a document upload. Creates a new DB row every time (no dedup)."""
    _validate_upload(file)

    content = await file.read()
    file_size = len(content)

    if file_size > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="File exceeds maximum upload size of 10 MB.",
        )

    sha256 = hash_sha256(content)
    file_path = file_handlers.save_file(
        UPLOAD_DIR, user_id, file.filename or "unnamed", content
    )

    document = Document(
        user_id=user_id,
        filename=file.filename or "unnamed",
        file_path=file_path,
        file_size=file_size,
        sha256_hash=sha256,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return document


async def list_documents(
    db: AsyncSession, user_id: int, page: int = 1, limit: int = 20
) -> tuple[list[Document], int]:
    """Return a page of documents owned by *user_id* and the total count."""
    base_query = select(Document).where(Document.user_id == user_id)
    count_query = select(func.count()).select_from(Document).where(Document.user_id == user_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * limit
    result = await db.execute(
        base_query.order_by(Document.uploaded_at.desc()).offset(offset).limit(limit)
    )
    documents = result.scalars().all()
    return list(documents), total


async def get_document(db: AsyncSession, user_id: int, doc_id: int) -> Document:
    """Fetch a single document owned by *user_id*. Raises 404 on ownership mismatch or missing."""
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.user_id == user_id)
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return doc


async def get_document_bytes(
    db: AsyncSession, user_id: int, doc_id: int
) -> tuple[bytes, str]:
    """Return the raw file bytes and filename for a document owned by *user_id*."""
    doc = await get_document(db, user_id, doc_id)
    try:
        content = file_handlers.read_file(doc.file_path)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file not found on disk",
        )
    return content, doc.filename


# ---------------------------------------------------------------------------
# Mutating / Sign operations — PR #2
# ---------------------------------------------------------------------------


async def delete_document(db: AsyncSession, user_id: int, doc_id: int) -> None:
    """Delete a document owned by *user_id*. Removes DB row and disk file."""
    doc = await get_document(db, user_id, doc_id)
    file_handlers.delete_file(doc.file_path)
    await db.delete(doc)
    await db.commit()


async def rename_document(
    db: AsyncSession, user_id: int, doc_id: int, new_filename: str
) -> Document:
    """Rename a document owned by *user_id*. Returns updated Document."""
    doc = await get_document(db, user_id, doc_id)
    doc.filename = new_filename
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


async def sign_document(
    db: AsyncSession,
    user_id: int,
    doc_id: int,
    certificate_id: Optional[int] = None,
) -> Signature:
    """Sign a document's SHA-256 hash using the user's RSA key.

    Raises 400 if the user has no key pair.
    Persists a Signature row with the base64-encoded signature blob.
    """
    doc = await get_document(db, user_id, doc_id)

    try:
        result = await crypto_service.sign_hash(db, user_id, doc.sha256_hash)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    signature = Signature(
        document_id=doc.id,
        user_id=user_id,
        certificate_id=certificate_id,
        signature_blob=result["signature"],
    )
    db.add(signature)
    await db.commit()
    await db.refresh(signature)
    return signature


async def list_signatures(
    db: AsyncSession, user_id: int, doc_id: int
) -> list[Signature]:
    """List all signatures for a document owned by *user_id*."""
    await get_document(db, user_id, doc_id)  # ownership check
    result = await db.execute(
        select(Signature).where(
            Signature.document_id == doc_id,
            Signature.user_id == user_id,
        ).order_by(Signature.signed_at.desc())
    )
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _validate_upload(file: UploadFile) -> None:
    """Raise 400 if the uploaded file is not a PDF."""
    filename = (file.filename or "").lower()
    if not filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted. Upload a file with .pdf extension.",
        )
