import pytest
import datetime  # Dodano import
from sqlalchemy import text, inspect
from sqlalchemy.exc import IntegrityError
from backend.database.models import db, Worker


def test_database_connection_alive(app):
    """
    Testuje, czy aplikacja może nawiązać połączenie z bazą danych
    i wykonać proste zapytanie SQL (SELECT 1).
    Nie wymaga fixtury db_session, wystarczy kontekst aplikacji.
    """
    with app.app_context():
        try:
            # Wykonanie surowego zapytania SQL, aby pominąć warstwę ORM
            # i sprawdzić samo połączenie.
            result = db.session.execute(text("SELECT 1"))
            value = result.scalar()
            assert value == 1
        except Exception as e:
            pytest.fail(f"Nie udało się połączyć z bazą danych: {str(e)}")


def test_database_schema_creation(db_session):
    """
    Sprawdza, czy SQLAlchemy poprawnie utworzyło tabele w bazie danych.
    Wymaga fixtury db_session, która wywołuje db.create_all().
    """
    # Używamy inspect do pobrania informacji o strukturze bazy
    inspector = inspect(db_session.engine)
    tables = inspector.get_table_names()

    # Sprawdzamy czy wymagane tabele istnieją
    assert "workers" in tables
    assert "entries" in tables


def test_database_transaction_commit_and_rollback(db_session):
    """
    Test integracyjny sprawdzający działanie sesji bazy danych:
    1. Poprawny zapis (commit).
    2. Wycofanie zmian przy błędzie (rollback).
    """
    # 1. Test Commita
    worker = Worker(
        name="Integration Test Worker",
        face_embedding=b'integration_test_blob',
        # POPRAWKA: Przekazujemy obiekt datetime, a nie string
        expiration_date=datetime.datetime(2099, 1, 1),
        secret="integration_secret"
    )
    db_session.session.add(worker)
    db_session.session.commit()

    # Sprawdzamy, czy dane faktycznie są w bazie (odpytując nową sesją lub tą samą)
    fetched_worker = db_session.session.get(Worker, worker.id)
    assert fetched_worker is not None
    assert fetched_worker.name == "Integration Test Worker"

    # 2. Test Rollbacka (wymuszony błąd IntegrityError - brak pola name)
    invalid_worker = Worker(
        face_embedding=b'fail_blob',
        # POPRAWKA: Tutaj również obiekt datetime
        expiration_date=datetime.datetime(2099, 1, 1),
        secret="fail_secret"
        # Brak pola name (nullable=False)
    )
    db_session.session.add(invalid_worker)

    with pytest.raises(IntegrityError):
        db_session.session.commit()

    # SQLAlchemy automatycznie robi rollback przy wyjątku w commicie,
    # ale sesja pozostaje w stanie "inactive" lub wymaga ręcznego rollback w niektórych konfiguracjach.
    # W testach sprawdźmy po prostu czy sesja nadal żyje po rollbacku.
    db_session.session.rollback()

    # Upewniamy się, że błędny rekord nie został dodany
    count = db_session.session.query(Worker).filter_by(secret="fail_secret").count()
    assert count == 0

    # Upewniamy się, że pierwszy (poprawny) rekord nadal istnieje
    count_valid = db_session.session.query(Worker).filter_by(name="Integration Test Worker").count()
    assert count_valid == 1