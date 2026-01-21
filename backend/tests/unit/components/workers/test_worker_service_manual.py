import pytest
import os
import io
import numpy as np
import face_recognition
from unittest.mock import patch, MagicMock
from datetime import datetime
from backend.app import create_app, db
from backend.database.models import Worker
from backend.components.workers import workerService


# ============================================================================
# Test Setup & Fixtures
# ============================================================================

@pytest.fixture
def app_context():
    """
    Creates an isolated application context with an in-memory SQLite database.
    Ensures a clean state for every test function using this fixture.
    """
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


# ============================================================================
# Test: Embedding Generation (Integration)
# ============================================================================

def test_create_worker_embedding_from_file():
    """
    Integration test for face embedding generation using a real image file.

    Verifies that:
    1. The test image file exists.
    2. The service converts the image to a binary BLOB (bytes).
    3. The BLOB can be deserialized back into a valid NumPy array of shape (128,).
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Calculate path: backend/tests/unit/components/workers -> backend/tests/assets
    image_path = os.path.normpath(os.path.join(current_dir, "../../../assets/testimg.jpg"))

    print(f"Looking for test image at: {image_path}")
    if not os.path.exists(image_path):
        pytest.skip(f"Skipped: Test image not found at {image_path}")

    image_input = face_recognition.load_image_file(image_path)

    # Execute service function
    result_blob = workerService.create_worker_embedding(image_input)

    # Basic assertions
    assert isinstance(result_blob, bytes)
    assert len(result_blob) > 0

    # Verify that the blob is a valid serialized NumPy array
    buffer = io.BytesIO(result_blob)
    embeddings = np.load(buffer, allow_pickle=True)

    assert len(embeddings) > 0, "No faces detected in the test image."
    # face_recognition library generates 128-dimensional vectors
    assert len(embeddings[0]) == 128


# ============================================================================
# Test: Worker CRUD Operations
# ============================================================================

@patch('backend.components.workers.workerService.create_worker_embedding')
def test_create_worker_adds_to_db(mock_create_embedding, app_context):
    """
    Tests if the `create_worker` function correctly persists a new worker to the database.

    We mock the embedding generation to avoid the overhead of the ML library
    and focus on database interactions.
    """
    mock_create_embedding.return_value = b'test_blob_data'
    name = "John Doe"
    fake_image = MagicMock()  # Mock the image object
    expiration = datetime(2025, 12, 31)

    with app_context.app_context():
        # Action: Create worker via service
        worker = workerService.create_worker(name, fake_image, expiration)

        assert worker.id is not None
        assert worker.name == name

        # Verification: Fetch from DB to ensure persistence
        fetched_worker = db.session.get(Worker, worker.id)
        assert fetched_worker is not None
        assert fetched_worker.name == "John Doe"
        assert fetched_worker.face_embedding == b'test_blob_data'


def test_extend_worker_expiration_success(app_context):
    """
    Tests the `extend_worker_expiration` functionality.

    Verifies that the expiration date is updated in the database object.
    """
    initial_date = datetime(2024, 1, 1)
    new_date = datetime(2030, 1, 1)

    with app_context.app_context():
        # 1. Setup: Create a worker with an initial date
        worker = Worker(
            name="Mark ToChange",
            face_embedding=b'dummy_data',
            expiration_date=initial_date,
            secret="dummy_secret"
        )
        db.session.add(worker)
        db.session.commit()

        # Retrieve the object (service requires an object, not ID)
        worker_to_update = db.session.get(Worker, worker.id)

        # 2. Action: Extend expiration
        updated_worker = workerService.extend_worker_expiration(worker_to_update, new_date)

        # 3. Verification
        assert updated_worker.expiration_date == new_date

        # Force session refresh to check DB state
        db.session.expire_all()
        fetched_worker = db.session.get(Worker, worker.id)
        assert fetched_worker.expiration_date == new_date


def test_update_worker_name_success(app_context):
    """
    Tests the `update_worker_name` functionality.

    Verifies that the worker's name is successfully updated in the database.
    """
    initial_name = "Jane Doe"
    new_name = "Jane Smith"

    with app_context.app_context():
        # Setup
        worker = Worker(
            name=initial_name,
            face_embedding=b'dummy_data',
            expiration_date=datetime(2025, 12, 12),
            secret="dummy_secret"
        )
        db.session.add(worker)
        db.session.commit()

        # Action
        worker_to_update = db.session.get(Worker, worker.id)
        workerService.update_worker_name(worker_to_update, new_name)

        # Verification
        db.session.expire_all()
        fetched_worker = db.session.get(Worker, worker.id)
        assert fetched_worker.name == new_name


def test_update_worker_face_embedding_success(app_context):
    """
    Tests the `update_worker_face_image` functionality.

    Verifies that providing a new image triggers the embedding recalculation
    and updates the database field.
    """
    initial_name = "Test Face Update"
    initial_face_data = b'old_dummy_embedding'
    new_raw_image = b'new_raw_image_data_jpg'
    mocked_embedding_result = b'new_calculated_embedding_123'

    with app_context.app_context():
        # Setup
        worker = Worker(
            name=initial_name,
            face_embedding=initial_face_data,
            expiration_date=datetime(2025, 12, 12),
            secret="dummy_secret"
        )
        db.session.add(worker)
        db.session.commit()

        # Mock the internal embedding function to isolate logic
        with patch('backend.components.workers.workerService.create_worker_embedding') as mock_embedding:
            mock_embedding.return_value = mocked_embedding_result

            # Action
            worker_to_update = db.session.get(Worker, worker.id)
            workerService.update_worker_face_image(worker_to_update, new_raw_image)

            # Assert internal call
            mock_embedding.assert_called_once_with(new_raw_image)

        # Verification
        db.session.expire_all()
        fetched_worker = db.session.get(Worker, worker.id)
        assert fetched_worker.face_embedding == mocked_embedding_result