import pytest
import io
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch, MagicMock


# --- Testy GET /api/workers ---

@patch('backend.components.workers.workerController.get_all_workers')
def test_get_all_workers_empty(mock_get_all, client):
    """Test for downloading the employee list when the database is empty."""
    mock_get_all.return_value = []
    response = client.get('/api/workers')
    assert response.status_code == 200
    assert response.json == []


@patch('backend.components.workers.workerController.get_all_workers')
def test_get_all_workers_populated(mock_get_all, client):
    """Test for downloading a list of employees with data."""
    # Używamy SimpleNamespace
    fake_worker = SimpleNamespace(
        id=1,
        name="Jan Kowalski",
        expiration_date=datetime(2030, 1, 1)
    )

    mock_get_all.return_value = [fake_worker]

    response = client.get('/api/workers')
    assert response.status_code == 200
    data = response.json
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]['name'] == "Jan Kowalski"


@patch('backend.components.workers.workerController.get_worker_by_id')
def test_get_single_worker_success(mock_get_by_id, client):
    """Test for downloading a single employee by ID."""
    fake_worker = SimpleNamespace(
        id=1,
        name="Jan Kowalski",
        expiration_date=datetime(2030, 1, 1)
    )

    mock_get_by_id.return_value = fake_worker

    response = client.get('/api/workers/1')
    assert response.status_code == 200
    assert response.json['name'] == "Jan Kowalski"


@patch('backend.components.workers.workerController.get_worker_by_id')
def test_get_single_worker_not_found(mock_get_by_id, client):
    """
    Test for a 404 error.
    Mock returns None, which (if it doesn't throw a ValueError in the service) will trigger an 'if not worker' in the controller.
    """
    mock_get_by_id.return_value = None

    response = client.get('/api/workers/999')
    assert response.status_code == 404


# --- Testy POST /api/workers (Tworzenie) ---

@patch('backend.components.workers.workerController.parse_image')
@patch('backend.components.workers.workerController.create_worker')
def test_create_worker_success(mock_create_worker, mock_parse_image, client):
    """Test for correct employee creation."""
    mock_parse_image.return_value = "fake_image_array"

    fake_worker = SimpleNamespace(
        id=1,
        name="Test Worker",
        expiration_date=datetime(2030, 1, 1)
    )
    mock_create_worker.return_value = fake_worker

    data = {
        'name': 'Test Worker',
        'expiration_date': '2030-01-01T00:00:00',
        'file': (io.BytesIO(b"fake_image_content"), 'face.jpg')
    }

    response = client.post(
        '/api/workers',
        data=data,
        content_type='multipart/form-data'
    )

    assert response.status_code == 200
    assert response.json['name'] == 'Test Worker'


def test_create_worker_missing_data(client):
    """Missing data validation test."""
    data = {'name': 'Incomplete Worker'}  # Brak pliku
    response = client.post(
        '/api/workers',
        data=data,
        content_type='multipart/form-data'
    )
    assert response.status_code == 400


# --- Testy PUT /api/workers/<id> (Aktualizacja) ---

@patch('backend.components.workers.workerController.get_worker_by_id')
@patch('backend.components.workers.workerController.update_worker_name')
@patch('backend.components.workers.workerController.extend_worker_expiration')
def test_update_worker_success(mock_extend, mock_update_name, mock_get_by_id, client):
    """Employee update test."""
    fake_worker = SimpleNamespace(
        id=1,
        name="Old Name",
        expiration_date=datetime(2030, 1, 1)
    )
    mock_get_by_id.return_value = fake_worker

    data = {
        'name': 'New Name',
        'expiration_date': '2035-01-01T00:00:00'
    }

    response = client.put(
        '/api/workers/1',
        data=data,
        content_type='multipart/form-data'
    )

    assert response.status_code == 200
    # Sprawdzamy czy mocki serwisów zostały wywołane z naszym obiektem
    mock_update_name.assert_called_with(fake_worker, 'New Name')
    mock_extend.assert_called()


@patch('backend.components.workers.workerController.get_worker_by_id')
def test_update_worker_not_found(mock_get_by_id, client):
    """Test to update a non-existent employee."""
    mock_get_by_id.return_value = None
    response = client.put('/api/workers/999', data={'name': 'Ghost'})
    assert response.status_code == 404


# --- Testy PUT /api/workers/invalidate/<id> ---

@patch('backend.components.workers.workerController.get_worker_by_id')
@patch('backend.components.workers.workerController.extend_worker_expiration')
def test_invalidate_worker(mock_extend, mock_get_by_id, client):
    """Employee invalidation test."""
    fake_worker = SimpleNamespace(
        id=1,
        name="Jan Kowalski",
        expiration_date=datetime(2030, 1, 1)
    )
    mock_get_by_id.return_value = fake_worker

    response = client.put('/api/workers/invalidate/1')

    assert response.status_code == 200
    mock_extend.assert_called()


@patch('backend.components.workers.workerController.get_worker_by_id')
def test_invalidate_worker_not_found(mock_get_by_id, client):
    """Test to invalidate a non-existent employee."""
    mock_get_by_id.return_value = None
    response = client.put('/api/workers/invalidate/999')
    assert response.status_code == 404


# --- Testy GET /api/workers/entrypass/<id> ---

@patch('backend.components.workers.workerController.generate_worker_entry_pass')
@patch('backend.components.workers.workerController.get_worker_by_id')
def test_get_worker_entry_pass(mock_get_by_id, mock_generate, client):
    """Pass download test."""
    fake_worker = SimpleNamespace(id=1)
    mock_get_by_id.return_value = fake_worker
    mock_generate.return_value = b"fake_png_bytes"

    response = client.get('/api/workers/entrypass/1')

    assert response.status_code == 200
    assert response.mimetype == 'image/png'


@patch('backend.components.workers.workerController.get_worker_by_id')
def test_get_worker_entry_pass_not_found(mock_get_by_id, client):
    """ Test to download a pass for a non-existent employee. """
    mock_get_by_id.return_value = None
    response = client.get('/api/workers/entrypass/999')
    assert response.status_code == 404