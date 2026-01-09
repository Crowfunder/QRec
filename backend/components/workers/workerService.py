import io
import numpy as np
import face_recognition

from backend.components.camera_verification.qrcode.qrcodeService import generate_secret
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
    worker_id = worker.id
    name = worker.name
    new_secret_value = generate_secret(worker_id, name)
    worker.secret = new_secret_value
    db.session.commit()
    return worker


def extend_worker_expiration(worker_id, new_expiration_date):
    """
    Extends the expiration date of a worker entry permit.

    **Parameters**:
    - `worker_id` (int): The ID of the worker whose expiration date is to be updated.
    - `new_expiration_date` (datetime): The new expiration date.

    **Returns**:
    - `Worker`: The updated Worker object.

    **Raises**:
    - `ValueError`: If no worker with the given ID is found.
    """
    worker = db.session.get(Worker, worker_id)
    if not worker:
        raise ValueError(f"Worker with id {worker_id} not found")
    worker.expiration_date = new_expiration_date
    db.session.commit()
    return worker


def update_worker_name(worker_id, new_name):
    """
    Updates the name of a worker.

    **Parameters**:
    - `worker_id` (int): The ID of the worker whose name is to be updated.
    - `new_name` (str): The new name for the worker.

    **Returns**:
    - `Worker`: The updated Worker object.

    **Raises**:
    - `ValueError`: If no worker with the given ID is found.
    """
    worker = db.session.get(Worker, worker_id)
    if not worker:
        raise ValueError(f"Worker with id {worker_id} not found")
    worker.name = new_name
    db.session.commit()
    return worker


def update_worker_face_image(worker_id, new_face_image):
    """
    Updates the face image of a worker.

    **Parameters**:
    - `worker_id` (int): The ID of the worker whose face image is to be updated.
    - `new_face_image` (ndarray): The new face image of the worker.

    **Returns**:
    - `Worker`: The updated Worker object.

    **Raises**:
    - `ValueError`: If no worker with the given ID is found.
    """
    worker = db.session.get(Worker, worker_id)
    if not worker:
        raise ValueError(f"Worker with id {worker_id} not found")
    new_face_embedding_blob = create_worker_embedding(new_face_image)
    worker.face_embedding = new_face_embedding_blob
    db.session.commit()
    return worker

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
