import secrets
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
socketio = SocketIO(app, cors_allowed_origins="*")

class Karta:
    def __init__(self, kolory, hierarchia):
        self.kolory = kolory
        self.hierarchia = hierarchia

    def __str__(self):
        return f"{self.hierarchia} of {self.kolory}"

class Talia:
    def __init__(self):
        self.karty = self.utworz_talie()
        self.wydane_karty = set()

    def utworz_talie(self):
        kolory = ['Kier', 'Karo', 'Trefl', 'Pik']
        hierarchia = ['Dwojka', 'Trojka', 'Czworka', 'Piatka', 'Szostka', 'Siodemka', 'Osemka', 'Dziewiatka', 'Dziesiatka', 'Walet', 'Dama', 'Krol', 'As']
        return [Karta(kolor, wartosc) for kolor in kolory for wartosc in hierarchia]


    def tasuj(self):
        secrets.SystemRandom().shuffle(self.karty)

    def rozdaj_karte(self, ilosc=1):
        wydane_karty = []
        for _ in range(ilosc):
            karta = self.karty.pop()
            while karta in self.wydane_karty:
                karta = self.karty.pop()
            wydane_karty.append(karta)
            self.wydane_karty.add(karta)
        return wydane_karty

class Gracz:
    def __init__(self, name, zetony):
        self.name = name
        self.zetony = zetony
        self.reka = []
        self.stawka = 0

    def dobierz_karte(self, karta):
        self.reka.append(karta)

    def pokaz_reke(self):
        return [str(karta) for karta in self.reka]
    
    def pas(self):
        self.zetony -= self.stawka
        self.stawka = 0

    def odpusc(self):
        pass  

    def sprawdzenie(self, stawka):
        if self.zetony >= stawka:
            self.zetony -= stawka
            self.stawka += stawka
        else:
            self.stawka += self.zetony
            self.zetony = 0

    def postawienie(self, stawka):
        if stawka <= self.zetony:
            self.zetony -= stawka
            self.stawka += stawka
        else:
            self.stawka += self.zetony
            self.zetony = 0

    def podbicie(self, aktualna_stawka, stawka):
        roznica = aktualna_stawka + stawka - self.stawka
        self.stawka += min(self.zetony, roznica)
        self.zetony -= min(self.zetony, roznica)

    def va_banque(self):
        self.stawka += self.zetony
        self.zetony = 0

gracze = {
    "gracz1": Gracz("gracz1", 100),
    "gracz2": Gracz("gracz2", 100),
    "gracz3": Gracz("gracz3", 100),
    "gracz4": Gracz("gracz4", 100)
}

class Pokoj:
    def __init__(self, nazwa, wlasciciel, haslo=None):
        self.nazwa = nazwa
        self.wlasciciel = wlasciciel
        self.haslo = haslo
        self.gracze = [wlasciciel]
        self.socket_id_wlasciciela = None

    def dodaj_gracza(self, gracz):
        self.gracze.append(gracz)

    def usun_gracza(self, gracz):
        if gracz in self.gracze:
            self.gracze.remove(gracz)

    def ustaw_haslo(self, haslo):
        self.haslo = haslo

    def czy_wlasciciel(self, gracz):
        return gracz == self.wlasciciel

pokoje = []

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('rejestracja')
def rejestracja(data):
    name = data.get('nazwa')
    if name:
        gracz = Gracz(name, 100)
        gracze[name] = gracz
        emit('komunikat', {"komunikat": "Rejestracja zakończona pomyślnie."})
    else:
        emit('komunikat', {"błąd": "Nazwa jest wymagana."})

@socketio.on('rozdanie')
def rozdanie(data):
    name = data.get('nazwa')
    if name in gracze:
        # Sprawdź, czy talia już istnieje
        if 'talia' not in globals():
            emit('komunikat', {"błąd": "Brak talii kart."})
            return

        # Rozdaj karty graczowi
        dealt_cards = talia.rozdaj_karte(2)
        gracze[name].dobierz_karte(dealt_cards)

        # Rozdaj karty na stół
        stol = talia.rozdaj_karte(5)

        # Wyślij informacje o kartach do klienta
        emit('karty', {"reka": gracze[name].pokaz_reke(), "stol": [str(karta) for karta in stol]})
    else:
        emit('komunikat', {"błąd": "Gracz nie został znaleziony."})
        
