import base64

import pytest
from httpx import AsyncClient

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
from app.services.crypto_service import (
    compute_hash,
    decrypt_content,
    encrypt_content,
    verify_signature,
)

AES_KEY = bytes.fromhex("01" * 32)


class TestSHA256:
    def test_hash_sha256_known_value(self):
        result = hash_sha256(b"hello")
        assert result == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"

    def test_hash_sha256_empty(self):
        result = hash_sha256(b"")
        assert result == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    def test_hash_sha256_different_inputs(self):
        assert hash_sha256(b"a") != hash_sha256(b"b")


class TestRSA:
    def test_generate_keypair_returns_keys(self):
        private, public = generate_rsa_keypair()
        assert private.startswith(b"-----BEGIN PRIVATE KEY-----")
        assert public.startswith(b"-----BEGIN PUBLIC KEY-----")

    def test_sign_and_verify(self):
        private, public = generate_rsa_keypair()
        data = b"test data to sign"
        signature = rsa_sign(private, data)
        assert rsa_verify(public, data, signature) is True

    def test_verify_wrong_data(self):
        private, public = generate_rsa_keypair()
        data = b"test data"
        signature = rsa_sign(private, data)
        assert rsa_verify(public, b"wrong data", signature) is False

    def test_verify_wrong_signature(self):
        private, public = generate_rsa_keypair()
        data = b"test data"
        signature = rsa_sign(private, data)
        tampered = bytearray(signature)
        tampered[0] ^= 0xFF
        assert rsa_verify(public, data, bytes(tampered)) is False

    def test_compute_fingerprint(self):
        private, public = generate_rsa_keypair()
        fp = compute_fingerprint(public)
        assert len(fp) == 64
        assert isinstance(fp, str)

    def test_encrypt_decrypt_private_key(self):
        private, public = generate_rsa_keypair()
        encrypted = encrypt_private_key(private, AES_KEY)
        decrypted = decrypt_private_key(encrypted, AES_KEY)
        assert decrypted == private

    def test_different_keys_different_fingerprints(self):
        _, pub1 = generate_rsa_keypair()
        _, pub2 = generate_rsa_keypair()
        assert compute_fingerprint(pub1) != compute_fingerprint(pub2)


class TestAES:
    def test_encrypt_decrypt(self):
        plaintext = b"Hello, SecureSign!"
        ciphertext, iv = aes_encrypt(plaintext, AES_KEY)
        decrypted = aes_decrypt(ciphertext, AES_KEY, iv)
        assert decrypted == plaintext

    def test_encrypt_different_ivs(self):
        pt = b"Same plaintext"
        ct1, iv1 = aes_encrypt(pt, AES_KEY)
        ct2, iv2 = aes_encrypt(pt, AES_KEY)
        assert ct1 != ct2
        assert iv1 != iv2

    def test_encrypt_decrypt_empty(self):
        ciphertext, iv = aes_encrypt(b"", AES_KEY)
        decrypted = aes_decrypt(ciphertext, AES_KEY, iv)
        assert decrypted == b""


class TestCryptoService:
    def test_compute_hash(self):
        content = b"Hello, World!"
        content_b64 = base64.b64encode(content).decode()
        result = compute_hash(content_b64, filename="test.txt")
        assert result["sha256_hash"] == hash_sha256(content)
        assert result["filename"] == "test.txt"
        assert result["size"] == len(content)

    def test_compute_hash_no_filename(self):
        content = base64.b64encode(b"data").decode()
        result = compute_hash(content)
        assert result["filename"] is None
        assert result["size"] == 4

    def test_encrypt_decrypt_roundtrip(self):
        plaintext = b"Secret message"
        b64 = base64.b64encode(plaintext).decode()
        encrypted = encrypt_content(b64)
        assert "encrypted_base64" in encrypted
        assert "iv" in encrypted

        decrypted = decrypt_content(encrypted["encrypted_base64"], encrypted["iv"])
        assert decrypted["decrypted_base64"] == b64

    def test_verify_signature_valid(self):
        private, public = generate_rsa_keypair()
        data = b"verify me"
        data_hash = hash_sha256(data)
        data_hash_bytes = bytes.fromhex(data_hash)
        signature = rsa_sign(private, data_hash_bytes)
        signature_b64 = base64.b64encode(signature).decode()

        result = verify_signature(data_hash, signature_b64, public.decode())
        assert result["valid"] is True

    def test_verify_signature_invalid(self):
        private, public = generate_rsa_keypair()
        data = b"verify me"
        data_hash = hash_sha256(data)
        data_hash_bytes = bytes.fromhex(data_hash)
        signature = rsa_sign(private, b"different data")
        signature_b64 = base64.b64encode(signature).decode()

        result = verify_signature(data_hash, signature_b64, public.decode())
        assert result["valid"] is False


@pytest.mark.asyncio
class TestCryptoAPI:
    async def test_hash_endpoint(self, client: AsyncClient, auth_token):
        content = base64.b64encode(b"test content").decode()
        resp = await client.post(
            "/api/v1/crypto/hash",
            json={"content_base64": content, "filename": "test.txt"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "sha256_hash" in data
        assert data["filename"] == "test.txt"

    async def test_hash_unauthenticated(self, client: AsyncClient):
        content = base64.b64encode(b"test").decode()
        resp = await client.post(
            "/api/v1/crypto/hash", json={"content_base64": content}
        )
        assert resp.status_code == 401

    async def test_key_generation(self, client: AsyncClient, auth_token):
        resp = await client.post(
            "/api/v1/crypto/keys/generate",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "fingerprint" in data
        assert "generated" in data["message"].lower()

    async def test_key_status(self, client: AsyncClient, auth_token):
        resp = await client.get(
            "/api/v1/crypto/keys/status",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "has_keys" in data

    async def test_encrypt_endpoint(self, client: AsyncClient, auth_token):
        content = base64.b64encode(b"secret data").decode()
        resp = await client.post(
            "/api/v1/crypto/encrypt",
            json={"content_base64": content},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "encrypted_base64" in data
        assert "iv" in data

    async def test_decrypt_endpoint(self, client: AsyncClient, auth_token):
        content = base64.b64encode(b"roundtrip data").decode()
        enc_resp = await client.post(
            "/api/v1/crypto/encrypt",
            json={"content_base64": content},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        enc_data = enc_resp.json()

        resp = await client.post(
            "/api/v1/crypto/decrypt",
            json={
                "encrypted_base64": enc_data["encrypted_base64"],
                "iv": enc_data["iv"],
            },
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["decrypted_base64"] == content

    async def test_verify_endpoint(self, client: AsyncClient):
        private, public = generate_rsa_keypair()
        data = b"verify test"
        data_hash = hash_sha256(data)
        data_hash_bytes = bytes.fromhex(data_hash)
        signature = rsa_sign(private, data_hash_bytes)
        signature_b64 = base64.b64encode(signature).decode()

        resp = await client.post(
            "/api/v1/crypto/verify",
            json={
                "document_hash": data_hash,
                "signature": signature_b64,
                "public_key": public.decode(),
            },
        )
        assert resp.status_code == 200
        assert resp.json()["valid"] is True

    async def test_sign_without_keys(self, client: AsyncClient, auth_token):
        resp = await client.post(
            "/api/v1/crypto/sign",
            json={"document_hash": "aa" * 32},
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 400
        assert "key" in resp.json()["detail"].lower()
