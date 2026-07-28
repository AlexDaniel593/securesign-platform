"""Unit tests for app.core.storage — S3 adapter with moto mock."""

import pytest
from fastapi import HTTPException

from app.core import storage


class TestEnsureBucketExists:
    """Idempotent bucket creation."""

    @pytest.mark.asyncio
    async def test_ensure_bucket_is_idempotent(self, s3_mock):
        """Calling ensure_bucket_exists multiple times does not error."""
        await storage.ensure_bucket_exists()
        await storage.ensure_bucket_exists()

    @pytest.mark.asyncio
    async def test_ensure_bucket_after_existing(self, s3_mock):
        """Calling after the fixture already created the bucket works."""
        import boto3

        await storage.ensure_bucket_exists()
        # Verify the bucket still exists via direct client
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.head_bucket(Bucket="test-bucket")


class TestUploadDownload:
    """Round-trip and missing-object error paths."""

    @pytest.mark.asyncio
    async def test_upload_roundtrip_bytes(self, s3_mock):
        """Upload bytes → download — content preserved."""
        content = b"hello minio roundtrip"
        user_id = 1
        filename = "test.pdf"

        key = await storage.upload_object(user_id, filename, content)

        # Key format: {user_id}/{uuid}_{filename}
        assert key.startswith(f"{user_id}/")
        assert key.endswith(f"_{filename}")

        downloaded = await storage.download_object(key)
        assert downloaded == content

    @pytest.mark.asyncio
    async def test_download_missing_object_returns_404(self, s3_mock):
        """Download of a non-existent key raises HTTP 404."""
        with pytest.raises(HTTPException) as exc:
            await storage.download_object("nonexistent/key.pdf")
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_upload_unique_keys(self, s3_mock):
        """Two uploads with same filename produce different keys."""
        content = b"same content"
        key_a = await storage.upload_object(1, "same.pdf", content)
        key_b = await storage.upload_object(1, "same.pdf", content)
        assert key_a != key_b

    @pytest.mark.asyncio
    async def test_different_users_separate_prefixes(self, s3_mock):
        """User 1 and User 2 get keys in different prefixes."""
        content = b"data"
        key_1 = await storage.upload_object(1, "doc.pdf", content)
        key_2 = await storage.upload_object(2, "doc.pdf", content)
        assert key_1.startswith("1/")
        assert key_2.startswith("2/")


class TestDelete:
    """Object deletion."""

    @pytest.mark.asyncio
    async def test_delete_removes_object(self, s3_mock):
        """After delete, download raises 404."""
        content = b"to be deleted"
        key = await storage.upload_object(1, "delete.pdf", content)

        # Object exists
        downloaded = await storage.download_object(key)
        assert downloaded == content

        # Delete it
        await storage.delete_object(key)

        # Now it's gone
        with pytest.raises(HTTPException) as exc:
            await storage.download_object(key)
        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_does_not_raise(self, s3_mock):
        """Deleting a key that does not exist is a no-op."""
        await storage.delete_object("nonexistent/key.pdf")
