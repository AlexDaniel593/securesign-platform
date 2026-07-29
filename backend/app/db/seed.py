import secrets

from sqlmodel import select

from app.core.config import settings
from app.core.security import hash_password
from app.core.time_utils import utc_now
from app.db.database import async_session
from app.db.models import User


async def seed_admin() -> None:
    """Create the admin user from env vars if it doesn't already exist."""
    async with async_session() as db:
        result = await db.execute(
            select(User).where(User.email == settings.ADMIN_EMAIL)
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            return

        salt = secrets.token_hex(32)
        password_hash = hash_password(settings.ADMIN_PASSWORD)

        admin = User(
            name=settings.ADMIN_NAME,
            email=settings.ADMIN_EMAIL,
            password_hash=password_hash,
            salt=salt,
            is_admin=True,
            is_active=True,
            created_at=utc_now(),
        )
        db.add(admin)
        await db.commit()
        print(f"[seed] Admin user created: {settings.ADMIN_EMAIL}")
