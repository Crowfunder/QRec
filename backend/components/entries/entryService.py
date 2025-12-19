from backend.app import db
from backend.database.models import Entry, Worker

def LogWorkerEntry(code: int, message: str, worker: Worker = None, image=None):
    if worker is None:
        worker_id = None
    else:
        worker_id = worker.id

    # Do not attach the image if the entry was successful
    if code == 0:
        image = None

    entry = Entry(
        worker_id = worker_id,
        code = code,
        message = message,
        face_image = image
    )
    db.session.add(entry)
    db.session.commit()
    return entry