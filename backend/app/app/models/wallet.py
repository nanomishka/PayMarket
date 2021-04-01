import datetime
import uuid

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import Numeric

from app.core.config import settings
from app.db.base_class import Base


class Wallet(Base):
    id = Column(Integer, primary_key=True)
    idempotency_key = Column(UUID(as_uuid=True), unique=True)

    wallet_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        unique=True,
        index=True,
        default=uuid.uuid4,
    )
    amount = Column(
        Numeric(scale=settings.CURRENCY_SCALE),
        nullable=False,
        default=0,
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.datetime.utcnow,
    )
    updated_at = Column(DateTime)
