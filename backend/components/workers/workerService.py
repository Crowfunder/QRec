import io
import numpy as np
import face_recognition

from backend.components.camera_verification.qrcode.qrcodeService import generate_secret
from backend.database.models import Worker

def get_worker_embedding(worker):
    """
    Returns and decodes worker face embedding from blob to np.array
    """
    blob = worker.face_image_embedding
    buffer = io.BytesIO(blob)
    arr = np.load(buffer)
    return arr


def create_worker_embedding(img):
    """
    Creates and encodes worker face embedding into BLOB for database
    """
    img_embedding = face_recognition.face_encodings(img)

    buffer = io.BytesIO()
    np.save(buffer, img_embedding)
    blob = buffer.getvalue()
    return blob

def newWorker(db, name, face_image, expiration_date):
    face_embedding_blob = create_worker_embedding(face_image)
    worker = Worker(
        name=name,
        face_image=face_embedding_blob,
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

def extendWorkerExpiration(db, worker_id, new_expiration_date):
    worker = db.session.get(Worker, worker_id)
    if not worker:
        raise ValueError(f"Worker with id {worker_id} not found")
    worker.expiration_date = new_expiration_date
    db.session.commit()
    return worker

def updateWorkerName(db, worker_id, new_name):
    worker = db.session.get(Worker, worker_id)
    if not worker:
        raise ValueError(f"Worker with id {worker_id} not found")
    worker.name = new_name
    db.session.commit()
    return worker

def updateWorkerFaceImage(db, worker_id, new_face_image):
    worker = db.session.get(Worker, worker_id)
    if not worker:
        raise ValueError(f"Worker with id {worker_id} not found")
    new_face_embedding_blob = create_worker_embedding(new_face_image)
    worker.face_image = new_face_embedding_blob
    db.session.commit()
    return worker
