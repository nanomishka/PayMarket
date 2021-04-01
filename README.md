### PayMarket
Payment system

Supports:
- create a wallet
- make deposit to the wallet
- transfer money to another wallet

#### How to run
Project stars with command:
```bash
docker-compose up
```

Run tests:
```bash
./scripts/test.sh
```


Api documentation is located on http://localhost/docs


### Architecture
- FastApi (python3.7)
- PostgreSQL (+ alembic, sqlalchemy)
