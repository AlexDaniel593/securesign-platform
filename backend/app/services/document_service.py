"""Business logic for document CRUD and S3 object orchestration.

Storage operations are delegated to app.core.storage (async boto3 S3 client).
Ownership enforcement, validation, and signing remain application-layer concerns.
"""

from typing import Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.core import storage
from app.core.crypto import hash_sha256
from app.core.time_utils import utc_now
from app.db.models import Document, Signature, Certificate, User
from app.services import crypto_service

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
    object_key = await storage.upload_object(
        user_id, file.filename or "unnamed", content
    )

    document = Document(
        user_id=user_id,
        filename=file.filename or "unnamed",
        object_key=object_key,
        file_size=file_size,
        sha256_hash=sha256,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return document


async def list_documents(
    db: AsyncSession, user_id: int, page: int = 1, limit: int = 20
) -> tuple[list[dict], int]:
    """Return a page of documents owned by *user_id* and the total count.

    Each document dict includes a ``signature_count`` integer computed via a
    scalar subquery on ``signatures.sha256_hash`` — no N+1, no eager load.
    Replaces the previous ``is_signed`` EXISTS subquery keyed on document_id.
    """
    sig_count = (
        select(func.count())
        .select_from(Signature)
        .where(Signature.sha256_hash == Document.sha256_hash)
        .correlate(Document)
        .scalar_subquery()
        .label("signature_count")
    )

    base_query = (
        select(Document, sig_count)
        .where(Document.user_id == user_id)
    )
    count_query = select(func.count()).select_from(Document).where(Document.user_id == user_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * limit
    result = await db.execute(
        base_query.order_by(Document.uploaded_at.desc()).offset(offset).limit(limit)
    )
    rows = result.all()

    documents = []
    for doc, signature_count in rows:
        doc_dict = {
            "id": doc.id,
            "filename": doc.filename,
            "file_size": doc.file_size,
            "sha256_hash": doc.sha256_hash,
            "uploaded_at": doc.uploaded_at,
            "signature_count": signature_count,
        }
        documents.append(doc_dict)
    return documents, total


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
    content = await storage.download_object(doc.object_key)
    return content, doc.filename


# ---------------------------------------------------------------------------
# Mutating / Sign operations
# ---------------------------------------------------------------------------


async def delete_document(db: AsyncSession, user_id: int, doc_id: int) -> None:
    """Delete a document owned by *user_id*. Removes S3 object first, then DB row."""
    doc = await get_document(db, user_id, doc_id)
    await storage.delete_object(doc.object_key)
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
        sha256_hash=doc.sha256_hash,
        signature_blob=result["signature"],
    )
    db.add(signature)
    await db.commit()
    await db.refresh(signature)
    return signature


async def list_signatures(
    db: AsyncSession, user_id: int, doc_id: int
) -> list[Signature]:
    """List all signatures for a document owned by *user_id*.

    Ownership check on the document row, then query signatures by
    sha256_hash so the owner sees all signers across copies of the
    same content.
    """
    doc = await get_document(db, user_id, doc_id)  # ownership check
    result = await db.execute(
        select(Signature).where(
            Signature.sha256_hash == doc.sha256_hash,
        ).order_by(Signature.signed_at.desc())
    )
    return list(result.scalars().all())


async def verify_document_signature(
    db: AsyncSession, user_id: int, doc_id: int, sig_id: int
) -> dict:
    """Verify a signature's cryptographic validity and certificate status.

    Orchestrates:
      1. Ownership check on the document (get sha256_hash)
      2. Fetch Signature row (validate sig.document_id == doc_id)
      3. Get signer's public key
      4. RSA verify (hash vs blob vs public key)
      5. Certificate validity check
      6. Persist verified_at + is_valid on Signature row
      7. Fetch User for signer_name/signer_email
      8. Return VerificationResult-shaped dict

    Raises:
      HTTPException(404) if sig doesn't belong to doc or doesn't exist.
      HTTPException(500) on MinIO/crypto errors.
    """
    # 1. Ownership check → get sha256_hash
    doc = await get_document(db, user_id, doc_id)

    # 2. Fetch Signature row
    result = await db.execute(
        select(Signature).where(Signature.id == sig_id)
    )
    sig = result.scalar_one_or_none()
    if sig is None or sig.document_id != doc_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signature not found for this document",
        )

    # 3. Get signer's public key
    try:
        public_key_pem = await crypto_service.get_public_key_for_user(db, sig.user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Signer's public key not found",
        )

    # 4. RSA verify
    verify_result = crypto_service.verify_signature(
        doc.sha256_hash, sig.signature_blob, public_key_pem
    )
    crypto_ok = verify_result["valid"]

    # 5. Certificate validity check
    cert_status = await check_certificate_validity(db, sig.certificate_id)
    # A missing cert ('not_found') does not invalidate — signing without a
    # certificate is valid in the current flow.
    cert_ok = cert_status in ("valid", "not_found")

    # 6. is_valid = crypto OK AND cert OK
    is_valid = crypto_ok and cert_ok

    # 7. Persist verified_at + is_valid
    sig.verified_at = utc_now()
    sig.is_valid = is_valid
    db.add(sig)
    await db.commit()
    await db.refresh(sig)

    # 8. Fetch User for identity
    user_result = await db.execute(select(User).where(User.id == sig.user_id))
    signer = user_result.scalar_one_or_none()
    signer_name = signer.name if signer else "Unknown"
    signer_email = signer.email if signer else "unknown@unknown"

    return {
        "is_valid": is_valid,
        "verified_at": sig.verified_at,
        "signer_name": signer_name,
        "signer_email": signer_email,
        "certificate_status": cert_status,
    }


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


async def check_certificate_validity(db: AsyncSession, cert_id: Optional[int]) -> str:
    """Return certificate validity status based on DB columns.

    Reads Certificate.revoked and valid_to; no PEM parsing.
    Returns: 'valid' | 'revoked' | 'expired' | 'not_found'
    """
    if cert_id is None:
        return "not_found"

    result = await db.execute(
        select(Certificate).where(Certificate.id == cert_id)
    )
    cert = result.scalar_one_or_none()

    if cert is None:
        return "not_found"

    if cert.revoked:
        return "revoked"

    now = utc_now()
    if cert.valid_to < now:
        return "expired"

    return "valid"
