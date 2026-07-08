from datetime import datetime
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    password_hash: str = Field(max_length=255)
    salt: str = Field(max_length=64)
    is_admin: bool = Field(default=False)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

    user_keys: List["UserKey"] = Relationship(back_populates="user")
    certificates: List["Certificate"] = Relationship(back_populates="user")
    documents: List["Document"] = Relationship(back_populates="user")
    signatures: List["Signature"] = Relationship(back_populates="user")
    audit_logs: List["AuditLog"] = Relationship(back_populates="user")


class UserKey(SQLModel, table=True):
    __tablename__ = "user_keys"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    private_key_encrypted: str = Field(max_length=4096)
    public_key: str = Field(max_length=2048)
    fingerprint: str = Field(max_length=64, unique=True)
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    last_used: Optional[datetime] = None

    user: User = Relationship(back_populates="user_keys")


class Certificate(SQLModel, table=True):
    __tablename__ = "certificates"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    subject_name: str = Field(max_length=255)
    public_key: str = Field(max_length=2048)
    issuer: str = Field(max_length=255, default="CA_SIMULADA")
    serial_number: str = Field(unique=True, index=True)
    valid_from: datetime
    valid_to: datetime
    revoked: bool = Field(default=False)
    revoked_at: Optional[datetime] = None
    revocation_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

    user: User = Relationship(back_populates="certificates")


class Document(SQLModel, table=True):
    __tablename__ = "documents"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    filename: str = Field(max_length=255)
    file_path: str = Field(max_length=512)
    file_size: int
    sha256_hash: str = Field(max_length=64, index=True)
    uploaded_at: datetime = Field(default_factory=lambda: datetime.utcnow())

    user: User = Relationship(back_populates="documents")
    signatures: List["Signature"] = Relationship(back_populates="document")


class Signature(SQLModel, table=True):
    __tablename__ = "signatures"

    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="documents.id")
    user_id: int = Field(foreign_key="users.id")
    certificate_id: Optional[int] = Field(default=None, foreign_key="certificates.id")
    signature_blob: str = Field(max_length=1024)
    signed_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    verified_at: Optional[datetime] = None
    is_valid: Optional[bool] = None

    document: Document = Relationship(back_populates="signatures")
    user: User = Relationship(back_populates="signatures")
    certificate: Optional[Certificate] = Relationship()


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    action: str = Field(max_length=100)
    resource_type: Optional[str] = Field(max_length=50)
    resource_id: Optional[str] = Field(max_length=255)
    ip_address: Optional[str] = Field(max_length=45)
    user_agent: Optional[str] = Field(max_length=512)
    details: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())

    user: Optional[User] = Relationship(back_populates="audit_logs")
