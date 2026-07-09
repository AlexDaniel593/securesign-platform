import base64
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.config import settings
from app.core.crypto import (
    aes_decrypt,
    aes_encrypt,
    compute_fingerprint,
    decrypt_private_key,
    encrypt_private_key,
    generate_rsa_keypair,
    hash_sha256,
    rsa_sign,
    rsa_verify,
)
from app.db.models import UserKey


async def get_user_key(db: AsyncSession, user_id: int) -> Optional[UserKey]:
    result = await db.execute(select(UserKey).where(UserKey.user_id == user_id))
    return result.scalar_one_or_none()


def compute_hash(content_b64: str, filename: Optional[str] = None) -> dict:
    content = base64.b64decode(content_b64)
    sha256_hash = hash_sha256(content)
    return {
        "sha256_hash": sha256_hash,
        "filename": filename,
        "size": len(content),
    }


async def get_key_status(db: AsyncSession, user_id: int) -> dict:
    user_key = await get_user_key(db, user_id)
    if user_key:
        return {"has_keys": True, "fingerprint": user_key.fingerprint}
    return {"has_keys": False, "fingerprint": None}


async def generate_keys(db: AsyncSession, user_id: int) -> dict:
    aes_key = bytes.fromhex(settings.AES_KEY)
    private_pem, public_pem = generate_rsa_keypair()
    private_encrypted = encrypt_private_key(private_pem, aes_key)
    fingerprint = compute_fingerprint(public_pem)

    existing_key = await get_user_key(db, user_id)
    if existing_key:
        existing_key.private_key_encrypted = private_encrypted
        existing_key.public_key = public_pem.decode()
        existing_key.fingerprint = fingerprint
        existing_key.created_at = datetime.now(timezone.utc)
        db.add(existing_key)
    else:
        new_key = UserKey(
            user_id=user_id,
            private_key_encrypted=private_encrypted,
            public_key=public_pem.decode(),
            fingerprint=fingerprint,
        )
        db.add(new_key)

    await db.commit()
    return {"fingerprint": fingerprint, "message": "RSA key pair generated successfully"}


async def sign_hash(
    db: AsyncSession, user_id: int, document_hash: str
) -> dict:
    user_key = await get_user_key(db, user_id)
    if not user_key:
        raise ValueError("No RSA key pair found. Generate keys first.")

    aes_key = bytes.fromhex(settings.AES_KEY)
    private_pem = decrypt_private_key(user_key.private_key_encrypted, aes_key)
    data = bytes.fromhex(document_hash)
    signature = rsa_sign(private_pem, data)
    signature_b64 = base64.b64encode(signature).decode()

    user_key.last_used = datetime.now(timezone.utc)
    db.add(user_key)
    await db.commit()

    return {
        "signature": signature_b64,
        "signed_at": datetime.now(timezone.utc),
    }


def verify_signature(document_hash: str, signature_b64: str, public_key_pem: str) -> dict:
    try:
        data = bytes.fromhex(document_hash)
        signature = base64.b64decode(signature_b64)
        is_valid = rsa_verify(public_key_pem.encode(), data, signature)
        if is_valid:
            return {"valid": True, "message": "Signature is valid"}
        return {"valid": False, "message": "Signature verification failed"}
    except Exception as e:
        return {"valid": False, "message": f"Verification error: {str(e)}"}


def encrypt_content(content_b64: str) -> dict:
    aes_key = bytes.fromhex(settings.AES_KEY)
    plaintext = base64.b64decode(content_b64)
    ciphertext, iv = aes_encrypt(plaintext, aes_key)
    return {
        "encrypted_base64": base64.b64encode(ciphertext).decode(),
        "iv": base64.b64encode(iv).decode(),
    }


def decrypt_content(encrypted_b64: str, iv_b64: str) -> dict:
    aes_key = bytes.fromhex(settings.AES_KEY)
    ciphertext = base64.b64decode(encrypted_b64)
    iv = base64.b64decode(iv_b64)
    plaintext = aes_decrypt(ciphertext, aes_key, iv)
    return {"decrypted_base64": base64.b64encode(plaintext).decode()}
