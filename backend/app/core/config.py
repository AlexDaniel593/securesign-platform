from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "SecureSign"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/securesign"

    SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60

    AES_KEY: str = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"

    CA_COUNTRY: str = "EC"
    CA_STATE: str = "Pichincha"
    CA_LOCALITY: str = "Quito"
    CA_ORG: str = "ESPE"
    CA_ORG_UNIT: str = "Seguridad"
    CA_COMMON_NAME: str = "CA_SIMULADA"
    CA_VALIDITY_DAYS: int = 365

    MINIO_ENDPOINT: str = "http://localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "securesign-documents"
    MINIO_SECURE: bool = False

    ADMIN_EMAIL: str = "admin@securesign.com"
    ADMIN_PASSWORD: str = "Admin123!"
    ADMIN_NAME: str = "Administrador"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
