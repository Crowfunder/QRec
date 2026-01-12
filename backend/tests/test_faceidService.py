import pytest
import os
import io
import numpy as np
import face_recognition
from unittest.mock import patch, MagicMock
from datetime import datetime

from backend.app import create_app, db
from backend.components.camera_verification.faceid import faceidService
from backend.components.workers import workerService
from backend.database.models import Worker


@pytest.fixture
def app_context():
    """Create app context with in-memory SQLite database for testing."""
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"
    })

    with app.app_context():
        db.create_all()
        yield app


@pytest.fixture
def test_worker(app_context):
    """Create a test worker with face embedding from testimg.jpg."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.normpath(os.path.join(current_dir, "testimg.jpg"))

    if not os.path.exists(image_path):
        pytest.skip(f"Test image not found at {image_path}")

    with app_context.app_context():
        # Load and create embedding from test image
        test_image = face_recognition.load_image_file(image_path)
        
        # Use workerService.create_worker to create worker properly
        worker = workerService.create_worker(
            name="Test Worker",
            face_image=test_image,
            expiration_date=datetime(2030, 12, 31)
        )
        yield worker


# ============================================================================
# Test verify_worker_face - Success Cases
# ============================================================================

def test_verify_worker_face_matching(app_context, test_worker):
    """Test successful face verification when faces match."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.normpath(os.path.join(current_dir, "testimg.jpg"))

    if not os.path.exists(image_path):
        pytest.skip(f"Test image not found at {image_path}")

    with app_context.app_context():
        # Load the same image for verification
        checked_image = face_recognition.load_image_file(image_path)

        # Verify should succeed
        result = faceidService.verify_worker_face(test_worker, checked_image)

        assert result is not None
        assert len(result) > 0
        assert result[0]


def test_verify_worker_face_with_different_image(app_context, test_worker):
    """Test face verification with a different person (should fail)."""
    # Create a dummy image with different face encoding
    dummy_image = np.random.randint(0, 256, (600, 800, 3), dtype=np.uint8)

    with app_context.app_context():
        with pytest.raises(faceidService.NoFacesFoundError):
            faceidService.verify_worker_face(test_worker, dummy_image)


# ============================================================================
# Test verify_worker_face - Error Cases
# ============================================================================

def test_verify_worker_face_no_faces_detected(app_context, test_worker):
    """Test verification fails when no face is detected in checked image."""
    # Create an image with no faces (random noise)
    blank_image = np.zeros((600, 800, 3), dtype=np.uint8)

    with app_context.app_context():
        with pytest.raises(faceidService.NoFacesFoundError) as exc_info:
            faceidService.verify_worker_face(test_worker, blank_image)

        assert "Nie znaleziono twarzy" in str(exc_info.value)


def test_verify_worker_face_multiple_faces_detected(app_context, test_worker):
    """Test verification fails when multiple faces are detected."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.normpath(os.path.join(current_dir, "testimg.jpg"))

    if not os.path.exists(image_path):
        pytest.skip(f"Test image not found at {image_path}")

    with app_context.app_context():
        # Load test image
        test_image = face_recognition.load_image_file(image_path)
        
        # Create a mock image with multiple face encodings
        with patch('face_recognition.face_encodings') as mock_encodings:
            # Simulate multiple faces detected
            mock_encodings.return_value = [np.random.randn(128), np.random.randn(128)]

            with pytest.raises(faceidService.MultipleWorkersError) as exc_info:
                faceidService.verify_worker_face(test_worker, test_image)

            assert "więcej niż jednego" in str(exc_info.value).lower()


def test_verify_worker_face_not_matching(app_context, test_worker):
    """Test verification fails when face does not match worker."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.normpath(os.path.join(current_dir, "testimg.jpg"))

    if not os.path.exists(image_path):
        pytest.skip(f"Test image not found at {image_path}")

    with app_context.app_context():
        test_image = face_recognition.load_image_file(image_path)

        # Mock face_recognition to return non-matching faces
        with patch('face_recognition.compare_faces') as mock_compare:
            mock_compare.return_value = [False]

            with pytest.raises(faceidService.FaceNotMatchingError) as exc_info:
                faceidService.verify_worker_face(test_worker, test_image)

            assert "Niezgodność" in str(exc_info.value)


def test_verify_worker_face_encoding_error(app_context, test_worker):
    """Test handling of face encoding errors."""
    dummy_image = np.zeros((600, 800, 3), dtype=np.uint8)

    with app_context.app_context():
        with patch('face_recognition.face_encodings') as mock_encodings:
            mock_encodings.side_effect = Exception("Face recognition library error")

            with pytest.raises(faceidService.FaceIDError):
                faceidService.verify_worker_face(test_worker, dummy_image)


def test_verify_worker_face_comparison_error(app_context, test_worker):
    """Test handling of face comparison errors."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.normpath(os.path.join(current_dir, "testimg.jpg"))

    if not os.path.exists(image_path):
        pytest.skip(f"Test image not found at {image_path}")

    with app_context.app_context():
        test_image = face_recognition.load_image_file(image_path)

        with patch('face_recognition.compare_faces') as mock_compare:
            mock_compare.side_effect = Exception("Comparison error")

            with pytest.raises(faceidService.FaceIDError):
                faceidService.verify_worker_face(test_worker, test_image)
