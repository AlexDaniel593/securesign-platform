import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestIssueCertificate:
    async def test_issue_without_keys(self, client: AsyncClient, auth_token):
        resp = await client.post(
            "/api/v1/certificates/issue",
            json={"subject_name": "Test User"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 400
        assert "key" in resp.json()["detail"].lower()

    async def test_issue_success(self, client: AsyncClient, auth_token):
        await client.post(
            "/api/v1/crypto/keys/generate",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        resp = await client.post(
            "/api/v1/certificates/issue",
            json={"subject_name": "Test User", "validity_days": 365},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["subject"] == "Test User"
        assert data["issuer"] == "CA_SIMULADA"
        assert "valid_from" in data
        assert "valid_to" in data
        assert "fingerprint" in data
        assert "id" in data

    async def test_issue_unauthorized(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/certificates/issue",
            json={"subject_name": "Test"},
        )
        assert resp.status_code == 401

    async def test_issue_default_validity(self, client: AsyncClient, auth_token):
        await client.post(
            "/api/v1/crypto/keys/generate",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        resp = await client.post(
            "/api/v1/certificates/issue",
            json={"subject_name": "Default Validity"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        from datetime import datetime, timezone

        valid_to = datetime.fromisoformat(data["valid_to"])
        valid_from = datetime.fromisoformat(data["valid_from"])
        diff = (valid_to - valid_from).days
        assert diff == 365


@pytest.mark.asyncio
class TestListCertificates:
    async def test_list_empty(self, client: AsyncClient, auth_token):
        resp = await client.get(
            "/api/v1/certificates",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    async def test_list_with_certificates(self, client: AsyncClient, auth_token):
        await client.post(
            "/api/v1/crypto/keys/generate",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        await client.post(
            "/api/v1/certificates/issue",
            json={"subject_name": "List Test"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        resp = await client.get(
            "/api/v1/certificates",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["subject"] == "List Test"

    async def test_list_filter_revoked(self, client: AsyncClient, auth_token):
        await client.post(
            "/api/v1/crypto/keys/generate",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        await client.post(
            "/api/v1/certificates/issue",
            json={"subject_name": "To Revoke"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        resp = await client.get(
            "/api/v1/certificates?revoked=true",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    async def test_list_unauthorized(self, client: AsyncClient):
        resp = await client.get("/api/v1/certificates")
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestGetCertificate:
    async def test_get_certificate_success(self, client: AsyncClient, auth_token):
        await client.post(
            "/api/v1/crypto/keys/generate",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        issue_resp = await client.post(
            "/api/v1/certificates/issue",
            json={"subject_name": "Detail Test"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        cert_id = issue_resp.json()["id"]

        resp = await client.get(
            f"/api/v1/certificates/{cert_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["subject"] == "Detail Test"
        assert data["issuer"] == "CA_SIMULADA"
        assert "public_key" in data
        assert data["revoked"] is False

    async def test_get_certificate_not_found(self, client: AsyncClient, auth_token):
        resp = await client.get(
            "/api/v1/certificates/9999",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 404

    async def test_get_other_user_certificate(self, client: AsyncClient, auth_token):
        await client.post(
            "/api/v1/crypto/keys/generate",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        issue_resp = await client.post(
            "/api/v1/certificates/issue",
            json={"subject_name": "Owner"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        cert_id = issue_resp.json()["id"]

        resp = await client.get(
            f"/api/v1/certificates/{cert_id}",
        )
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestRevokeCertificate:
    async def test_revoke_success(self, client: AsyncClient, auth_token):
        await client.post(
            "/api/v1/crypto/keys/generate",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        issue_resp = await client.post(
            "/api/v1/certificates/issue",
            json={"subject_name": "Revoke Test"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        cert_id = issue_resp.json()["id"]

        resp = await client.post(
            f"/api/v1/certificates/{cert_id}/revoke",
            json={"reason": "Key compromised"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "revoked successfully" in data["message"].lower()
        assert "revoked_at" in data

    async def test_revoke_twice(self, client: AsyncClient, auth_token):
        await client.post(
            "/api/v1/crypto/keys/generate",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        issue_resp = await client.post(
            "/api/v1/certificates/issue",
            json={"subject_name": "Double Revoke"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        cert_id = issue_resp.json()["id"]

        await client.post(
            f"/api/v1/certificates/{cert_id}/revoke",
            json={},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        resp = await client.post(
            f"/api/v1/certificates/{cert_id}/revoke",
            json={},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 400
        assert "already revoked" in resp.json()["detail"].lower()

    async def test_revoke_not_found(self, client: AsyncClient, auth_token):
        resp = await client.post(
            "/api/v1/certificates/9999/revoke",
            json={},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 404

    async def test_revoke_unauthorized(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/certificates/1/revoke",
            json={"reason": "test"},
        )
        assert resp.status_code == 401

    async def test_revoke_without_reason(self, client: AsyncClient, auth_token):
        await client.post(
            "/api/v1/crypto/keys/generate",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        issue_resp = await client.post(
            "/api/v1/certificates/issue",
            json={"subject_name": "No Reason"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        cert_id = issue_resp.json()["id"]

        resp = await client.post(
            f"/api/v1/certificates/{cert_id}/revoke",
            json={},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200

    async def test_revoke_other_user_certificate(self, client: AsyncClient, auth_token):
        await client.post(
            "/api/v1/crypto/keys/generate",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        issue_resp = await client.post(
            "/api/v1/certificates/issue",
            json={"subject_name": "Other Owner"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        cert_id = issue_resp.json()["id"]

        import uuid

        other_email = f"other-{uuid.uuid4().hex[:12]}@example.com"
        await client.post(
            "/api/v1/auth/register",
            json={"name": "Other", "email": other_email, "password": "OtherPass1!"},
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": other_email, "password": "OtherPass1!"},
        )
        other_token = login_resp.json()["access_token"]

        resp = await client.post(
            f"/api/v1/certificates/{cert_id}/revoke",
            json={},
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert resp.status_code == 404


@pytest.mark.asyncio
class TestVerifyCertificate:
    async def test_verify_invalid_pem(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/certificates/verify",
            json={"certificate_pem": "not-a-valid-cert"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is False
        assert "Invalid certificate" in data["reason"]

    async def test_verify_public_endpoint(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/certificates/verify",
            json={"certificate_pem": "invalid"},
        )
        assert resp.status_code == 200

    async def test_verify_valid_certificate(self, client: AsyncClient, auth_token):
        await client.post(
            "/api/v1/crypto/keys/generate",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        await client.post(
            "/api/v1/certificates/issue",
            json={"subject_name": "Verify Test"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        resp = await client.post(
            "/api/v1/certificates/verify",
            json={"certificate_pem": "-----BEGIN CERTIFICATE-----\nMIIB\n-----END CERTIFICATE-----"},
        )
        assert resp.status_code == 200
        assert resp.json()["valid"] is False


@pytest.mark.asyncio
class TestCheckCertificate:
    async def test_check_active(self, client: AsyncClient, auth_token):
        await client.post(
            "/api/v1/crypto/keys/generate",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        issue_resp = await client.post(
            "/api/v1/certificates/issue",
            json={"subject_name": "Check Test"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        cert_id = issue_resp.json()["id"]

        resp = await client.get(
            f"/api/v1/certificates/check/{cert_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
        assert data["status"] == "active"

    async def test_check_revoked(self, client: AsyncClient, auth_token):
        await client.post(
            "/api/v1/crypto/keys/generate",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        issue_resp = await client.post(
            "/api/v1/certificates/issue",
            json={"subject_name": "Check Revoked"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        cert_id = issue_resp.json()["id"]

        await client.post(
            f"/api/v1/certificates/{cert_id}/revoke",
            json={},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        resp = await client.get(
            f"/api/v1/certificates/check/{cert_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is False
        assert data["status"] == "revoked"

    async def test_check_not_found(self, client: AsyncClient, auth_token):
        resp = await client.get(
            "/api/v1/certificates/check/9999",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 404

    async def test_check_unauthorized(self, client: AsyncClient):
        resp = await client.get("/api/v1/certificates/check/1")
        assert resp.status_code == 401
