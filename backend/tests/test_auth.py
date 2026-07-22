import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestRegister:
    async def test_register_success(self, client: AsyncClient):
        payload = {"name": "Test User", "email": "test@example.com", "password": "SecurePass1!"}
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["name"] == "Test User"

    async def test_register_duplicate_email(self, client: AsyncClient):
        payload = {"name": "Dup User", "email": "dup@example.com", "password": "SecurePass1!"}
        await client.post("/api/v1/auth/register", json=payload)
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 409
        assert "already registered" in resp.json()["detail"].lower()

    async def test_register_weak_password_no_upper(self, client: AsyncClient):
        payload = {"name": "Weak User", "email": "weak@example.com", "password": "securepass1!"}
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 422

    async def test_register_weak_password_no_lower(self, client: AsyncClient):
        payload = {"name": "Weak2 User", "email": "weak2@example.com", "password": "SECUREPASS1!"}
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 422

    async def test_register_weak_password_no_number(self, client: AsyncClient):
        payload = {"name": "Weak3 User", "email": "weak3@example.com", "password": "SecurePass!"}
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 422

    async def test_register_weak_password_no_special(self, client: AsyncClient):
        payload = {"name": "Weak4 User", "email": "weak4@example.com", "password": "SecurePass1"}
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 422

    async def test_register_short_password(self, client: AsyncClient):
        payload = {"name": "Short User", "email": "short@example.com", "password": "Sh0rt!"}
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 422

    async def test_register_invalid_email(self, client: AsyncClient):
        payload = {"name": "Bad Email", "email": "not-an-email", "password": "SecurePass1!"}
        resp = await client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestLogin:
    async def test_login_success(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/register",
            json={"name": "Login User", "email": "login@example.com", "password": "SecurePass1!"},
        )
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "SecurePass1!"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "login@example.com"

    async def test_login_wrong_password(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/register",
            json={"name": "WrongPW User", "email": "wrongpw@example.com", "password": "SecurePass1!"},
        )
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "wrongpw@example.com", "password": "WrongPass1!"},
        )
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "SecurePass1!"},
        )
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestMe:
    async def test_me_authenticated(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/register",
            json={"name": "Me User", "email": "me@example.com", "password": "SecurePass1!"},
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "me@example.com", "password": "SecurePass1!"},
        )
        token = login_resp.json()["access_token"]

        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == "me@example.com"

    async def test_me_unauthenticated(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    async def test_me_invalid_token(self, client: AsyncClient):
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalidtoken"},
        )
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestLogout:
    async def test_logout_authenticated(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/register",
            json={"email": "logout@example.com", "password": "SecurePass1!"},
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "logout@example.com", "password": "SecurePass1!"},
        )
        token = login_resp.json()["access_token"]

        resp = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert "successful" in resp.json()["message"].lower()

    async def test_logout_unauthenticated(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/logout")
        assert resp.status_code == 401


@pytest.mark.asyncio
class TestChangePassword:
    async def test_change_password_success(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/register",
            json={"name": "ChangePW User", "email": "changepw@example.com", "password": "SecurePass1!"},
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "changepw@example.com", "password": "SecurePass1!"},
        )
        token = login_resp.json()["access_token"]

        resp = await client.put(
            "/api/v1/auth/change-password",
            json={"current_password": "SecurePass1!", "new_password": "NewSecure1!"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

        login_resp2 = await client.post(
            "/api/v1/auth/login",
            json={"email": "changepw@example.com", "password": "NewSecure1!"},
        )
        assert login_resp2.status_code == 200

    async def test_change_password_wrong_current(self, client: AsyncClient):
        await client.post(
            "/api/v1/auth/register",
            json={"name": "WrongPW2 User", "email": "wrongpw2@example.com", "password": "SecurePass1!"},
        )
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "wrongpw2@example.com", "password": "SecurePass1!"},
        )
        token = login_resp.json()["access_token"]

        resp = await client.put(
            "/api/v1/auth/change-password",
            json={"current_password": "WrongPass1!", "new_password": "NewSecure1!"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400

    async def test_change_password_unauthenticated(self, client: AsyncClient):
        resp = await client.put(
            "/api/v1/auth/change-password",
            json={"current_password": "SecurePass1!", "new_password": "NewSecure1!"},
        )
        assert resp.status_code == 401
