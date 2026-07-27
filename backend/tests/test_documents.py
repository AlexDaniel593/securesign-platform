"""Tests for documents endpoints — migrated to S3 storage (moto mock).

All tests use the s3_mock autouse fixture from conftest.py. No local disk
I/O occurs; no monkeypatch on UPLOAD_DIR or tmp_path fixtures.
"""

import io
import uuid

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_pdf_content() -> bytes:
    """Return minimal valid PDF bytes for upload tests."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n"
        b"trailer<</Size 4/Root 1 0 R>>\n"
        b"startxref\n190\n%%EOF"
    )


async def _upload_doc(client: AsyncClient, token: str, filename: str = "test.pdf", content: bytes | None = None) -> dict:
    """Upload a test document and return the response JSON."""
    pdf = content or make_pdf_content()
    resp = await client.post(
        "/api/v1/documents/upload",
        files={"file": (filename, io.BytesIO(pdf), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    return resp


async def _register_and_login(client: AsyncClient, email: str, password: str = "SecurePass1!") -> str:
    """Register a new user, log in, return access token."""
    await client.post("/api/v1/auth/register", json={"name": "Test User", "email": email, "password": password})
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


async def _generate_keys(client: AsyncClient, token: str) -> None:
    """Generate RSA keys for the authenticated user."""
    resp = await client.post(
        "/api/v1/crypto/keys/generate",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, f"Key generation failed: {resp.text}"


# ---------------------------------------------------------------------------
# POST /documents/upload
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestDocumentUpload:
    async def test_upload_pdf_success(self, client: AsyncClient, auth_token: str, s3_mock):
        """Upload a valid PDF returns 201 with document metadata."""
        resp = await _upload_doc(client, auth_token)
        assert resp.status_code == 201
        data = resp.json()
        assert data["filename"] == "test.pdf"
        assert data["sha256_hash"]
        assert len(data["sha256_hash"]) == 64  # SHA-256 hex
        assert data["file_size"] > 0
        assert "uploaded_at" in data
        assert "id" in data

    async def test_upload_reject_non_pdf(self, client: AsyncClient, auth_token: str, s3_mock):
        """Uploading a .txt file returns 400."""
        resp = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("notes.txt", io.BytesIO(b"hello world"), "text/plain")},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 400

    async def test_upload_reject_oversized(self, client: AsyncClient, auth_token: str, monkeypatch, s3_mock):
        """Uploading a PDF larger than max size returns 413."""
        monkeypatch.setattr("app.services.document_service.MAX_UPLOAD_SIZE", 10)  # 10 bytes

        big = make_pdf_content()  # much more than 10 bytes
        resp = await _upload_doc(client, auth_token, content=big)
        assert resp.status_code == 413

    async def test_upload_duplicate_creates_new_record(self, client: AsyncClient, auth_token: str, s3_mock):
        """Uploading the same PDF content again creates a NEW Document row."""
        r1 = await _upload_doc(client, auth_token)
        r2 = await _upload_doc(client, auth_token)

        assert r1.status_code == 201
        assert r2.status_code == 201
        assert r1.json()["sha256_hash"] == r2.json()["sha256_hash"]
        assert r1.json()["id"] != r2.json()["id"]  # NEW record, no dedup

    async def test_upload_requires_auth(self, client: AsyncClient):
        """Unauthenticated upload returns 401."""
        resp = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", io.BytesIO(make_pdf_content()), "application/pdf")},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /documents (list)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestDocumentList:
    async def test_list_default_pagination(self, client: AsyncClient, auth_token: str, s3_mock):
        """GET /documents returns paginated list with defaults."""
        for i in range(3):
            await _upload_doc(client, auth_token, f"doc{i}.pdf")

        resp = await client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 3
        assert data["total"] == 3
        assert data["page"] == 1
        assert data["limit"] == 20

    async def test_list_custom_pagination(self, client: AsyncClient, auth_token: str, s3_mock):
        """GET /documents with page and limit returns correct slice."""
        for i in range(5):
            await _upload_doc(client, auth_token, f"doc{i}.pdf")

        resp = await client.get(
            "/api/v1/documents?page=2&limit=2",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2  # 3rd page
        assert data["total"] == 5
        assert data["page"] == 2
        assert data["limit"] == 2

    async def test_list_excludes_other_users(self, client: AsyncClient, auth_token: str, s3_mock):
        """User A's list does not include user B's documents."""
        await _upload_doc(client, auth_token, "mine.pdf")

        # Create second user
        token_b = await _register_and_login(client, "other@example.com")
        await _upload_doc(client, token_b, "theirs.pdf")

        # User A sees only their own
        resp = await client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["filename"] == "mine.pdf"

    async def test_list_requires_auth(self, client: AsyncClient):
        """Unauthenticated list returns 401."""
        resp = await client.get("/api/v1/documents")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /documents/{id} (metadata)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestDocumentGet:
    async def test_owner_gets_metadata(self, client: AsyncClient, auth_token: str, s3_mock):
        """Owner can GET metadata for their document."""
        upload = await _upload_doc(client, auth_token, "meta.pdf")
        doc_id = upload.json()["id"]

        resp = await client.get(
            f"/api/v1/documents/{doc_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == doc_id
        assert data["filename"] == "meta.pdf"
        assert "sha256_hash" in data
        assert data["file_size"] > 0
        assert "uploaded_at" in data

    async def test_non_owner_gets_404(self, client: AsyncClient, auth_token: str, s3_mock):
        """Non-owner accessing metadata returns 404 (no existence leak)."""
        upload = await _upload_doc(client, auth_token, "secret.pdf")
        doc_id = upload.json()["id"]

        # Second user tries to access
        token_b = await _register_and_login(client, "intruder@example.com")
        resp = await client.get(
            f"/api/v1/documents/{doc_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 404

    async def test_missing_document_returns_404(self, client: AsyncClient, auth_token: str):
        """GET /documents/99999 returns 404 for non-existent document."""
        resp = await client.get(
            "/api/v1/documents/99999",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 404

    async def test_get_requires_auth(self, client: AsyncClient):
        """Unauthenticated get returns 401."""
        resp = await client.get("/api/v1/documents/1")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /documents/{id}/download
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestDocumentDownload:
    async def test_owner_downloads(self, client: AsyncClient, auth_token: str, s3_mock):
        """Owner can download the stored PDF bytes as octet-stream."""
        pdf = make_pdf_content()
        upload = await _upload_doc(client, auth_token, "dl.pdf", content=pdf)
        doc_id = upload.json()["id"]

        resp = await client.get(
            f"/api/v1/documents/{doc_id}/download",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        assert resp.headers.get("content-type") == "application/octet-stream"
        assert resp.content == pdf

    async def test_non_owner_download_returns_404(self, client: AsyncClient, auth_token: str, s3_mock):
        """Non-owner downloading returns 404."""
        pdf = make_pdf_content()
        upload = await _upload_doc(client, auth_token, "priv.pdf", content=pdf)
        doc_id = upload.json()["id"]

        token_b = await _register_and_login(client, "thief@example.com")
        resp = await client.get(
            f"/api/v1/documents/{doc_id}/download",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 404

    async def test_download_requires_auth(self, client: AsyncClient):
        """Unauthenticated download returns 401."""
        resp = await client.get("/api/v1/documents/1/download")
        assert resp.status_code == 401


# =====================================================================
# Mutating + Sign + Signatures endpoints
# =====================================================================


# ---------------------------------------------------------------------------
# DELETE /documents/{id}
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestDocumentDelete:
    async def test_owner_deletes_document(self, client: AsyncClient, auth_token: str, s3_mock):
        """Owner DELETE removes the S3 object and the DB row."""
        upload = await _upload_doc(client, auth_token, "delete-me.pdf")
        doc_id = upload.json()["id"]

        resp = await client.delete(
            f"/api/v1/documents/{doc_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "Document deleted successfully"

        # Verify the document no longer exists via GET
        get_resp = await client.get(
            f"/api/v1/documents/{doc_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert get_resp.status_code == 404

    async def test_non_owner_delete_returns_404(self, client: AsyncClient, auth_token: str, s3_mock):
        """Non-owner DELETE returns 404 (no existence leak)."""
        upload = await _upload_doc(client, auth_token, "mine.pdf")
        doc_id = upload.json()["id"]

        token_b = await _register_and_login(client, "intruder-del@example.com")
        resp = await client.delete(
            f"/api/v1/documents/{doc_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 404

    async def test_delete_requires_auth(self, client: AsyncClient):
        """Unauthenticated DELETE returns 401."""
        resp = await client.delete("/api/v1/documents/1")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# PUT /documents/{id} (rename only)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestDocumentRename:
    async def test_owner_renames_document(self, client: AsyncClient, auth_token: str, s3_mock):
        """Owner PUT renames the document and returns {id, filename} without updated_at."""
        upload = await _upload_doc(client, auth_token, "original.pdf")
        doc_id = upload.json()["id"]

        resp = await client.put(
            f"/api/v1/documents/{doc_id}",
            json={"filename": "renamed.pdf"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == doc_id
        assert data["filename"] == "renamed.pdf"
        assert "updated_at" not in data

        # Verify via GET
        get_resp = await client.get(
            f"/api/v1/documents/{doc_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["filename"] == "renamed.pdf"

    async def test_non_owner_rename_returns_404(self, client: AsyncClient, auth_token: str, s3_mock):
        """Non-owner PUT returns 404."""
        upload = await _upload_doc(client, auth_token, "mine.pdf")
        doc_id = upload.json()["id"]

        token_b = await _register_and_login(client, "intruder-ren@example.com")
        resp = await client.put(
            f"/api/v1/documents/{doc_id}",
            json={"filename": "stolen.pdf"},
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 404

    async def test_rename_empty_filename_returns_422(self, client: AsyncClient, auth_token: str, s3_mock):
        """PUT with empty filename returns 422 (Pydantic validation)."""
        upload = await _upload_doc(client, auth_token)
        doc_id = upload.json()["id"]

        resp = await client.put(
            f"/api/v1/documents/{doc_id}",
            json={"filename": ""},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 422

    async def test_rename_requires_auth(self, client: AsyncClient):
        """Unauthenticated PUT returns 401."""
        resp = await client.put(
            "/api/v1/documents/1",
            json={"filename": "test.pdf"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /documents/{id}/sign
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestDocumentSign:
    async def test_owner_signs_document(self, client: AsyncClient, auth_token: str, s3_mock):
        """Owner signs their document and gets signature back."""
        # Upload a document
        upload = await _upload_doc(client, auth_token, "sign-me.pdf")
        doc_id = upload.json()["id"]

        # Generate RSA keys for the user
        await _generate_keys(client, auth_token)

        # Sign the document
        resp = await client.post(
            f"/api/v1/documents/{doc_id}/sign",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "signature_id" in data
        assert "signature" in data
        assert len(data["signature"]) > 0  # base64 encoded signature
        assert "signed_at" in data

    async def test_sign_with_certificate_id(self, client: AsyncClient, auth_token: str, s3_mock):
        """Signing with a certificate_id stores it in the Signature row."""
        upload = await _upload_doc(client, auth_token, "cert-sign.pdf")
        doc_id = upload.json()["id"]

        # Generate keys first
        await _generate_keys(client, auth_token)

        # Issue a certificate (requires keys)
        cert_resp = await client.post(
            "/api/v1/certificates/issue",
            json={"subject_name": "Test User"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert cert_resp.status_code == 201, f"Cert issue failed: {cert_resp.text}"
        cert_id = cert_resp.json()["id"]

        # Sign with certificate_id
        resp = await client.post(
            f"/api/v1/documents/{doc_id}/sign",
            json={"certificate_id": cert_id},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 201
        # Verify the signature appears in the signatures list and includes certificate_id
        sig_list = await client.get(
            f"/api/v1/documents/{doc_id}/signatures",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert sig_list.status_code == 200
        sigs = sig_list.json()["signatures"]
        assert len(sigs) == 1
        assert sigs[0]["certificate_id"] == cert_id

    async def test_sign_without_keys_returns_400(self, client: AsyncClient, auth_token: str, s3_mock):
        """Signing when user has no RSA keys returns 400."""
        upload = await _upload_doc(client, auth_token, "no-keys.pdf")
        doc_id = upload.json()["id"]

        # No key generation — user has no keys yet
        resp = await client.post(
            f"/api/v1/documents/{doc_id}/sign",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 400
        assert "key" in resp.json()["detail"].lower()

    async def test_non_owner_sign_returns_404(self, client: AsyncClient, auth_token: str, s3_mock):
        """Non-owner signing returns 404."""
        upload = await _upload_doc(client, auth_token, "mine.pdf")
        doc_id = upload.json()["id"]

        token_b = await _register_and_login(client, "intruder-sign@example.com")
        # Generate keys for the intruder (they need keys for sign to process)
        await _generate_keys(client, token_b)

        resp = await client.post(
            f"/api/v1/documents/{doc_id}/sign",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 404

    async def test_sign_requires_auth(self, client: AsyncClient):
        """Unauthenticated sign returns 401."""
        resp = await client.post("/api/v1/documents/1/sign")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /documents/{id}/signatures
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestDocumentSignatures:
    async def test_owner_lists_signatures(self, client: AsyncClient, auth_token: str, s3_mock):
        """Owner can list signatures for their document."""
        upload = await _upload_doc(client, auth_token, "signed.pdf")
        doc_id = upload.json()["id"]

        # Generate keys and sign the document
        await _generate_keys(client, auth_token)
        await client.post(
            f"/api/v1/documents/{doc_id}/sign",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        resp = await client.get(
            f"/api/v1/documents/{doc_id}/signatures",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "signatures" in data
        assert len(data["signatures"]) == 1
        sig = data["signatures"][0]
        assert "id" in sig
        assert "signature_blob" in sig
        assert "signed_at" in sig
        assert sig["certificate_id"] is None

    async def test_non_owner_signatures_returns_404(self, client: AsyncClient, auth_token: str, s3_mock):
        """Non-owner listing signatures returns 404."""
        upload = await _upload_doc(client, auth_token, "mine.pdf")
        doc_id = upload.json()["id"]

        token_b = await _register_and_login(client, "intruder-sigs@example.com")
        resp = await client.get(
            f"/api/v1/documents/{doc_id}/signatures",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 404

    async def test_owner_empty_signatures_list(self, client: AsyncClient, auth_token: str, s3_mock):
        """Owner listing signatures for an unsigned document returns empty list."""
        upload = await _upload_doc(client, auth_token, "unsigned.pdf")
        doc_id = upload.json()["id"]

        resp = await client.get(
            f"/api/v1/documents/{doc_id}/signatures",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "signatures" in data
        assert data["signatures"] == []

    async def test_signatures_requires_auth(self, client: AsyncClient):
        """Unauthenticated signatures list returns 401."""
        resp = await client.get("/api/v1/documents/1/signatures")
        assert resp.status_code == 401


# =====================================================================
# Service-layer primitives (Phase 1)
# =====================================================================


@pytest.mark.asyncio
class TestPublicKeyForUser:
    """Unit tests for crypto_service.get_public_key_for_user."""

    async def test_missing_user_raises_value_error(self, session: AsyncSession):
        """Calling with a user_id that has no key raises ValueError."""
        from app.services.crypto_service import get_public_key_for_user

        with pytest.raises(ValueError):
            await get_public_key_for_user(session, 99999)

    async def test_user_with_key_returns_pem(self, session: AsyncSession):
        """A user with a stored key returns the public key PEM string."""
        from app.services.crypto_service import get_public_key_for_user
        from app.db.models import User, UserKey

        user = User(name="Keyholder", email="keyholder@test.com", password_hash="x", salt="x")
        session.add(user)
        await session.flush()

        key = UserKey(
            user_id=user.id,
            private_key_encrypted="encrypted-dummy",
            public_key="-----BEGIN PUBLIC KEY-----\nMIIB...\n-----END PUBLIC KEY-----",
            fingerprint="abc123",
        )
        session.add(key)
        await session.commit()

        pem = await get_public_key_for_user(session, user.id)
        assert pem == key.public_key
        assert pem.startswith("-----BEGIN PUBLIC KEY-----")


@pytest.mark.asyncio
class TestCertificateValidity:
    """Unit tests for document_service.check_certificate_validity."""

    async def test_null_cert_id_returns_not_found(self, session: AsyncSession):
        """cert_id=None returns 'not_found'."""
        from app.services.document_service import check_certificate_validity

        result = await check_certificate_validity(session, None)
        assert result == "not_found"

    async def test_revoked_certificate(self, session: AsyncSession):
        """A revoked certificate returns 'revoked'."""
        from datetime import datetime, timedelta, timezone

        from app.db.models import Certificate, User
        from app.services.document_service import check_certificate_validity

        user = User(name="CertOwner", email="certowner@test.com", password_hash="x", salt="x")
        session.add(user)
        await session.flush()

        cert = Certificate(
            user_id=user.id,
            subject_name="Revoked Cert",
            public_key="pk",
            issuer="CA_SIMULADA",
            serial_number="REV-001",
            valid_from=datetime.now(timezone.utc) - timedelta(days=10),
            valid_to=datetime.now(timezone.utc) + timedelta(days=10),
            revoked=True,
        )
        session.add(cert)
        await session.commit()

        result = await check_certificate_validity(session, cert.id)
        assert result == "revoked"

    async def test_expired_certificate(self, session: AsyncSession):
        """A certificate with valid_to in the past returns 'expired'."""
        from datetime import datetime, timedelta, timezone

        from app.db.models import Certificate, User
        from app.services.document_service import check_certificate_validity

        user = User(name="CertOwner2", email="certowner2@test.com", password_hash="x", salt="x")
        session.add(user)
        await session.flush()

        cert = Certificate(
            user_id=user.id,
            subject_name="Expired Cert",
            public_key="pk",
            issuer="CA_SIMULADA",
            serial_number="EXP-001",
            valid_from=datetime.now(timezone.utc) - timedelta(days=30),
            valid_to=datetime.now(timezone.utc) - timedelta(days=1),
        )
        session.add(cert)
        await session.commit()

        result = await check_certificate_validity(session, cert.id)
        assert result == "expired"

    async def test_valid_certificate(self, session: AsyncSession):
        """A certificate not revoked and not expired returns 'valid'."""
        from datetime import datetime, timedelta, timezone

        from app.db.models import Certificate, User
        from app.services.document_service import check_certificate_validity

        user = User(name="CertOwner3", email="certowner3@test.com", password_hash="x", salt="x")
        session.add(user)
        await session.flush()

        cert = Certificate(
            user_id=user.id,
            subject_name="Valid Cert",
            public_key="pk",
            issuer="CA_SIMULADA",
            serial_number="VAL-001",
            valid_from=datetime.now(timezone.utc) - timedelta(days=10),
            valid_to=datetime.now(timezone.utc) + timedelta(days=10),
        )
        session.add(cert)
        await session.commit()

        result = await check_certificate_validity(session, cert.id)
        assert result == "valid"

    async def test_missing_cert_id_returns_not_found(self, session: AsyncSession):
        """A non-existent cert_id returns 'not_found'."""
        from app.services.document_service import check_certificate_validity

        result = await check_certificate_validity(session, 99999)
        assert result == "not_found"


# =====================================================================
# POST /documents/{doc_id}/verify/{sig_id}  (Phase 3 RED)
# =====================================================================


@pytest.mark.asyncio
class TestDocumentVerify:
    """API integration tests for the signature verification endpoint.

    RED phase — endpoint does not exist yet; all tests expected to get 404
    until the route is registered.
    """

    async def _sign_and_get_sig_id(self, client: AsyncClient, token: str, doc_id: int) -> int:
        """Sign a document and return the signature ID."""
        resp = await client.post(
            f"/api/v1/documents/{doc_id}/sign",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201, f"Sign failed: {resp.text}"
        return resp.json()["signature_id"]

    async def test_verify_valid_signature(self, client: AsyncClient, auth_token: str, s3_mock):
        """Verifying a valid signature returns is_valid=true and persists DB columns."""
        # Upload + generate keys
        upload = await _upload_doc(client, auth_token, "verify-me.pdf")
        doc_id = upload.json()["id"]
        await _generate_keys(client, auth_token)

        # Sign
        sig_id = await self._sign_and_get_sig_id(client, auth_token, doc_id)

        # Verify
        resp = await client.post(
            f"/api/v1/documents/{doc_id}/verify/{sig_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_valid"] is True
        assert data["verified_at"] is not None
        assert data["signer_name"]
        assert data["signer_email"]
        assert data["certificate_status"] == "not_found"

        # DB persistence check — signatures list shows is_valid
        sig_list = await client.get(
            f"/api/v1/documents/{doc_id}/signatures",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert sig_list.status_code == 200
        sigs = sig_list.json()["signatures"]
        verified = next((s for s in sigs if s["id"] == sig_id), None)
        assert verified is not None
        assert verified["is_valid"] is True

    async def test_verify_tampered_signature(self, client: AsyncClient, auth_token: str, s3_mock):
        """Verifying a tampered signature blob returns is_valid=false."""
        upload = await _upload_doc(client, auth_token, "tamper-me.pdf")
        doc_id = upload.json()["id"]
        await _generate_keys(client, auth_token)

        sig_id = await self._sign_and_get_sig_id(client, auth_token, doc_id)

        # Tamper the signature blob in the DB directly
        from app.db.database import async_session
        async with async_session() as db:
            from sqlmodel import select
            from app.db.models import Signature

            result = await db.execute(select(Signature).where(Signature.id == sig_id))
            sig = result.scalar_one()
            sig.signature_blob = "tampered-" + sig.signature_blob  # corrupt it
            await db.commit()

        # Verify should now return is_valid=false
        resp = await client.post(
            f"/api/v1/documents/{doc_id}/verify/{sig_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_valid"] is False
        assert data["verified_at"] is not None

    async def test_verify_revoked_certificate(self, client: AsyncClient, auth_token: str, s3_mock):
        """Verifying a signature with a revoked certificate returns is_valid=false, status=revoked."""
        upload = await _upload_doc(client, auth_token, "revoked-cert.pdf")
        doc_id = upload.json()["id"]
        await _generate_keys(client, auth_token)

        # Issue a certificate
        cert_resp = await client.post(
            "/api/v1/certificates/issue",
            json={"subject_name": "Revoked User"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert cert_resp.status_code == 201
        cert_id = cert_resp.json()["id"]

        # Sign with the certificate
        sign_resp = await client.post(
            f"/api/v1/documents/{doc_id}/sign",
            json={"certificate_id": cert_id},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert sign_resp.status_code == 201
        sig_id = sign_resp.json()["signature_id"]

        # Revoke the certificate
        revoke_resp = await client.post(
            f"/api/v1/certificates/{cert_id}/revoke",
            json={"reason": "Testing"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert revoke_resp.status_code == 200, f"Revoke failed: {revoke_resp.text}"

        # Verify should report revoked
        resp = await client.post(
            f"/api/v1/documents/{doc_id}/verify/{sig_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_valid"] is False
        assert data["certificate_status"] == "revoked"

    async def test_verify_expired_certificate(self, client: AsyncClient, auth_token: str, s3_mock):
        """Verifying a signature with an expired certificate returns is_valid=false, status=expired."""
        upload = await _upload_doc(client, auth_token, "expired-cert.pdf")
        doc_id = upload.json()["id"]
        await _generate_keys(client, auth_token)

        # Issue a certificate
        cert_resp = await client.post(
            "/api/v1/certificates/issue",
            json={"subject_name": "Expiring User"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert cert_resp.status_code == 201
        cert_id = cert_resp.json()["id"]

        # Manually expire the certificate by setting valid_to in the past
        from app.db.database import async_session
        from datetime import datetime, timedelta, timezone
        async with async_session() as db:
            from sqlmodel import select
            from app.db.models import Certificate

            result = await db.execute(select(Certificate).where(Certificate.id == cert_id))
            cert = result.scalar_one()
            cert.valid_to = datetime.now(timezone.utc) - timedelta(days=1)
            await db.commit()

        # Sign with the expired certificate
        sign_resp = await client.post(
            f"/api/v1/documents/{doc_id}/sign",
            json={"certificate_id": cert_id},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert sign_resp.status_code == 201
        sig_id = sign_resp.json()["signature_id"]

        # Verify should report expired
        resp = await client.post(
            f"/api/v1/documents/{doc_id}/verify/{sig_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_valid"] is False
        assert data["certificate_status"] == "expired"

    async def test_verify_sig_doc_mismatch_returns_404(self, client: AsyncClient, auth_token: str, s3_mock):
        """Verifying a signature against a different document returns 404."""
        # Upload two documents
        up1 = await _upload_doc(client, auth_token, "doc-a.pdf")
        up2 = await _upload_doc(client, auth_token, "doc-b.pdf")
        doc_a = up1.json()["id"]
        doc_b = up2.json()["id"]
        await _generate_keys(client, auth_token)

        # Sign doc-a
        sig_id = await self._sign_and_get_sig_id(client, auth_token, doc_a)

        # Try to verify doc-a's signature against doc-b → 404
        resp = await client.post(
            f"/api/v1/documents/{doc_b}/verify/{sig_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 404

    async def test_verify_requires_auth(self, client: AsyncClient):
        """Unauthenticated verify returns 401."""
        resp = await client.post("/api/v1/documents/1/verify/1")
        assert resp.status_code == 401

    async def test_enriched_signatures_list(self, client: AsyncClient, auth_token: str, s3_mock):
        """Signatures list includes signer_name, signer_email, is_valid, verified_at."""
        upload = await _upload_doc(client, auth_token, "enriched.pdf")
        doc_id = upload.json()["id"]
        await _generate_keys(client, auth_token)

        await self._sign_and_get_sig_id(client, auth_token, doc_id)

        resp = await client.get(
            f"/api/v1/documents/{doc_id}/signatures",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        sigs = resp.json()["signatures"]
        assert len(sigs) >= 1
        sig = sigs[0]
        assert "signer_name" in sig
        assert "signer_email" in sig
        # Not yet verified — should be null
        assert sig["is_valid"] is None
        assert sig["verified_at"] is None


@pytest.mark.asyncio
class TestDocumentIsSigned:
    """Tests for is_signed indicator on document list."""

    async def test_document_list_includes_is_signed(self, client: AsyncClient, auth_token: str, s3_mock):
        """Document list items include is_signed boolean."""
        # Upload one unsigned document
        up1 = await _upload_doc(client, auth_token, "unsigned.pdf")
        doc_id = up1.json()["id"]

        # Check list — unsigned → is_signed=false
        resp = await client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        unsigned = next((d for d in items if d["id"] == doc_id), None)
        assert unsigned is not None
        assert unsigned["is_signed"] is False

        # Sign the document
        await _generate_keys(client, auth_token)
        await client.post(
            f"/api/v1/documents/{doc_id}/sign",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        # Re-check list — signed → is_signed=true
        resp2 = await client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp2.status_code == 200
        items2 = resp2.json()["items"]
        signed = next((d for d in items2 if d["id"] == doc_id), None)
        assert signed is not None
        assert signed["is_signed"] is True
