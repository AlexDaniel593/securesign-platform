"""Synchronous disk I/O utilities for document file storage.

Pattern: uploads/{user_id}/{uuid}_{original_filename}.pdf
All paths returned are relative to the project root / current working directory.
"""

import uuid
from pathlib import Path


def ensure_user_dir(base_dir: Path, user_id: int) -> Path:
    """Create and return uploads/{user_id}/ directory under base_dir."""
    user_dir = base_dir / "uploads" / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def save_file(base_dir: Path, user_id: int, filename: str, content: bytes) -> str:
    """Save file bytes to disk and return the relative path.

    The filename is prefixed with a UUID to avoid collisions: {uuid}_{filename}.
    """
    user_dir = ensure_user_dir(base_dir, user_id)
    safe_name = f"{uuid.uuid4()}_{filename}"
    file_path = user_dir / safe_name
    file_path.write_bytes(content)
    return str(file_path)


def read_file(file_path: str) -> bytes:
    """Read and return file bytes from disk."""
    return Path(file_path).read_bytes()


def delete_file(file_path: str) -> None:
    """Delete the file at file_path if it exists."""
    p = Path(file_path)
    if p.exists():
        p.unlink()
