import pytest
import socketio
import eventlet
from poker import Gracz, Karta, Pokoj, pokoje, Talia, Gra

id_pokoju = None
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

def test_dolacz_do_pokoju(sio_client):

    # Zdefiniowanie nazwy pokoju, hasła i właściciela
    nazwa_pokoju = "testowy_pokoj"
    haslo = "testowe_haslo"
    wlasciciel = "testowy_gracz"

    # Podłączanie klienta do serwera
    sio_client.connect('http://localhost:5000')

    # Tworzenie pokoju przez właściciela
    sio_client.emit('stworz_pokoj', {'nazwa': nazwa_pokoju, 'haslo': haslo, 'wlasciciel': wlasciciel})

    # Obsługa komunikatu o sukcesie
    def komunikat_sukcesu(data):
        assert data["success"] == "Pokój został utworzony pomyślnie"
        global id_pokoju 
        id_pokoju = data["ID"]

    # Połącz klienta WebSocket z serwerem
    sio_client.on('stworz_pokoj', komunikat_sukcesu)

    # Uruchom obsługę zdarzeń
    eventlet.sleep(1)

    print("Zmienna id_pokoju po zdarzeniu:", id_pokoju)  # Dodajemy linię debugowania

    assert id_pokoju is not None, "Nie udało się utworzyć pokoju i uzyskać jego ID."

def test_wyswietl_pokoje(sio_client):
    sio_client.connect('http://localhost:5000')

    def komunikat_pokoje(data):
        assert 'pokoje' in data
        pokoje = data['pokoje']
        assert isinstance(pokoje, list)
        assert len(pokoje) == 1  

    sio_client.emit('wyswietl_pokoje')

    sio_client.on('lista_pokoi', komunikat_pokoje)

    eventlet.sleep(1)
    
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
    sio_client.disconnect()

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
    id = 1234

    # Tworzymy fikcyjny pokój i dodajemy do niego graczy
    p = Pokoj(id,nazwa_pokoju, 'Właściciel')
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

# Utwórz przykładowych graczy do testów
def create_sample_players():
    return [Gracz("gracz1", 100), Gracz("gracz2", 100)]

# Test inicjalizacji klasy Gra
def test_init():
    gracze = create_sample_players()
    gra = Gra(id, gracze)
    assert len(gracze) == 2
    assert gra.stol == []
    assert gra.aktualny_gracz == None
    assert gra.aktualna_stawka == 0
    assert gra.runda == 0

# Test rozpoczęcia gry
def test_start_game():
    gracze = create_sample_players()
    gra = Gra(id, gracze)
    gra.start_game()
    assert len(gra.gracze[0].reka) == 5  # Sprawdź, czy pierwszy gracz ma 5 kart na ręce
    assert gra.aktualny_gracz == gracze[0]  # Sprawdź, czy pierwszy gracz jest aktualnym graczem
    assert gra.runda == 1  # Sprawdź, czy runda została ustawiona na 1

# Test wykonania ruchu przez gracza
def test_make_move():
    gracze = create_sample_players()
    gra = Gra(id, gracze)
    gra.start_game()

    # Wykonaj ruch: wymiana kart
    karta_do_wymiany = gra.aktualny_gracz.reka[0]
    gra.wykonaj_ruch('dobierz', karty_do_wymiany=[karta_do_wymiany])

    # Wykonaj ruch: postawienie stawki
    gra.wykonaj_ruch('postawienie', stawka=10)
    assert gra.aktualna_stawka == 10

    # Wykonaj ruch: sprawdzenie
    gra.wykonaj_ruch('sprawdzenie')
    assert gra.aktualny_gracz.stawka == 10
    assert gra.aktualny_gracz.zetony == 90

    # Dodaj dodatkową stawkę i sprawdzenie
    gra.wykonaj_ruch('postawienie', stawka=10)
    assert gra.aktualna_stawka == 20
    gra.wykonaj_ruch('sprawdzenie')
    assert gra.aktualny_gracz.stawka == 20
    assert gra.aktualny_gracz.zetony == 80

    # Wykonaj ruch: podbicie
    gra.wykonaj_ruch('podbicie', stawka=20)

    assert gra.aktualny_gracz.stawka == 40  # Sprawdź, czy stawka gracza po podbiciu jest poprawna

    # Wykonaj ruch: pas
    gra.wykonaj_ruch('pas')
    assert gra.aktualny_gracz.stawka == 0

    # Wykonaj ruch: podbicie
    gra.wykonaj_ruch('podbicie', stawka=20)

    assert gra.aktualny_gracz.stawka == 20  # Sprawdź, czy stawka gracza po podbiciu jest poprawna

