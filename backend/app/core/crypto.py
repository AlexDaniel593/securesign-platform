import base64
import hashlib
import os

from cryptography.hazmat.primitives import hashes, padding, serialization
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def hash_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def generate_rsa_keypair() -> tuple[bytes, bytes]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem, public_pem


def rsa_sign(private_key_pem: bytes, data: bytes) -> bytes:
    private_key = serialization.load_pem_private_key(private_key_pem, password=None)
    return private_key.sign(data, asym_padding.PKCS1v15(), hashes.SHA256())


def rsa_verify(public_key_pem: bytes, data: bytes, signature: bytes) -> bool:
    try:
        public_key = serialization.load_pem_public_key(public_key_pem)
        public_key.verify(signature, data, asym_padding.PKCS1v15(), hashes.SHA256())
        return True
    except Exception:
        return False


def aes_encrypt(plaintext: bytes, key: bytes) -> tuple[bytes, bytes]:
    iv = os.urandom(16)
    padder = padding.PKCS7(128).padder()
    padded = padder.update(plaintext) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()
    return ciphertext, iv


def aes_decrypt(ciphertext: bytes, key: bytes, iv: bytes) -> bytes:
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return unpadder.update(padded) + unpadder.finalize()


def encrypt_private_key(private_pem: bytes, key: bytes) -> str:
    ciphertext, iv = aes_encrypt(private_pem, key)
    combined = iv + ciphertext
    return base64.b64encode(combined).decode()


def decrypt_private_key(encrypted_b64: str, key: bytes) -> bytes:
    combined = base64.b64decode(encrypted_b64)
    iv = combined[:16]
    ciphertext = combined[16:]
    return aes_decrypt(ciphertext, key, iv)


def compute_fingerprint(public_key_pem: bytes) -> str:
    return hashlib.sha256(public_key_pem).hexdigest()
