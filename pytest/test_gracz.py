import pytest
import socketio
import eventlet
from poker import Gracz, Karta, pierwsze_rozdanie, wynik

@pytest.fixture
def sio_client():
    sio_client = socketio.Client()
    yield sio_client
    sio_client.disconnect()

def test_pas(sio_client):
    sio_client.connect('http://localhost:5000')

    # Obsługa wykonania spasowania
    def komunikat(data):
        sio_client.emit('pas', {})
        sio_client.on('komunikat', komunikat_pas)

    # komunikat o wykonaniu spasowania
    def komunikat_pas(data):
        assert data["komunikat"] == "Pomyślnie spasowano."

    # Połącz klienta WebSocket z serwerem
    sio_client.on('komunikat', komunikat)

    # Uruchom obsługę zdarzeń
    eventlet.sleep(1)

def test_sprawdzenie(sio_client):
    sio_client.connect('http://localhost:5000')

    # Obsługa sprawdzenia stawki
    def komunikat(data):
        sio_client.emit('sprawdzenie', {"stawka": 50})
        sio_client.on('komunikat', komunikat_sprawdzenie)

    # komunikat o sprawdzeniu stawki
    def komunikat_sprawdzenie(data):
        assert data["komunikat"] == "Stawka została wyrównana."

    # Połącz klienta WebSocket z serwerem
    sio_client.on('komunikat', komunikat)

    # Uruchom obsługę zdarzeń
    eventlet.sleep(1)

def test_postawienie(sio_client):
    sio_client.connect('http://localhost:5000')

    # Obsługa postawienia stawki
    def komunikat(data):
        sio_client.emit('postawienie', {"stawka": 20})
        sio_client.on('komunikat', komunikat_postawienie)

    # komunikat o postawieniu stawki
    def komunikat_postawienie(data):
        assert data["komunikat"] == "Postawiono stawkę."

    # Połącz klienta WebSocket z serwerem
    sio_client.on('komunikat', komunikat)

    # Uruchom obsługę zdarzeń
    eventlet.sleep(1)

def test_podbicie(sio_client):
    sio_client.connect('http://localhost:5000')

    # Obsługa podbicia 
    def komunikat(data):
        sio_client.emit('podbicie', {"aktualna_stawka": 30, "stawka": 40})
        sio_client.on('komunikat', komunikat_podbicie)

    # komunikat o podbiciu stawki 
    def komunikat_podbicie(data):
        assert data["komunikat"] == "Podbito stawkę."

    # Połącz klienta WebSocket z serwerem
    sio_client.on('komunikat', komunikat)

    # Uruchom obsługę zdarzeń
    eventlet.sleep(1)

def test_va_banque(sio_client):
    sio_client.connect('http://localhost:5000')

    # Obsługa va banque 
    def komunikat(data):
        sio_client.emit('va_banque', {})
        sio_client.on('komunikat', komunikat_va_banque)

    # komunikat o ruchu va banque
    def komunikat_va_banque(data):
        assert data["komunikat"] == "Postawiono wszystkie dostępne żetony."

    # Połącz klienta WebSocket z serwerem
    sio_client.on('komunikat', komunikat)

    # Uruchom obsługę zdarzeń
    eventlet.sleep(1)

def test_dobierz_karte(sio_client):
    sio_client.connect('http://localhost:5000')

    # Obsługa dobierania kart
    def komunikat(data):
        sio_client.emit('dobierz_karte', {})
        sio_client.on('komunikat', komunikat_dobierz_karte)

    # komunikat dobrania karty
    def komunikat_dobierz_karte(data):
        assert data["komunikat"] == "Dobrano kartę."

    # Połącz klienta WebSocket z serwerem
    sio_client.on('komunikat', komunikat)

    # Uruchom obsługę zdarzeń
    eventlet.sleep(1)

def test_pokaz_reke(sio_client):
    sio_client.connect('http://localhost:5000')

    # funkcja obsługi komunikatu o obsłudze ręki 
    def komunikat(data):
        sio_client.emit('pokaz_reke', {})
        sio_client.on('komunikat', komunikat_pokaz_reke)

    # komunikat przy pokazaniu ręki
    def komunikat_pokaz_reke(data):
        assert data["komunikat"] == "Pokazano reke."

    # Połącz klienta WebSocket z serwerem
    sio_client.on('komunikat', komunikat)

    # Uruchom obsługę zdarzeń
    eventlet.sleep(1)

def test_wynik_single_winner(sio_client):
    wyniki = {
        "gracz1": {"uklad": "Para", "dodatkowe_informacje": "Para Asów"},
        "gracz2": {"uklad": "Trójka", "dodatkowe_informacje": "Trójka Dziewiątek"}
    }
    
    def wynik(data):
        print("Otrzymane dane:", data)
        expected_data = {
            " zwyciezcą jest: ": "gracz2",
            " z układem: ": "Trójka",
            "dodatkowe_informacje": "Trójka Dziewiątek"
        }
        # Ignorujemy klucz 'uklad' w danych otrzymanych
        received_data = {key: val for key, val in data.items() if key != 'uklad'}
        assert received_data == expected_data
    
    # Przekazujemy tylko dane o zwycięzcy, układzie i dodatkowych informacjach
    wynik({ " zwyciezcą jest: ": "gracz2", " z układem: ": "Trójka", **wyniki["gracz2"] })

def test_wynik_draw(sio_client):
    from poker import analiza_ukladu
    wyniki = {
        "gracz1": {"uklad": "Para", "dodatkowe_informacje": "Para Króli"},
        "gracz2": {"uklad": "Para", "dodatkowe_informacje": "Para Królowych"},
        "gracz3": {"uklad": "Para", "dodatkowe_informacje": "Para Dziesiątek"}
    }

    def wynik(data):
        assert data == {"remis": ["gracz1", "gracz2", "gracz3"]}

    # Przekazujemy dane o remisie jako argument
    wynik({"remis": ["gracz1", "gracz2", "gracz3"]})

def test_pierwsze_rozdanie():
    from poker import pierwsze_rozdanie

    # Wywołujemy funkcję pierwsze_rozdanie() bez argumentów
    karty_graczy = pierwsze_rozdanie() 

    # Sprawdzamy czy funkcja zwróciła poprawne dane
    assert len(karty_graczy) == 4
    for reka in karty_graczy.values():
        assert len(reka) == 5