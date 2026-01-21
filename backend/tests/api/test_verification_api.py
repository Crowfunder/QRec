import pytest
import io
from unittest.mock import patch, MagicMock
from backend.components.camera_verification.qrcode.qrcodeService import NoCodeFoundError
from backend.components.camera_verification.faceid.faceidService import FaceNotMatchingError

# ============================================================================
# Test Helpers & Fixtures
# ============================================================================

def mock_response_obj(code, message, logged=True):
    r = MagicMock()
    r.code = code
    r.message = message
    r.logged = logged
    r.asdict.return_value = {"code": code, "message": message, "logged": logged}
    return r


@pytest.fixture
def mock_image_file():
    """Creates a fake image file to upload in the form."""
    return (io.BytesIO(b"fake_image_bytes"), "test_image.jpg")

# ============================================================================
# Test Basic Validation (Input)
# ============================================================================

def test_post_scan_no_file(client):
    """
    Checks the endpoint's behavior when a file has not been transferred.
    Expected status: 400.
    """
    response = client.post('/api/skan')
    assert response.status_code == 400
    assert "Brak pliku" in response.get_json()['error']


# ============================================================================
# Test Happy Path (Success)
# ============================================================================

@patch('backend.components.camera_verification.verificationController.parse_image')
@patch('backend.components.camera_verification.verificationController.get_worker_from_qr_code')
@patch('backend.components.camera_verification.verificationController.verify_worker_face')
@patch('backend.components.camera_verification.verificationController.verification_response_handler')
@patch('backend.components.camera_verification.verificationController.log_worker_entry')
def test_post_scan_success(mock_log, mock_handler, mock_verify, mock_get_worker, mock_parse, client, mock_image_file):
    """
    Positive scenario: valid QR code and matching face.
    Expected status: 200.
    """
    # 1. Konfiguracja mocków dla sukcesu
    mock_get_worker.return_value = MagicMock(id=1, name="Jan Testowy")
    mock_verify.return_value = True  # Twarz zweryfikowana

    # Handler zwraca kod 0 (sukces)
    mock_handler.return_value = mock_response_obj(code=0, message="Weryfikacja udana")

    # 2. Wykonanie żądania
    data = {'file': mock_image_file}
    response = client.post('/api/skan', data=data, content_type='multipart/form-data')

    # 3. Asercje
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['code'] == 0
    assert json_data['message'] == "Weryfikacja udana"

    # Sprawdzenie czy wywołano logowanie
    mock_log.assert_called_once()

# ============================================================================
# Test Error Mapping Logic (Exceptions -> HTTP Codes)
# ============================================================================

@patch('backend.components.camera_verification.verificationController.parse_image')
@patch('backend.components.camera_verification.verificationController.get_worker_from_qr_code')
@patch('backend.components.camera_verification.verificationController.verification_response_handler')
@patch('backend.components.camera_verification.verificationController.log_worker_entry')
def test_post_scan_qr_error_bad_request(mock_log, mock_handler, mock_get_worker, mock_parse, client, mock_image_file):
    """
    Client error scenario (400): e.g., missing QR code or corrupted code.
    The controller maps codes < 10 to HTTP 400.
    """
    # Symulujemy rzucenie wyjątku przez serwis QR
    mock_get_worker.side_effect = NoCodeFoundError("Nie znaleziono kodu")

    # Symulujemy, że handler mapuje ten błąd na kod wewnętrzny 2 (z zakresu < 10)
    mock_handler.return_value = mock_response_obj(code=2, message="Nie znaleziono kodu QR")

    data = {'file': mock_image_file}
    response = client.post('/api/skan', data=data, content_type='multipart/form-data')

    assert response.status_code == 400
    assert response.get_json()['code'] == 2
    # Nawet przy błędzie logowanie powinno zostać wywołane (jeśli handler ustawił logged=True)
    mock_log.assert_called_once()


@patch('backend.components.camera_verification.verificationController.parse_image')
@patch('backend.components.camera_verification.verificationController.get_worker_from_qr_code')
@patch('backend.components.camera_verification.verificationController.verify_worker_face')
@patch('backend.components.camera_verification.verificationController.verification_response_handler')
@patch('backend.components.camera_verification.verificationController.log_worker_entry')
def test_post_scan_face_mismatch_forbidden(mock_log, mock_handler, mock_verify, mock_get_worker, mock_parse, client,
                                           mock_image_file):
    """
    Permission error scenario (403): Face does not match pattern.
    The controller maps codes >= 10 (that are not a multiple of 10) to HTTP 403.
    """
    mock_get_worker.return_value = MagicMock(id=1)

    # Symulacja błędu weryfikacji twarzy
    mock_verify.side_effect = FaceNotMatchingError("Twarz nie pasuje")

    # Symulujemy, że handler mapuje to na kod 12
    mock_handler.return_value = mock_response_obj(code=12, message="Twarz nie pasuje do wzorca")

    data = {'file': mock_image_file}
    response = client.post('/api/skan', data=data, content_type='multipart/form-data')

    assert response.status_code == 403
    assert response.get_json()['code'] == 12

    # Upewniamy się, że próba wejścia została zalogowana
    mock_log.assert_called_once()


@patch('backend.components.camera_verification.verificationController.parse_image')
@patch('backend.components.camera_verification.verificationController.get_worker_from_qr_code')
@patch('backend.components.camera_verification.verificationController.verification_response_handler')
@patch('backend.components.camera_verification.verificationController.log_worker_entry')
def test_post_scan_internal_server_error(mock_log, mock_handler, mock_get_worker, mock_parse, client, mock_image_file):
    """
    Server error scenario (500).
    The controller maps codes that are multiples of 10 (e.g., 20, 30) or -1 to HTTP 500.
    """
    mock_get_worker.side_effect = Exception("Nieoczekiwany błąd bazy danych")

    # Symulujemy kod błędu krytycznego (np. 20)
    mock_handler.return_value = mock_response_obj(code=20, message="Błąd wewnętrzny")

    data = {'file': mock_image_file}
    response = client.post('/api/skan', data=data, content_type='multipart/form-data')

    assert response.status_code == 500
    assert response.get_json()['code'] == 20

    mock_log.assert_called_once()

# ============================================================================
# Test Audit Logging
# ============================================================================

@patch('backend.components.camera_verification.verificationController.parse_image')
@patch('backend.components.camera_verification.verificationController.get_worker_from_qr_code')
@patch('backend.components.camera_verification.verificationController.verify_worker_face')
@patch('backend.components.camera_verification.verificationController.verification_response_handler')
@patch('backend.components.camera_verification.verificationController.log_worker_entry')
def test_scan_logs_even_on_failure(mock_log, mock_handler, mock_verify, mock_get_worker, mock_parse, client,
                                   mock_image_file):
    """
    Verifies that the log_worker_entry function is called even if it fails if the handler returns
    the logged=True flag.
    """
    mock_verify.side_effect = FaceNotMatchingError("Błąd")

    # logged=True oznacza, że próba wejścia ma zostać odnotowana w bazie
    mock_handler.return_value = mock_response_obj(code=12, message="Fail", logged=True)

    client.post('/api/skan', data={'file': mock_image_file}, content_type='multipart/form-data')

    mock_log.assert_called_once()
    # Sprawdzamy czy przekazano odpowiednie argumenty do logowania
    args, _ = mock_log.call_args
    assert args[0] == 12  # code
    assert args[1] == "Fail"  # message