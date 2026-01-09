from flask import Blueprint, request, send_file
from datetime import datetime
import io

from backend.database.schema.schemas import WorkerSchema
from backend.components.utils.imageUtils import parse_image
from backend.components.workers.workerService import (
    create_worker, extend_worker_expiration, update_worker_name, update_worker_face_image, get_all_workers, get_worker_by_id, generate_worker_entry_pass
)
bp = Blueprint('bp_workers', __name__)

@bp.route('/api/workers', defaults={'worker_id': None}, methods=['GET'])
@bp.route('/api/workers/<worker_id>', methods=['GET'])
def get_workers(worker_id):
    """
    [GET] Retrieves workers from the database.

    **Parameters**:
    - `worker_id` (int|None): The ID of the worker to retrieve. If `None`, retrieves all workers.

    **Returns**:
    - `tuple`: A tuple containing the serialized worker(s) and the HTTP status code.
      - If `worker_id` is provided and the worker exists, returns the serialized worker and status code 200.
      - If `worker_id` is not provided, returns all workers and status code 200.
      - If the worker is not found, returns a 404 status code.
    """
    if worker_id:
        worker = get_worker_by_id(worker_id)
        if not worker:
            return 'Worker not found', 404
        serialized = WorkerSchema(many=False).dump(worker)
    else:
        worker = get_all_workers()
        serialized = WorkerSchema(many=True).dump(worker)

    return serialized, 200
    

@bp.route('/api/workers', methods=['POST'])
def create_worker_endpoint():
    """
    [POST] Creates a new worker in the database.

    **Form Body**:
    - `name` (str): The name of the worker.
    - `expiration_date` (str): The expiration date for the worker's access in ISO format.
    - `file` (FileStorage): The image file of the worker's face.

    **Returns**:
    - `tuple`: A tuple containing the serialized worker and the HTTP status code 200.
    """
    name = request.form.get('name')
    expiration_date = request.form.get('expiration_date')
    image_file = request.files['file']
    if not name or not expiration_date or not image_file:
        return 'Missing worker data', 400

    expiration_date = datetime.fromisoformat(expiration_date)
    face_image = parse_image(image_file.read())
    worker = create_worker(name, face_image, expiration_date)

    # TODO: the endpoint should return **THE QR CODE**

    return WorkerSchema(many=False).dump(worker), 200


@bp.route('/api/workers/<worker_id>', methods=['PUT'])
def update_worker(worker_id):
    """
    [PUT] Updates an existing worker in the database.

    **Parameters**:
    - `worker_id` (int): The ID of the worker to update.

    **Request Body**:
    - `name` (str|optional): The new name for the worker.
    - `expiration_date` (str|optional): The new expiration date in ISO format.
    - `file` (FileStorage|optional): The new image file of the worker's face.

    **Returns**:
    - `tuple`: A tuple containing the serialized updated worker and the HTTP status code 200.
      - If the worker is not found, returns a 404 status code.
    """
    worker = get_worker_by_id(worker_id)
    if not worker:
        return 'Worker not found', 404

    name = request.form.get('name')
    if name:
        update_worker_name(worker, name)

    expiration_date = request.form.get('expiration_date')
    if expiration_date:
        expiration_date = datetime.fromisoformat(expiration_date)
        extend_worker_expiration(worker, expiration_date)

    image_file = request.files.get('file')
    if image_file:
        face_image = parse_image(image_file.read())
        update_worker_face_image(worker, face_image)

    return WorkerSchema(many=False).dump(worker), 200

@bp.route('/api/workers/invalidate/<worker_id>', methods=['PUT'])
def invalidate_worker(worker_id):
    """
    [PUT] Invalidate an existing worker entry permit in the database.

    **Parameters**:
    - `worker_id` (int): The ID of the worker to update.

    **Returns**:
    - `tuple`: A tuple containing the serialized updated worker and the HTTP status code 200.
      - If the worker is not found, returns a 404 status code.
    """
    worker = get_worker_by_id(worker_id)
    if not worker:
        return 'Worker not found', 404

    expiration_date = datetime.now()
    extend_worker_expiration(worker, expiration_date)

    return WorkerSchema(many=False).dump(worker), 200


@bp.route('/api/workers/entrypass/<worker_id>', methods=['GET'])
def get_worker_entry_pass(worker_id):
    """
    [GET] Return the worker entry pass for printing.

    **Parameters**:
    - `worker_id` (int): The ID of the worker's pass.

    **Returns**:
    - `bytes`: Entry pass image encoded as png.
      - If the worker is not found, returns a 404 status code.
    """
    worker = get_worker_by_id(worker_id)
    if not worker:
        return 'Worker not found', 404

    image = generate_worker_entry_pass(worker)

    return send_file(io.BytesIO(image), mimetype="image/png", as_attachment=False), 200