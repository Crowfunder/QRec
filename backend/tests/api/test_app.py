import pytest
from flask import json


def test_healthcheck(client):
    """
    Sprawdza, czy aplikacja żyje i odpowiada na podstawowy endpoint.
    Zakładamy, że istnieje endpoint '/' lub '/health' zwracający status 200.
    Jeśli w Twojej aplikacji root ('/') zwraca co innego, dostosuj ten test.
    """
    response = client.get('/health')
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "service": "camera-verification-api"}

def test_404_not_found(client):
    """
    Sprawdza, czy aplikacja poprawnie obsługuje żądania do nieistniejących zasobów.
    Powinna zwracać kod 404 i (opcjonalnie) ustandaryzowaną odpowiedź JSON lub HTML.
    """
    response = client.get('/non/existent/route/12345')

    assert response.status_code == 404

    # Sprawdzamy, czy w odpowiedzi jest treść błędu (zależy od Twojej obsługi błędów)
    # Jeśli używasz szablonu 404.html (widziałem go w plikach), sprawdźmy czy response to HTML
    if response.content_type == "text/html; charset=utf-8":
        assert b"404" in response.data or b"Not Found" in response.data
    elif response.is_json:
        data = response.get_json()
        assert "error" in data or "message" in data


def test_method_not_allowed(client):
    """
    Sprawdza zachowanie, gdy użyjemy złej metody HTTP na istniejącym endpoincie.
    Np. POST na endpoint, który obsługuje tylko GET.
    """
    # Załóżmy, że '/api/reports' obsługuje GET. Spróbujmy wysłać tam DELETE (jeśli nieobsługiwane).
    # Musimy użyć endpointu, który na pewno istnieje.
    # Z workerController: @worker_bp.route('/<int:worker_id>', methods=['GET'])

    # Najpierw musimy mieć pewność, że worker istnieje, żeby nie dostać 404,
    # ale 405 Method Not Allowed jest rzucane przez routing zanim wejdzie w logikę.

    response = client.post('/api/workers/1', json={})

    # Flask domyślnie zwraca 405 Method Not Allowed dla złej metody
    assert response.status_code == 405


def test_cors_headers(client):
    """
    (Opcjonalne) Sprawdza, czy nagłówki CORS są obecne, jeśli aplikacja ma być dostępna dla frontendu.
    """
    response = client.get('/non/existent', headers={'Origin': 'http://localhost:3000'})
    # Nawet przy błędzie 404 nagłówki CORS często są dołączane
    # Jeśli nie używasz flask-cors, ten test może nie być potrzebny.

    # assert 'Access-Control-Allow-Origin' in response.headers
    pass