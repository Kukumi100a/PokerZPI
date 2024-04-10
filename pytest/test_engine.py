import pytest
import requests
from poker import app as flask_app

@pytest.fixture
def app():
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

def test_rejestracja(client):
    response = client.post('/rejestracja', json={"nazwa": "Testowy gracz"})
    assert response.status_code == 200
    assert response.json["komunikat"] == "Rejestracja zakończona pomyślnie."

def test_rozdanie(client):
    response = client.post('/rozdanie', json={"nazwa": "Testowy gracz"})
    assert response.status_code == 200
    assert len(response.json["reka"]) == 5
