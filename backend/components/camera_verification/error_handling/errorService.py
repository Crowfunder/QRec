from backend.components.camera_verification.error_handling.errorConfig import (
    EXCEPTION_MAP,
    ErrorResponse
)

def verification_response_handler(e: Exception|None = None) -> ErrorResponse:
    """
    Handles passed verification response (Exception?). Returns respective error code, error message and whether to log the event.

    **Parameters**:
    - `e` (Exception|None): Exception if one was caught, if no exception was caught this parameter can be None.

    **Returns**:
    - `ErrorResponse` - Response object with decisions and additional info for the back-end.
    """
    try:
        response = EXCEPTION_MAP[type(e)]
    except KeyError:
        response = EXCEPTION_MAP[Exception]
        response.message += str(e)

    return response


