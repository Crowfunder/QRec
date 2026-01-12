import pytest
import os
import io
import numpy as np
import cv2
import face_recognition
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime, timedelta
from flask import Flask

from backend.app import create_app, db
from backend.components.camera_verification import verificationController
from backend.components.workers import workerService
from backend.database.models import Worker
from backend.components.utils import imageUtils


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
            name="Jacob Czajka",
            face_image=test_image,
            expiration_date=datetime(2029, 1, 1)
        )

        yield worker


@pytest.fixture
def client(app_context):
    """Create Flask test client."""
    test_client = app_context.test_client()
    yield test_client
    test_client.delete()


@pytest.fixture
def test_image_with_qrcode(app_context, client, test_worker):
    """
    Create a composite test image by joining testimg.jpg with the worker's QR code.
    Places QR code beside the face image without distortion.
    Returns the composite image as bytes.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    testimg_path = os.path.normpath(os.path.join(current_dir, "testimg.jpg"))

    if not os.path.exists(testimg_path):
        pytest.skip(f"Test image not found at {testimg_path}")

    with app_context.app_context():
        # Get the QR code from the API endpoint
        response = client.get(f'/api/workers/entrypass/{test_worker.id}')
        
        if response.status_code != 200:
            pytest.skip("Failed to generate QR code from API")

        # Read QR code from response
        qr_code_bytes = response.data
        qr_code_array = np.frombuffer(qr_code_bytes, np.uint8)
        qr_code_image = cv2.imdecode(qr_code_array, cv2.IMREAD_COLOR)

        if qr_code_image is None:
            pytest.skip("Failed to decode QR code image")

        # Load the face image
        face_image = cv2.imread(testimg_path)

        if face_image is None:
            pytest.skip("Failed to load test image")

        # Make QR code 70% of face image height (much larger)
        qr_height = int(face_image.shape[0] * 0.7)
        qr_width = int(qr_height)  # QR codes are square - maintain aspect ratio
        
        qr_resized = cv2.resize(qr_code_image, (qr_width, qr_height), interpolation=cv2.INTER_AREA)

        # Create composite image by placing QR code beside face image (not on top)
        # Total width = face_width + qr_width + small padding
        padding = 20
        total_width = face_image.shape[1] + qr_width + padding * 2
        
        # Use the taller of the two images as height
        total_height = max(face_image.shape[0], qr_height) + padding * 2

        composite_image = np.ones((total_height, total_width, 3), dtype=np.uint8) * 255

        # Place face image on the left
        face_y_start = (total_height - face_image.shape[0]) // 2
        face_x_start = padding
        composite_image[
            face_y_start:face_y_start + face_image.shape[0],
            face_x_start:face_x_start + face_image.shape[1]
        ] = face_image

        # Place QR code on the right
        qr_y_start = (total_height - qr_height) // 2
        qr_x_start = face_x_start + face_image.shape[1] + padding
        composite_image[
            qr_y_start:qr_y_start + qr_height,
            qr_x_start:qr_x_start + qr_width
        ] = qr_resized

        # Encode composite image to bytes
        success, buffer = cv2.imencode('.jpg', composite_image)
        if not success:
            pytest.skip("Failed to encode composite image")

        return buffer.tobytes()


# ============================================================================
# Test POST /api/skan - Success Cases
# ============================================================================

def test_post_camera_scan_success(client, app_context, test_worker, test_image_with_qrcode):
    """
    Test successful verification with valid QR code and matching face.
    QR code detection is iffy so it's attempted 10 times before we assume the endpoint is broken.
    """
    with app_context.app_context():
        # Send request with composite image containing QR code and face
        i = 0
        response = None
        while i != 10:
            response = client.post(
                '/api/skan',
                data={'file': (io.BytesIO(test_image_with_qrcode), 'composite.jpg')},
                content_type='multipart/form-data'
            )
            i+=1

            if response.status_code == 200:
                break

        assert response.status_code == 200


# ============================================================================
# Test POST /api/skan - Error Cases
# ============================================================================

def test_post_camera_scan_missing_file(client):
    """Test endpoint returns 400 when file is missing."""
    response = client.post(
        '/api/skan',
        data={},
        content_type='multipart/form-data'
    )

    assert response.status_code == 400
    assert 'error' in response.json
    assert 'Brak pliku w żądaniu' in response.json['error']


def test_post_camera_scan_invalid_image(client):
    """Test endpoint returns 500 when image file is corrupted."""
    invalid_image_bytes = b"This is not a valid image"

    response = client.post(
        '/api/skan',
        data={'file': (io.BytesIO(invalid_image_bytes), 'invalid.jpg')},
        content_type='multipart/form-data'
    )

    assert response.status_code == 500


def test_post_camera_scan_empty_file(client):
    """Test endpoint returns 500 when file is empty."""
    response = client.post(
        '/api/skan',
        data={'file': (io.BytesIO(b''), 'empty.jpg')},
        content_type='multipart/form-data'
    )

    assert response.status_code == 500


def test_post_camera_scan_no_qr_code(client, app_context):
    """Test endpoint returns 400 when no QR code is found in image."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    testimg_path = os.path.normpath(os.path.join(current_dir, "testimg.jpg"))

    if not os.path.exists(testimg_path):
        pytest.skip(f"Test image not found at {testimg_path}")

    with app_context.app_context():
        # Use plain face image without QR code
        with open(testimg_path, 'rb') as f:
            image_bytes = f.read()
            response = client.post(
                '/api/skan',
                data={'file': (io.BytesIO(image_bytes), 'testimg.jpg')},
                content_type='multipart/form-data'
            )

            assert response.status_code == 400


