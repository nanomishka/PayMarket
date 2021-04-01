import uuid

from decimal import Decimal

from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models import Wallet
from app.models import Transaction

WALLET_ID = '11111111-1111-1111-1111-111111111111'
IDEMPOTENCY_KEY = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
HEADERS = {'Idempotency-Key': IDEMPOTENCY_KEY}


def test_wallet_donate(client: TestClient, db: Session) -> None:
    db_wallet = {'wallet_id': WALLET_ID, 'amount': 11.11}
    request = {'wallet_id': WALLET_ID, 'amount': 22.22}
    expected = {'wallet_id': WALLET_ID, 'amount': 33.33}

    # save in db
    db.add(Wallet(**db_wallet))
    db.commit()

    response = client.post('v1/wallet/donate', json=request, headers=HEADERS)
    assert response.status_code == 200
    assert response.json() == expected

    # check idempotency
    response = client.post('v1/wallet/donate', json=request, headers=HEADERS)
    assert response.json() == expected

    # check DB wallet
    db_wallet = db.query(Wallet).filter(Wallet.wallet_id == WALLET_ID).first()
    assert not db_wallet.idempotency_key
    assert db_wallet.amount == Decimal(str(expected['amount']))
    assert db_wallet.updated_at

    # check DB transaction
    db_transaction = (
        db.query(Transaction)
        .filter(Transaction.idempotency_key == IDEMPOTENCY_KEY)
        .first()
    )
    assert db_transaction.amount == Decimal(str(request['amount']))
    assert db_transaction.to_wallet_id == uuid.UUID(WALLET_ID)
    assert db_transaction.to_wallet_amount == Decimal(str(expected['amount']))
    assert db_wallet.created_at


def test_wallet_donate_precision(client: TestClient, db: Session) -> None:
    def _get_headers():
        return {'Idempotency-Key': uuid.uuid4().hex}

    # save in db
    db.add(Wallet(wallet_id=WALLET_ID))
    db.commit()

    request = {'wallet_id': WALLET_ID, 'amount': 0.1}

    # check double problem
    assert 0.2 + 0.1 != 0.3
    assert 0.7 + 0.1 != 0.8

    for value in range(1, 10):
        response = client.post(
            'v1/wallet/donate',
            json=request,
            headers=_get_headers(),
        )
        assert response.json() == {'wallet_id': WALLET_ID, 'amount': value / 10}


def test_wallet_donate_not_found(client: TestClient) -> None:
    response = client.post(
        'v1/wallet/donate',
        json={'wallet_id': WALLET_ID, 'amount': 100},
        headers=HEADERS,
    )

    assert response.status_code == 404
    assert response.json() == {'detail': 'Wallet is not found'}


def test_wallet_donate_amount_error(client: TestClient) -> None:
    response = client.post(
        'v1/wallet/donate',
        json={'wallet_id': WALLET_ID, 'amount': 0},
        headers=HEADERS,
    )
    assert response.status_code == 422
    assert response.json() == {
        'detail': [
            {
                'ctx': {'limit_value': 0},
                'loc': ['body', 'amount'],
                'msg': 'ensure this value is greater than 0',
                'type': 'value_error.number.not_gt',
            }
        ]
    }


def test_wallet_donate_invalid_amount_precision(client: TestClient) -> None:
    response = client.post(
        'v1/wallet/donate',
        json={'wallet_id': WALLET_ID, 'amount': 100.123},
        headers=HEADERS,
    )

    assert response.status_code == 422
    assert response.json() == {
        'detail': [
            {
                'ctx': {'decimal_places': 2},
                'loc': ['body', 'amount'],
                'msg': 'ensure that there are no more than 2 decimal places',
                'type': 'value_error.decimal.max_places',
            }
        ]
    }
