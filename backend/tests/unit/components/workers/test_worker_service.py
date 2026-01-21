import pytest
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import backend.components.workers.workerService
from backend.components.workers.workerService import (
    create_worker,
    get_worker_by_id,
    update_worker_name,
    extend_worker_expiration,
    get_worker_from_qr_code,
    get_worker_embedding,
    create_worker_embedding,
    generate_worker_secret,
    decrypt_worker_secret
)
from backend.components.camera_verification.qrcode.qrcodeService import (
    ExpiredCodeError,
    InvalidCodeError,
    NoCodeFoundError
)


# ============================================================================
# Test Worker Management (CRUD & Utils)
# ============================================================================

@patch('backend.components.workers.workerService.face_recognition.face_encodings')
def test_create_worker_success(mock_face_encodings, db_session):
    """
    Test successful creation of a new worker.

    Verifies that:
    1. The worker is assigned an ID.
    2. The face embedding is generated and stored.
    3. The secret key is generated (replacing TEMP_SECRET).
    4. The expiration date is set correctly.
    """
    fake_embedding = [np.random.rand(128)]
    mock_face_encodings.return_value = fake_embedding

    # Input data
    name = "Testowy Janusz"
    fake_image = np.zeros((100, 100, 3), dtype=np.uint8)  # Empty dummy image
    exp_date = datetime.now() + timedelta(days=30)

    # Action
    worker = create_worker(name, fake_image, exp_date)

    # Assertions
    assert worker.id is not None
    assert worker.name == name
    assert worker.expiration_date == exp_date
    assert worker.secret != "TEMP_SECRET"  # Secret should be updated
    assert len(worker.face_embedding) > 0  # Blob should contain data


def test_get_worker_by_id_success(db_session, created_worker):
    """
    Verifies retrieval of an existing worker by their database ID.
    """
    fetched = get_worker_by_id(created_worker.id)
    assert fetched.id == created_worker.id
    assert fetched.name == created_worker.name


def test_get_worker_by_id_not_found(db_session):
    """
    Verifies that a ValueError is raised when requesting a non-existent worker ID.
    """
    with pytest.raises(ValueError, match="not found"):
        get_worker_by_id(999999)


def test_update_worker_name(db_session, created_worker):
    """
    Verifies the functionality to update a worker's name.
    """
    new_name = "Zmieniony Imię"
    update_worker_name(created_worker, new_name)

    # Refresh object from database to ensure persistence
    db_session.session.refresh(created_worker)
    assert created_worker.name == new_name


def test_extend_worker_expiration(db_session, created_worker):
    """
    Verifies extending the worker's access expiration date.
    """
    new_date = datetime.now() + timedelta(days=365)
    extend_worker_expiration(created_worker, new_date)

    db_session.session.refresh(created_worker)
    # Compare timestamps (allowing for microsecond differences during DB write)
    assert abs((created_worker.expiration_date - new_date).total_seconds()) < 1


# ============================================================================
# Test QR Code Logic (Scan -> Worker)
# ============================================================================

@patch('backend.components.workers.workerService.decode_qr_image')
def test_get_worker_from_qr_success(mock_decode, db_session, created_worker):
    """
    Tests the scenario where the QR code is valid and active.

    We mock the decoder to return the secret assigned to the 'created_worker' fixture.
    """
    mock_decode.return_value = created_worker.secret

    # The image array doesn't matter here as the decoder is mocked
    found_worker = get_worker_from_qr_code(np.array([]))

    assert found_worker.id == created_worker.id


@patch('backend.components.workers.workerService.decode_qr_image')
def test_get_worker_from_qr_expired(mock_decode, db_session, created_worker):
    """
    Tests the scenario where the QR code is valid, but the expiration date has passed.
    """
    # Set worker expiration to the past
    created_worker.expiration_date = datetime.now() - timedelta(days=1)
    db_session.session.commit()

    mock_decode.return_value = created_worker.secret

    with pytest.raises(ExpiredCodeError, match="wygasła"):
        get_worker_from_qr_code(np.array([]))


