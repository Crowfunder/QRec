import pytest
import numpy as np
import cv2
from unittest.mock import patch, MagicMock

from backend.components.utils import imageUtils


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
