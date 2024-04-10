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
    hierarchia = ['Dwójka', 'Trójka', 'Czwórka', 'Piątka', 'Szóstka', 'Siódemka', 'Ósemka', 'Dziewiątka', 'Dziesiątka', 'Giermek', 'Dama', 'Król', 'As']

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

gracze = {}

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

if __name__ == "__main__":
    app.run(debug=True)
