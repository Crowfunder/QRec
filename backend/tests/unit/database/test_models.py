import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from backend.database.models import Worker, Entry


def test_create_worker_success(db_session, sample_worker_data):
    """
    Testuje poprawne utworzenie i zapisanie pracownika (Worker).
    """
    worker = Worker(
        name=sample_worker_data["name"],
        face_embedding=sample_worker_data["face_embedding"],
        expiration_date=sample_worker_data["expiration_date"],
        secret=sample_worker_data["secret"]
    )

    db_session.session.add(worker)
    db_session.session.commit()

    assert worker.id is not None
    assert worker.name == "Jan Kowalski"
    assert worker.secret == "super_secret_qr_code_content"
    assert isinstance(worker.face_embedding, bytes)


def test_create_worker_missing_fields(db_session):
    """
    Testuje, czy baza danych rzuca błąd (IntegrityError),
    gdy próbujemy zapisać pracownika bez wymaganych pól (nullable=False).
    """
    # Brak pola 'name' i 'secret'
    worker = Worker(
        face_embedding=b'some_data',
        expiration_date=datetime.now()
    )

    db_session.session.add(worker)

    with pytest.raises(IntegrityError):
        db_session.session.commit()


def test_create_entry_linked_to_worker(db_session, created_worker):
    """
    Testuje utworzenie wpisu (Entry) powiązanego z istniejącym pracownikiem.
    """
    entry = Entry(
        worker_id=created_worker.id,
        code=200,
        message="Access Granted",
        face_image=b'snapshot_blob'
    )

    db_session.session.add(entry)
    db_session.session.commit()

    assert entry.id is not None
    assert entry.worker_id == created_worker.id
    assert entry.message == "Access Granted"


def test_create_entry_without_worker(db_session):
    """
    Testuje utworzenie wpisu (Entry) bez powiązania z pracownikiem (worker_id jest nullable).
    Np. w przypadku próby wejścia osoby nierozpoznanej.
    """
    entry = Entry(
        worker_id=None,
        code=404,
        message="User not found",
        face_image=b'unknown_face_blob'
    )

    db_session.session.add(entry)
    db_session.session.commit()

    assert entry.id is not None
    assert entry.worker_id is None


def test_entry_default_date(db_session):
    """
    Testuje, czy pole 'date' w modelu Entry otrzymuje domyślną wartość (server_default),
    jeśli nie zostanie podane przy tworzeniu obiektu.
    """
    entry = Entry(
        code=200,
        message="Test Date",
        worker_id=None
    )

    db_session.session.add(entry)
    db_session.session.commit()

    # Po commicie musimy odświeżyć obiekt, aby pobrać wartość wygenerowaną przez serwer bazy danych
    db_session.session.refresh(entry)

    assert entry.date is not None
    assert isinstance(entry.date, datetime)


def test_entry_missing_required_fields(db_session):
    """
    Testuje brak wymaganych pól w modelu Entry (code, message).
    """
    entry = Entry(
        worker_id=None
        # Brak code i message
    )

    db_session.session.add(entry)

    with pytest.raises(IntegrityError):
        db_session.session.commit()