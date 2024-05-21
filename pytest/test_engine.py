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

    # Zdefiniuj funkcję obsługi komunikatu 'rejestracja' wysłanego przez serwer
    def komunikat(data):
        if "komunikat" in data:
            assert data["komunikat"] == "Rejestracja zakończona pomyślnie."
        elif "błąd" in data:
            assert data["błąd"] == "Nazwa jest wymagana."
        else:
            assert False, "Otrzymano nieoczekiwany komunikat"
        sio_client.disconnect()

    # Połącz klienta WebSocket z serwerem
    sio_client.connect('http://localhost:5000')

    # Zarejestruj funkcję obsługi komunikatu 'rejestracja'
    sio_client.on('rejestracja', komunikat)

    # Wyślij komunikat rejestracji do serwera za pomocą WebSocket
    sio_client.emit('rejestracja', {"nazwa": "Testowy gracz"})

    # Uruchom obsługę zdarzeń
    eventlet.sleep(1)
    sio_client.disconnect()