# Aby uruchomić testy trzeba wpisać polecenia:
# pytest backend/tests/test_workerService.py
# Inaczej nie będzie działać

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
from backend.components.camera_verification.qrcode import qrcodeService

def test_create_worker_embedding_from_mockup():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.normpath(os.path.join(current_dir, "../../mockups", "Worker View Accept.png"))

    print(f"Szukam pliku pod adresem: {image_path}")

    if not os.path.exists(image_path):
        pytest.fail(f"Test nie znalazł pliku graficznego! Sprawdzana ścieżka: {image_path}")
    image_input = face_recognition.load_image_file(image_path)

    # WYKONANIE FUNKCJI
    result_blob = workerService.createWorkerEmbedding(image_input)

    assert isinstance(result_blob, bytes)
    assert len(result_blob) > 0

    # Weryfikacja czy da się to odczytać jako numpy array
    buffer = io.BytesIO(result_blob)
    embeddings = np.load(buffer, allow_pickle=True)

    assert len(embeddings) > 0, (
        "Nie wykryto żadnej twarzy na podanym obrazku!"
        "Upewnij się, że 'Worker View Accept.png' zawiera wyraźną twarz."
    )

    # Sprawdzenie czy wektor ma standardowy wymiar (128 cech)
    assert len(embeddings[0]) == 128
    print(embeddings)

#-----------------------------------------------------------------------------

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

@patch('backend.components.workers.workerService.createWorkerEmbedding')
def test_new_worker_service_adds_to_db(mock_create_embedding, app_context):
    mock_create_embedding.return_value = b'test_blob_data'

    name = "Jan Testowy"
    fake_image = MagicMock()
    expiration = datetime(2025, 12, 31)

    with app_context.app_context():

        worker = newWorker(db, name, fake_image, expiration)
        assert worker.id is not None
        assert worker.name == name
        # Sprawdzanie czy dane faktycznie są w bazie danych
        fetched_worker = db.session.get(Worker, worker.id)
        assert fetched_worker is not None
        assert fetched_worker.name == "Jan Testowy"
        assert fetched_worker.face_image == b'test_blob_data'

#-----------------------------------------------------------------------------

def test_extend_worker_expiration_success(app_context):
    initial_date = datetime(2024, 1, 1)
    new_date = datetime(2030, 1, 1)

    with app_context.app_context():
        worker = Worker(
            name="Marek DoZmiany",
            face_image=b'dummy_data',
            expiration_date=initial_date,
            secret=qrcodeService.generateSecret(name="Marek DoZmiany", worker_id=67)
        )
        db.session.add(worker)
        db.session.commit()
        worker_id = worker.id

        # Wykonanie funkcji
        updated_worker = workerService.extendWorkerExpiration(db, worker_id, new_date)

        # Assert - Sprawdzenie czy zwrócony obiekt ma nową datę
        assert updated_worker.expiration_date == new_date

        # Assert- Sprawdzenie czy zmiana zapisała się w bazie
        db.session.expire_all()  # Wymuszenie odświeżenie danych z bazy
        fetched_worker = db.session.get(Worker, worker_id)
        assert fetched_worker.expiration_date == new_date

def test_extend_worker_expiration_not_found(app_context):
    """Test czy funkcja rzuca błąd, gdy pracownik nie istnieje"""

    non_existent_id = 99999
    new_date = datetime(2030, 1, 1)

    with app_context.app_context():
        # Powinien być wyjątek ValueError
        with pytest.raises(ValueError) as excinfo:
            workerService.extendWorkerExpiration(db, non_existent_id, new_date)
        assert f"Worker with id {non_existent_id} not found" in str(excinfo.value)

#-----------------------------------------------------------------------------

def test_update_worker_name_success(app_context):
    initial_name = "Jan Kowalski"
    new_name = "Jan Nowak"

    with app_context.app_context():
        worker = Worker(
            name=initial_name,
            face_image=b'dummy_data',
            expiration_date=datetime(2025,12,12),
            secret=qrcodeService.generateSecret(name=initial_name, worker_id=67)
        )
        db.session.add(worker)
        db.session.commit()
        worker_id = worker.id

        # Wykonanie funkcji
        updated_worker = workerService.updateWorkerName(db, worker_id, new_name)

        # Assert - Sprawdzenie czy zwrócony obiekt ma nową datę
        assert updated_worker.name == new_name

        # Assert - Sprawdzenie czy zmiana zapisała się w bazie
        db.session.expire_all()  # Wymuszenie odświeżenie danych z bazy
        fetched_worker = db.session.get(Worker, worker_id)
        assert fetched_worker.name == new_name


def test_extend_worker_name_not_found(app_context):
    """Test czy funkcja rzuca błąd, gdy pracownik nie istnieje"""

    non_existent_id = 99999
    new_name = "name_does_not_matter"

    with app_context.app_context():
        # Powinien być wyjątek ValueError
        with pytest.raises(ValueError) as excinfo:
            workerService.updateWorkerName(db, non_existent_id, new_name)

        assert f"Worker with id {non_existent_id} not found" in str(excinfo.value)

#-----------------------------------------------------------------------------

def test_update_worker_face_image_success(app_context):
    """Test poprawnej aktualizacji zdjęcia twarzy (embeddingu) pracownika"""

    initial_name = "Test Face Update"
    initial_face_data = b'old_dummy_embedding'

    # Dane wejściowe do testu
    new_raw_image = b'new_raw_image_data_jpg'
    mocked_embedding_result = b'new_calculated_embedding_123'

    with app_context.app_context():
        worker = Worker(
            name=initial_name,
            face_image=initial_face_data,
            expiration_date=datetime(2025, 12, 12),
            secret=qrcodeService.generateSecret(name=initial_name, worker_id=67)
        )
        db.session.add(worker)
        db.session.commit()
        worker_id = worker.id

        with patch('backend.components.workers.workerService.createWorkerEmbedding') as mock_embedding:
            # Konfigurujemy mocka, żeby zwracał ustalone dane
            mock_embedding.return_value = mocked_embedding_result
            updated_worker = workerService.updateWorkerFaceImage(db, worker_id, new_raw_image)
            mock_embedding.assert_called_once_with(new_raw_image)

        # 3. Assert - weryfikacja obiektu zwróconego
        assert updated_worker.face_image == mocked_embedding_result

        # 4. Assert - weryfikacja w bazie danych
        db.session.expire_all()
        fetched_worker = db.session.get(Worker, worker_id)
        assert fetched_worker.face_image == mocked_embedding_result

def test_update_worker_face_image_not_found(app_context):
    """Test czy funkcja rzuca błąd, gdy pracownik nie istnieje przy zmianie zdjęcia"""

    non_existent_id = 88888
    new_raw_image = b'some_image_data'

    with app_context.app_context():
        # Oczekujemy wyjątku ValueError
        with pytest.raises(ValueError) as excinfo:
            workerService.updateWorkerFaceImage(db, non_existent_id, new_raw_image)
        assert f"Worker with id {non_existent_id} not found" in str(excinfo.value)