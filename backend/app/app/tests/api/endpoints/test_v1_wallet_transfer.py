import uuid
from decimal import Decimal
from typing import Dict
from typing import Any

from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models import Wallet
from app.models import Transaction

IDEMPOTENCY_KEY = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
HEADERS = {'Idempotency-Key': IDEMPOTENCY_KEY}
FROM_WALLET_ID = '11111111-1111-1111-1111-111111111111'
TO_WALLET_ID = '22222222-2222-2222-2222-222222222222'


def check_db_wallet(db: Session, wallet: Dict[str, Any], has_updated_at=True):
    db_wallet = (
        db.query(Wallet)
        .filter(Wallet.wallet_id == wallet['wallet_id'])
        .first()
    )
    assert not db_wallet.idempotency_key
    assert db_wallet.amount == Decimal(str(wallet['amount']))
    assert bool(db_wallet.updated_at) == has_updated_at


def test_wallet_transfer(client: TestClient, db: Session) -> None:
    db_from_wallet = {'wallet_id': FROM_WALLET_ID, 'amount': 25.3}
    db_to_wallet = {'wallet_id': TO_WALLET_ID, 'amount': 10.01}
    db.add(Wallet(**db_from_wallet))
    db.add(Wallet(**db_to_wallet))
    db.commit()

    request = {
        'from_wallet_id': FROM_WALLET_ID,
        'to_wallet_id': TO_WALLET_ID,
        'amount': 7.12,
    }
    from_wallet_expected = {'wallet_id': FROM_WALLET_ID, 'amount': 18.18}
    to_wallet_expected = {'wallet_id': TO_WALLET_ID, 'amount': 17.13}

    response = client.post('v1/wallet/transfer', json=request, headers=HEADERS)
    assert response.status_code == 200
    assert response.json() == from_wallet_expected

    # check idempotency
    response = client.post('v1/wallet/transfer', json=request, headers=HEADERS)
    assert response.json() == from_wallet_expected

    check_db_wallet(db, from_wallet_expected)
    check_db_wallet(db, to_wallet_expected)

    # check DB transaction
    db_transaction = (
        db.query(Transaction)
        .filter(Transaction.idempotency_key == IDEMPOTENCY_KEY)
        .first()
    )
    assert db_transaction.amount == Decimal(str(request['amount']))
    assert db_transaction.from_wallet_id == uuid.UUID(FROM_WALLET_ID)
    assert db_transaction.from_wallet_amount == Decimal(
        str(from_wallet_expected['amount'])
    )
    assert db_transaction.to_wallet_id == uuid.UUID(TO_WALLET_ID)
    assert db_transaction.to_wallet_amount == Decimal(
        str(to_wallet_expected['amount'])
    )
    assert db_transaction.created_at


def test_wallet_transfer_not_enough_money(
        client: TestClient,
        db: Session,
) -> None:
    db_from_wallet = {'wallet_id': FROM_WALLET_ID, 'amount': 5}
    db.add(Wallet(**db_from_wallet))
    db.commit()

    request = {
        'from_wallet_id': FROM_WALLET_ID,
        'to_wallet_id': TO_WALLET_ID,
        'amount': 7,
    }

    response = client.post('v1/wallet/transfer', json=request, headers=HEADERS)
    assert response.status_code == 400
    assert response.json() == {'detail': 'not enough money'}

    check_db_wallet(db, db_from_wallet, has_updated_at=False)
    assert not (
        db.query(Transaction)
        .filter(Transaction.idempotency_key == IDEMPOTENCY_KEY)
        .first()
    )


def test_wallet_transfer_self(client: TestClient, db: Session) -> None:
    request = {
        'from_wallet_id': FROM_WALLET_ID,
        'to_wallet_id': FROM_WALLET_ID,
        'amount': 1,
    }

    response = client.post('v1/wallet/transfer', json=request, headers=HEADERS)
    assert response.status_code == 400
    assert response.json() == {'detail': 'self-transfer is not possible'}
