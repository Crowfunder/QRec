from flask import Blueprint, request, jsonify

from backend.components.camera_verification.qrcode.qrcodeService import getWorkerFromQRCode
from backend.components.camera_verification.faceid.faceidService import verifyWorkerFace
from backend.components.camera_verification.error_handling.errorService import VerificationResponseHandler
from backend.components.utils.imageUtils import parseImage


bp = Blueprint('bp_verification', __name__)

@bp.route('/api/skan', methods=['POST'])
def post_camera_scan():
    if 'file' not in request.files:
        return jsonify({'error': 'Brak pliku w żądaniu (oczekiwano klucza "file").'}), 400

    # Load and parse image
    img = parseImage(request.files['file'])

    http_code, response = None, None
    try:
        worker = getWorkerFromQRCode(img)
        verifyWorkerFace(worker, img)
        http_code = 200
        response = VerificationResponseHandler()

    except Exception as e:
        response = VerificationResponseHandler(e)
        if response.code == -1:
            http_code = 500
        elif response.code < 10:
            http_code = 400
        else:
            http_code = 503

    finally:
        return jsonify({response.asdict()}), http_code
