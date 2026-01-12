from flask import Blueprint, request, jsonify

from backend.components.workers.workerService import get_worker_from_qr_code
from backend.components.camera_verification.faceid.faceidService import verify_worker_face
from backend.components.camera_verification.error_handling.errorService import verification_response_handler
from backend.components.utils.imageUtils import parse_image
from backend.components.entries.entryService import log_worker_entry


bp = Blueprint('bp_verification', __name__)

@bp.route('/api/skan', methods=['POST'])
def post_camera_scan():
    """
    [POST] Verifies a worker by scanning a QR code and matching their face.

    **Request Body**:
    - `file` (FileStorage): The image file containing the QR code and the worker's face.

    **Process**:
    - Extracts and decodes the QR code from the image.
    - Retrieves the worker associated with the QR code.
    - Verifies the worker's face matches the one stored in the database.

    **Returns**:
    - `tuple`: A tuple containing the verification result and the HTTP status code.
      - On success:
        - HTTP 200: Verification successful.
      - On failure:
        - HTTP 400: Malformed request (e.g., missing file or invalid QR code).
        - HTTP 403: Permission denied (e.g., expired QR code or face mismatch).
        - HTTP 500: Internal server error.

    **Example Response**:
    ```json
    {
        "code": 0,
        "message": "Weryfikacja udana.",
        "logged": true
    }
    ```
    """
    if 'file' not in request.files:
        return jsonify({'error': 'Brak pliku w żądaniu (oczekiwano klucza "file").'}), 400

    # Load and parse image
    img_bytes = request.files['file'].read()
    img_parsed = parse_image(img_bytes)

    http_code, response, worker = None, None, None
    try:
        worker = get_worker_from_qr_code(img_parsed)
        verify_worker_face(worker, img_parsed)
        http_code = 200
        response = verification_response_handler()

    except Exception as e:
        response = verification_response_handler(e)
        if response.code == -1:
            http_code = 500  # Unknown internal server error
        elif response.code < 10:
            http_code = 400  # Malformed request
        elif response.code % 10 == 0:
            http_code = 500  # Known internal server error
        else:
            http_code = 403  # Permission denied

    finally:
        if response.logged:
            log_worker_entry(response.code, response.message, worker, img_bytes)
        return jsonify(response.asdict()), http_code
