import numpy as np
import cv2
from flask import Blueprint, request, jsonify
from backend.components.qrcode.qrcodeService import (
    decodeQRImage,
    getWorkerByQRCodeSecret,
    QRCodeError,
    MultipleCodesError,
    NoCodeFoundError
)


bp = Blueprint('bp_qrcode', __name__)


@bp.route('/test', methods=['GET'])
def test():

    return 'ok', 200



def getWorkerFromQRCode(file_stream):
    try:
        qr_secret = decodeQRImage(file_stream)
        worker = getWorkerByQRCodeSecret(qr_secret)
        return worker

    except (MultipleCodesError, NoCodeFoundError, ValueError) as e:
        raise e

    except Exception as e:
        print(f"Internal Error in getWorkerFromQRCode: {e}")
        raise e