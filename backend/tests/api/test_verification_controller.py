import pytest
import os
import io
from unittest.mock import patch, MagicMock
from backend.app import create_app


# -----------------------------------------------------------------------------
# Fixtures (lokalne, skoro brak conftest.py)
# -----------------------------------------------------------------------------

@pytest.fixture
def client():
    """
    Tworzy klienta testowego z aplikacją działającą na bazie w pamięci.
    """
    # Ustawiamy bazę w pamięci, aby nie tworzyć plików
    os.environ["FLASK_DB_PATH"] = ":memory:"

    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "QR_SECRET_KEY": b'test_secret'
    })

    with app.test_client() as client:
        with app.app_context():
            pass
        yield client

    # Sprzątanie
    if "FLASK_DB_PATH" in os.environ:
        del os.environ["FLASK_DB_PATH"]


@pytest.fixture
def mock_response_object():
    """
    Pomocniczy mock symulujący obiekt zwracany przez verification_response_handler.
    """
    mock = MagicMock()
    mock.asdict.return_value = {"code": 0, "message": "Test Message"}
    mock.code = 0
    mock.message = "Test Message"
    mock.logged = False
    return mock


# -----------------------------------------------------------------------------
# Testy Endpointu /api/skan
# -----------------------------------------------------------------------------

def test_scan_no_file(client):
    """Sprawdza reakcję na brak pliku w żądaniu."""
    response = client.post('/api/skan')

    assert response.status_code == 400
    assert "Brak pliku" in response.get_json()['error']


@patch('backend.components.camera_verification.verificationController.parse_image')
@patch('backend.components.camera_verification.verificationController.get_worker_from_qr_code')
@patch('backend.components.camera_verification.verificationController.verify_worker_face')
@patch('backend.components.camera_verification.verificationController.verification_response_handler')
@patch('backend.components.camera_verification.verificationController.log_worker_entry')
def test_scan_success(mock_log, mock_handler, mock_verify, mock_get_worker, mock_parse, client, mock_response_object):
    """
    Scenariusz:
    - parse_image zwraca cokolwiek
    - get_worker znajduje pracownika
    - verify_face przechodzi bez błędu
    - handler zwraca sukces (code 0)
    """
    # Setup mocków
    mock_get_worker.return_value = MagicMock(id=1)  # Znaleziono pracownika
    mock_verify.return_value = True  # Twarz pasuje

    # Konfiguracja odpowiedzi handlera (Sukces -> code 0)
    mock_response_object.code = 0
    mock_response_object.message = "Weryfikacja udana"
    mock_response_object.logged = True
    mock_handler.return_value = mock_response_object

    # Wykonanie żądania (przesyłamy dummy plik)
    data = {
        'file': (io.BytesIO(b'fake_image_data'), 'test.jpg')
    }
    response = client.post('/api/skan', data=data, content_type='multipart/form-data')

    # Asercje
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['code'] == 0

    # Sprawdź czy zalogowano wejście
    mock_log.assert_called_once()
    mock_handler.assert_called()  # Powinien być wywołany bez argumentów (sukces)


@patch('backend.components.camera_verification.verificationController.parse_image')
@patch('backend.components.camera_verification.verificationController.get_worker_from_qr_code')
@patch('backend.components.camera_verification.verificationController.verification_response_handler')
def test_scan_malformed_request(mock_handler, mock_get_worker, mock_parse, client, mock_response_object):
    """
    Test błędu 400 (Malformed Request).
    Symulujemy sytuację, gdzie handler zwraca kod < 10 (np. 1 - brak kodu QR).
    """
    # Symulujemy rzucenie wyjątku przez serwis (np. InvalidCodeError)
    mock_get_worker.side_effect = Exception("Some error")

    # Handler mapuje ten wyjątek na kod błędu 1 (Błąd danych wejściowych)
    mock_response_object.code = 1
    mock_handler.return_value = mock_response_object

    data = {'file': (io.BytesIO(b'img'), 'test.jpg')}
    response = client.post('/api/skan', data=data, content_type='multipart/form-data')

    # Wg logiki kontrolera: if response.code < 10: http_code = 400
    assert response.status_code == 400


@patch('backend.components.camera_verification.verificationController.parse_image')
@patch('backend.components.camera_verification.verificationController.get_worker_from_qr_code')
@patch('backend.components.camera_verification.verificationController.verification_response_handler')
def test_scan_permission_denied(mock_handler, mock_get_worker, mock_parse, client, mock_response_object):
    """
    Test błędu 403 (Permission Denied).
    Symulujemy kod błędu > 10, który nie jest wielokrotnością 10 (np. 13 - twarz nie pasuje).
    """
    mock_get_worker.side_effect = Exception("Face mismatch")

    # Handler zwraca np. kod 13
    mock_response_object.code = 13
    mock_handler.return_value = mock_response_object

    data = {'file': (io.BytesIO(b'img'), 'test.jpg')}
    response = client.post('/api/skan', data=data, content_type='multipart/form-data')

    # Wg logiki kontrolera: else: http_code = 403
    assert response.status_code == 403


@patch('backend.components.camera_verification.verificationController.parse_image')
@patch('backend.components.camera_verification.verificationController.get_worker_from_qr_code')
@patch('backend.components.camera_verification.verificationController.verification_response_handler')
def test_scan_internal_server_error(mock_handler, mock_get_worker, mock_parse, client, mock_response_object):
    """
    Test błędu 500 (Internal Server Error).
    Symulujemy kod -1 lub wielokrotność 10 (np. 20 - błąd bazy).
    """
    mock_get_worker.side_effect = Exception("Critical fail")

    # Przypadek 1: code = -1
    mock_response_object.code = -1
    mock_handler.return_value = mock_response_object

    data = {'file': (io.BytesIO(b'img'), 'test.jpg')}
    response = client.post('/api/skan', data=data, content_type='multipart/form-data')
    assert response.status_code == 500