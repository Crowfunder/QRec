import pytest
import numpy as np
import cv2
from backend.components.utils.imageUtils import parse_image, encode_image


# --------------------------------------------------------------------------
# Testy funkcji parse_image (Bytes -> Array)
# --------------------------------------------------------------------------

def test_parse_image_success():
    """
    Sprawdza, czy poprawne bajty obrazu są konwertowane na macierz numpy.
    Weryfikuje również, czy wynik ma poprawny kształt.
    """
    # 1. Przygotuj sztuczny obrazek (10x10, czarny) w pamięci
    # OpenCV domyślnie używa BGR, więc tworzymy go jako BGR
    original_img = np.zeros((10, 10, 3), dtype=np.uint8)

    # 2. Zakoduj go do bajtów (symulacja uploadu pliku)
    _, buffer = cv2.imencode('.png', original_img)
    image_bytes = buffer.tobytes()

    # 3. Wywołaj testowaną funkcję
    result_img = parse_image(image_bytes)

    # 4. Asercje
    assert isinstance(result_img, np.ndarray)
    assert result_img.shape == (10, 10, 3)


def test_parse_image_color_conversion():
    """
    Sprawdza, czy funkcja poprawnie konwertuje format kolorów z BGR na RGB.
    """
    # Tworzymy obraz 1x1 piksel w kolorze NIEBIESKIM.
    # W OpenCV (BGR) niebieski to [255, 0, 0].
    bgr_pixel = np.array([[[255, 0, 0]]], dtype=np.uint8)

    # Kodujemy do PNG
    _, buffer = cv2.imencode('.png', bgr_pixel)
    image_bytes = buffer.tobytes()

    # Parsujemy (funkcja powinna zamienić BGR -> RGB)
    rgb_pixel = parse_image(image_bytes)

    # W RGB niebieski to [0, 0, 255].
    # Sprawdzamy, czy kanały zostały odwrócone.
    assert rgb_pixel[0, 0, 0] == 0  # R
    assert rgb_pixel[0, 0, 1] == 0  # G
    assert rgb_pixel[0, 0, 2] == 255  # B


def test_parse_image_invalid_bytes():
    """
    Sprawdza, czy funkcja rzuca ValueError, gdy otrzyma nieprawidłowe bajty
    (np. plik tekstowy zamiast obrazka).
    """
    garbage_bytes = b"to nie jest obrazek, tylko losowy tekst"

    with pytest.raises(ValueError, match="Nie udało się przetworzyć pliku jako obrazu"):
        parse_image(garbage_bytes)


# --------------------------------------------------------------------------
# Testy funkcji encode_image (Array -> Bytes)
# --------------------------------------------------------------------------

def test_encode_image_default_png():
    """
    Sprawdza domyślne kodowanie do formatu PNG.
    """
    # Tworzymy prosty obraz RGB
    img = np.zeros((10, 10, 3), dtype=np.uint8)

    # Wywołanie bez podania formatu (domyślnie .png)
    result_bytes = encode_image(img)

    assert isinstance(result_bytes, bytes)
    assert len(result_bytes) > 0

    # Magiczne bajty PNG to: 89 50 4E 47
    # Sprawdzamy nagłówek, żeby upewnić się, że to PNG
    assert result_bytes.startswith(b'\x89PNG')


def test_encode_image_custom_format_jpg():
    """
    Sprawdza kodowanie do formatu JPG.
    """
    img = np.zeros((10, 10, 3), dtype=np.uint8)

    result_bytes = encode_image(img, encode_format=".jpg")

    assert isinstance(result_bytes, bytes)
    assert len(result_bytes) > 0
    # Magiczne bajty JPEG zaczynają się zazwyczaj od FF D8
    assert result_bytes.startswith(b'\xff\xd8')


def test_encode_image_failure():
    """
    Sprawdza, czy funkcja rzuca ValueError, gdy OpenCV nie uda się zakodować obrazu.
    Symulujemy to podając nieprawidłowy format pliku lub pustą tablicę w sposób,
    który powoduje błąd funkcji cv2.imencode.
    """
    # Pusta tablica lub tablica o złym kształcie zazwyczaj zwróci False w imencode
    bad_img = np.zeros((0, 0, 0), dtype=np.uint8)

    with pytest.raises(ValueError, match="Nie udało się zenkodować obrazu"):
        encode_image(bad_img)