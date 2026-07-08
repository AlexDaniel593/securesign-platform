## Stack Tecnológico

| Componente | Tecnología | Versión | Propósito |
|------------|------------|---------|------------|
| Framework | FastAPI | 0.104+ | API REST asíncrona |
| Lenguaje | Python | 3.11+ | Lógica de negocio y criptografía |
| ORM | SQLModel | 0.0.14+ | Modelado de BD + schemas Pydantic |
| Driver BD | asyncpg | 0.29+ | Conexión asíncrona a PostgreSQL |
| Base de Datos | PostgreSQL | 15 | Persistencia de datos |
| Criptografía | cryptography | 41.0+ | AES, RSA, SHA-256 |
| JWT | python-jose | 3.3+ | Generación y validación de tokens |
| Variables entorno | python-dotenv | 1.0+ | Gestión de .env |
| Migraciones | Alembic | 1.12+ | Control de versiones de BD |

## Estructura de Carpetas

```text
backend/
├── app/
│   ├── __init__.py
│   │
│   ├── api/                                 # Endpoints de la API
│   │   └── v1/                              # Versión 1
│   │       ├── __init__.py
│   │       ├── auth.py                      # POST /auth/register, /auth/login, /auth/me
│   │       ├── crypto.py                    # POST /crypto/hash, /crypto/sign, /crypto/verify
│   │       ├── certificates.py              # POST /certificates/issue, /certificates/revoke
│   │       ├── documents.py                 # POST /documents/upload, GET /documents
│   │       └── audit.py                     # ⏳ GET /audit/logs (pendiente)
│   │
│   ├── core/                                # Núcleo de seguridad y criptografía
│   │   ├── __init__.py
│   │   ├── config.py                        # Variables de entorno (SECRET_KEY, AES_KEY, DATABASE_URL)
│   │   ├── security.py                      # JWT (create_token, decode_token, get_current_user)
│   │   ├── crypto.py                        # SHA-256, AES-256, RSA-2048
│   │   └── ca.py                            # CA simulada (emitir, firmar, validar certificados X.509)
│   │
│   ├── db/                                  # Base de datos con SQLModel
│   │   ├── __init__.py
│   │   ├── database.py                      # Engine, async session, get_db() dependency
│   │   └── models.py                        # Modelos SQLModel (User, UserKey, Certificate, Document, Signature, AuditLog)
│   │
│   ├── dependencies/                        # Dependencias de FastAPI (inyección)
│   │   ├── __init__.py
│   │   ├── auth.py                          # get_current_user, get_current_admin_user
│   │   ├── database.py                      # get_db (inyecta sesión de BD)
│   │   └── logging.py                       # log_action (registra acción en BD)
│   │
│   ├── middleware/                          # Middlewares de FastAPI
│   │   ├── __init__.py
│   │   ├── logging.py                       # Logging middleware (IP, método, endpoint, tiempo)
│   │   ├── security.py                      # Security headers (CORS, CSP, HSTS)
│   │   └── error_handler.py                 # Manejo global de excepciones
│   │
│   ├── services/                            # Lógica de negocio compleja
│   │   ├── __init__.py
│   │   ├── crypto_service.py                # Firma, verificación, hash, cifrado/descifrado
│   │   ├── cert_service.py                  # Emisión, revocación, validación de certificados
│   │   ├── document_service.py              # Subida, almacenamiento, eliminación de documentos
│   │   └── audit_service.py                 # Registro de logs (⏳)
│   │
│   └── utils/                               # Utilidades varias
│       ├── __init__.py
│       ├── file_handlers.py                 # Guardar/leer/eliminar documentos en disco
│       └── validators.py                    # Validaciones (email, tamaño archivo, tipo archivo)
│
├── uploads/                                 # Directorio para documentos (montado en disco)
│   └── {user_id}/                           # Carpeta por usuario
│       └── {uuid}_{original_filename}.pdf   # Documento almacenado
│
├── alembic/                                 # Migraciones Alembic
│   ├── versions/
│   └── alembic.ini
│
├── .env                                     # Variables de entorno (NO commitear)
├── .env.example                             # Plantilla de variables de entorno
├── .gitignore                               # Ignorar .env, uploads/, __pycache__, etc.
├── requirements.txt                         # Dependencias del proyecto
├── Dockerfile                               # Build de la imagen Docker
├── docker-compose.yml                       # Orquestación de servicios
└── main.py                                  # Entry point: FastAPI app
```
db/models.py
```python
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime, timezone
from typing import Optional, List
import uuid

# Tabla: users
class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    password_hash: str = Field(max_length=255)
    salt: str = Field(max_length=64)
    is_admin: bool = Field(default=False)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    user_keys: List["UserKey"] = Relationship(back_populates="user")
    certificates: List["Certificate"] = Relationship(back_populates="user")
    documents: List["Document"] = Relationship(back_populates="user")
    signatures: List["Signature"] = Relationship(back_populates="user")
    audit_logs: List["AuditLog"] = Relationship(back_populates="user")

# Tabla: user_keys (claves RSA cifradas)
class UserKey(SQLModel, table=True):
    __tablename__ = "user_keys"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    private_key_encrypted: str = Field(max_length=4096)  # Cifrada con AES
    public_key: str = Field(max_length=2048)
    fingerprint: str = Field(max_length=64, unique=True)  # SHA-256 de la pública
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_used: Optional[datetime] = None
    
    # Relaciones
    user: User = Relationship(back_populates="user_keys")

# Tabla: certificates
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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    user: User = Relationship(back_populates="certificates")

# Tabla: documents
class Document(SQLModel, table=True):
    __tablename__ = "documents"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    filename: str = Field(max_length=255)
    file_path: str = Field(max_length=512)  # Ruta en disco
    file_size: int  # Bytes
    sha256_hash: str = Field(max_length=64, index=True)
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    user: User = Relationship(back_populates="documents")
    signatures: List["Signature"] = Relationship(back_populates="document")

# Tabla: signatures
class Signature(SQLModel, table=True):
    __tablename__ = "signatures"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="documents.id")
    user_id: int = Field(foreign_key="users.id")
    certificate_id: Optional[int] = Field(foreign_key="certificates.id")
    signature_blob: str = Field(max_length=1024)  # Base64
    signed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    verified_at: Optional[datetime] = None
    is_valid: Optional[bool] = None
    
    # Relaciones
    document: Document = Relationship(back_populates="signatures")
    user: User = Relationship(back_populates="signatures")
    certificate: Optional["Certificate"] = Relationship()

# Tabla: audit_logs
class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")  # NULL si no autenticado
    action: str = Field(max_length=100)  # LOGIN_SUCCESS, SIGN_DOCUMENT, etc.
    resource_type: Optional[str] = Field(max_length=50)  # user, document, certificate
    resource_id: Optional[str] = Field(max_length=255)
    ip_address: Optional[str] = Field(max_length=45)  # IPv4 o IPv6
    user_agent: Optional[str] = Field(max_length=512)
    details: Optional[str] = None  # JSON string
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relaciones
    user: Optional[User] = Relationship(back_populates="audit_logs")
```
## Tabla completa de endpoints

