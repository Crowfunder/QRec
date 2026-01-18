import pytest
import numpy as np
import cv2

from backend.components.camera_verification.qrcode.qrcodeService import (
    generate_qr_code,
    decode_qr_image,
    NoCodeFoundError,
    MultipleCodesError
)
from backend.components.utils.imageUtils import parse_image, encode_image

# -----------------------------------------------------------------------------
# Testy imageUtils.py
# -----------------------------------------------------------------------------

def test_image_encode_parse_roundtrip():
    """
    Sprawdza, czy obraz stworzony w numpy, zakodowany do bajtów i odkodowany
    z powrotem jest (prawie) taki sam.
    """
    # 1. Stwórz prosty obraz (100x100, czarny kwadrat na białym tle)
    original_img = np.ones((100, 100, 3), dtype=np.uint8) * 255
    original_img[25:75, 25:75] = 0  # Czarny środek

    # 2. Zakoduj do PNG (bytes)
    img_bytes = encode_image(original_img, encode_format=".png")
    assert isinstance(img_bytes, bytes)
    assert len(img_bytes) > 0

    # 3. Odkoduj z powrotem do numpy (ndarray)
    decoded_img = parse_image(img_bytes)

    # 4. Sprawdź wymiary i typ
    assert decoded_img.shape == original_img.shape
    assert decoded_img.dtype == original_img.dtype

    # 5. Sprawdź czy zawartość jest identyczna.
    np.testing.assert_array_equal(decoded_img, original_img)


def test_parse_image_invalid_bytes():
    """Sprawdza zachowanie przy próbie sparsowania uszkodzonych bajtów."""
    garbage_bytes = b'\x00\x01\x02'  # Za mało danych, nieprawidłowy nagłówek

    with pytest.raises(ValueError) as excinfo:
        parse_image(garbage_bytes)

    assert "Nie udało się przetworzyć pliku" in str(excinfo.value)

# -----------------------------------------------------------------------------
# Testy qrcodeService.py
# -----------------------------------------------------------------------------

def test_generate_qr_code_returns_valid_image():
    """Sprawdza, czy generator zwraca poprawne bajty obrazu PNG."""
    secret = "TEST_SECRET_123"
    qr_bytes = generate_qr_code(secret)

    assert isinstance(qr_bytes, bytes)
    # Sprawdź sygnaturę PNG (magic number)
    assert qr_bytes.startswith(b'\x89PNG\r\n\x1a\n')


def test_generate_and_decode_cycle():
    """
    Scenariusz Happy Path:
    1. Wygeneruj kod QR dla sekretu.
    2. Przekształć bajty na obraz (ndarray).
    3. Zdekoduj obraz.
    4. Porównaj odczytany tekst z oryginałem.
    """
    secret = "SUPER_TAJNE_HASLO_123"

    # 1. Generuj
    qr_bytes = generate_qr_code(secret)

    # 2. Parsuj do ndarray (symulacja odebrania pliku przez serwer)
    qr_image = parse_image(qr_bytes)

    # 3. Dekoduj (pyzbar)
    decoded_text = decode_qr_image(qr_image)

    # 4. Assert
    assert decoded_text == secret


def test_decode_no_qr_code_found():
    """Sprawdza rzucenie wyjątku, gdy na obrazku nie ma kodu QR."""
    # Pusty biały obraz
    empty_image = np.ones((200, 200, 3), dtype=np.uint8) * 255

    with pytest.raises(NoCodeFoundError):
        decode_qr_image(empty_image)


def test_decode_multiple_qr_codes():
    """
    Sprawdza rzucenie wyjątku, gdy na obrazku są dwa kody QR.
    Test tworzy obraz poprzez sklejenie dwóch wygenerowanych kodów obok siebie.
    """
    # 1. Generuj dwa różne kody
    qr1_bytes = generate_qr_code("SECRET_A")
    qr2_bytes = generate_qr_code("SECRET_B")

    img1 = parse_image(qr1_bytes)
    img2 = parse_image(qr2_bytes)

    # Upewnij się, że mają tę samą wysokość przed sklejeniem (powinny, bo ten sam scaler)
    # Jeśli resize w generate_qr_code jest stały, powinno być ok.
    # Dla pewności resize do najmniejszego wspólnego mianownika (opcjonalne w tym teście)

    # 2. Sklej obrazy w poziomie (axis=1) - dodajmy biały odstęp
    spacer = np.ones((img1.shape[0], 50, 3), dtype=np.uint8) * 255
    combined_image = np.hstack((img1, spacer, img2))

    # Konwersja z powrotem na uint8 (hstack może czasem zmienić typ)
    combined_image = combined_image.astype(np.uint8)

    # 3. Próba dekodowania
    with pytest.raises(MultipleCodesError) as excinfo:
        decode_qr_image(combined_image)

    assert "Wykryto 2 kodów QR" in str(excinfo.value)
