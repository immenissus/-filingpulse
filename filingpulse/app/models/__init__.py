"""
app/models/__init__.py
======================
Exposes all SQLAlchemy models in a single module.
Required for Alembic to autogenerate tables correctly.
"""

from app.models.base import Base, TimestampMixin
from app.models.jurisdiction import Jurisdiction
from app.models.subscriber import Subscriber
from app.models.filing import Filing
from app.models.quarantined_filing import QuarantinedFiling
from app.models.alert_sent import AlertSent

__all__ = [
    "Base",
    "TimestampMixin",
    "Jurisdiction",
    "Subscriber",
    "Filing",
    "QuarantinedFiling",
    "AlertSent",
]