def analiza_ukladu(reka):
    kolory = [karta.kolory for karta in reka]
    hierarchie = [karta.hierarchia for karta in reka]
    
    # Sprawdź czy mamy kolor
    if len(set(kolory)) == 1:
        return {"uklad": "Kolor", "dodatkowe_informacje": None}

    # Sprawdź czy mamy parę
    pary = []
    for i, karta1 in enumerate(reka):
        for karta2 in reka[i+1:]:
            if karta1.hierarchia == karta2.hierarchia:
                pary.append(karta1.hierarchia)
    if pary:
        return {"uklad": "Para", "dodatkowe_informacje": pary[0]}

    # Sprawdź czy mamy dwie pary
    unikalne_pary = list(set(pary))
    if len(unikalne_pary) >= 2:
        return {"uklad": "Dwie pary", "dodatkowe_informacje": unikalne_pary[:2]}

    # Sprawdź czy mamy trójkę
    for karta in reka:
        if reka.count(karta) == 3:
            return {"uklad": "Trójka", "dodatkowe_informacje": karta.hierarchia}

    # Sprawdź czy mamy karetę
    for karta in reka:
        if reka.count(karta) == 4:
            return {"uklad": "Kareta", "dodatkowe_informacje": karta.hierarchia}

    # Sprawdź czy mamy strita
    hierarchie_int = sorted([Talia.hierarchia.index(karta.hierarchia) for karta in reka])
    if len(set(hierarchie_int)) == 5 and max(hierarchie_int) - min(hierarchie_int) == 4:
        return {"uklad": "Strit", "dodatkowe_informacje": reka[-1].hierarchia}

    # W przeciwnym razie zwróć kartę najwyższą
    return {"uklad": "Karta najwyższa", "dodatkowe_informacje": reka[-1].hierarchia}


def pierwsze_rozdanie():
    talia = Talia()
    karty_graczy = {}
    for gracz_name, gracz_obj in gracze.items():
        reka = []
        for _ in range(5):
            karta = talia.rozdaj_karte()
            reka.append(karta)
        karty_graczy[gracz_name] = reka
    return karty_graczy



@socketio.on('request_result')
def wynik(stan_gry):
    if stan_gry:
        uklady = ['Kolor', 'Para', 'Dwie pary', 'Trójka', 'Kareta', 'Strit', 'Karta najwyższa']
        wyniki = {}
        for name, reka in stan_gry.items():
            wyniki[name] = analiza_ukladu(reka)
        
        max_uklad = max(wyniki.values(), key=lambda x: uklady.index(x['uklad']))
        zwyciezcy = [name for name, info in wyniki.items() if info['uklad'] == max_uklad['uklad']]
        
        if len(zwyciezcy) == 1:
            zwyciezca = zwyciezcy[0]
            emit('Wynik gry:', {" zwyciezcą jest: ": zwyciezca, " z układem: ": max_uklad['uklad'], "dodatkowe_informacje": max_uklad.get('dodatkowe_informacje', '')})
        else:
            emit('Wynik gry:', {"remis": zwyciezcy})
    else:
        emit('komunikat', {"błąd": "Brak danych o stanie gry."})
        return

@socketio.on('stworz_pokoj')
def stworz_pokoj(data):
    nazwa_pokoju = data.get('nazwa')
    haslo = data.get('haslo')
    wlasciciel = data.get('wlasciciel')

    if not nazwa_pokoju or not wlasciciel:
        emit('komunikat', {"error": "Brak wymaganych danych"})
    elif any(p.nazwa == nazwa_pokoju for p in pokoje):
        emit('komunikat', {"error": "Pokój o tej nazwie już istnieje"})
    else:
        pokoj = Pokoj(nazwa_pokoju, wlasciciel, haslo)
        pokoje.append(pokoj)
        emit('komunikat', {"success": "Pokój został utworzony pomyślnie"})

@socketio.on('dolacz_do_pokoju')
def dolacz_do_pokoju(data):
    nazwa_pokoju = data.get('nazwa')
    haslo = data.get('haslo')
    gracz = data.get('gracz')

    pokoj = next((p for p in pokoje if p.nazwa == nazwa_pokoju), None)
    if not pokoj:
        emit('komunikat', {'error': 'Pokój o podanej nazwie nie istnieje'})
    elif pokoj.haslo and pokoj.haslo != haslo:
        emit('komunikat', {'error': 'Nieprawidłowe hasło do pokoju'})
    else:
        pokoj.dodaj_gracza(gracz)
        emit('komunikat', {'success': f'Dołączono do pokoju {nazwa_pokoju}'})

@socketio.on('opusc_pokoj')
def opusc_pokoj(data):
    nazwa_pokoju = data.get('nazwa')
    gracz = data.get('gracz')

    pokoj = next((p for p in pokoje if p.nazwa == nazwa_pokoju), None)
    if pokoj:
        pokoj.usun_gracza(gracz)
        emit('komunikat', {'success': f'Opuszczono pokój {nazwa_pokoju}'})

@socketio.on('ustaw_haslo')
def ustaw_haslo(data):
    nazwa_pokoju = data.get('nazwa')
    haslo = data.get('haslo')
    gracz = data.get('gracz')

    pokoj = next((p for p in pokoje if p.nazwa == nazwa_pokoju), None)
    if pokoj and pokoj.czy_wlasciciel(gracz):
        pokoj.ustaw_haslo(haslo)
        emit('komunikat', {'success': f'Hasło do pokoju {nazwa_pokoju} zostało ustawione'})

@socketio.on('wyswietl_pokoje')
def wyswietl_pokoje():
    if pokoje:
        nazwy_pokoi = [p.nazwa for p in pokoje]
        emit('pokoje', {'pokoje': nazwy_pokoi})
    else:
        emit('komunikat', {'komunikat': 'Obecnie nie ma żadnych dostępnych pokojów.'})

if __name__ == "__main__":
    socketio.run(app, debug=True)
