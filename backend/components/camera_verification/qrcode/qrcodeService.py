from flask import request, send_file, Response
import cv2
import numpy as np
import hashlib

from backend.components.utils.imageUtils import encode_image


def generate_qr_code(secret: str):
    '''
    Generates a QR code image from given secret.

    **Parameters**:
    - `secret` (str): Secret to be encoded.

    **Returns**:
    - `bytes`: QR code image bytes encoded as PNG 
    '''
    encoder = cv2.QRCodeEncoder().create()
    scale = 12
    qr = encoder.encode(secret)

    qr = cv2.resize(qr, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)

    border = 4 * scale
    qr = cv2.copyMakeBorder(
        qr, border, border, border, border,
        cv2.BORDER_CONSTANT, value=255
    )

    _, qr = cv2.threshold(qr, 127, 255, cv2.THRESH_BINARY)
    return encode_image(qr)


def decode_qr_image(img) -> str:
    """
    Input an image loaded into numpy array and return decoded QR code data as string.

    **Parameters**:
    - `img` (ndarray): Decoded image in ndarray.

    **Returns**:
    - `str`: Decoded QR code
    """
    qr_detector = cv2.QRCodeDetector()
    retval, decoded_info, points, straight_qrcode = qr_detector.detectAndDecodeMulti(img)
    if retval and decoded_info is not None:
        valid_codes = [code for code in decoded_info if code]
        count = len(valid_codes)

        if count == 1:
            return valid_codes[0]
        elif count > 1:
            raise MultipleCodesError(f"Wykryto {count} kodów QR. Wymagany jest dokładnie jeden.")
        else:
            raise NoCodeFoundError("Wykryto wzorzec QR, ale nie udało się go odczytać.")

    raise NoCodeFoundError("Nie wykryto kodu QR.")


class QRCodeError(Exception):
    """Base error class for QR codes"""
    pass

class MultipleCodesError(QRCodeError):
    """Raised when more than one code is detected"""
    pass

class NoCodeFoundError(QRCodeError):
    """Raised when no code is detected"""
    pass

class InvalidCodeError(QRCodeError):
    """Raised when invalid code is detected"""
    pass

class ExpiredCodeError(QRCodeError):
    """Raised when the QR code is expired"""
    pass