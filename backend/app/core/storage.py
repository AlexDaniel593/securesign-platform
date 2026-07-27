"""Async S3 storage adapter backed by MinIO (boto3 client).

All blocking boto3 calls are wrapped in asyncio.to_thread() so FastAPI's
event loop stays responsive. Error translation: botocore.ClientError and
EndpointConnectionError become HTTP 503, except download_object which
returns 404 for NoSuchKey to preserve the existing API contract.

Bucket must exist before first use — call ensure_bucket_exists() at startup.
"""

import asyncio
import uuid
from functools import lru_cache

import boto3
from botocore.exceptions import ClientError, EndpointConnectionError
from fastapi import HTTPException, status

from app.core.config import settings


@lru_cache()
def _get_client():
    """Return a module-level boto3 S3 client (thread-safe by boto3 guarantee).

    Cached via lru_cache to defer creation until the first call, which lets
    test fixtures intercept with moto's mock_aws() context manager.

    When MINIO_ENDPOINT is empty or None (test mode), boto3 uses the default
    AWS S3 endpoint, which moto intercepts automatically.
    """
    client_kwargs: dict = {
        "service_name": "s3",
        "aws_access_key_id": settings.MINIO_ACCESS_KEY,
        "aws_secret_access_key": settings.MINIO_SECRET_KEY,
        "use_ssl": settings.MINIO_SECURE,
        "region_name": "us-east-1",
    }
    if settings.MINIO_ENDPOINT:
        client_kwargs["endpoint_url"] = settings.MINIO_ENDPOINT
    return boto3.client(**client_kwargs)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def ensure_bucket_exists() -> None:
    """Create the private bucket if it does not already exist.  Idempotent.

    Called once at backend startup.  Raises HTTP 503 when MinIO is unreachable.
    """
    client = _get_client()
    try:
        await asyncio.to_thread(_ensure_bucket_sync, client)
    except (ClientError, EndpointConnectionError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable",
        )


async def upload_object(user_id: int, filename: str, content: bytes) -> str:
    """Persist *content* under key ``{user_id}/{uuid}_{filename}``.

    Returns the full S3 object key so the caller can store it in the DB.
    """
    client = _get_client()
    object_key = f"{user_id}/{uuid.uuid4()}_{filename}"
    try:
        await asyncio.to_thread(
            client.put_object,
            Bucket=settings.MINIO_BUCKET_NAME,
            Key=object_key,
            Body=content,
        )
        return object_key
    except (ClientError, EndpointConnectionError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable",
        )


async def download_object(object_key: str) -> bytes:
    """Return the raw bytes stored at *object_key*.

    Raises HTTP 404 when the object does not exist (preserving the existing
    API contract) and HTTP 503 when the storage service is unreachable.
    """
    client = _get_client()
    try:
        response = await asyncio.to_thread(
            client.get_object,
            Bucket=settings.MINIO_BUCKET_NAME,
            Key=object_key,
        )
        body: bytes = await asyncio.to_thread(response["Body"].read)
        return body
    except ClientError as exc:
        if _is_no_such_key(exc):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable",
        )
    except EndpointConnectionError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable",
        )


async def delete_object(object_key: str) -> None:
    """Delete the object at *object_key*.  Raises HTTP 503 on storage failure."""
    client = _get_client()
    try:
        await asyncio.to_thread(
            client.delete_object,
            Bucket=settings.MINIO_BUCKET_NAME,
            Key=object_key,
        )
    except (ClientError, EndpointConnectionError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service unavailable",
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _ensure_bucket_sync(client) -> None:
    """Check-create bucket synchronously (called inside to_thread)."""
    try:
        client.head_bucket(Bucket=settings.MINIO_BUCKET_NAME)
    except ClientError:
        client.create_bucket(Bucket=settings.MINIO_BUCKET_NAME)


def _is_no_such_key(exc: ClientError) -> bool:
    """Return True when the ClientError is a 'NoSuchKey' response."""
    code = exc.response.get("Error", {}).get("Code", "")
    return code == "NoSuchKey"
