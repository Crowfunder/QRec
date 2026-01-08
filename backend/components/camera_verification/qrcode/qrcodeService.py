import json
import random
from cryptography.fernet import Fernet
from backend.config import QR_SECRET_KEY

from flask import request, send_file, Response
from sqlalchemy import select
import cv2
import numpy as np
import hashlib
from backend.app import db
from backend.database.models import Worker
from datetime import datetime


def get_worker_from_qr_code(img) -> Worker:
    '''
    Method that reads the QR code and returns a Worker that belongs to the code.

    **Parameters**:
    - `img` (ndarray): Decoded image in ndarray.

    **Returns**:
    - `Worker` - Worker belonging to the scanned code.

    **Raises**:
    - `InvalidCodeError` - The code is invalid or no worker with the code was found.
    - `MultipleCodesError` - Multiple QR codes were detected on the image.
    - `NoCodeFoundError` - No QR codes were found on the image.
    - `ExpiredCodeError` - The QR code is expired.
    - `ValueError` - ??? (Unspecified error)
    '''
    try:
        qr_secret = decode_qr_image(img)
        worker = get_worker_by_qr_code_secret(qr_secret)

        if not worker:
            raise InvalidCodeError("Wykryto niepoprawny kod QR")

        # Check if the worker's expiration date has passed
        if worker.expiration_date and worker.expiration_date < datetime.utcnow():
            raise ExpiredCodeError("Przepustka wygasła")

        return worker

    except (MultipleCodesError, NoCodeFoundError, InvalidCodeError, ExpiredCodeError, ValueError) as e:
        raise e

    except Exception as e:
        print(f"Internal Error in getWorkerFromQRCode: {e}")
        raise e



def generate_qr_code():

    pass

def validate_qr_code():
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

class InvalidCodeError(QRCodeError):
    """Raised when invalid code is detected"""
    pass

class ExpiredCodeError(QRCodeError):
    """Raised when the QR code is expired"""
    pass

def decode_qr_image(img) -> str:
    """
    Input an image loaded into numpy array and return decoded QR code data as string.

    **Parameters**:
    - img (ndarray): Decoded image in ndarray.

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


def generate_secret(worker_id: int, name: str) -> str:
    '''
    Generate a secret for the worker QR code.

    **Parameters**:
    - `worker_id` (int): Unique numeric ID of the worker.
    - `name` (str): Worker display name; included to add entropy but not treated as a secret.

    **Returns**:
    - `str`: Hex-encoded SHA-256 hash of the string "{worker_id}:{name}:{rand}",
        where `rand` is a 6-digit random nonce. 
    '''

    rand_value = str(random.randint(100000, 999999))
    data = {
        "worker_id": worker_id,
        "name": name,
        "rand_value": rand_value
    }
    json_data = json.dumps(data).encode('utf-8')
    fernet = Fernet(QR_SECRET_KEY)
    secret = fernet.encrypt(json_data)
    return secret.decode('utf-8')

def decryptSecret(encrypted_secret: str):
    try:
        fernet = Fernet(QR_SECRET_KEY)
        decrypted = fernet.decrypt(encrypted_secret.encode('utf-8'))
        data = json.loads(decrypted.decode('utf-8'))
        return data
    except Exception as e:
        print(f"Błąd deszyfrowania: {e}")
        return None

def get_worker_by_qr_code_secret(secret: str):
    '''
    Get a Worker by the secret decoded from the QR code.

    **Parameters**:
    - `secret` (str): Secret extracted from the QR code. 

    **Returns**:
    - `Worker|None`: Worker belonging to the secret, if found.
    '''
    stmt = select(Worker).where(Worker.secret == secret)
    result = db.session.execute(stmt).scalar_one_or_none()
    return result