# ============================================================================
# Test POST /api/skan - Error Cases - Expired QR Code
# ============================================================================
def test_post_camera_scan_expired_qr_code(client, app_context, test_worker, test_image_with_qrcode):
    """
    Test endpoint returns 403 when QR code is expired.
    Repeat at most 10 times if fails, QR code detection often fails.
    """
    with app_context.app_context():
        with patch('backend.components.workers.workerService.get_worker_from_qr_code') as mock_get_worker:
            mock_get_worker.return_value = test_worker

            # Store original expiration date
            original_expiration = test_worker.expiration_date
            
            # Set worker expiration to the past
            workerService.extend_worker_expiration(workerService.get_worker_by_id(test_worker.id), datetime.now() - timedelta(days=5))
            
            i = 0
            response = 10
            while i != 10:
                # Send request with expired worker's QR code
                response = client.post(
                    '/api/skan',
                    data={'file': (io.BytesIO(test_image_with_qrcode), 'composite.jpg')},
                    content_type='multipart/form-data'
                )
                if response.status_code == 403:
                    break
                i+= 1
            
            # Should return 403 because the QR code is expired
            assert response.status_code == 403
            
            # Restore original expiration date
            workerService.extend_worker_expiration(workerService.get_worker_by_id(test_worker.id), original_expiration)


# ============================================================================
# Test POST /api/skan - Response Structure
# ============================================================================

def test_post_camera_scan_response_structure(client, app_context, test_worker, test_image_with_qrcode):
    """Test that response always contains 'code' and 'messages' field."""
    with app_context.app_context():
        with patch('backend.components.workers.workerService.get_worker_from_qr_code') as mock_get_worker:
            with patch('backend.components.camera_verification.faceid.faceidService.verify_worker_face') as mock_verify:
                mock_get_worker.return_value = test_worker
                mock_verify.return_value = [True]

                response = client.post(
                    '/api/skan',
                    data={'file': (io.BytesIO(test_image_with_qrcode), 'composite.jpg')},
                    content_type='multipart/form-data'
                )

                assert 'code' in response.json
                assert 'message' in response.json