from flask import Blueprint, request, jsonify

from backend.components.camera_verification.qrcode.qrcodeService import get_worker_from_qr_code
from backend.components.camera_verification.faceid.faceidService import verify_worker_face
from backend.components.camera_verification.error_handling.errorService import verification_response_handler
from backend.components.utils.imageUtils import parse_image
from backend.components.entries.entryService import log_worker_entry


bp = Blueprint('bp_verification', __name__)

@bp.route('/api/skan', methods=['POST'])
def post_camera_scan():
    '''
    TODO: Swagger docstring for post_camera_scan
    '''
    if 'file' not in request.files:
        return jsonify({'error': 'Brak pliku w żądaniu (oczekiwano klucza "file").'}), 400

    # Load and parse image
    img_parsed = parse_image(request.files['file'])
    img_bytes = request.files['file'].read()

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
        log_worker_entry(response.code, response.message, worker, img_bytes)
        return jsonify({response.asdict()}), http_code
