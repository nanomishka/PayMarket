import decimal
import uuid

from pydantic import BaseModel, condecimal

from app.core.config import settings


class WalletGetRequest(BaseModel):
    wallet_id: uuid.UUID


class WalletResponse(BaseModel):
    wallet_id: uuid.UUID
    amount: decimal.Decimal


class WalletDonateRequest(BaseModel):
    wallet_id: uuid.UUID
    amount: condecimal(gt=0, decimal_places=settings.CURRENCY_SCALE)


class WalletTransferRequest(BaseModel):
    from_wallet_id: uuid.UUID
    to_wallet_id: uuid.UUID
    amount: condecimal(gt=0, decimal_places=settings.CURRENCY_SCALE)
