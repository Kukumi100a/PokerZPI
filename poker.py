import secrets
from flask import Flask, session, request, jsonify

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Klucz sesji, losowy i unikalny

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

    def tasuj(self):
        secrets.SystemRandom().shuffle(self.karty)

    def rozdaj_karte(self):
        return self.karty.pop()

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

def analiza_ukladu(reka):
    # Sprawdź czy mamy kolor
    kolory = [karta.kolory for karta in reka]
    if len(set(kolory)) == 1:
        return "Kolor", None

    # Sprawdź czy mamy parę
    pary = []
    for i, karta1 in enumerate(reka):
        for karta2 in reka[i+1:]:
            if karta1.hierarchia == karta2.hierarchia:
                pary.append(karta1.hierarchia)
    if pary:
        return "Para", pary[0]

    # Sprawdź czy mamy dwie pary
    unikalne_pary = list(set(pary))
    if len(unikalne_pary) >= 2:
        return "Dwie pary", unikalne_pary[:2]

    # Sprawdź czy mamy trójkę
    for karta in reka:
        if reka.count(karta) == 3:
            return "Trójka", karta.hierarchia

    # Sprawdź czy mamy karetę
    for karta in reka:
        if reka.count(karta) == 4:
            return "Kareta", karta.hierarchia

    # Sprawdź czy mamy strita
    hierarchie_int = sorted([Talia.hierarchia.index(karta.hierarchia) for karta in reka])
    if len(set(hierarchie_int)) == 5 and max(hierarchie_int) - min(hierarchie_int) == 4:
        return "Strit", reka[-1].hierarchia  # Załóżmy, że strit zaczyna się od najwyższej karty

    # W przeciwnym razie zwróć kartę najwyższą
    return "Karta najwyższa", reka[-1].hierarchia

gracze = {Gracz("gracz1", 100),   
          Gracz("gracz2", 100)}

@app.route('/rejestracja', methods=['POST'])
def rejestracja():
    data = request.json
    name = data.get('nazwa')
    if name:
        gracz = Gracz(name)
        gracze[name] = gracz
        return jsonify({"komunikat": "Rejestracja zakończona pomyślnie."}), 200
    else:
        return jsonify({"błąd": "Nazwa jest wymagana."}), 400

@app.route('/rozdanie', methods=['POST'])
def rozdanie():
    name = request.json.get('nazwa')
    if name in gracze:
        talia = Talia()
        for _ in range(5):
            gracze[name].dobierz_karte(talia.rozdaj_karte())
        return jsonify({"reka": gracze[name].pokaz_reke()}), 200
    else:
        return jsonify({"błąd": "Gracz nie został znaleziony."}), 404

# analiza wszystkich rąk i zwrócenie wyniku 
@app.route('/wynik', methods=['GET'])    
def wynik():
    uklady = ['Kolor', 'Para', 'Dwie pary', 'Trójka', 'Kareta', 'Strit', 'Karta najwyższa']
    wyniki = {}

    for gracz in gracze:
        uklad, dodatkowe_informacje = analiza_ukladu(gracz.reka)
        wyniki[gracz.name] = {"uklad": uklad, "dodatkowe_informacje": dodatkowe_informacje}

    max_uklad = max(wyniki.values(), key=lambda x: uklady.index(x['uklad']))
    zwyciezcy = [name for name, info in wyniki.items() if info['uklad'] == max_uklad['uklad']]

    if len(zwyciezcy) == 1:
        zwyciezca = zwyciezcy[0]
        return jsonify({"zwyciezca": zwyciezca, "uklad": max_uklad['uklad'], "dodatkowe_informacje": max_uklad['dodatkowe_informacje']}), 200
    else:
        return jsonify({"remis": zwyciezcy}), 200

# rozdanie kart wszystkim graczom    
@app.route('/pierwsze_rozdanie', methods=['GET'])
def pierwsze_rozdanie():
    talia = Talia()
    for gracz in gracze:
        for _ in range(5):
            gracz.dobierz_karte(talia.rozdaj_karte())
            
    karty_graczy = {gracz.name: gracz.pokaz_reke() for gracz in gracze}
    return jsonify(karty_graczy), 200


if __name__ == "__main__":
    app.run(debug=True)
