from flask import Blueprint, request, jsonify

from backend.components.camera_verification.qrcode.qrcodeService import getWorkerFromQRCode
from backend.components.camera_verification.faceid.faceidService import verifyWorkerFace
from backend.components.camera_verification.error_handling.errorService import VerificationResponseHandler
from backend.components.utils.imageUtils import parseImage
from backend.components.entries.entryService import LogWorkerEntry


bp = Blueprint('bp_verification', __name__)

@bp.route('/api/skan', methods=['POST'])
def post_camera_scan():
    if 'file' not in request.files:
        return jsonify({'error': 'Brak pliku w żądaniu (oczekiwano klucza "file").'}), 400

    # Load and parse image
    img = parseImage(request.files['file'])

    http_code, response, worker = None, None, None
    try:
        worker = getWorkerFromQRCode(img)
        verifyWorkerFace(worker, img)
        http_code = 200
        response = VerificationResponseHandler()

    except Exception as e:
        response = VerificationResponseHandler(e)
        if response.code == -1:
            http_code = 500  # Unknown internal server error
        elif response.code < 10:
            http_code = 400  # Malformed request
        elif response.code % 10 == 0:
            http_code = 500  # Known internal server error
        else:
            http_code = 403  # Permission denied

    finally:
        LogWorkerEntry(response.code, response.message, worker, img)
        return jsonify({response.asdict()}), http_code
