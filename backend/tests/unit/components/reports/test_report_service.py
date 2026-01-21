import pytest
from datetime import datetime, timedelta
from backend.database.models import Entry, Worker
from backend.components.reports.reportService import log_worker_entry, get_report_data


# --------------------------------------------------------------------------
# Testy funkcji log_worker_entry
# --------------------------------------------------------------------------

def test_log_worker_entry_success_removes_image(db_session, created_worker):
    """
    Checks whether, on successful entry (code=0), the image is deleted (set to None),
    even if it was passed to the function.
    """
    fake_image = b'some_image_bytes'

    entry = log_worker_entry(
        code=0,
        message="Access Granted",
        worker=created_worker,
        image=fake_image
    )

    # Sprawdzamy czy obiekt został zwrócony i ma ID (czyli jest w sesji/bazie)
    assert entry.id is not None
    assert entry.worker_id == created_worker.id
    assert entry.code == 0
    # Kluczowy test logiki biznesowej: code 0 -> image musi być None
    assert entry.face_image is None


def test_log_worker_entry_failure_keeps_image(db_session, created_worker):
    """
    Checks whether the photo is saved in the database on an unsuccessful entry (code!=0).
    """
    fake_image = b'evidence_image_bytes'

    entry = log_worker_entry(
        code=1,  # Błąd/Odmowa
        message="Face mismatch",
        worker=created_worker,
        image=fake_image
    )

    assert entry.id is not None
    assert entry.code == 1
    # Przy błędzie zdjęcie powinno zostać zachowane
    assert entry.face_image == fake_image


def test_log_worker_entry_unknown_person(db_session):
    """
    Checks login entry for an unrecognized person (worker=None).
    """
    entry = log_worker_entry(
        code=2,
        message="Unknown person",
        worker=None,
        image=b'intruder_face'
    )

    assert entry.id is not None
    assert entry.worker_id is None
    assert entry.message == "Unknown person"


# --------------------------------------------------------------------------
# Testy funkcji get_report_data
# --------------------------------------------------------------------------

@pytest.fixture
def report_data_setup(db_session, created_worker):
    """
    A support fixture that creates a test data set for reporting.

    Creates 4 entries with different dates and statuses.
    """
    base_time = datetime(2023, 1, 1, 12, 0, 0)

    # Drugi pracownik do testów filtrowania
    worker2 = Worker(name="Adam Nowak", face_embedding=b'123', expiration_date=datetime.now(), secret="sec")
    db_session.session.add(worker2)
    db_session.session.commit()

    entries = [
        # 1. Wpis poprawny, Worker 1, Data: base_time (najstarszy)
        Entry(worker_id=created_worker.id, code=0, message="OK", date=base_time),

        # 2. Wpis błędny, Worker 1, Data: base_time + 1 dzień
        Entry(worker_id=created_worker.id, code=1, message="Error", date=base_time + timedelta(days=1)),

        # 3. Wpis poprawny, Worker 2, Data: base_time + 2 dni
        Entry(worker_id=worker2.id, code=0, message="OK", date=base_time + timedelta(days=2)),

        # 4. Wpis błędny, Brak Workera, Data: base_time + 3 dni (najnowszy)
        Entry(worker_id=None, code=2, message="Unknown", date=base_time + timedelta(days=3))
    ]

    db_session.session.add_all(entries)
    db_session.session.commit()

    return {
        "base_time": base_time,
        "worker1": created_worker,
        "worker2": worker2
    }


def test_get_report_data_all(db_session, report_data_setup):
    """Test downloading all data (no filters)."""
    results = get_report_data()

    assert len(results) == 4
    # Sprawdzenie sortowania (domyślnie malejąco po dacie - najnowsze pierwsze)
    assert results[0][0].message == "Unknown"  # Najnowszy (+3 dni)
    assert results[-1][0].message == "OK"  # Najstarszy (+0 dni)

    # Sprawdzenie czy zwraca krotki (Entry, Worker)
    first_entry, first_worker = results[0]
    assert isinstance(first_entry, Entry)
    assert first_worker is None  # Ten wpis nie miał workera


def test_get_report_data_filter_by_worker(db_session, report_data_setup):
    """Test filtering by employee ID."""
    worker1 = report_data_setup["worker1"]

    results = get_report_data(worker_id=worker1.id)

    # Worker 1 ma 2 wpisy
    assert len(results) == 2
    for entry, worker in results:
        assert entry.worker_id == worker1.id
        assert worker.id == worker1.id


def test_get_report_data_filter_by_date(db_session, report_data_setup):
    """Test filtering by date range."""
    base_time = report_data_setup["base_time"]

    # Filtrujemy od dnia +1 do dnia +2 (powinny być 2 wpisy)
    date_from = base_time + timedelta(days=1)
    date_to = base_time + timedelta(days=2)

    results = get_report_data(date_from=date_from, date_to=date_to)

    assert len(results) == 2
    messages = [r[0].message for r in results]
    assert "Error" in messages  # +1 dzień
    assert "OK" in messages  # +2 dni


def test_get_report_data_filter_valid_invalid(db_session, report_data_setup):
    """Test filtering by status (valid/invalid)."""

    # 1. Tylko poprawne (code == 0) -> Powinny być 2 (jeden workera1, jeden workera2)
    valid_results = get_report_data(show_valid=True, show_invalid=False)
    assert len(valid_results) == 2
    for r in valid_results:
        assert r[0].code == 0

    # 2. Tylko błędne (code != 0) -> Powinny być 2
    invalid_results = get_report_data(show_valid=False, show_invalid=True)
    assert len(invalid_results) == 2
    for r in invalid_results:
        assert r[0].code != 0

    # 3. Oba zaznaczone -> Wszystkie 4
    all_results = get_report_data(show_valid=True, show_invalid=True)
    assert len(all_results) == 4

    # 4. Żaden niezaznaczony -> Domyślnie wszystkie 4 (zgodnie z logiką funkcji)
    none_results = get_report_data(show_valid=False, show_invalid=False)
    assert len(none_results) == 4