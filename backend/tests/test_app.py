import pytest
from backend import app as flask_app


@pytest.fixture
def client(app_context):
    """Create Flask test client."""
    return app_context.test_client()


def test_home(client):
    response = client.get("/")
    assert response.status_code == 200
