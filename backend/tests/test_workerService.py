# test_workerService.py
# Aby uruchomić testy trzeba wpisać polecenia:
# pytest backend/tests/test_workerService.py

import pytest
import os
import io
import numpy as np
import face_recognition
from unittest.mock import patch, MagicMock
from datetime import datetime
from backend.app import create_app, db
from backend.components.workers import workerService
from backend.database.models import Worker
from backend.components.workers.workerService import newWorker

# Zakładam, że qrcodeService masz poprawnie zaimplementowany.
# Jeśli tam też jest snake_case, upewnij się, że wywołujesz generate_secret a nie generateSecret.
from backend.components.camera_verification.qrcode import qrcodeService


def test_create_worker_embedding_from_mockup():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Dostosuj ścieżkę jeśli jest inna, tutaj zakładamy strukturę backend/tests/
    image_path = os.path.normpath(os.path.join(current_dir, "../../mockups", "Worker View Accept.png"))

    print(f"Szukam pliku pod adresem: {image_path}")
    if not os.path.exists(image_path):
        pytest.fail(f"Test nie znalazł pliku graficznego! Sprawdzana ścieżka: {image_path}")

    image_input = face_recognition.load_image_file(image_path)

    # POPRAWKA 1: Użycie poprawnej nazwy funkcji (snake_case)
    result_blob = workerService.create_worker_embedding(image_input)

    assert isinstance(result_blob, bytes)
    assert len(result_blob) > 0

    buffer = io.BytesIO(result_blob)
    embeddings = np.load(buffer, allow_pickle=True)

    assert len(embeddings) > 0, (
        "Nie wykryto żadnej twarzy na podanym obrazku! "
        "Upewnij się, że 'Worker View Accept.png' zawiera wyraźną twarz."
    )
    # Sprawdzenie czy wektor ma standardowy wymiar (128 cech)
    # create_worker_embedding zapisuje listę encodingów, więc embeddings[0] to pierwszy wektor
    assert len(embeddings[0]) == 128
    print(embeddings)


# -----------------------------------------------------------------------------

@pytest.fixture
def app_context():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


# POPRAWKA 2: Poprawna ścieżka do patcha (snake_case)
@patch('backend.components.workers.workerService.create_worker_embedding')
def test_new_worker_service_adds_to_db(mock_create_embedding, app_context):
    mock_create_embedding.return_value = b'test_blob_data'
    name = "Jan Testowy"
    fake_image = MagicMock()
    expiration = datetime(2025, 12, 31)

    with app_context.app_context():
        # POPRAWKA 3: Usunięto argument 'db', funkcja korzysta z globalnego db w kontekście
        worker = newWorker(name, fake_image, expiration)

        assert worker.id is not None
        assert worker.name == name

        fetched_worker = db.session.get(Worker, worker.id)
        assert fetched_worker is not None
        assert fetched_worker.name == "Jan Testowy"
        assert fetched_worker.face_embedding == b'test_blob_data'


# -----------------------------------------------------------------------------

def test_extend_worker_expiration_success(app_context):
    initial_date = datetime(2024, 1, 1)
    new_date = datetime(2030, 1, 1)

    with app_context.app_context():
        # Uwaga: Tutaj używasz qrcodeService.generateSecret.
        # Upewnij się, że ta metoda istnieje (w workerService.py importujesz generate_secret snake_case'em).
        worker = Worker(
            name="Marek DoZmiany",
            face_embedding=b'dummy_data',
            expiration_date=initial_date,
            secret="dummy_secret"  # Uproszczenie dla testu, chyba że potrzebujesz qrcodeService
        )
        db.session.add(worker)
        db.session.commit()
        worker_id = worker.id

        # POPRAWKA 4: Usunięto argument 'db'
        updated_worker = workerService.extendWorkerExpiration(worker_id, new_date)

        assert updated_worker.expiration_date == new_date

        db.session.expire_all()
        fetched_worker = db.session.get(Worker, worker_id)
        assert fetched_worker.expiration_date == new_date


def test_extend_worker_expiration_not_found(app_context):
    non_existent_id = 99999
    new_date = datetime(2030, 1, 1)

    with app_context.app_context():
        with pytest.raises(ValueError) as excinfo:
            # POPRAWKA 5: Usunięto argument 'db'
            workerService.extendWorkerExpiration(non_existent_id, new_date)
        assert f"Worker with id {non_existent_id} not found" in str(excinfo.value)


# -----------------------------------------------------------------------------

def test_update_worker_name_success(app_context):
    initial_name = "Jan Kowalski"
    new_name = "Jan Nowak"

    with app_context.app_context():
        worker = Worker(
            name=initial_name,
            face_embedding=b'dummy_data',
            expiration_date=datetime(2025, 12, 12),
            secret="dummy_secret"
        )
        db.session.add(worker)
        db.session.commit()
        worker_id = worker.id

        # POPRAWKA 6: Usunięto argument 'db'
        updated_worker = workerService.updateWorkerName(worker_id, new_name)

        assert updated_worker.name == new_name

        db.session.expire_all()
        fetched_worker = db.session.get(Worker, worker_id)
        assert fetched_worker.name == new_name


def test_extend_worker_name_not_found(app_context):
    non_existent_id = 99999
    new_name = "name_does_not_matter"

    with app_context.app_context():
        with pytest.raises(ValueError) as excinfo:
            # POPRAWKA 7: Usunięto argument 'db'
            workerService.updateWorkerName(non_existent_id, new_name)
        assert f"Worker with id {non_existent_id} not found" in str(excinfo.value)


# -----------------------------------------------------------------------------

def test_update_worker_face_embedding_success(app_context):
    initial_name = "Test Face Update"
    initial_face_data = b'old_dummy_embedding'
    new_raw_image = b'new_raw_image_data_jpg'
    mocked_embedding_result = b'new_calculated_embedding_123'

    with app_context.app_context():
        worker = Worker(
            name=initial_name,
            face_embedding=initial_face_data,
            expiration_date=datetime(2025, 12, 12),
            secret="dummy_secret"
        )
        db.session.add(worker)
        db.session.commit()
        worker_id = worker.id

        # POPRAWKA 8: Poprawna nazwa w patchu
        with patch('backend.components.workers.workerService.create_worker_embedding') as mock_embedding:
            mock_embedding.return_value = mocked_embedding_result

            # POPRAWKA 9: Usunięto argument 'db'
            updated_worker = workerService.updateWorkerFaceImage(worker_id, new_raw_image)

            mock_embedding.assert_called_once_with(new_raw_image)

        assert updated_worker.face_embedding == mocked_embedding_result

        db.session.expire_all()
        fetched_worker = db.session.get(Worker, worker_id)
        assert fetched_worker.face_embedding == mocked_embedding_result


def test_update_worker_face_embedding_not_found(app_context):
    non_existent_id = 88888
    new_raw_image = b'some_image_data'

    with app_context.app_context():
        with pytest.raises(ValueError) as excinfo:
            # POPRAWKA 10: Usunięto argument 'db'
            workerService.updateWorkerFaceImage(non_existent_id, new_raw_image)
        assert f"Worker with id {non_existent_id} not found" in str(excinfo.value)