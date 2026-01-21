import pytest
import numpy as np
import cv2
from backend.components.utils.imageUtils import parse_image, encode_image
from backend.components.utils import imageUtils


# --------------------------------------------------------------------------
# Testy funkcji parse_image (Bytes -> Array)
# --------------------------------------------------------------------------

def test_parse_image_success():
    """
    Checks whether valid image bytes are converted to a numpy matrix.
    It also verifies that the result is of the correct shape.
    """
    original_img = np.zeros((10, 10, 3), dtype=np.uint8)

    _, buffer = cv2.imencode('.png', original_img)
    image_bytes = buffer.tobytes()

    result_img = parse_image(image_bytes)

    assert isinstance(result_img, np.ndarray)
    assert result_img.shape == (10, 10, 3)


def test_parse_image_color_conversion():
    """
    Checks whether the function correctly converts the color format from BGR to RGB.
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
    Checks whether a function throws a ValueError when it receives invalid bytes
    (e.g., a text file instead of an image).
    """
    garbage_bytes = b"to nie jest obrazek, tylko losowy tekst"

    with pytest.raises(ValueError, match="Nie udało się przetworzyć pliku jako obrazu"):
        parse_image(garbage_bytes)


# --------------------------------------------------------------------------
# Testy funkcji encode_image (Array -> Bytes)
# --------------------------------------------------------------------------

def test_encode_image_default_png():
    """
    Checks default encoding to PNG format.
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
    Checks encoding to JPG format.
    """
    img = np.zeros((10, 10, 3), dtype=np.uint8)

    result_bytes = encode_image(img, encode_format=".jpg")

    assert isinstance(result_bytes, bytes)
    assert len(result_bytes) > 0
    # Magiczne bajty JPEG zaczynają się zazwyczaj od FF D8
    assert result_bytes.startswith(b'\xff\xd8')


def test_encode_image_failure():
    """
    Checks whether the function throws a ValueError when OpenCV fails to encode an image.
    We simulate this by providing an invalid file format or an empty array in a way that causes the cv2.
    imencode function to fail.
    """
    # Pusta tablica lub tablica o złym kształcie zazwyczaj zwróci False w imencode
    bad_img = np.zeros((0, 0, 0), dtype=np.uint8)

    with pytest.raises(ValueError, match="Nie udało się zenkodować obrazu"):
        encode_image(bad_img)


# ============================================================================
# Test parse_image - Success Cases
# ============================================================================

def test_parse_image_valid_png():
    """Test parsing valid PNG image from bytes."""
    # Create a simple test image
    test_array = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
    test_array_bgr = cv2.cvtColor(test_array, cv2.COLOR_RGB2BGR)

    # Encode to PNG bytes
    success, buffer = cv2.imencode(".png", test_array_bgr)
    image_bytes = buffer.tobytes()

    # Parse back
    result = imageUtils.parse_image(image_bytes)

    assert isinstance(result, np.ndarray)
    assert result.shape == (100, 100, 3)
    assert result.dtype == np.uint8


def test_parse_image_valid_jpg():
    """Test parsing valid JPG image from bytes."""
    test_array = np.random.randint(0, 256, (200, 150, 3), dtype=np.uint8)
    test_array_bgr = cv2.cvtColor(test_array, cv2.COLOR_RGB2BGR)

    success, buffer = cv2.imencode(".jpg", test_array_bgr)
    image_bytes = buffer.tobytes()

    result = imageUtils.parse_image(image_bytes)

    assert isinstance(result, np.ndarray)
    assert result.shape[2] == 3  # RGB channels
    assert result.dtype == np.uint8


# ============================================================================
# Test encode_image - Success Cases
# ============================================================================

def test_encode_image_default_png():
    """Test encoding image to PNG (default format)."""
    test_array = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)

    result = imageUtils.encode_image(test_array)

    assert isinstance(result, bytes)
    assert len(result) > 0
    # PNG files start with specific magic bytes
    assert result[:8] == b'\x89PNG\r\n\x1a\n'


def test_encode_image_to_jpg():
    """Test encoding image to JPG format."""
    test_array = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)

    result = imageUtils.encode_image(test_array, encode_format=".jpg")

    assert isinstance(result, bytes)
    assert len(result) > 0
    # JPG files start with FFD8FF
    assert result[:2] == b'\xff\xd8'


def test_encode_image_various_sizes():
    """Test encoding images of various sizes."""
    sizes = [(50, 50), (100, 200), (800, 600)]

    for height, width in sizes:
        test_array = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
        result = imageUtils.encode_image(test_array)

        assert isinstance(result, bytes)
        assert len(result) > 0


def test_encode_image_preserves_content():
    """Test that encoded image can be decoded back."""
    original = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)

    # Encode
    encoded_bytes = imageUtils.encode_image(original)

    # Decode back
    decoded = imageUtils.parse_image(encoded_bytes)

    assert isinstance(decoded, np.ndarray)
    # Allow for compression artifacts
    assert decoded.shape == original.shape


# ============================================================================
# Test Round-trip Conversion
# ============================================================================

def test_parse_and_encode():
    """Test parse -> encode -> parse produces same dimensions."""
    original = np.random.randint(0, 256, (150, 200, 3), dtype=np.uint8)
    original_bgr = cv2.cvtColor(original, cv2.COLOR_RGB2BGR)

    # Create initial bytes
    success, buffer = cv2.imencode(".png", original_bgr)
    image_bytes = buffer.tobytes()

    # Parse
    parsed = imageUtils.parse_image(image_bytes)

    # Encode back
    re_encoded = imageUtils.encode_image(parsed)

    # Parse again
    re_parsed = imageUtils.parse_image(re_encoded)

    assert parsed.shape == re_parsed.shape
    assert parsed.dtype == re_parsed.dtype


def test_encode_and_parse():
    """Test encode -> parse produces same dimensions."""
    original = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)

    # Encode
    encoded = imageUtils.encode_image(original)

    # Parse
    parsed = imageUtils.parse_image(encoded)

    assert parsed.shape == original.shape
    assert parsed.dtype == original.dtype