import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from backend.components.camera_verification.faceid.faceidService import (
    verify_worker_face,
    FaceIDError,
    MultipleWorkersError,
    NoFacesFoundError,
    FaceNotMatchingError
)
from backend.database.models import Worker


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

@pytest.fixture
def mock_worker(app):
    """
    Tworzy prostego mocka obiektu Worker.
    Wymaga kontekstu aplikacji, ponieważ Worker jest modelem SQLAlchemy,
    a MagicMock(spec=Worker) próbuje uzyskać dostęp do atrybutów klasy powiązanych z DB.
    """
    with app.app_context():
        worker = MagicMock(spec=Worker)
        worker.id = 1
        worker.name = "Test Worker"
        return worker


@pytest.fixture
def fake_image():
    """Tworzy pustą tablicę numpy udającą obraz."""
    return np.zeros((100, 100, 3), dtype=np.uint8)


# --------------------------------------------------------------------------
# Testy verify_worker_face
# --------------------------------------------------------------------------

@patch('backend.components.camera_verification.faceid.faceidService.face_recognition.compare_faces')
@patch('backend.components.camera_verification.faceid.faceidService.face_recognition.face_encodings')
@patch('backend.components.camera_verification.faceid.faceidService.get_worker_embedding')
def test_verify_worker_face_success(mock_get_embedding, mock_encodings, mock_compare, mock_worker, fake_image):
    """
    Scenariusz pozytywny:
    1. Pobrano embedding pracownika.
    2. Znaleziono dokładnie jedną twarz na zdjęciu.
    3. Twarz pasuje do wzorca.
    """
    # Setup
    fake_worker_embedding = [np.random.rand(128)]
    fake_scanned_embedding = [np.random.rand(128)]  # Lista z jednym elementem (jedna twarz)

    mock_get_embedding.return_value = fake_worker_embedding
    mock_encodings.return_value = fake_scanned_embedding
    mock_compare.return_value = [True]  # Twarze pasują

    # Action
    result = verify_worker_face(mock_worker, fake_image)

    # Assert
    assert result == [True]
    mock_get_embedding.assert_called_once_with(mock_worker)
    mock_encodings.assert_called_once_with(fake_image)
    mock_compare.assert_called_once_with(fake_worker_embedding, fake_scanned_embedding)


@patch('backend.components.camera_verification.faceid.faceidService.face_recognition.face_encodings')
@patch('backend.components.camera_verification.faceid.faceidService.get_worker_embedding')
def test_verify_worker_face_multiple_faces(mock_get_embedding, mock_encodings, mock_worker, fake_image):
    """
    Sprawdza, czy rzucany jest wyjątek MultipleWorkersError, gdy na zdjęciu jest więcej niż jedna twarz.
    """
    mock_get_embedding.return_value = [np.random.rand(128)]
    # Symulujemy znalezienie 2 twarzy
    mock_encodings.return_value = [np.random.rand(128), np.random.rand(128)]

    with pytest.raises(MultipleWorkersError, match="Wykryto więcej niż jednego pracownika"):
        verify_worker_face(mock_worker, fake_image)


@patch('backend.components.camera_verification.faceid.faceidService.face_recognition.face_encodings')
@patch('backend.components.camera_verification.faceid.faceidService.get_worker_embedding')
def test_verify_worker_face_no_faces(mock_get_embedding, mock_encodings, mock_worker, fake_image):
    """
    Sprawdza, czy rzucany jest wyjątek NoFacesFoundError, gdy nie wykryto twarzy.
    """
    mock_get_embedding.return_value = [np.random.rand(128)]
    # Pusta lista - brak twarzy
    mock_encodings.return_value = []

    with pytest.raises(NoFacesFoundError, match="Nie znaleziono twarzy"):
        verify_worker_face(mock_worker, fake_image)


@patch('backend.components.camera_verification.faceid.faceidService.face_recognition.compare_faces')
@patch('backend.components.camera_verification.faceid.faceidService.face_recognition.face_encodings')
@patch('backend.components.camera_verification.faceid.faceidService.get_worker_embedding')
def test_verify_worker_face_not_matching(mock_get_embedding, mock_encodings, mock_compare, mock_worker, fake_image):
    """
    Sprawdza, czy rzucany jest wyjątek FaceNotMatchingError, gdy twarz nie pasuje do pracownika.
    """
    mock_get_embedding.return_value = [np.random.rand(128)]
    mock_encodings.return_value = [np.random.rand(128)]
    # Porównanie zwraca False
    mock_compare.return_value = [False]

    with pytest.raises(FaceNotMatchingError, match="Niezgodność zeskanowanej twarzy"):
        verify_worker_face(mock_worker, fake_image)


@patch('backend.components.camera_verification.faceid.faceidService.face_recognition.face_encodings')
@patch('backend.components.camera_verification.faceid.faceidService.get_worker_embedding')
def test_verify_worker_face_library_error(mock_get_embedding, mock_encodings, mock_worker, fake_image):
    """
    Sprawdza, czy ogólne błędy biblioteki face_recognition są łapane i rzucane jako FaceIDError.
    """
    mock_get_embedding.return_value = [np.random.rand(128)]
    # Symulujemy błąd biblioteki (np. problem z pamięcią, zły format danych)
    mock_encodings.side_effect = Exception("Critical Library Fail")

    with pytest.raises(FaceIDError, match="Critical Library Fail"):
        verify_worker_face(mock_worker, fake_image)