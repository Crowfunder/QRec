import pytest
import numpy as np
from unittest.mock import patch, MagicMock

# Importujemy funkcję testowaną oraz wyjątki
from backend.components.camera_verification.faceid.faceidService import (
    verify_worker_face,
    NoFacesFoundError,
    MultipleWorkersError,
    FaceNotMatchingError,
    FaceIDError
)
from backend.database.models import Worker

# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def mock_worker():
    """Tworzy prosty obiekt pracownika do testów."""
    # Atrybuty nie mają znaczenia, bo i tak mockujemy funkcję pobierającą embedding
    return Worker(id=1, name="Jan Testowy", face_embedding=b'dummy_blob')

@pytest.fixture
def fake_image():
    """Tworzy pusty obraz numpy (atrapę)."""
    return np.zeros((100, 100, 3), dtype=np.uint8)


# -----------------------------------------------------------------------------
# Testy
# -----------------------------------------------------------------------------

@patch('backend.components.camera_verification.faceid.faceidService.face_recognition')
@patch('backend.components.camera_verification.faceid.faceidService.get_worker_embedding')
def test_verify_worker_face_success(mock_get_embedding, mock_face_rec, mock_worker, fake_image):
    """
    Scenariusz:
    - Worker ma embedding w bazie.
    - Na zdjęciu wykryto dokładnie 1 twarz.
    - Twarze pasują do siebie.
    """
    # 1. Setup mocków
    # workerService zwraca wektor embedding pracownika
    mock_get_embedding.return_value = np.array([0.1, 0.2, 0.3])

    # face_recognition wykrywa jedną twarz na przesłanym zdjęciu
    mock_face_rec.face_encodings.return_value = [np.array([0.1, 0.2, 0.3])]

    # face_recognition potwierdza zgodność (True)
    mock_face_rec.compare_faces.return_value = [True]

    # 2. Wykonanie
    result = verify_worker_face(mock_worker, fake_image)

    # 3. Asercje
    assert result == [True]
    mock_face_rec.face_encodings.assert_called_once_with(fake_image)
    mock_face_rec.compare_faces.assert_called_once()


@patch('backend.components.camera_verification.faceid.faceidService.face_recognition')
@patch('backend.components.camera_verification.faceid.faceidService.get_worker_embedding')
def test_verify_worker_face_no_faces_found(mock_get_embedding, mock_face_rec, mock_worker, fake_image):
    """
    Scenariusz błędu: Na przesłanym zdjęciu nie wykryto żadnej twarzy.
    """
    mock_get_embedding.return_value = np.array([0.1])

    # Zwracamy pustą listę (brak wykrytych twarzy)
    mock_face_rec.face_encodings.return_value = []

    with pytest.raises(NoFacesFoundError) as excinfo:
        verify_worker_face(mock_worker, fake_image)

    assert "Nie znaleziono twarzy" in str(excinfo.value)


@patch('backend.components.camera_verification.faceid.faceidService.face_recognition')
@patch('backend.components.camera_verification.faceid.faceidService.get_worker_embedding')
def test_verify_worker_face_multiple_faces(mock_get_embedding, mock_face_rec, mock_worker, fake_image):
    """
    Scenariusz błędu: Na przesłanym zdjęciu wykryto więcej niż jedną twarz.
    """
    mock_get_embedding.return_value = np.array([0.1])

    # Zwracamy listę z dwoma elementami
    mock_face_rec.face_encodings.return_value = [np.array([0.1]), np.array([0.2])]

    with pytest.raises(MultipleWorkersError) as excinfo:
        verify_worker_face(mock_worker, fake_image)

    assert "Wykryto więcej niż jednego pracownika" in str(excinfo.value)


@patch('backend.components.camera_verification.faceid.faceidService.face_recognition')
@patch('backend.components.camera_verification.faceid.faceidService.get_worker_embedding')
def test_verify_worker_face_not_matching(mock_get_embedding, mock_face_rec, mock_worker, fake_image):
    """
    Scenariusz błędu: Wykryto twarz, ale nie należy ona do pracownika (brak zgodności).
    """
    mock_get_embedding.return_value = np.array([0.1])

    # Wykryto jedną twarz
    mock_face_rec.face_encodings.return_value = [np.array([0.9])]  # Inny wektor

    # Porównanie zwraca False
    mock_face_rec.compare_faces.return_value = [False]

    with pytest.raises(FaceNotMatchingError) as excinfo:
        verify_worker_face(mock_worker, fake_image)

    assert "Niezgodność zeskanowanej twarzy" in str(excinfo.value)


@patch('backend.components.camera_verification.faceid.faceidService.face_recognition')
@patch('backend.components.camera_verification.faceid.faceidService.get_worker_embedding')
def test_verify_worker_face_library_error(mock_get_embedding, mock_face_rec, mock_worker, fake_image):
    """
    Scenariusz błędu: Biblioteka face_recognition rzuca nieoczekiwany wyjątek.
    """
    mock_get_embedding.return_value = np.array([0.1])

    mock_face_rec.face_encodings.side_effect = Exception("Critical library failure")

    with pytest.raises(FaceIDError) as excinfo:
        verify_worker_face(mock_worker, fake_image)
    assert "Critical library failure" in str(excinfo.value)