import io
import numpy as np
import face_recognition

def get_worker_embedding(worker):
    """
    Returns and decodes worker face embedding from blob to np.array
    """
    blob = worker.getFace()
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
