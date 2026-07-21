"""Tests for documents endpoints — PR #1 + PR #2.

Covers: file_handlers unit tests + API integration tests for all 8 endpoints.
"""

import io
import uuid
from pathlib import Path

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
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
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
# 4.1 — File handlers unit tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestFileHandlers:
    async def test_save_then_read_roundtrip(self, tmp_path):
        """Save PDF bytes, read them back — roundtrip preserves content."""
        from app.utils.file_handlers import ensure_user_dir, save_file, read_file

        user_dir = ensure_user_dir(tmp_path, 1)
        pdf = make_pdf_content()
        rel_path = save_file(tmp_path, 1, "roundtrip.pdf", pdf)

        assert user_dir.exists()
        parts = Path(rel_path).parts
        assert parts[-2] == "1"  # user_id directory
        assert parts[-3] == "uploads"  # uploads parent
        assert rel_path.endswith("_roundtrip.pdf")

        read_back = read_file(rel_path)
        assert read_back == pdf

    async def test_delete_removes_file(self, tmp_path):
        """Delete utility removes the file from disk."""
        from app.utils.file_handlers import delete_file, ensure_user_dir, save_file, read_file

        ensure_user_dir(tmp_path, 1)
        rel_path = save_file(tmp_path, 1, "delete_me.pdf", make_pdf_content())

        assert Path(rel_path).exists()

        delete_file(rel_path)
        assert not Path(rel_path).exists()

    async def test_ensure_user_dir_creates_directory(self, tmp_path):
        """ensure_user_dir creates nested user directory."""
        from app.utils.file_handlers import ensure_user_dir

        user_dir = ensure_user_dir(tmp_path, 42)
        assert user_dir.is_dir()
        assert user_dir.name == "42"
        assert user_dir.parent == tmp_path / "uploads"

    async def test_save_file_unique_names(self, tmp_path):
        """Two saves with same filename produce different paths (UUID prefix)."""
        from app.utils.file_handlers import ensure_user_dir, save_file

        ensure_user_dir(tmp_path, 1)
        path_a = save_file(tmp_path, 1, "same.pdf", make_pdf_content())
        path_b = save_file(tmp_path, 1, "same.pdf", make_pdf_content())

        assert path_a != path_b  # UUID prefix guarantees uniqueness


# ---------------------------------------------------------------------------
# 4.2 — POST /documents/upload
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestDocumentUpload:
    async def test_upload_pdf_success(self, client: AsyncClient, auth_token: str, tmp_path, monkeypatch):
        """Upload a valid PDF returns 201 with document metadata."""
        import app.services.document_service as svc
        monkeypatch.setattr(svc, "UPLOAD_DIR", tmp_path)

        resp = await _upload_doc(client, auth_token)
        assert resp.status_code == 201
        data = resp.json()
        assert data["filename"] == "test.pdf"
        assert data["sha256_hash"]
        assert len(data["sha256_hash"]) == 64  # SHA-256 hex
        assert data["file_size"] > 0
        assert "uploaded_at" in data
        assert "id" in data

    async def test_upload_reject_non_pdf(self, client: AsyncClient, auth_token: str, tmp_path, monkeypatch):
        """Uploading a .txt file returns 400."""
        import app.services.document_service as svc
        monkeypatch.setattr(svc, "UPLOAD_DIR", tmp_path)

        resp = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("notes.txt", io.BytesIO(b"hello world"), "text/plain")},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 400

    async def test_upload_reject_oversized(self, client: AsyncClient, auth_token: str, tmp_path, monkeypatch):
        """Uploading a PDF larger than max size returns 413."""
        import app.services.document_service as svc
        monkeypatch.setattr(svc, "UPLOAD_DIR", tmp_path)
        monkeypatch.setattr(svc, "MAX_UPLOAD_SIZE", 10)  # 10 bytes for testing

        big = make_pdf_content()  # much more than 10 bytes
        resp = await _upload_doc(client, auth_token, content=big)
        assert resp.status_code == 413

    async def test_upload_duplicate_creates_new_record(self, client: AsyncClient, auth_token: str, tmp_path, monkeypatch):
        """Uploading the same PDF content again creates a NEW Document row."""
        import app.services.document_service as svc
        monkeypatch.setattr(svc, "UPLOAD_DIR", tmp_path)

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
# 4.3 — GET /documents (list)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestDocumentList:
    async def test_list_default_pagination(self, client: AsyncClient, auth_token: str, tmp_path, monkeypatch):
        """GET /documents returns paginated list with defaults."""
        import app.services.document_service as svc
        monkeypatch.setattr(svc, "UPLOAD_DIR", tmp_path)

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

    async def test_list_custom_pagination(self, client: AsyncClient, auth_token: str, tmp_path, monkeypatch):
        """GET /documents with page and limit returns correct slice."""
        import app.services.document_service as svc
        monkeypatch.setattr(svc, "UPLOAD_DIR", tmp_path)

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

    async def test_list_excludes_other_users(self, client: AsyncClient, auth_token: str, tmp_path, monkeypatch):
        """User A's list does not include user B's documents."""
        import app.services.document_service as svc
        monkeypatch.setattr(svc, "UPLOAD_DIR", tmp_path)

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
# 4.4 — GET /documents/{id} (metadata)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestDocumentGet:
    async def test_owner_gets_metadata(self, client: AsyncClient, auth_token: str, tmp_path, monkeypatch):
        """Owner can GET metadata for their document."""
        import app.services.document_service as svc
        monkeypatch.setattr(svc, "UPLOAD_DIR", tmp_path)

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

    async def test_non_owner_gets_404(self, client: AsyncClient, auth_token: str, tmp_path, monkeypatch):
        """Non-owner accessing metadata returns 404 (no existence leak)."""
        import app.services.document_service as svc
        monkeypatch.setattr(svc, "UPLOAD_DIR", tmp_path)

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
# 4.5 — GET /documents/{id}/download
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestDocumentDownload:
    async def test_owner_downloads(self, client: AsyncClient, auth_token: str, tmp_path, monkeypatch):
        """Owner can download the stored PDF bytes as octet-stream."""
        import app.services.document_service as svc
        monkeypatch.setattr(svc, "UPLOAD_DIR", tmp_path)

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

    async def test_non_owner_download_returns_404(self, client: AsyncClient, auth_token: str, tmp_path, monkeypatch):
        """Non-owner downloading returns 404."""
        import app.services.document_service as svc
        monkeypatch.setattr(svc, "UPLOAD_DIR", tmp_path)

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
# PR #2: Mutating + Sign + Signatures endpoints
# =====================================================================


