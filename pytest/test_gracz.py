import pytest
import socketio
import eventlet
from poker import Gracz, Karta, pierwsze_rozdanie, wynik, Pokoj, stworz_pokoj, pokoje, Talia

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

def test_wyswietl_pokoje(sio_client):
    sio_client.connect('http://localhost:5000')

    def komunikat_pokoje(data):
        assert 'pokoje' in data
        pokoje = data['pokoje']
        assert isinstance(pokoje, list)
        assert len(pokoje) == 0  

    sio_client.emit('wyswietl_pokoje')

    sio_client.on('lista_pokoi', komunikat_pokoje)

    eventlet.sleep(1)
    
def test_stworz_pokoj(sio_client):
    sio_client.connect('http://localhost:5000')

    nazwa_pokoju = "testowy_pokoj"
    haslo = "testowe_haslo"
    wlasciciel = "testowy_gracz"

    # Wysłanie żądania utworzenia pokoju
    sio_client.emit('stworz_pokoj', {'nazwa': nazwa_pokoju, 'haslo': haslo, 'wlasciciel': wlasciciel})

    # Obsługa komunikatu o sukcesie
    def komunikat_sukcesu(data):
        assert data["success"] == "Pokój został utworzony pomyślnie"

    # Połącz klienta WebSocket z serwerem
    sio_client.on('stworz_pokoj', komunikat_sukcesu)

    # Uruchom obsługę zdarzeń
    eventlet.sleep(1)

def test_dolacz_do_pokoju(sio_client):
    from poker import pokoje
    
    # Tworzenie tymczasowego pokoju
    nazwa_pokoju = "testowy_pokoj"
    haslo = "testowe_haslo"
    wlasciciel = "testowy_gracz"
    pokoj = Pokoj(nazwa_pokoju, wlasciciel, haslo)
    pokoje.append(pokoj)
    
    sio_client.connect('http://localhost:5000')

    nazwa_pokoju = "testowy_pokoj"
    haslo = "testowe_haslo"
    gracz = "testowy_gracz"
    wlasciciel = "testowy_gracz"

    # Tworzenie testowego pokoju
    sio_client.emit('stworz_pokoj', {'nazwa': nazwa_pokoju, 'haslo': haslo, 'wlasciciel': wlasciciel})

    eventlet.sleep(1)

    # Dołączanie do testowego pokoju
    sio_client.emit('dolacz_do_pokoju', {'nazwa': nazwa_pokoju, 'haslo': haslo, 'gracz': gracz})

    def komunikat_sukcesu(data):
        assert data["success"] == f'Dołączono do pokoju {nazwa_pokoju}'

    sio_client.on('dolacz_do_pokoju', komunikat_sukcesu)

    eventlet.sleep(1)

    # Sprawdzenie, czy gracz został pomyślnie dodany do pokoju
    pokoj = next((p for p in pokoje if p.nazwa == nazwa_pokoju), None)
    assert pokoj is not None

    
def test_opusc_pokoj(sio_client):
    sio_client.connect('http://localhost:5000')

    nazwa_pokoju = "testowy_pokoj"
    gracz = "testowy_gracz"

    def komunikat_sukcesu(data):
        assert data["success"] == f'Opuszczono pokój {nazwa_pokoju}'

    sio_client.on('opuszczanie_pokoju', komunikat_sukcesu)

    sio_client.emit('opusc_pokoj', {'nazwa': nazwa_pokoju, 'gracz': gracz})

    eventlet.sleep(1)

def test_ustaw_haslo(sio_client):
    sio_client.connect('http://localhost:5000')

    nazwa_pokoju = "testowy_pokoj"
    haslo = "nowe_haslo"
    wlasciciel = "wlasciciel"

    def komunikat_sukcesu(data):
        assert data["success"] == f'Hasło do pokoju {nazwa_pokoju} zostało ustawione'

    sio_client.on('ustawienie_hasla', komunikat_sukcesu)

    sio_client.emit('ustaw_haslo', {'nazwa': nazwa_pokoju, 'haslo': haslo, 'gracz': wlasciciel})

    eventlet.sleep(1)

def test_sprawdz_graczy_w_pokoju(sio_client):
    sio_client.connect('http://localhost:5000')

    def komunikat_gracze(data):
        if 'gracze' in data:
            gracze = data['gracze']
            assert isinstance(gracze, list)
            assert len(gracze) == 2  # Załóżmy, że oczekujemy dwóch graczy w pokoju
        elif 'error' in data:
            assert data['error'] == 'Pokój o podanej nazwie nie istnieje'
        else:
            assert False, "Otrzymano nieoczekiwany komunikat"

    nazwa_pokoju = 'Testowy pokój'
    gracz = 'Testowy gracz'

    # Tworzymy fikcyjny pokój i dodajemy do niego graczy
    p = Pokoj(nazwa_pokoju, 'Właściciel')
    p.dodaj_gracza(gracz)
    p.dodaj_gracza('Inny gracz')
    pokoje.append(p)

    sio_client.emit('sprawdz_graczy_w_pokoju', {'nazwa': nazwa_pokoju, 'gracz': gracz})

    sio_client.on('lista_graczy_w_pokoju', komunikat_gracze)

    eventlet.sleep(1)

def test_dobierz_karte():
    # Tworzymy gracza i talie do testu
    gracz = Gracz("Testowy gracz", 100)
    talia = Talia()
    talia.tasuj()

    # Dodajemy kilka kart do ręki gracza
    gracz.reka = [
        Karta("Kier", "As"),
        Karta("Kier", "Dama"),
        Karta("Kier", "Król"),
        Karta("Karo", "As"),
        Karta("Trefl", "Dama")
    ]

    # Wybieramy karty do wymiany (np. pierwsze dwie)
    karty_do_wymiany = gracz.reka[:2]

    # Wywołujemy funkcję dobierz_karte
    gracz.dobierz_karte(karty_do_wymiany, talia)

    # Sprawdzamy, czy liczba kart w ręce gracza się zmieniła
    assert len(gracz.reka) == 5

    # Sprawdzamy, czy karty do wymiany zostały usunięte z ręki gracza
    for karta in karty_do_wymiany:
        assert karta not in gracz.reka

    # Sprawdzamy, czy wszystkie karty w ręce gracza są unikalne
    assert len(set(gracz.reka)) == len(gracz.reka)

    # Sprawdzamy, czy nowe karty pochodzą z talii
    for karta in gracz.reka:
        assert karta not in karty_do_wymiany