| Metodo | Endpoint | Autenticacion | Request Body | Response | Descripcion |
|--------|----------|---------------|--------------|----------|-------------|
| POST | /auth/register | No | { email, password } | { id, email, created_at } | Registrar nuevo usuario |
| POST | /auth/login | No | { email, password } | { access_token, token_type, user } | Login devuelve JWT |
| GET | /auth/me | Si (JWT) | - | { id, email, is_admin, created_at } | Obtener perfil propio |
| POST | /auth/logout | Si (JWT) | - | { message } | Logout opcional |
| PUT | /auth/change-password | Si (JWT) | { current_password, new_password } | { message } | Cambiar contrasena |
| POST | /crypto/hash | Si (JWT) | { content_base64, filename? } | { sha256_hash, filename, size } | Calcular SHA-256 |
| POST | /crypto/sign | Si (JWT) | { document_hash, certificate_id? } | { signature, signed_at, certificate_id } | Firmar hash con RSA |
| POST | /crypto/verify | No | { document_hash, signature, public_key } | { valid, message } | Verificar firma |
| POST | /crypto/encrypt | Si (JWT) | { content_base64, password? } | { encrypted_base64, iv } | Cifrar con AES-256 |
| POST | /crypto/decrypt | Si (JWT) | { encrypted_base64, iv, password? } | { decrypted_base64 } | Descifrar con AES-256 |
| GET | /crypto/keys/status | Si (JWT) | - | { has_keys, fingerprint? } | Verificar si tiene claves RSA |
| POST | /crypto/keys/generate | Si (JWT) | - | { fingerprint, message } | Generar nuevo par RSA |
| POST | /certificates/issue | Si (JWT) | { subject_name, validity_days? } | { id, subject, issuer, valid_from, valid_to, fingerprint } | Emitir certificado digital |
| GET | /certificates | Si (JWT) | Query: ?revoked=false | { items: [...], total } | Listar certificados del usuario |
| GET | /certificates/{id} | Si (JWT) | - | { id, subject, public_key, issuer, valid_from, valid_to, revoked } | Obtener detalle de certificado |
| POST | /certificates/{id}/revoke | Si (JWT) | { reason? } | { message, revoked_at } | Revocar certificado |
| POST | /certificates/verify | No | { certificate_pem, document_hash?, signature? } | { valid, reason, expires_in_days } | Validar certificado |
| GET | /certificates/check/{id} | Si (JWT) | - | { valid, status } | Verificar estado de certificado |
| POST | /documents/upload | Si (JWT) | multipart/form-data: file | { id, filename, sha256_hash, file_size, uploaded_at } | Subir documento |
| GET | /documents | Si (JWT) | Query: ?page=1&limit=20 | { items: [...], total, page, limit } | Listar documentos paginado |
| GET | /documents/{id} | Si (JWT) | - | { id, filename, file_size, sha256_hash, uploaded_at } | Obtener metadata del documento |
| GET | /documents/{id}/download | Si (JWT) | - | application/octet-stream | Descargar archivo original |
| DELETE | /documents/{id} | Si (JWT) | - | { message } | Eliminar documento |
| PUT | /documents/{id} | Si (JWT) | { filename? } | { id, filename, updated_at } | Actualizar metadata |
| POST | /documents/{id}/sign | Si (JWT) | { certificate_id? } | { signature_id, signature, signed_at } | Firmar documento existente |
| GET | /documents/{id}/signatures | Si (JWT) | - | { signatures: [...] } | Listar firmas del documento |

