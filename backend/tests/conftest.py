import os
import pytest
import datetime
from backend.app import create_app
from backend.database.models import db as _db, Worker


@pytest.fixture(scope="session")
def app():
    """
    Tworzy instancję aplikacji Flask skonfigurowaną do testów.
    Używa bazy danych w pamięci (SQLite :memory:).
    Scope='session' oznacza, że aplikacja jest tworzona raz na całe uruchomienie testów,
    ale kontekst bazy danych będzie resetowany w innych fixturach.
    """
    # Ustawiamy zmienną środowiskową, aby app.py wybrał in-memory DB
    # Zanim wywołamy create_app()
    os.environ["FLASK_DB_PATH"] = ":memory:"

    app = create_app()

    app.config.update({
        "TESTING": True,
        "DEBUG": False,
        # Nadpisujemy na wszelki wypadek, choć zmienna ENV wyżej powinna to załatwić
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
    })

    yield app

    # Sprzątanie po zakończeniu wszystkich testów (opcjonalne dla :memory:)
    os.environ.pop("FLASK_DB_PATH", None)


@pytest.fixture(scope="function")
def client(app):
    """
    Klient testowy do wykonywania zapytań HTTP (GET, POST itp.) do naszej aplikacji.
    """
    return app.test_client()


@pytest.fixture(scope="function")
def runner(app):
    """
    Runner do testowania komend CLI (jeśli będziesz takie pisał).
    """
    return app.test_cli_runner()


@pytest.fixture(scope="function")
def db_session(app):
    """
    Fixture, która tworzy czystą bazę danych przed każdym testem
    i usuwa ją po teście. Zapewnia izolację danych.
    """
    with app.app_context():
        _db.create_all()  # Tworzy tabele (Workers, Entries)

        yield _db  # Tu dzieje się test

        _db.session.remove()
        _db.drop_all()  # Czyści bazę po teście


@pytest.fixture(scope="function")
def sample_worker_data():
    """
    Zwraca słownik z danymi przykładowego pracownika.
    Przydatne, gdy chcemy utworzyć pracownika ręcznie w teście.
    """
    return {
        "name": "Jan Kowalski",
        "face_embedding": b'fake_binary_embedding_data_123',  # Symulacja BLOBa
        "expiration_date": datetime.datetime.now() + datetime.timedelta(days=365),
        "secret": "super_secret_qr_code_content"
    }


@pytest.fixture(scope="function")
def created_worker(db_session, sample_worker_data):
    """
    Tworzy i zapisuje pracownika w bazie danych.
    Użyj tej fixtury, jeśli test wymaga, aby pracownik już istniał w bazie.
    """
    worker = Worker(
        name=sample_worker_data["name"],
        face_embedding=sample_worker_data["face_embedding"],
        expiration_date=sample_worker_data["expiration_date"],
        secret=sample_worker_data["secret"]
    )
    db_session.session.add(worker)
    db_session.session.commit()

    return worker