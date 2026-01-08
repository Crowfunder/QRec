from backend.app import db
from backend.database.models import Entry, Worker

def log_worker_entry(code: int, message: str, worker: Worker|None = None, image=None) -> Entry:
    '''
    Log a worker entry.

    **Parameters**:
    - `code` (int): Numeric verification response code for the entry.
    - `message` (str): Human-readable verification response message.
    - `worker` (Worker|None): Worker, if a worker was found.
    - `image` (bytes|None): If the policy enforces saving image of the event, raw image bytes.

    **Returns**:
    - `Entry`: Database entry object.
    '''

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