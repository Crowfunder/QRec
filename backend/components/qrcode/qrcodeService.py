import random

from flask import request, send_file, Response
from sqlalchemy import select
import cv2
import numpy as np
import hashlib
from backend.app import db
from backend.database.models import Worker

def generateQRCode():
    pass

def validateQRCode():
    pass


class QRCodeError(Exception):
    """Base error class for QR codes"""
    pass

class MultipleCodesError(QRCodeError):
    """Raised when more than one code is detected"""
    pass

class NoCodeFoundError(QRCodeError):
    """Raised when no code is detected"""
    pass

def decodeQRImage(file_stream) -> str:
    """
    Input a file stream (bytes) and return decoded QR code data as string.
    """
    if hasattr(file_stream, 'seek'):
        file_stream.seek(0) # Ensure we're at the start of the file
    file_bytes = np.frombuffer(file_stream.read(), np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Nie udało się przetworzyć pliku jako obrazu.")
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


def generateSecret(worker_id: int, name: str) -> str:
    rand_value = str(random.randint(100000, 999999))
    raw_string = f"{worker_id}:{name}:{rand_value}"
    secret_hash = hashlib.sha256(raw_string.encode()).hexdigest()
    return secret_hash

def getWorkerByQRCodeSecret(secret: str):
    stmt = select(Worker).where(Worker.secret == secret)
    result = db.session.execute(stmt).scalar_one_or_none()
    return result
