from backend.components.camera_verification.faceid import faceidService
from backend.components.workers import workerService
import pytest
import os
import numpy as np
import face_recognition
from unittest.mock import patch, MagicMock
from datetime import datetime

from backend.components.camera_verification.faceid.faceidService import (
    verify_worker_face,
    FaceIDError,
    MultipleWorkersError,
    NoFacesFoundError,
    FaceNotMatchingError
)
from backend.database.models import Worker


# ============================================================================
# Fixtures & Setup
# ============================================================================

@pytest.fixture
def mock_worker(app):
    """Creates a simple mock of a Worker object."""
    with app.app_context():
        worker = MagicMock(spec=Worker)
        worker.id = 1
        worker.name = "Test Worker Mock"
        return worker

@pytest.fixture
def fake_image():
    """Creates an empty numpy array imitating an image."""
    return np.zeros((100, 100, 3), dtype=np.uint8)


@pytest.fixture
def test_image_path():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.normpath(os.path.join(current_dir, "../../../../../tests/assets/testimg.jpg"))
    if not os.path.exists(path):
        pytest.skip(f"Test image not found at {path}")
    return path


@pytest.fixture
def test_worker(app, db_session, test_image_path):  # <--- Dodano db_session
    """Creates a real worker with embedding from the testimg.jpg file."""
    with app.app_context():
        # Load and create embedding from test image
        test_image = face_recognition.load_image_file(test_image_path)

        worker = workerService.create_worker(
            name="Test Worker Real",
            face_image=test_image,
            expiration_date=datetime(2030, 12, 31)
        )
        yield worker

# --------------------------------------------------------------------------
# Testy verify_worker_face
# --------------------------------------------------------------------------

@patch('backend.components.camera_verification.faceid.faceidService.face_recognition.compare_faces')
@patch('backend.components.camera_verification.faceid.faceidService.face_recognition.face_encodings')
@patch('backend.components.camera_verification.faceid.faceidService.get_worker_embedding')
def test_verify_worker_face_success_mocked(mock_get_embedding, mock_encodings, mock_compare, mock_worker, fake_image):
    """Success Test Using Mocks."""
    fake_worker_embedding = [np.random.rand(128)]
    fake_scanned_embedding = [np.random.rand(128)]

    mock_get_embedding.return_value = fake_worker_embedding
    mock_encodings.return_value = fake_scanned_embedding
    mock_compare.return_value = [True]

    result = verify_worker_face(mock_worker, fake_image)

    assert result == [True]


@patch('backend.components.camera_verification.faceid.faceidService.face_recognition.face_encodings')
@patch('backend.components.camera_verification.faceid.faceidService.get_worker_embedding')
def test_verify_worker_face_multiple_faces_mocked(mock_get_embedding, mock_encodings, mock_worker, fake_image):
    """Multiple Face Error Test (Mock)."""
    mock_get_embedding.return_value = [np.random.rand(128)]
    mock_encodings.return_value = [np.random.rand(128), np.random.rand(128)]

    with pytest.raises(MultipleWorkersError, match="Wykryto więcej niż jednego pracownika"):
        verify_worker_face(mock_worker, fake_image)

@patch('backend.components.camera_verification.faceid.faceidService.face_recognition.compare_faces')
@patch('backend.components.camera_verification.faceid.faceidService.face_recognition.face_encodings')
@patch('backend.components.camera_verification.faceid.faceidService.get_worker_embedding')
def test_verify_worker_face_not_matching_mocked(mock_get_embedding, mock_encodings, mock_compare, mock_worker, fake_image):
    """Face mismatch test (mock)."""
    mock_get_embedding.return_value = [np.random.rand(128)]
    mock_encodings.return_value = [np.random.rand(128)]
    mock_compare.return_value = [False]

    with pytest.raises(FaceNotMatchingError, match="Niezgodność zeskanowanej twarzy"):
        verify_worker_face(mock_worker, fake_image)


# ============================================================================
# Test verify_worker_face - Success Cases
# ============================================================================


def test_verify_worker_face_matching_real(app, test_worker, test_image_path):
    """Test successful face verification when faces match."""
    with app.app_context():
        checked_image = face_recognition.load_image_file(test_image_path)
        result = faceidService.verify_worker_face(test_worker, checked_image)

        assert result is not None
        assert len(result) > 0
        assert result[0]