# ---------------------------------------------------------------------------
# 4.6 — DELETE /documents/{id}
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestDocumentDelete:
    async def test_owner_deletes_document(self, client: AsyncClient, auth_token: str, tmp_path, monkeypatch):
        """Owner DELETE removes the DB row and the file from disk."""
        import app.services.document_service as svc
        monkeypatch.setattr(svc, "UPLOAD_DIR", tmp_path)

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

    async def test_non_owner_delete_returns_404(self, client: AsyncClient, auth_token: str, tmp_path, monkeypatch):
        """Non-owner DELETE returns 404 (no existence leak)."""
        import app.services.document_service as svc
        monkeypatch.setattr(svc, "UPLOAD_DIR", tmp_path)

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
# 4.7 — PUT /documents/{id} (rename only)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestDocumentRename:
    async def test_owner_renames_document(self, client: AsyncClient, auth_token: str, tmp_path, monkeypatch):
        """Owner PUT renames the document and returns {id, filename} without updated_at."""
        import app.services.document_service as svc
        monkeypatch.setattr(svc, "UPLOAD_DIR", tmp_path)

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

    async def test_non_owner_rename_returns_404(self, client: AsyncClient, auth_token: str, tmp_path, monkeypatch):
        """Non-owner PUT returns 404."""
        import app.services.document_service as svc
        monkeypatch.setattr(svc, "UPLOAD_DIR", tmp_path)

        upload = await _upload_doc(client, auth_token, "mine.pdf")
        doc_id = upload.json()["id"]

        token_b = await _register_and_login(client, "intruder-ren@example.com")
        resp = await client.put(
            f"/api/v1/documents/{doc_id}",
            json={"filename": "stolen.pdf"},
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 404

    async def test_rename_empty_filename_returns_422(self, client: AsyncClient, auth_token: str, tmp_path, monkeypatch):
        """PUT with empty filename returns 422 (Pydantic validation)."""
        import app.services.document_service as svc
        monkeypatch.setattr(svc, "UPLOAD_DIR", tmp_path)

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
# 4.8 — POST /documents/{id}/sign
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestDocumentSign:
    async def test_owner_signs_document(self, client: AsyncClient, auth_token: str, tmp_path, monkeypatch):
        """Owner signs their document and gets signature back."""
        import app.services.document_service as svc
        monkeypatch.setattr(svc, "UPLOAD_DIR", tmp_path)

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

    async def test_sign_with_certificate_id(self, client: AsyncClient, auth_token: str, tmp_path, monkeypatch):
        """Signing with a certificate_id stores it in the Signature row."""
        import app.services.document_service as svc
        monkeypatch.setattr(svc, "UPLOAD_DIR", tmp_path)

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

    async def test_sign_without_keys_returns_400(self, client: AsyncClient, auth_token: str, tmp_path, monkeypatch):
        """Signing when user has no RSA keys returns 400."""
        import app.services.document_service as svc
        monkeypatch.setattr(svc, "UPLOAD_DIR", tmp_path)

        upload = await _upload_doc(client, auth_token, "no-keys.pdf")
        doc_id = upload.json()["id"]

        # No key generation — user has no keys yet
        resp = await client.post(
            f"/api/v1/documents/{doc_id}/sign",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 400
        assert "key" in resp.json()["detail"].lower()

    async def test_non_owner_sign_returns_404(self, client: AsyncClient, auth_token: str, tmp_path, monkeypatch):
        """Non-owner signing returns 404."""
        import app.services.document_service as svc
        monkeypatch.setattr(svc, "UPLOAD_DIR", tmp_path)

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
# 4.9 — GET /documents/{id}/signatures
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestDocumentSignatures:
    async def test_owner_lists_signatures(self, client: AsyncClient, auth_token: str, tmp_path, monkeypatch):
        """Owner can list signatures for their document."""
        import app.services.document_service as svc
        monkeypatch.setattr(svc, "UPLOAD_DIR", tmp_path)

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

    async def test_non_owner_signatures_returns_404(self, client: AsyncClient, auth_token: str, tmp_path, monkeypatch):
        """Non-owner listing signatures returns 404."""
        import app.services.document_service as svc
        monkeypatch.setattr(svc, "UPLOAD_DIR", tmp_path)

        upload = await _upload_doc(client, auth_token, "mine.pdf")
        doc_id = upload.json()["id"]

        token_b = await _register_and_login(client, "intruder-sigs@example.com")
        resp = await client.get(
            f"/api/v1/documents/{doc_id}/signatures",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert resp.status_code == 404

    async def test_owner_empty_signatures_list(self, client: AsyncClient, auth_token: str, tmp_path, monkeypatch):
        """Owner listing signatures for an unsigned document returns empty list."""
        import app.services.document_service as svc
        monkeypatch.setattr(svc, "UPLOAD_DIR", tmp_path)

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
