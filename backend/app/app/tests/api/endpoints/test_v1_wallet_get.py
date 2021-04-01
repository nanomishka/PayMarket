from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models import Wallet

WALLET_ID = '11111111-1111-1111-1111-111111111111'


def test_wallet_get_success(client: TestClient, db: Session) -> None:
    expected_wallet = {'wallet_id': WALLET_ID, 'amount': 12.34}

    # save in db
    db.add(Wallet(**expected_wallet))
    db.commit()

    response = client.post(
        'v1/wallet/get', json={'wallet_id': expected_wallet['wallet_id']}
    )
    assert response.status_code == 200
    assert response.json() == expected_wallet


def test_wallet_get_not_found(client: TestClient) -> None:
    response = client.post('v1/wallet/get', json={'wallet_id': WALLET_ID})
    assert response.status_code == 404
    assert response.json() == {'detail': 'Wallet is not found'}
