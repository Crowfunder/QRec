import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from backend.components.camera_verification.qrcode.qrcodeService import (
    generate_qr_code,
    decode_qr_image,
    MultipleCodesError,
    NoCodeFoundError
)


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

@pytest.fixture
def fake_image():
    """Tworzy pustą tablicę numpy udającą obraz (dla decode)."""
    return np.zeros((100, 100, 3), dtype=np.uint8)


# --------------------------------------------------------------------------
# Testy generate_qr_code
# --------------------------------------------------------------------------

@patch('backend.components.camera_verification.qrcode.qrcodeService.encode_image')
@patch('backend.components.camera_verification.qrcode.qrcodeService.cv2')
def test_generate_qr_code_success(mock_cv2, mock_encode_image):
    """
    Testuje generowanie kodu QR.
    Sprawdza, czy wywoływane są odpowiednie metody z biblioteki cv2 oraz funkcja kodująca wynik.
    """
    # Setup
    secret = "my_secret_code"

    # Mockowanie łańcucha wywołań cv2
    mock_encoder = MagicMock()
    mock_cv2.QRCodeEncoder.return_value.create.return_value = mock_encoder

    # Mockowanie wyników operacji na obrazie
    # encode zwraca surowy obraz QR
    mock_encoder.encode.return_value = np.zeros((10, 10), dtype=np.uint8)
    # resize zwraca przeskalowany obraz
    mock_cv2.resize.return_value = np.zeros((100, 100), dtype=np.uint8)
    # copyMakeBorder dodaje ramkę
    mock_cv2.copyMakeBorder.return_value = np.zeros((120, 120), dtype=np.uint8)
    # threshold zwraca (retval, image)
    mock_cv2.threshold.return_value = (127, np.zeros((120, 120), dtype=np.uint8))

    # Mock encode_image (zwraca bytes)
    expected_bytes = b'fake_png_bytes'
    mock_encode_image.return_value = expected_bytes

    # Action
    result = generate_qr_code(secret)

    # Assert
    assert result == expected_bytes

    # Weryfikacja czy encoder został utworzony i użyty z sekretem
    mock_cv2.QRCodeEncoder.return_value.create.assert_called_once()
    mock_encoder.encode.assert_called_once_with(secret)

    # Weryfikacja czy zakodowano ostateczny obraz
    mock_encode_image.assert_called_once()


# --------------------------------------------------------------------------
# Testy decode_qr_image
# --------------------------------------------------------------------------

@patch('backend.components.camera_verification.qrcode.qrcodeService.pyzbar.decode')
def test_decode_qr_image_success(mock_decode, fake_image):
    """
    Scenariusz pozytywny: Wykryto dokładnie jeden kod QR.
    """
    # Setup
    mock_qr_obj = MagicMock()
    mock_qr_obj.data = b"decoded_secret_123"

    # pyzbar.decode zwraca listę znalezionych obiektów
    mock_decode.return_value = [mock_qr_obj]

    # Action
    result = decode_qr_image(fake_image)

    # Assert
    assert result == "decoded_secret_123"
    mock_decode.assert_called_once_with(fake_image)


@patch('backend.components.camera_verification.qrcode.qrcodeService.pyzbar.decode')
def test_decode_qr_image_multiple_codes(mock_decode, fake_image):
    """
    Scenariusz negatywny: Wykryto więcej niż jeden kod QR.
    Oczekiwany wyjątek: MultipleCodesError.
    """
    # Setup
    obj1 = MagicMock()
    obj1.data = b"code1"
    obj2 = MagicMock()
    obj2.data = b"code2"

    mock_decode.return_value = [obj1, obj2]

    # Action & Assert
    with pytest.raises(MultipleCodesError, match="Wykryto 2 kodów QR"):
        decode_qr_image(fake_image)


@patch('backend.components.camera_verification.qrcode.qrcodeService.pyzbar.decode')
def test_decode_qr_image_no_code_empty_list(mock_decode, fake_image):
    """
    Scenariusz negatywny: Biblioteka zwraca pustą listę (brak kodów).
    Oczekiwany wyjątek: NoCodeFoundError.
    """
    # Setup
    mock_decode.return_value = []

    # Action & Assert
    with pytest.raises(NoCodeFoundError, match="Nie wykryto kodu QR"):
        decode_qr_image(fake_image)


@patch('backend.components.camera_verification.qrcode.qrcodeService.pyzbar.decode')
def test_decode_qr_image_no_code_none(mock_decode, fake_image):
    """
    Scenariusz negatywny: Biblioteka zwraca None (teoretyczny przypadek błędu biblioteki).
    Oczekiwany wyjątek: NoCodeFoundError.
    """
    # Setup
    mock_decode.return_value = None

    # Action & Assert
    with pytest.raises(NoCodeFoundError, match="Nie wykryto kodu QR"):
        decode_qr_image(fake_image)


@patch('backend.components.camera_verification.qrcode.qrcodeService.pyzbar.decode')
def test_decode_qr_image_decoding_utf8_error(mock_decode, fake_image):
    """
    Sprawdza, czy błąd dekodowania bajtów (np. złe kodowanie) rzuci standardowy błąd Pythonowy
    lub czy przejdzie (zależnie od implementacji, tutaj testujemy domyślne zachowanie .decode()).
    """
    # Setup
    mock_qr_obj = MagicMock()
    # Niepoprawna sekwencja UTF-8
    mock_qr_obj.data = b'\xff\xfe\xfa'

    mock_decode.return_value = [mock_qr_obj]

    # Action & Assert
    # Metoda .decode("utf-8") rzuci UnicodeDecodeError, chyba że dodamy obsługę errors='ignore'.
    # W obecnym kodzie nie ma obsługi błędów dekodowania, więc oczekujemy UnicodeDecodeError.
    with pytest.raises(UnicodeDecodeError):
        decode_qr_image(fake_image)