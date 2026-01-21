import pytest
from flask import json


# ============================================================================
# Test General Application Endpoints
# ============================================================================

def test_healthcheck(client):
    """
    Endpoint healthcheck test to check service status.

    Verifies that the application is running and responding to the primary monitoring endpoint.
    Expects a status of 200 and a service ID in JSON format.
    """
    # Wyślij żądanie GET do endpointu monitorowania
    response = client.get('/health')

    # Sprawdź kod statusu
    assert response.status_code == 200

    # Sprawdź poprawność zwróconej struktury JSON
    expected_response = {"status": "ok", "service": "camera-verification-api"}
    assert response.get_json() == expected_response


# ============================================================================
# Test HTTP Error Handling
# ============================================================================

def test_404_not_found(client):
    """
    Tests handling requests to non-existent resources (Error 404).

    Checks whether the application correctly returns a 404 error code for unknown paths.
    It also verifies whether the response content is appropriate (HTML for browsers or JSON for APIs),
    depending on the global error handling configuration.
    """

    # Próba dostępu do losowej, nieistniejącej ścieżki
    response = client.get('/non/existent/route/12345')

    # Weryfikacja kodu błędu
    assert response.status_code == 404

    # Analiza typu zawartości odpowiedzi (Content-Type)
    if response.content_type == "text/html; charset=utf-8":
        # Jeśli aplikacja zwraca szablon HTML (np. templates/404.html)
        assert b"404" in response.data or b"Not Found" in response.data
    elif response.is_json:
        # Jeśli aplikacja zwraca błąd w formacie JSON
        data = response.get_json()
        assert "error" in data or "message" in data


def test_method_not_allowed(client):
    """
    Test behavior using a disallowed HTTP method (Error 405).

    Verifies that Flask routing correctly blocks requests (e.g., POST)
    to endpoints defined only for another method (e.g., GET).
    """

    # Próba wysłania POST na endpoint tylko do odczytu
    response = client.post('/api/workers/1', json={})

    # Flask powinien automatycznie zwrócić 405 Method Not Allowed
    assert response.status_code == 405


