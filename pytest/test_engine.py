import pytest
import socketio
import eventlet
from poker import app as flask_app

@pytest.fixture
def app():
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

def test_rejestracja(client):
    # Utwórz klienta WebSocket
    sio_client = socketio.Client()

    # Zdefiniuj funkcję obsługi komunikatu 'komunikat' wysłanego przez serwer
    def komunikat(data):
        assert data["komunikat"] == "Rejestracja zakończona pomyślnie."
        sio_client.disconnect()

    # Połącz klienta WebSocket z serwerem
    sio_client.connect('http://localhost:5000')

    # Zarejestruj funkcję obsługi komunikatu 'komunikat'
    sio_client.on('komunikat', komunikat)

    # Wyślij komunikat rejestracji do serwera za pomocą WebSocket
    sio_client.emit('rejestracja', {"nazwa": "Testowy gracz"})

    # Uruchom obsługę zdarzeń
    eventlet.sleep(1)
    sio_client.disconnect()

def test_rozdanie(client):
    # Utwórz klienta WebSocket
    sio_client = socketio.Client()

    # Zdefiniuj funkcję obsługi komunikatu 'karty' wysłanego przez serwer
    def karty(data):
        assert len(data["reka"]) == 2
        assert len(data["stol"]) == 5
        sio_client.disconnect()

    # Połącz klienta WebSocket z serwerem
    sio_client.connect('http://localhost:5000')

    # Zarejestruj funkcję obsługi komunikatu 'karty'
    sio_client.on('karty', karty)

    # Wyślij komunikat o rozdaniu kart do serwera za pomocą WebSocket
    sio_client.emit('rozdanie', {"nazwa": "Testowy gracz"})

    # Uruchom obsługę zdarzeń
    eventlet.sleep(1)
    sio_client.disconnect()