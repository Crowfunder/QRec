import pytest
import io
import os
from backend.app import create_app, db
from backend.database.models import Worker


# -----------------------------------------------------------------------------
# Fixtures (Lokalne - wymagane, bo brak conftest.py)
# -----------------------------------------------------------------------------

@pytest.fixture
def client():
    """
    Tworzy klienta testowego z izolowaną bazą danych w pamięci.
    """
    # 1. Ustawienie bazy w pamięci RAM
    os.environ["FLASK_DB_PATH"] = ":memory:"

    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "QR_SECRET_KEY": b'test_secret_key_for_api_tests'
    })

    # 2. Utworzenie kontekstu i tabel
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            # Sprzątanie po teście
            db.session.remove()
            db.drop_all()

    # 3. Czyszczenie zmiennych środowiskowych
    if "FLASK_DB_PATH" in os.environ:
        del os.environ["FLASK_DB_PATH"]


# -----------------------------------------------------------------------------
# Testy API
# -----------------------------------------------------------------------------

def test_create_worker_api_success(client):
    """
    Testuje endpoint POST /api/workers (tworzenie pracownika).
    """
    # Symulujemy przesłanie formularza z plikiem
    data = {
        'name': 'Nowy Pracownik API',
        'expiration_date': '2030-01-01',
        'file': (io.BytesIO(b'fake_face_bytes'), 'face.jpg')
    }

    # content_type='multipart/form-data' jest kluczowe przy przesyłaniu plików
    response = client.post('/api/workers', data=data, content_type='multipart/form-data')

    # Oczekujemy kodu 201 (Created) lub 200 (zależnie od implementacji kontrolera)
    # Jeśli Twój kontroler zwraca 200 po utworzeniu, zmień poniższą linię na 200.
    # W standardzie REST zazwyczaj jest to 201.
    assert response.status_code in [200, 201]

    json_data = response.get_json()
    assert json_data['name'] == 'Nowy Pracownik API'
    assert 'id' in json_data


def test_create_worker_api_missing_data(client):
    """Sprawdza walidację braku pliku."""
    data = {
        'name': 'Bez Pliku',
        'expiration_date': '2030-01-01'
    }
    # Brak pola 'file' w data
    response = client.post('/api/workers', data=data, content_type='multipart/form-data')

    # Oczekujemy błędu 400 (Bad Request)
    assert response.status_code == 400
    assert "error" in response.get_json() or "message" in response.get_json()


def test_get_workers_list(client):
    """Testuje endpoint GET /api/workers."""
    # 1. Najpierw dodajmy kogoś ręcznie do bazy, żeby lista nie była pusta
    #    (Można użyć client.post, albo bezpośrednio db.session jeśli mamy dostęp)
    client.post('/api/workers', data={
        'name': 'Jan Lista',
        'expiration_date': '2025-01-01',
        'file': (io.BytesIO(b'img'), 'f.jpg')
    }, content_type='multipart/form-data')

    # 2. Pobranie listy
    response = client.get('/api/workers')

    assert response.status_code == 200
    json_data = response.get_json()

    assert isinstance(json_data, list)
    assert len(json_data) >= 1
    # Sprawdzamy czy dodany pracownik tam jest
    names = [w['name'] for w in json_data]
    assert 'Jan Lista' in names


def test_get_worker_pass_qr(client):
    """
    Testuje endpoint generowania przepustki (QR code).
    Zakładamy endpoint: /api/workers/<id>/pass (lub /qrcode/<id> zależnie od Twojego routingu)
    """
    # 1. Utwórz pracownika i pobierz ID
    res = client.post('/api/workers', data={
        'name': 'Jan QR',
        'expiration_date': '2025-12-12',
        'file': (io.BytesIO(b'x'), 'x.jpg')
    }, content_type='multipart/form-data')

    created_worker = res.get_json()
    worker_id = created_worker['id']

    # 2. Pobierz przepustkę
    # UWAGA: Upewnij się, jaki masz dokładnie URL w workerController.py
    # Zazwyczaj: /api/workers/<id>/qr lub /api/workers/<id>/pass
    # Tutaj zakładam /api/workers/<id>/qrcode na podstawie typowych nazw
    response = client.get(f'/api/workers/{worker_id}/qrcode')

    if response.status_code == 404:
        pytest.fail(
            "Endpoint nie znaleziony. Sprawdź URL w workerController (np. czy to /qrcode, /pass czy /entry-pass).")

    assert response.status_code == 200
    # Sprawdź czy to obrazek (PNG)
    assert response.mimetype == 'image/png'
    assert len(response.data) > 0