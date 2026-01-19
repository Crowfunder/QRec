import pytest
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from backend.database.models import Worker
from backend.components.workers.workerService import (
    create_worker,
    get_worker_by_id,
    update_worker_name,
    extend_worker_expiration,
    get_worker_from_qr_code,
    get_worker_embedding,
    create_worker_embedding
)
from backend.components.camera_verification.qrcode.qrcodeService import (
    ExpiredCodeError,
    InvalidCodeError,
    NoCodeFoundError
)


# --------------------------------------------------------------------------
# Testy tworzenia i edycji pracownika
# --------------------------------------------------------------------------

@patch('backend.components.workers.workerService.face_recognition.face_encodings')
def test_create_worker_success(mock_face_encodings, db_session):
    """
    Testuje pełny proces tworzenia pracownika:
    1. Mockuje bibliotekę face_recognition (zwraca losowy wektor).
    2. Sprawdza czy pracownik trafił do bazy.
    3. Sprawdza czy wygenerowano sekret QR (inny niż tymczasowy).
    """
    # Setup mocka - symulujemy, że biblioteka znalazła jedną twarz (wektor 128 liczb)
    fake_embedding = [np.random.rand(128)]
    mock_face_encodings.return_value = fake_embedding

    # Dane wejściowe
    name = "Testowy Janusz"
    fake_image = np.zeros((100, 100, 3), dtype=np.uint8)  # Pusty obrazek
    exp_date = datetime.now() + timedelta(days=30)

    # Akcja
    worker = create_worker(name, fake_image, exp_date)

    # Asercje
    assert worker.id is not None
    assert worker.name == name
    assert worker.expiration_date == exp_date
    assert worker.secret != "TEMP_SECRET"  # Sekret powinien zostać zaktualizowany
    assert len(worker.face_embedding) > 0  # Blob powinien zawierać dane


def test_get_worker_by_id_success(db_session, created_worker):
    """Sprawdza pobieranie istniejącego pracownika."""
    fetched = get_worker_by_id(created_worker.id)
    assert fetched.id == created_worker.id
    assert fetched.name == created_worker.name


def test_get_worker_by_id_not_found(db_session):
    """Sprawdza czy rzucany jest błąd dla nieistniejącego ID."""
    with pytest.raises(ValueError, match="not found"):
        get_worker_by_id(999999)


def test_update_worker_name(db_session, created_worker):
    """Sprawdza aktualizację imienia."""
    new_name = "Zmieniony Imię"
    update_worker_name(created_worker, new_name)

    # Odświeżamy obiekt z bazy
    db_session.session.refresh(created_worker)
    assert created_worker.name == new_name


def test_extend_worker_expiration(db_session, created_worker):
    """Sprawdza przedłużanie ważności przepustki."""
    new_date = datetime.now() + timedelta(days=365)
    extend_worker_expiration(created_worker, new_date)

    db_session.session.refresh(created_worker)
    # Porównujemy timestampy (może być mikrosekundowa różnica przy zapisie do DB, stąd delta)
    assert abs((created_worker.expiration_date - new_date).total_seconds()) < 1


# --------------------------------------------------------------------------
# Testy logiki QR (Scan -> Worker)
# --------------------------------------------------------------------------

@patch('backend.components.workers.workerService.decode_qr_image')
def test_get_worker_from_qr_success(mock_decode, db_session, created_worker):
    """
    Testuje scenariusz, gdy kod QR jest poprawny i ważny.
    Mockujemy dekoder, aby zwracał sekret przypisany do created_worker.
    """
    mock_decode.return_value = created_worker.secret

    found_worker = get_worker_from_qr_code(np.array([]))  # Obrazek nie ma znaczenia bo mockujemy

    assert found_worker.id == created_worker.id


@patch('backend.components.workers.workerService.decode_qr_image')
def test_get_worker_from_qr_expired(mock_decode, db_session, created_worker):
    """
    Testuje scenariusz, gdy kod jest poprawny, ale data ważności minęła.
    """
    # Ustawiamy datę pracownika na przeszłą
    created_worker.expiration_date = datetime.now() - timedelta(days=1)
    db_session.session.commit()

    mock_decode.return_value = created_worker.secret

    with pytest.raises(ExpiredCodeError, match="wygasła"):
        get_worker_from_qr_code(np.array([]))


@patch('backend.components.workers.workerService.decode_qr_image')
def test_get_worker_from_qr_invalid_secret(mock_decode, db_session):
    """
    Testuje scenariusz, gdy kod QR zawiera sekret, którego nie ma w bazie.
    """
    mock_decode.return_value = "jakis_nieistniejacy_sekret_123"

    with pytest.raises(InvalidCodeError, match="niepoprawny kod QR"):
        get_worker_from_qr_code(np.array([]))


@patch('backend.components.workers.workerService.decode_qr_image')
def test_get_worker_from_qr_no_code(mock_decode, db_session):
    """
    Testuje sytuację, gdy biblioteka dekodująca nie znajdzie kodu na zdjęciu.
    """
    mock_decode.side_effect = NoCodeFoundError("Nie znaleziono kodu")

    with pytest.raises(NoCodeFoundError):
        get_worker_from_qr_code(np.array([]))


# --------------------------------------------------------------------------
# Testy techniczne (Embeddings / NumPy)
# --------------------------------------------------------------------------

def test_embedding_serialization_roundtrip():
    """
    Sprawdza, czy konwersja NumPy Array -> BLOB -> NumPy Array działa poprawnie.
    Jest to kluczowe, bo BLOB jest zapisywany w bazie SQLite.
    """
    # 1. Tworzymy sztuczny wektor twarzy (128 floatów)
    original_embedding = np.random.rand(128)

    # Uwaga: create_worker_embedding normalnie używa face_recognition.
    # Tutaj testujemy "ręcznie" logikę save/load z numpy, która jest wewnątrz funkcji,
    # albo mockujemy face_recognition.
    # W workerService funkcja create_worker_embedding robi: encoding -> io -> bytes.

    # Żeby przetestować tylko io/numpy bez face_recognition, możemy zasymulować
    # funkcję create_worker_embedding w prostszy sposób lub użyć mocka:

    with patch('backend.components.workers.workerService.face_recognition.face_encodings') as mock_enc:
        mock_enc.return_value = [original_embedding]

        # 2. Tworzymy BLOB (udajemy, że przekazujemy obrazek)
        blob = create_worker_embedding(np.zeros((10, 10)))

        # 3. Tworzymy fake'owy obiekt pracownika z tym blobem
        fake_worker = MagicMock()
        fake_worker.face_embedding = blob

        # 4. Odczytujemy BLOB z powrotem do tablicy
        restored_arr = get_worker_embedding(fake_worker)

        # 5. Porównujemy (musi być to samo lub bardzo blisko - float precision)
        # Ponieważ create_worker_embedding bierze pierwszy element listy [0],
        # a my w mocku zwróciliśmy [original_embedding], powinno się zgadzać.
        # Należy pamiętać, że np.save zapisuje cały array.

        # Funkcja create_worker_embedding robi: img_embedding = face_encodings(img) (to zwraca listę!)
        # a potem np.save(buffer, img_embedding).
        # Więc odczytany restored_arr będzie listą zawierającą wektory.

        np.testing.assert_array_almost_equal(restored_arr[0], original_embedding)