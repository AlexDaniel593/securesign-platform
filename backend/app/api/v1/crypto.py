from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import User
from app.dependencies.auth import get_current_user
from app.services import crypto_service

router = APIRouter()


class HashRequest(BaseModel):
    content_base64: str
    filename: Optional[str] = None


class HashResponse(BaseModel):
    sha256_hash: str
    filename: Optional[str]
    size: int


class SignRequest(BaseModel):
    document_hash: str
    certificate_id: Optional[int] = None


class SignResponse(BaseModel):
    signature: str
    signed_at: datetime
    certificate_id: Optional[int] = None


class VerifyRequest(BaseModel):
    document_hash: str
    signature: str
    public_key: str


class VerifyResponse(BaseModel):
    valid: bool
    message: str


class EncryptRequest(BaseModel):
    content_base64: str


class EncryptResponse(BaseModel):
    encrypted_base64: str
    iv: str


class DecryptRequest(BaseModel):
    encrypted_base64: str
    iv: str


class DecryptResponse(BaseModel):
    decrypted_base64: str


class KeyStatusResponse(BaseModel):
    has_keys: bool
    fingerprint: Optional[str] = None


class KeyGenerateResponse(BaseModel):
    fingerprint: str
    message: str


@router.post("/hash", response_model=HashResponse)
async def compute_hash(
    body: HashRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        result = crypto_service.compute_hash(body.content_base64, body.filename)
        return HashResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid base64 content: {str(e)}",
        )


@router.post("/sign", response_model=SignResponse)
async def sign_document(
    body: SignRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await crypto_service.sign_hash(db, current_user.id, body.document_hash)
        return SignResponse(
            signature=result["signature"],
            signed_at=result["signed_at"],
            certificate_id=body.certificate_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signing failed: {str(e)}",
        )


@router.post("/verify", response_model=VerifyResponse)
async def verify_signature(
    body: VerifyRequest,
):
    result = crypto_service.verify_signature(
        body.document_hash, body.signature, body.public_key
    )
    return VerifyResponse(**result)


@router.post("/encrypt", response_model=EncryptResponse)
async def encrypt_content(
    body: EncryptRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        result = crypto_service.encrypt_content(body.content_base64)
        return EncryptResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Encryption failed: {str(e)}",
        )


@router.post("/decrypt", response_model=DecryptResponse)
async def decrypt_content(
    body: DecryptRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        result = crypto_service.decrypt_content(body.encrypted_base64, body.iv)
        return DecryptResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Decryption failed: {str(e)}",
        )


@router.get("/keys/status", response_model=KeyStatusResponse)
async def key_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await crypto_service.get_key_status(db, current_user.id)
    return KeyStatusResponse(**result)


@router.post("/keys/generate", response_model=KeyGenerateResponse)
async def generate_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await crypto_service.generate_keys(db, current_user.id)
        return KeyGenerateResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Key generation failed: {str(e)}",
        )