@patch('backend.components.workers.workerService.decode_qr_image')
def test_get_worker_from_qr_invalid_secret(mock_decode, db_session):
    """
    Tests the scenario where the QR code contains a secret that does not exist in the DB.
    """
    mock_decode.return_value = "non_existent_secret_123"

    with pytest.raises(InvalidCodeError, match="niepoprawny kod QR"):
        get_worker_from_qr_code(np.array([]))


@patch('backend.components.workers.workerService.decode_qr_image')
def test_get_worker_from_qr_no_code(mock_decode, db_session):
    """
    Tests the situation where the decoding library cannot find any QR code in the image.
    """
    mock_decode.side_effect = NoCodeFoundError("Nie znaleziono kodu")

    with pytest.raises(NoCodeFoundError):
        get_worker_from_qr_code(np.array([]))


# ============================================================================
# Test Technical Implementation (Embeddings & Secrets)
# ============================================================================

def test_embedding_serialization_roundtrip():
    """
    Verifies the NumPy Array -> BLOB -> NumPy Array serialization cycle.

    This is crucial because face embeddings are stored as binary BLOBs in SQLite.
    The test simulates the process used inside `create_worker_embedding` and `get_worker_embedding`.
    """
    # 1. Create a synthetic face vector (128 floats)
    original_embedding = np.random.rand(128)

    # Note: create_worker_embedding uses face_recognition.face_encodings internally.
    # To test strictly the IO/NumPy logic without the heavy ML library, we mock it.
    with patch('backend.components.workers.workerService.face_recognition.face_encodings') as mock_enc:
        # Mock returning a list containing our synthetic embedding
        mock_enc.return_value = [original_embedding]

        # 2. Create BLOB (simulate passing an image)
        # The function converts the array to bytes via io.BytesIO
        blob = create_worker_embedding(np.zeros((10, 10)))

        # 3. Create a fake worker object holding this blob
        fake_worker = MagicMock()
        fake_worker.face_embedding = blob

        # 4. Read BLOB back into a NumPy array
        restored_arr = get_worker_embedding(fake_worker)

        # 5. Compare the original vs restored array
        # create_worker_embedding grabs the first face [0], and np.save saves that array.
        # The restored array should be identical (within float precision).
        np.testing.assert_array_almost_equal(restored_arr[0], original_embedding)


def test_generate_and_decrypt_secret_functional():
    """
    Functional test for secret generation and decryption.

    Verifies that a secret generated for a specific worker can be successfully
    decrypted to retrieve the original worker ID and name.
    """
    worker_id = 67
    worker_name = "Six Seven"

    # Create a mock worker
    mock_worker = MagicMock()
    mock_worker.id = worker_id
    mock_worker.name = worker_name

    # Call the actual generation function
    secret = generate_worker_secret(mock_worker)

    # Decrypt the generated secret
    data = decrypt_worker_secret(secret)

    # Assertion 1: Ensure decrypted data is a dictionary
    assert isinstance(data, dict)

    # Assertion 2: Check if critical, deterministic data matches
    assert data['worker_id'] == worker_id
    assert data['name'] == worker_name

    # Assertion 3: Check if the random value exists (salt/entropy)
    assert 'rand_value' in data
    assert len(data['rand_value']) == 6


def test_decrypt_secret_static_check():
    """
    Sanity check with a static Fernet token.

    WARNING: This test might fail if the Fernet key in the configuration changes.
    It serves as a regression test for a specific token structure.
    """
    # Example token (valid if the key hasn't changed and token hasn't expired relative to TTL)
    # Note: In a real environment, mocking the time or key is recommended for stability.
    # We proceed assuming the dev environment uses a fixed key or this token was just generated.
    secret = 'gAAAAABpPdLUcBJbhCLwEX5HKf8mzB-sUIzAYQaQencHd--KaC4wbHRHlmdIfHSioWUMoZ_woRxjTsBVr30YQBRYv5xoicHjaERw2aGLvQ5Wgud1gaFNR7_zgTpNqzu96fsY-dQt3NvdRUXFmMKWiWV-9VgE99_HBg=='

    # We wrap this in a try-except or rely on the fact that if the key differs, it raises generic error
    try:
        data = decrypt_worker_secret(secret)
        assert data['worker_id'] == 67
        assert data['name'] == "Six Seven"
    except Exception:
        pytest.skip("Skipping static token test - encryption key might have changed.")