def test_verify_worker_face_with_different_image_real(app, test_worker):
    """Test face verification with a different person (should fail)."""
    dummy_image = np.zeros((600, 800, 3), dtype=np.uint8)

    with app.app_context():
        with pytest.raises(faceidService.NoFacesFoundError):
            faceidService.verify_worker_face(test_worker, dummy_image)




# ============================================================================
# Test verify_worker_face - Error Cases
# ============================================================================

def test_verify_worker_face_no_faces_detected(app, test_worker):
    """Test verification fails when no face is detected in checked image."""
    # Create an image with no faces (random noise)
    blank_image = np.zeros((600, 800, 3), dtype=np.uint8)

    with app.app_context():
        with pytest.raises(faceidService.NoFacesFoundError) as exc_info:
            faceidService.verify_worker_face(test_worker, blank_image)

        assert "Nie znaleziono twarzy" in str(exc_info.value)


@patch('backend.components.camera_verification.faceid.faceidService.face_recognition.compare_faces')
@patch('backend.components.camera_verification.faceid.faceidService.face_recognition.face_encodings')
@patch('backend.components.camera_verification.faceid.faceidService.get_worker_embedding')
def test_verify_worker_face_not_matching(mock_get_embedding, mock_encodings, mock_compare, mock_worker, fake_image):
    """
    Checks whether a FaceNotMatchingError exception is thrown when a face does not match the worker.
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
    Checks whether generic face_recognition library errors are caught and thrown as FaceIDError.
    """
    mock_get_embedding.return_value = [np.random.rand(128)]
    # Symulujemy błąd biblioteki (np. problem z pamięcią, zły format danych)
    mock_encodings.side_effect = Exception("Critical Library Fail")

    with pytest.raises(FaceIDError, match="Critical Library Fail"):
        verify_worker_face(mock_worker, fake_image)


def test_verify_worker_face_multiple_faces_detected_real(app, test_worker, test_image_path):
    """Test verification fails when multiple faces are detected."""
    with app.app_context():
        test_image = face_recognition.load_image_file(test_image_path)

        with patch('face_recognition.face_encodings') as mock_encodings:
            mock_encodings.return_value = [np.random.randn(128), np.random.randn(128)]

            with pytest.raises(faceidService.MultipleWorkersError) as exc_info:
                faceidService.verify_worker_face(test_worker, test_image)

            assert "więcej niż jednego" in str(exc_info.value).lower()


def test_verify_worker_face_not_matching_real(app, test_worker, test_image_path):
    """Test verification fails when face does not match worker."""
    with app.app_context():
        test_image = face_recognition.load_image_file(test_image_path)

        # Mock face_recognition to return non-matching faces
        with patch('face_recognition.compare_faces') as mock_compare:
            mock_compare.return_value = [False]

            with pytest.raises(faceidService.FaceNotMatchingError) as exc_info:
                faceidService.verify_worker_face(test_worker, test_image)

            assert "Niezgodność" in str(exc_info.value)


def test_verify_worker_face_encoding_error(app, test_worker):
    """Test handling of face encoding errors."""
    dummy_image = np.zeros((600, 800, 3), dtype=np.uint8)

    with app.app_context():
        with patch('face_recognition.face_encodings') as mock_encodings:
            mock_encodings.side_effect = Exception("Face recognition library error")

            with pytest.raises(faceidService.FaceIDError):
                faceidService.verify_worker_face(test_worker, dummy_image)


def test_verify_worker_face_comparison_error(app, test_worker):
    """Test handling of face comparison errors."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.normpath(os.path.join(current_dir, "../../../../assets/testimg.jpg"))

    if not os.path.exists(image_path):
        pytest.skip(f"Test image not found at {image_path}")

    with app.app_context():
        test_image = face_recognition.load_image_file(image_path)

        with patch('face_recognition.compare_faces') as mock_compare:
            mock_compare.side_effect = Exception("Comparison error")

            with pytest.raises(faceidService.FaceIDError):
                faceidService.verify_worker_face(test_worker, test_image)