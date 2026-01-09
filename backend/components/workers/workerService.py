from datetime import datetime
import io
from cryptography.fernet import Fernet
import numpy as np
import face_recognition
from sqlalchemy import select
import random
import json

from backend.components.camera_verification.qrcode.qrcodeService import ExpiredCodeError, InvalidCodeError, MultipleCodesError, NoCodeFoundError, decode_qr_image, generate_qr_code
from backend.config import QR_SECRET_KEY
from backend.database.models import Worker
from backend.app import db

def get_worker_embedding(worker):
    """
    Decodes and returns the worker's face embedding from the database.

    **Parameters**:
    - `worker` (Worker): The Worker object whose face embedding is to be retrieved.

    **Returns**:
    - `np.array`: The decoded face embedding as a NumPy array.
    """
    blob = worker.face_embedding
    buffer = io.BytesIO(blob)
    arr = np.load(buffer)
    return arr


def generate_worker_entry_pass(worker: Worker):
    """
    Generates the worker entry pass as png image.

    **Parameters**:
    - `worker` (Worker): Worker to generate an entry pass for.

    **Returns**:
    - `bytes`: Bytes of PNG image containing the worker entry pass.
    """
    # TODO: Create a fun, pretty access card, not just bare qr code.
    # TODO 2: Should probably be returned as pdf for certainer printing.
    qrcode = generate_qr_code(worker.secret)
    return qrcode
    


def create_worker_embedding(img):
    """
    Creates and encodes a worker's face embedding into a BLOB format for storage in the database.

    **Parameters**:
    - `img` (ndarray): The image of the worker's face.

    **Returns**:
    - `bytes`: The encoded face embedding as a BLOB.
    """
    img_embedding = face_recognition.face_encodings(img)

    buffer = io.BytesIO()
    np.save(buffer, img_embedding)
    blob = buffer.getvalue()
    return blob


def generate_worker_secret(worker: Worker) -> str:
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
        "worker_id": worker.id,
        "name": worker.name,
        "rand_value": rand_value
    }
    json_data = json.dumps(data).encode('utf-8')
    fernet = Fernet(QR_SECRET_KEY)
    secret = fernet.encrypt(json_data)
    return secret.decode('utf-8')


def decrypt_worker_secret(encrypted_secret: str):
    try:
        fernet = Fernet(QR_SECRET_KEY)
        decrypted = fernet.decrypt(encrypted_secret.encode('utf-8'))
        data = json.loads(decrypted.decode('utf-8'))
        return data
    except Exception as e:
        print(f"Błąd deszyfrowania: {e}")
        return None


def create_worker(name, face_image, expiration_date):
    """
    Creates a new worker and stores their information in the database.

    **Parameters**:
    - `name` (str): The name of the worker.
    - `face_image` (ndarray): The image of the worker's face.
    - `expiration_date` (datetime): The expiration date for the worker's access.

    **Returns**:
    - `Worker`: The newly created Worker object.
    """
    face_embedding_blob = create_worker_embedding(face_image)
    worker = Worker(
        name=name,
        face_embedding=face_embedding_blob,
        expiration_date=expiration_date,
        secret="TEMP_SECRET"
    )
    db.session.add(worker)
    db.session.flush()
    new_secret_value = generate_worker_secret(worker)
    worker.secret = new_secret_value
    db.session.commit()
    return worker


def extend_worker_expiration(worker: Worker, new_expiration_date):
    """
    Extends the expiration date of a worker entry permit.

    **Parameters**:
    - `worker` (Worker): The worker object whose expiration date is to be updated.
    - `new_expiration_date` (datetime): The new expiration date.
    """
    worker.expiration_date = new_expiration_date
    db.session.commit()
    return worker


def update_worker_name(worker: Worker, new_name: str):
    """
    Updates the name of a worker.

    **Parameters**:
    - `worker` (Worker): The worker object whose name is to be updated.
    - `new_name` (str): The new name for the worker.
    """
    worker.name = new_name
    db.session.commit()


def update_worker_face_image(worker: Worker, new_face_image):
    """
    Updates the face image of a worker.

    **Parameters**:
    - `worker` (Worker): The worker object whose face image is to be updated.
    - `new_face_image` (ndarray): The new face image of the worker.
    """
    new_face_embedding_blob = create_worker_embedding(new_face_image)
    worker.face_embedding = new_face_embedding_blob
    db.session.commit()


def get_all_workers():
    """
    Retrieves all workers from the database.

    **Returns**:
    - `list[Worker]`: A list of all Worker objects.
    """
    workers = db.session.query(Worker).all()
    return workers


def get_worker_by_id(worker_id):
    """
    Retrieves a worker from the database by their ID.

    **Parameters**:
    - `worker_id` (int): The ID of the worker to retrieve.

    **Returns**:
    - `Worker`: The Worker object if found.

    **Raises**:
    - `ValueError`: If no worker with the given ID is found.
    """
    worker = db.session.get(Worker, worker_id)
    if not worker:
        raise ValueError(f"Worker with id {worker_id} not found")
    return worker


def get_worker_by_secret(secret: str):
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
    '''
    try:
        qr_secret = decode_qr_image(img)
        worker = get_worker_by_secret(qr_secret)

        if not worker:
            raise InvalidCodeError("Wykryto niepoprawny kod QR")

        # Check if the worker's expiration date has passed
        if worker.expiration_date and worker.expiration_date < datetime.now():
            raise ExpiredCodeError("Przepustka wygasła")

        return worker

    except (MultipleCodesError, NoCodeFoundError, InvalidCodeError, ExpiredCodeError) as e:
        raise e

    except Exception as e:
        print(f"Internal Error in getWorkerFromQRCode: {e}")
        raise e