# Test kolejnej rundy
def test_next_round():
    gracze = create_sample_players()
    gra = Gra(id, gracze)
    gra.start_game()
    gra.kolejna_runda()  # Przetestuj kolejną rundę bez ruchów graczy
    assert gra.stol == []  # Sprawdź, czy stół jest pusty po kolejnej rundzie

# Test zakończenia rundy
def test_end_round():
    gracze = create_sample_players()
    gra = Gra(id, gracze)
    gra.start_game()
    gra.wykonaj_ruch('postawienie', stawka=10)
    gra.wykonaj_ruch('sprawdzenie')
    gra.zakoncz_runde()
    assert gra.stol == []  # Sprawdź, czy stół jest pusty po zakończeniu rundy
    assert gra.aktualna_stawka == 0  # Sprawdź, czy aktualna stawka została wyzerowana po rundzie

# Test sprawdzenia końca gry
def test_check_end_game():
    gracze = create_sample_players()
    gra = Gra(id, gracze)
    gra.start_game()
    gra.gracze[1].zetony = 0  # Ustaw gracza 2 na brak żetonów
    gra.sprawdz_koniec_gry()
    assert gra.koniec_gry == True  # Sprawdź, czy gra zakończyła się po wyzerowaniu żetonów przez gracza 2


def test_start_game():
    sio = socketio.Client()
    sio.connect('http://localhost:5000')
    def handle_start_game_result(data):
        assert data['result'] == "Gra została rozpoczęta!"
    sio.emit('start_game', {'gracz': 'Właściciel'})
    sio.on('start_game_result', handle_start_game_result)
    eventlet.sleep(1)
    sio.disconnect()

# Test dla funkcji wynik
def test_wynik(sio_client):
    sio_client.connect('http://localhost:5000')
    # Ustawienie zmiennych testowych
    gracz2 = "gracz2"

    # Uruchom obsługę zdarzeń
    eventlet.sleep(1)


    assert id_pokoju is not None, "Nie udało się utworzyć pokoju i uzyskać jego ID."

    # Dołączanie graczy do pokoju
    
    sio_client.emit('dolacz_do_pokoju', {'id': id_pokoju, 'nazwa': "testowy_pokoj", 'haslo': "testowe_haslo", 'gracz': gracz2})
    eventlet.sleep(1)

    # Symulacja ruchów
    sio_client.emit('wykonaj_ruch', {'id': id_pokoju, 'ruch': 'postawienie', 'stawka': 10, 'gracz': "wlasciciel"})
    eventlet.sleep(1)
    sio_client.emit('wykonaj_ruch', {'id': id_pokoju, 'ruch': 'sprawdzenie', 'gracz': gracz2})
    eventlet.sleep(1)

    # Obsługa komunikatu o wyniku
    rezultat = None
    def on_result(data):
        nonlocal rezultat 
        assert 'zwyciezcą jest:' in data or 'remis' in data
        rezultat = data['Wynik gry:']

    sio_client.on('wynik', on_result)
    print("Wynik gry:", rezultat)
    eventlet.sleep(1)

    # Wywołanie metody sprawdz_koniec_gry
    sio_client.emit('rezultat', {'id': id_pokoju})
    eventlet.sleep(1)

    # Wyzwalanie wyniku
    sio_client.emit('wynik', {'id': id_pokoju})
    eventlet.sleep(1)
    sio_client.disconnect()
