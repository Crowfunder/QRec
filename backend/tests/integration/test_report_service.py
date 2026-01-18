import pytest
import os
from datetime import datetime, timedelta
from backend.app import create_app, db
from backend.database.models import Worker, Entry
from backend.components.reports import reportService


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def app_context():
    """Tworzy aplikację Flask z bazą danych w pamięci RAM."""
    # FIX: Ustawiamy zmienną środowiskową, aby uniknąć błędów zapisu na dysku
    os.environ["FLASK_DB_PATH"] = ":memory:"

    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "QR_SECRET_KEY": b'test_key'
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

    if "FLASK_DB_PATH" in os.environ:
        del os.environ["FLASK_DB_PATH"]


@pytest.fixture
def sample_worker(app_context):
    """Pomocnicza fixture tworząca pracownika."""
    worker = Worker(
        name="Tester Raportów",
        face_embedding=b'dummy',
        expiration_date=datetime(2099, 1, 1),
        secret="secret"
    )
    db.session.add(worker)
    db.session.commit()
    return worker


# -----------------------------------------------------------------------------
# Testy: log_worker_entry
# -----------------------------------------------------------------------------

def test_log_worker_entry_success(app_context, sample_worker):
    """
    Sprawdza logowanie udanego wejścia (code 0).
    Zgodnie z logiką biznesową, dla code=0 obrazek NIE powinien być zapisany.
    """
    img_data = b'fake_image_bytes'

    entry = reportService.log_worker_entry(
        code=0,
        message="Weryfikacja OK",
        worker=sample_worker,
        image=img_data
    )

    assert entry.id is not None
    assert entry.code == 0
    assert entry.worker_id == sample_worker.id
    # Sprawdzenie logiki biznesowej: sukces = brak zdjęcia w bazie
    assert entry.face_image is None

    # Weryfikacja w bazie
    saved = db.session.get(Entry, entry.id)
    assert saved.message == "Weryfikacja OK"


def test_log_worker_entry_failure(app_context, sample_worker):
    """
    Sprawdza logowanie nieudanego wejścia (code != 0).
    Tutaj obrazek POWINIEN zostać zapisany.
    """
    img_data = b'evidence_image_bytes'

    entry = reportService.log_worker_entry(
        code=403,
        message="Twarz nie pasuje",
        worker=sample_worker,
        image=img_data
    )

    assert entry.code == 403
    assert entry.face_image == img_data  # Zdjęcie zachowane


def test_log_worker_entry_anonymous(app_context):
    """Sprawdza logowanie próby wejścia bez rozpoznanego pracownika."""
    entry = reportService.log_worker_entry(
        code=404,
        message="Nie wykryto pracownika",
        worker=None,  # Brak obiektu pracownika
        image=b'some_img'
    )

    assert entry.worker_id is None
    assert entry.message == "Nie wykryto pracownika"


# -----------------------------------------------------------------------------
# Testy: get_report_data (Filtrowanie)
# -----------------------------------------------------------------------------

@pytest.fixture
def seed_entries(app_context, sample_worker):
    """Wypełnia bazę serią wpisów do testowania raportów."""
    base_time = datetime(2024, 6, 1, 12, 0, 0)

    # Wpis 1: Sukces, Worker A, Data bazowa
    e1 = Entry(worker_id=sample_worker.id, code=0, message="OK", date=base_time)

    # Wpis 2: Błąd, Worker A, Data bazowa + 1 dzień
    e2 = Entry(worker_id=sample_worker.id, code=1, message="Err", date=base_time + timedelta(days=1))

    # Wpis 3: Błąd, Nieznany pracownik, Data bazowa + 2 dni
    e3 = Entry(worker_id=None, code=404, message="Unknown", date=base_time + timedelta(days=2))

    db.session.add_all([e1, e2, e3])
    db.session.commit()
    return [e1, e2, e3]


def test_report_filter_all_explicit(app_context, seed_entries, sample_worker):
    """Sprawdza czy pobiera wszystko, gdy zaznaczono oba checkboxy lub żadnego."""
    # show_valid=True, show_invalid=True
    results = reportService.get_report_data(show_valid=True, show_invalid=True)
    assert len(results) == 3

    # show_valid=False, show_invalid=False (domyślny fallback)
    results_default = reportService.get_report_data(show_valid=False, show_invalid=False)
    assert len(results_default) == 3


def test_report_filter_valid_only(app_context, seed_entries):
    """Sprawdza filtrowanie tylko poprawnych wejść (code == 0)."""
    results = reportService.get_report_data(show_valid=True, show_invalid=False)

    assert len(results) == 1
    entry, worker = results[0]
    assert entry.code == 0
    assert entry.message == "OK"


def test_report_filter_invalid_only(app_context, seed_entries):
    """Sprawdza filtrowanie tylko błędnych wejść (code != 0)."""
    results = reportService.get_report_data(show_valid=False, show_invalid=True)

    assert len(results) == 2
    codes = [r[0].code for r in results]
    assert 0 not in codes
    assert 1 in codes
    assert 404 in codes


def test_report_filter_by_worker(app_context, seed_entries, sample_worker):
    """Sprawdza filtrowanie po ID pracownika."""
    # Powinniśmy dostać 2 wpisy dla sample_worker (jeden valid, jeden invalid)
    # Trzeci wpis (anonymous) powinien zostać odfiltrowany
    results = reportService.get_report_data(worker_id=sample_worker.id)

    assert len(results) == 2
    for entry, worker in results:
        assert entry.worker_id == sample_worker.id


def test_report_filter_by_date(app_context, seed_entries):
    """Sprawdza zakres dat."""
    # seed_entries[1] ma datę base + 1 dzień
    target_date = datetime(2024, 6, 2)

    # Szukamy dokładnie w tym dniu (od północy do końca dnia)
    date_from = target_date.replace(hour=0, minute=0, second=0)
    date_to = target_date.replace(hour=23, minute=59, second=59)

    results = reportService.get_report_data(date_from=date_from, date_to=date_to)

    assert len(results) == 1
    assert results[0][0].code == 1  # To był wpis z błędem z drugiego dnia