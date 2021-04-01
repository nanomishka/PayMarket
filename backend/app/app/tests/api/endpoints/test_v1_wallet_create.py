import uuid

from sqlalchemy.orm import Session
from fastapi.testclient import TestClient


from app.models import Wallet


def test_wallet_create(client: TestClient, db: Session, mocker) -> None:
    idempotency_key = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
    headers = {'Idempotency-Key': idempotency_key}

    expected_wallet = {
        'wallet_id': '11111111-1111-1111-1111-111111111111',
        'amount': 0,
    }
    mocker.patch('uuid.uuid4', return_value=expected_wallet['wallet_id'])

    response = client.post('v1/wallet/create', headers=headers)
    assert response.status_code == 200
    assert response.json() == expected_wallet

    # check idempotency
    client.post('v1/wallet/create', headers=headers)
    response = client.post('v1/wallet/create', headers=headers)
    assert response.status_code == 200
    assert response.json() == expected_wallet

    # check DB wallet
    db_wallet = (
        db.query(Wallet)
        .filter(Wallet.wallet_id == expected_wallet['wallet_id'])
        .first()
    )
    assert db_wallet.idempotency_key == uuid.UUID(idempotency_key)
    assert db_wallet.amount == 0
    assert db_wallet.created_at
    assert not db_wallet.updated_at


def test_wallet_create_error(client: TestClient, db: Session, mocker) -> None:
    response = client.post(
        'v1/wallet/create', headers={'Idempotency-Key': 'invalid_uuid'}
    )
    assert response.status_code == 422
    assert response.json() == {
        'detail': [
            {
                'loc': ['header', 'idempotency-key'],
                'msg': 'value is not a valid uuid',
                'type': 'type_error.uuid',
            }
        ]
    }
