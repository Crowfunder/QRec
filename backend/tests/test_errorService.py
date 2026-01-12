import pytest
from unittest.mock import patch, MagicMock

from backend.components.camera_verification.error_handling import errorService
from backend.components.camera_verification.error_handling.errorConfig import ErrorResponse
from backend.components.camera_verification.faceid.faceidService import (
    FaceIDError,
    NoFacesFoundError,
    MultipleWorkersError,
    FaceNotMatchingError
)
from backend.components.camera_verification.qrcode.qrcodeService import (
    QRCodeError,
    NoCodeFoundError,
    InvalidCodeError,
    MultipleCodesError,
    ExpiredCodeError
)


# ============================================================================
# Test verification_response_handler - Success Cases
# ============================================================================

def test_verification_response_handler_no_exception():
    """Test handler with no exception returns success response."""
    response = errorService.verification_response_handler(None)

    assert isinstance(response, ErrorResponse)
    assert response is not None


def test_verification_response_handler_returns_error_response():
    """Test that handler always returns ErrorResponse object."""
    exception = Exception("Test error")
    response = errorService.verification_response_handler(exception)

    assert isinstance(response, ErrorResponse)
    assert hasattr(response, 'code')
    assert hasattr(response, 'message')
    assert hasattr(response, 'logged')


# ============================================================================
# Test verification_response_handler - Generic Exception Cases
# ============================================================================

def test_verification_response_handler_unknown_exception():
    """Test handler with unknown exception type returns default response."""
    exception = ValueError("Unknown error type")
    response = errorService.verification_response_handler(exception)

    assert isinstance(response, ErrorResponse)
    assert response.code is not None
    # Message should include the exception details
    assert str(exception) in response.message


def test_verification_response_handler_runtime_error():
    """Test handler with RuntimeError exception."""
    exception = RuntimeError("Runtime error occurred")
    response = errorService.verification_response_handler(exception)

    assert isinstance(response, ErrorResponse)
    assert "Runtime error occurred" in response.message


def test_verification_response_handler_type_error():
    """Test handler with TypeError exception."""
    exception = TypeError("Type mismatch error")
    response = errorService.verification_response_handler(exception)

    assert isinstance(response, ErrorResponse)
    assert "Type mismatch error" in response.message


# ============================================================================
# Test verification_response_handler - Response Properties
# ============================================================================

def test_verification_response_handler_response_has_logged():
    """Test that response includes logged property."""
    exception = NoFacesFoundError("Test error")
    response = errorService.verification_response_handler(exception)

    assert hasattr(response, 'logged')
    assert isinstance(response.logged, bool)


def test_verification_response_handler_response_has_code():
    """Test that response includes error code."""
    exception = MultipleWorkersError("Test error")
    response = errorService.verification_response_handler(exception)

    assert hasattr(response, 'code')
    assert response.code is not None


def test_verification_response_handler_response_has_message():
    """Test that response includes error message."""
    exception = FaceNotMatchingError("Face mismatch")
    response = errorService.verification_response_handler(exception)

    assert hasattr(response, 'message')
    assert len(response.message) > 0


# ============================================================================
# Test verification_response_handler - Exception Message Preservation
# ============================================================================
def test_verification_response_handler_appends_to_default_message():
    """Test that unknown exception message is appended to default response."""
    custom_error = "Detailed error information"
    exception = IOError(custom_error)
    response = errorService.verification_response_handler(exception)

    assert custom_error in response.message


# ============================================================================
# Test verification_response_handler - Edge Cases
# ============================================================================
def test_verification_response_handler_with_empty_exception_message():
    """Test handler with exception that has empty message."""
    exception = Exception("")
    response = errorService.verification_response_handler(exception)

    assert isinstance(response, ErrorResponse)
    assert response.code is not None


def test_verification_response_handler_multiple_calls_consistency():
    """Test that handler returns consistent responses for same exception type."""
    exception1 = NoFacesFoundError("Error 1")
    exception2 = NoFacesFoundError("Error 2")

    response1 = errorService.verification_response_handler(exception1)
    response2 = errorService.verification_response_handler(exception2)

    # Both should be valid responses
    assert isinstance(response1, ErrorResponse)
    assert isinstance(response2, ErrorResponse)
    # Codes should match for same exception type
    assert response1.code == response2.code