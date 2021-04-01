import datetime

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Numeric

from app.core.config import settings
from app.db.base_class import Base


class Transaction(Base):
    id = Column(Integer, primary_key=True)
    idempotency_key = Column(UUID(as_uuid=True), unique=True)
    amount = Column(Numeric(scale=settings.CURRENCY_SCALE))

    from_wallet_id = Column(
        UUID(as_uuid=True), ForeignKey("wallet.wallet_id"), index=True,
    )
    from_wallet_amount = Column(Numeric(scale=settings.CURRENCY_SCALE))

    to_wallet_id = Column(
        UUID(as_uuid=True), ForeignKey("wallet.wallet_id"), index=True,
    )
    to_wallet_amount = Column(Numeric(scale=settings.CURRENCY_SCALE))

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.datetime.utcnow,
    )
