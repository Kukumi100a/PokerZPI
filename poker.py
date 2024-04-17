import secrets
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
socketio = SocketIO(app)

class Karta:
    def __init__(self, kolory, hierarchia):
        self.kolory = kolory
        self.hierarchia = hierarchia

    def __str__(self):
        return f"{self.hierarchia} of {self.kolory}"

class Talia:
    kolory = ['Kier', 'Karo', 'Trefl', 'Pik']
    hierarchia = ['Dwojka', 'Trojka', 'Czworka', 'Piatka', 'Szostka', 'Siodemka', 'Osemka', 'Dziewiatka', 'Dziesiatka', 'Walet', 'Dama', 'Krol', 'As']

    def __init__(self):
        self.karty = [Karta(kolor, hierarchia) for kolor in self.kolory for hierarchia in self.hierarchia]
        self.tasuj()
        self.wydane_karty = set()

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

gracze = [Gracz("gracz1", 100),   
          Gracz("gracz2", 100),
          Gracz("gracz3", 100),
          Gracz("gracz4", 100)]

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
        talia = Talia()
        gracze[name].dobierz_karte(talia.rozdaj_karte(2))
        stol = talia.rozdaj_karte(5)
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

def pierwsze_rozdanie():
    talia = Talia()
    karty_graczy = {}
    for gracz in gracze:
        reka = []
        for _ in range(5):
            karta = talia.rozdaj_karte()
            reka.append(karta)
        karty_graczy[gracz.name] = reka
    return karty_graczy

if __name__ == "__main__":
    socketio.run(app, debug=True)
