import pytest
import datetime  # Dodano import
from sqlalchemy import text, inspect
from sqlalchemy.exc import IntegrityError
from backend.database.models import db, Worker


def test_database_connection_alive(app):
    """
    Tests whether the application can connect to the database and execute a simple SQL query (SELECT 1).
    It doesn't require a db_session configuration; the application context is sufficient.
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
    Verifies that SQLAlchemy has successfully created the tables in the database.
    Requires the db_session fixture, which calls db.create_all().
    """
    # Używamy inspect do pobrania informacji o strukturze bazy
    inspector = inspect(db_session.engine)
    tables = inspector.get_table_names()

    # Sprawdzamy czy wymagane tabele istnieją
    assert "workers" in tables
    assert "entries" in tables

# ============================================================================
# Test Transaction Management
# ============================================================================

def test_database_transaction_commit_and_rollback(db_session):
    """
    Integration test to verify the functionality of the database session:
    1. Successful write (commit).
    2. Rollback on error.
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

    db_session.session.rollback()

    # Upewniamy się, że błędny rekord nie został dodany
    count = db_session.session.query(Worker).filter_by(secret="fail_secret").count()
    assert count == 0

    # Upewniamy się, że pierwszy (poprawny) rekord nadal istnieje
    count_valid = db_session.session.query(Worker).filter_by(name="Integration Test Worker").count()
    assert count_valid == 1