## Endpoints pendientes (requieren decision del docente)

| Metodo | Endpoint | Autenticacion | Permiso | Response | Descripcion |
|--------|----------|---------------|---------|----------|-------------|
| GET | /audit/logs | Si (JWT) | Usuario normal | { items: [...] } | Ver los propios logs del usuario |
| GET | /audit/logs/all | Si (JWT) | Admin | { items: [...] } | Ver todos los logs del sistema |
| GET | /audit/metrics | Si (JWT) | Admin | { total_users, total_docs, total_signatures, failed_logins } | Metricas globales |
| GET | /admin/users | Si (JWT) | Admin | { items: [...] } | Listar todos los usuarios |
| GET | /admin/users/{id} | Si (JWT) | Admin | { id, email, is_admin, created_at, is_active } | Ver detalle de usuario |
| DELETE | /admin/users/{id} | Si (JWT) | Admin | { message } | Eliminar cualquier usuario |

## Resumen de endpoints

| Categoria           | Cantidad |
| ------------------- | -------- |
| Autenticacion       | 5        |
| Criptografia        | 7        |
| Certificados        | 6        |
| Documentos          | 9        |
| Subtotal definidos  | 27       |
| Auditoria pendiente | 3        |
| Admin pendiente     | 3        |
| Total potencial     | 33       |