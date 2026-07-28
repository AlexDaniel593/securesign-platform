"""Timezone utilities for database-safe datetime handling.

All PostgreSQL columns in this project are TIMESTAMP WITHOUT TIME ZONE
(naive). Any timezone-aware datetime assigned to a naive column causes
asyncpg to raise `DataError: can't subtract offset-naive and
offset-aware datetimes`. SQLite (used in tests) is lenient about this,
which is why the bug was invisible in the test suite and only
surfaced against real Postgres.

Use these helpers at every DB write/comparison boundary instead of
`datetime.utcnow()` (naive but deprecated since Python 3.12) or
`datetime.now(timezone.utc)` (aware, unsafe for naive columns).
"""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return the current UTC time as a naive datetime, safe for DB storage."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_naive_utc(dt: datetime) -> datetime:
    """Convert a timezone-aware datetime to naive UTC. No-op if already naive."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
        return dt.replace(tzinfo=None)
    return dt
