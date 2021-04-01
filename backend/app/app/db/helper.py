import datetime
import uuid

from fastapi import HTTPException
from psycopg2.errors import UniqueViolation
from sqlalchemy import exc
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.schemas import WalletDonateRequest
from app.schemas import WalletTransferRequest
from app.schemas import WalletResponse
from app.models import Wallet
from app.models import Transaction


class DBHelper:

    @classmethod
    def wallet_get(cls, db: Session, wallet_id: uuid.UUID) -> WalletResponse:
        wallet = db.query(Wallet).filter(Wallet.wallet_id == wallet_id).first()

        if not wallet:
            raise HTTPException(status_code=404, detail='Wallet is not found')

        return WalletResponse(
            wallet_id=wallet.wallet_id,
            amount=wallet.amount,
        )

    @classmethod
    def wallet_create(
            cls,
            db: Session,
            idempotency_key: uuid.UUID,
    ) -> WalletResponse:
        query = (
            pg_insert(Wallet)
            .values(wallet_id=uuid.uuid4(), idempotency_key=idempotency_key)
            .returning(Wallet.wallet_id, Wallet.amount)
        )
        query = query.on_conflict_do_update(
            constraint='wallet_idempotency_key_key',
            set_=dict(idempotency_key=query.excluded.idempotency_key),
        )
        result = db.execute(query).first()
        db.commit()

        return WalletResponse(
            wallet_id=result['wallet_id'],
            amount=result['amount'],
        )

    @classmethod
    def wallet_donate(
            cls,
            db: Session,
            idempotency_key: uuid.UUID,
            request: WalletDonateRequest,
    ) -> WalletResponse:
        try:
            db_wallet = (
                db.query(Wallet)
                .filter(Wallet.wallet_id == request.wallet_id)
                .with_for_update()
                .first()
            )
            if not db_wallet:
                raise HTTPException(
                    status_code=404,
                    detail='Wallet is not found',
                )

            utcnow = datetime.datetime.utcnow()

            db_wallet.amount = db_wallet.amount + request.amount
            db_wallet.updated_at = utcnow
            db.add(db_wallet)

            insert_transaction = (
                pg_insert(Transaction)
                .values(
                    idempotency_key=idempotency_key,
                    amount=request.amount,
                    to_wallet_id=db_wallet.wallet_id,
                    to_wallet_amount=db_wallet.amount,
                    created_at=utcnow,
                )
                .returning(Transaction.to_wallet_amount)
            )
            db.execute(insert_transaction).first()

            db.commit()

            return WalletResponse(
                wallet_id=db_wallet.wallet_id,
                amount=db_wallet.amount,
            )
        except exc.IntegrityError:
            db.rollback()

            existed_transaction = (
                db.query(Transaction)
                .filter(Transaction.idempotency_key == idempotency_key)
                .first()
            )

            return WalletResponse(
                wallet_id=existed_transaction.to_wallet_id,
                amount=existed_transaction.to_wallet_amount,
            )

    @classmethod
    def wallet_transfer(
            cls,
            db: Session,
            idempotency_key: uuid.UUID,
            request: WalletTransferRequest,
    ) -> WalletResponse:
        db.connection(execution_options={'isolation_level': 'SERIALIZABLE'})

        while True:
            try:
                db_from_wallet = (
                    db.query(Wallet)
                    .filter(Wallet.wallet_id == request.from_wallet_id)
                    .first()
                )
                if not db_from_wallet:
                    raise HTTPException(
                        status_code=404, detail='from_wallet_id is not found'
                    )

                if db_from_wallet.amount < request.amount:
                    raise HTTPException(status_code=400, detail='not enough money')

                db_to_wallet = (
                    db.query(Wallet)
                    .filter(Wallet.wallet_id == request.to_wallet_id)
                    .first()
                )
                if not db_to_wallet:
                    raise HTTPException(
                        status_code=404,
                        detail='db_to_wallet is not found',
                    )

                utcnow = datetime.datetime.utcnow()

                db_from_wallet.amount = db_from_wallet.amount - request.amount
                db_from_wallet.updated_at = utcnow
                db_to_wallet.amount = db_to_wallet.amount + request.amount
                db_to_wallet.updated_at = utcnow
                db.add(db_from_wallet)
                db.add(db_to_wallet)

                # insert Transaction
                insert_transaction = pg_insert(Transaction).values(
                    idempotency_key=idempotency_key,
                    amount=request.amount,
                    from_wallet_id=db_from_wallet.wallet_id,
                    from_wallet_amount=db_from_wallet.amount,
                    to_wallet_id=db_to_wallet.wallet_id,
                    to_wallet_amount=db_to_wallet.amount,
                    created_at=utcnow,
                )
                db.execute(insert_transaction).first()

                db.commit()

                return WalletResponse(
                    wallet_id=db_from_wallet.wallet_id,
                    amount=db_from_wallet.amount,
                )
            except exc.IntegrityError as exception:
                db.rollback()

                if isinstance(exception.orig, UniqueViolation):
                    existed_transaction = (
                        db.query(Transaction)
                        .filter(Transaction.idempotency_key == idempotency_key)
                        .first()
                    )

                    return WalletResponse(
                        wallet_id=existed_transaction.from_wallet_id,
                        amount=existed_transaction.from_wallet_amount,
                    )
