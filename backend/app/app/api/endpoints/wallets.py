import uuid

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Header
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.db.helper import DBHelper
from app.schemas import WalletGetRequest
from app.schemas import WalletResponse
from app.schemas import WalletDonateRequest
from app.schemas import WalletTransferRequest

router = APIRouter()


@router.post('/v1/wallet/create', response_model=WalletResponse)
def v1_wallet_create(
    db: Session = Depends(get_db_session),
    idempotency_key: uuid.UUID = Header(...),
):
    return DBHelper.wallet_create(db, idempotency_key)


@router.post('/v1/wallet/get', response_model=WalletResponse)
def v1_wallet_get(
    request: WalletGetRequest,
    db: Session = Depends(get_db_session),
):
    return DBHelper.wallet_get(db, request.wallet_id)


@router.post('/v1/wallet/donate', response_model=WalletResponse)
def v1_wallet_donate(
    request: WalletDonateRequest,
    idempotency_key: uuid.UUID = Header(...),
    db: Session = Depends(get_db_session),
):
    return DBHelper.wallet_donate(db, idempotency_key, request)


@router.post('/v1/wallet/transfer', response_model=WalletResponse)
def v1_wallet_transfer(
    request: WalletTransferRequest,
    idempotency_key: uuid.UUID = Header(...),
    db: Session = Depends(get_db_session),
):
    if request.from_wallet_id == request.to_wallet_id:
        raise HTTPException(
            status_code=400,
            detail='self-transfer is not possible',
        )
    return DBHelper.wallet_transfer(db, idempotency_key, request)
