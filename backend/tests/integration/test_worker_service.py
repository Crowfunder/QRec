import pytest
import datetime
import os  # <--- Wymagany import
from unittest.mock import patch, MagicMock
from backend.app import create_app, db
from backend.database.models import Worker
from backend.components.workers import workerService


# -----------------------------------------------------------------------------
# Fixtures (Konfiguracja środowiska testowego)
# -----------------------------------------------------------------------------

@pytest.fixture
def app_context():
    """Tworzy aplikację Flask z bazą danych w pamięci RAM."""

    # FIX: Ustawiamy zmienną środowiskową PRZED utworzeniem aplikacji.
    # Dzięki temu create_app() użyje "sqlite:///:memory:" zamiast próbować
    # tworzyć plik w nieistniejącym katalogu 'instance'.
    os.environ["FLASK_DB_PATH"] = ":memory:"

    app = create_app()

    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "QR_SECRET_KEY": b'test_secret_key_32_bytes_long_1234'
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

    # Sprzątanie po teście
    if "FLASK_DB_PATH" in os.environ:
        del os.environ["FLASK_DB_PATH"]


# -----------------------------------------------------------------------------
# Testy
# -----------------------------------------------------------------------------

@patch('backend.components.workers.workerService.create_worker_embedding')
def test_create_worker_success(mock_embedding, app_context):
    """Sprawdza, czy tworzenie pracownika zapisuje go w bazie i generuje sekret."""
    mock_embedding.return_value = b'fake_embedding_blob'
    name = "Jan Testowy"
    fake_image = MagicMock()
    expiration = datetime.datetime(2030, 1, 1)

    worker = workerService.create_worker(name, fake_image, expiration)

    assert worker.id is not None
    assert worker.name == name
    assert worker.face_embedding == b'fake_embedding_blob'
    assert worker.secret != "TEMP_SECRET"

    saved_worker = db.session.get(Worker, worker.id)
    assert saved_worker is not None
    assert saved_worker.name == name


def test_get_worker_by_id_found(app_context):
    """Sprawdza pobieranie istniejącego pracownika."""
    worker = Worker(
        name="Istniejacy",
        face_embedding=b'data',
        expiration_date=datetime.datetime.now(),
        secret="secret"
    )
    db.session.add(worker)
    db.session.commit()

    fetched = workerService.get_worker_by_id(worker.id)

    assert fetched.id == worker.id
    assert fetched.name == "Istniejacy"


def test_get_worker_by_id_not_found(app_context):
    """Sprawdza rzucanie wyjątku dla nieistniejącego ID."""
    with pytest.raises(ValueError) as excinfo:
        workerService.get_worker_by_id(99999)

    assert "Worker with id 99999 not found" in str(excinfo.value)


@patch('backend.components.workers.workerService.create_worker_embedding')
def test_extend_worker_expiration(mock_embedding, app_context):
    """Sprawdza aktualizację daty ważności przepustki."""
    mock_embedding.return_value = b'data'
    old_date = datetime.datetime(2024, 1, 1)
    worker = workerService.create_worker("Marek", None, old_date)

    new_date = datetime.datetime(2025, 1, 1)

    updated_worker = workerService.extend_worker_expiration(worker, new_date)

    assert updated_worker.expiration_date == new_date

    db.session.expire_all()
    from_db = db.session.get(Worker, worker.id)
    assert from_db.expiration_date == new_date


@patch('backend.components.workers.workerService.create_worker_embedding')
def test_update_worker_name(mock_embedding, app_context):
    """Sprawdza zmianę nazwy pracownika."""
    mock_embedding.return_value = b'data'
    worker = workerService.create_worker("Stara Nazwa", None, datetime.datetime.now())

    workerService.update_worker_name(worker, "Nowa Nazwa")

    assert worker.name == "Nowa Nazwa"

    db.session.expire_all()
    from_db = db.session.get(Worker, worker.id)
    assert from_db.name == "Nowa Nazwa"


@patch('backend.components.workers.workerService.create_worker_embedding')
def test_update_worker_face_image(mock_embedding, app_context):
    """Sprawdza aktualizację zdjęcia (i embeddingu) pracownika."""
    # 1. Tworzenie pracownika
    mock_embedding.return_value = b'old_embedding'
    worker = workerService.create_worker("Test Face", None, datetime.datetime.now())

    # 2. Zmiana mocka dla nowego zdjęcia
    mock_embedding.return_value = b'new_embedding_123'
    new_fake_image = MagicMock()

    workerService.update_worker_face_image(worker, new_fake_image)

    assert mock_embedding.call_count == 2
    mock_embedding.assert_called_with(new_fake_image)

    assert worker.face_embedding == b'new_embedding_123'

    db.session.expire_all()
    from_db = db.session.get(Worker, worker.id)
    assert from_db.face_embedding == b'new_embedding_123'


def test_get_worker_by_secret(app_context):
    """Sprawdza wyszukiwanie pracownika po sekrecie (QR)."""
    worker = Worker(
        name="Szukany",
        face_embedding=b'data',
        expiration_date=datetime.datetime.now(),
        secret="unikalny_sekret_qr"
    )
    db.session.add(worker)
    db.session.commit()

    found = workerService.get_worker_by_secret("unikalny_sekret_qr")
    not_found = workerService.get_worker_by_secret("błędny_sekret")

    assert found is not None
    assert found.id == worker.id
    assert not_found is None