import pytest
from datetime import datetime, timedelta
from backend.database.models import Entry, Worker

# ============================================================================
# Test Fixtures & Data Setup
# ============================================================================

@pytest.fixture
def populate_entries(db_session, created_worker):
    """
    A helper fixture that adds a series of entries to the database to test filtering and statistics.
    It creates entries for 'created_worker' (from conftest) and an additional worker.
    """
    # Dodajemy drugiego pracownika dla różnorodności
    worker_2 = Worker(
        name="Test Worker 2",
        face_embedding=b'dummy_embedding',
        expiration_date=datetime.now() + timedelta(days=30),
        secret="secret_2"
    )
    db_session.session.add(worker_2)
    db_session.session.commit()

    base_time = datetime.now()

    entries = [
        # Wpis 1: Dzisiaj, Poprawny, Worker 1
        Entry(
            worker_id=created_worker.id,
            code=0,
            message="Wstęp przyznany",
            date=base_time,
            face_image=b'img1'
        ),
        # Wpis 2: Dzisiaj, Niepoprawny (błąd weryfikacji), Worker 1
        Entry(
            worker_id=created_worker.id,
            code=1,
            message="Błąd weryfikacji twarzy",
            date=base_time - timedelta(minutes=10),
            face_image=b'img2'
        ),
        # Wpis 3: Wczoraj, Poprawny, Worker 2
        Entry(
            worker_id=worker_2.id,
            code=0,
            message="Wstęp przyznany",
            date=base_time - timedelta(days=1),
            face_image=b'img3'
        ),
        # Wpis 4: Przedwczoraj, Niepoprawny (nieznany pracownik - brak worker_id)
        Entry(
            worker_id=None,
            code=2,
            message="Nie rozpoznano pracownika",
            date=base_time - timedelta(days=2),
            face_image=b'img4'
        )
    ]

    db_session.session.add_all(entries)
    db_session.session.commit()

    return {
        "worker_1": created_worker,
        "worker_2": worker_2,
        "entries": entries
    }


# ============================================================================
# Test GET /api/raport - Basic Retrieval
# ============================================================================


def test_get_report_empty(client, db_session):
    """
    Tests report download when the database is empty.
    """
    response = client.get('/api/raport')

    assert response.status_code == 200
    data = response.get_json()
    assert data['count'] == 0
    assert data['data'] == []
    # Sprawdzenie czy statystyki są wyzerowane
    assert data['statistics']['total_entries'] == 0


def test_get_report_all_data(client, populate_entries):
    """
    Tests downloading all data without filters (default sorting).
    """
    response = client.get('/api/raport')

    assert response.status_code == 200
    data = response.get_json()

    # Mamy 4 wpisy w fixturze
    assert data['count'] == 4
    assert len(data['data']) == 4

    # Sprawdzenie poprawności statystyk
    stats = data['statistics']
    assert stats['total_entries'] == 4
    assert stats['valid_entries'] == 2  # Wpis 1 i 3
    assert stats['invalid_entries'] == 2  # Wpis 2 i 4
    assert stats['success_rate_percent'] == 50.0


# ============================================================================
# Test GET /api/raport - Filtering Logic
# ============================================================================

def test_filter_by_worker_id(client, populate_entries):
    """
    Testing filtering by employee ID.
    """
    worker_1 = populate_entries['worker_1']

    # Filtrujemy tylko dla worker_1 (powinien mieć 2 wpisy: 1 valid, 1 invalid)
    response = client.get(f'/api/raport?pracownik_id={worker_1.id}')

    assert response.status_code == 200
    data = response.get_json()

    assert data['count'] == 2
    for item in data['data']:
        assert item['worker_id'] == worker_1.id


def test_filter_by_date_range(client, populate_entries):
    """
    Tests filtering by date (date_from, date_to).
    """
    # Chcemy pobrać wpisy tylko z "dzisiaj"
    today_str = datetime.now().strftime('%Y-%m-%d')

    # date_from = dzisiaj, date_to = dzisiaj (obejmuje cały dzień do 23:59:59 wg logiki w kontrolerze)
    response = client.get(f'/api/raport?date_from={today_str}&date_to={today_str}')

    assert response.status_code == 200
    data = response.get_json()

    # Powinny być 2 wpisy z dzisiaj (dla worker_1)
    assert data['count'] == 2
    for item in data['data']:
        assert item['date'].startswith(today_str)


def test_filter_valid_only(client, populate_entries):
    """
    Tests the 'wejscia_poprawne' flag - it should return only entries with code 0.
    """
    # Przekazujemy parametr 'wejscia_poprawne' (wystarczy jego obecność)
    response = client.get('/api/raport?wejscia_poprawne=true')

    assert response.status_code == 200
    data = response.get_json()

    assert data['count'] == 2
    for item in data['data']:
        assert item['code'] == 0


def test_filter_invalid_only(client, populate_entries):
    """
    Tests the 'wejscia_niepoprawne' flag - it should return entries with the code != 0.
    """
    response = client.get('/api/raport?wejscia_niepoprawne=true')

    assert response.status_code == 200
    data = response.get_json()

    assert data['count'] == 2
    for item in data['data']:
        assert item['code'] != 0


def test_invalid_date_format(client):
    """
    Tests error handling for bad date format (400 Bad Request).
    """
    response = client.get('/api/raport?date_from=bad-format')
    assert response.status_code == 400
    assert 'error' in response.get_json()


# ============================================================================
# Test GET /api/raport/pdf - PDF Generation
# ============================================================================


def test_pdf_generation(client, populate_entries):
    """
    Tests the PDF generation endpoint (/api/report/pdf).
    Checks whether the correct MIME type is returned and whether there is no 500 error.
    """
    response = client.get('/api/raport/pdf')

    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/pdf'
    # Sprawdzamy, czy plik nie jest pusty
    assert len(response.data) > 0
    # Sprawdzamy nagłówek Content-Disposition (czy jest jako attachment)
    assert 'attachment' in response.headers['Content-Disposition']
    assert '.pdf' in response.headers['Content-Disposition']


def test_pdf_generation_empty(client, db_session):
    """
    Tests PDF generation with no data (should generate an empty report without error).
    """
    response = client.get('/api/raport/pdf')
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/pdf'

# ============================================================================
# Test Statistics Logic
# ============================================================================


def test_statistics_calculation(client, populate_entries):
    """
    Detailed test of the correctness of calculating statistics in JSON.
    """
    worker_1 = populate_entries['worker_1']

    response = client.get('/api/raport')
    stats = response.get_json()['statistics']

    # Sprawdzenie "most_valid_entries_worker" (powinien być worker_1 lub worker_2, obaj mają po 1)
    # W implementacji licznika (Counter) kolejność przy remisie zależy od kolejności dodawania
    assert stats['most_valid_entries_worker']['count'] == 1

    # Sprawdzenie "most_invalid_attempts_worker"
    # Worker 1 ma 1 nieudane, Worker "None" ma 1 nieudane.
    # Sprawdzamy czy w ogóle zwróciło obiekt
    assert stats['most_invalid_attempts_worker'] is not None
    assert stats['most_invalid_attempts_worker']['count'] == 1