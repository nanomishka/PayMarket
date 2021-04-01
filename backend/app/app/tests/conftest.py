from typing import Generator

import pytest
from fastapi.testclient import TestClient

from app.db.session import DBSessionMaker
from app.db.base_class import Base
from app.main import app


@pytest.fixture()
def db() -> Generator:
    session = DBSessionMaker()
    yield session

    # clear DB
    session.execute(
        'TRUNCATE {} RESTART IDENTITY;'.format(','.join(
            table.name for table in reversed(Base.metadata.sorted_tables)
        ))
    )
    session.commit()


@pytest.fixture(scope='module')
def client() -> Generator:
    with TestClient(app) as c:
        yield c
