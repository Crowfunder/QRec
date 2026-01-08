from backend.components.camera_verification.error_handling.errorConfig import (
    EXCEPTION_MAP
)

def verification_response_handler(e: Exception = None):
    """
    Handles passed exception, returns respective error code and message
    """
    try:
        response = EXCEPTION_MAP[type(e)]
    except KeyError:
        response = EXCEPTION_MAP[Exception]
        response.text += str(e)

    return response


