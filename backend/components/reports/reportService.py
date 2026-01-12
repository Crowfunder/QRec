from backend.app import db
from backend.database.models import Entry, Worker
from sqlalchemy import or_
from datetime import datetime, time
from typing import List, Tuple, Optional

def get_report_data(date_from: datetime = None,
                    date_to: datetime = None,
                    worker_id: int = None,
                    show_valid: bool = False,
                    show_invalid: bool = False) -> List[Tuple[Entry, Optional[Worker]]]:
    '''
        Retrieves entry report data by joining Entry records with Worker data.

        This function handles filtering by date range, specific worker, and entry validity status.
        Results are sorted in descending order by date.

        **Parameters**:
        - `date_from` (datetime): Start date (inclusive). Defaults to None.
        - `date_to` (datetime): End date (inclusive). Defaults to None.
        - `worker_id` (int): Worker ID to filter by. Defaults to None.
        - `show_valid` (bool): Whether to include valid entries (code 0). If selected together with show_invalid (or both are unselected), returns all types.
        - `show_invalid` (bool): Whether to include invalid entries (code != 0). If selected together with show_valid (or both are unselected), returns all types.

        **Returns**:
        - `List[Tuple[Entry, Optional[Worker]]]` - A list of tuples where the first element is the entry object (Entry) and the second is the worker object (Worker) or None if the entry has no assigned worker.
    '''
    query = db.session.query(Entry, Worker).outerjoin(Worker, Entry.worker_id == Worker.id)

    if date_from:
        query = query.filter(Entry.date >= date_from)

    if date_to:
        query = query.filter(Entry.date <= date_to)

    if worker_id:
        query = query.filter(Entry.worker_id == worker_id)

    # Logika filtrów:
    # 1. Oba zaznaczone -> Pokaż wszystko (pass)
    # 2. Tylko valid -> kod == 0
    # 3. Tylko invalid -> kod != 0
    # 4. Żaden niezaznaczony -> Pokaż wszystko (domyślne zachowanie query bez filtrów)
    if show_valid and show_invalid:
        pass
    elif show_valid:
        query = query.filter(Entry.code == 0)
    elif show_invalid:
        query = query.filter(Entry.code != 0)

    query = query.order_by(Entry.date.desc())

    return query.all()