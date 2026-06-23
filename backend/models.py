"""SQLAlchemy models.

Models are introduced per migration group defined in ``database/migrations``.
The database owner keeps this module aligned with ``database/schema.sql``.
"""

from database import Base

__all__ = ["Base"]

