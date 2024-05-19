import secrets
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from collections import Counter

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
socketio = SocketIO(app, cors_allowed_origins="*")

hierarchia = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

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
        hierarchia = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
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

    def dobierz_karte(self, karty_do_wymiany, talia):
        # Usuń karty do wymiany z ręki gracza
        for karta in karty_do_wymiany:
            self.reka.remove(karta)
        
        # Dobierz nowe karty z talii
        nowe_karty = talia.rozdaj_karte(len(karty_do_wymiany))
        self.reka.extend(nowe_karty)

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

    def aktualizuj_pokoj(self, stara_nazwa, nowa_nazwa):
        if self.pokoj == stara_nazwa:
            self.pokoj = nowa_nazwa

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
        self.game_started = False

    # Funkcja umożliwiająca właścicielowi zmianę ustawień pokoju
    def zmien_ustawienia_pokoju(self, nowa_nazwa=None, nowe_haslo=None, wlasciciel=None):
        if wlasciciel != self.wlasciciel:
            return "Tylko właściciel pokoju może zmieniać ustawienia."
        
        if nowa_nazwa:
            stare_id = self.nazwa
            self.nazwa = nowa_nazwa

            for gracz in self.gracze:
                gracz.aktualizuj_pokoj(stare_id, nowa_nazwa)
        
        if nowe_haslo:
            self.haslo = nowe_haslo

        return "Ustawienia pokoju zostały zmienione."

    def dodaj_gracza(self, gracz):
        self.gracze.append(gracz)

    def usun_gracza(self, gracz):
        if gracz in self.gracze:
            self.gracze.remove(gracz)

    def ustaw_haslo(self, haslo):
        self.haslo = haslo

    def czy_wlasciciel(self, gracz):
        return gracz == self.wlasciciel
    
    def usun_gracza_przymusowo(self, gracz):
        if gracz != self.wlasciciel:
            self.gracze.remove(gracz)
            return True
        else:
            return False
    
    @staticmethod
    @socketio.on('start_game')
    def start_game(self, gracz):
        if gracz == self.wlasciciel:
            if len(self.gracze) >= 2:
                self.game_started = True
                print("Gra została rozpoczęta!")
                talia = Talia()  # Utwórz obiekt talii
                karty_graczy = Gra.pierwsze_rozdanie(gracze)  # Rozdaj początkowe karty graczom
                stol = Gra.rozdaj_karty_na_stol(talia)  # Rozdaj karty na stół
            else:
                print("W grze muszą brać udział co najmniej dwaj gracze.")
        else:
            print("Tylko właściciel pokoju może rozpocząć grę.")


    @staticmethod
    @socketio.on('sprawdz_graczy_w_pokoju')
    def sprawdz_graczy_w_pokoju(data):
        nazwa_pokoju = data.get('nazwa')
        gracz = data.get('gracz')

        pokoj = next((p for p in pokoje if p.nazwa == nazwa_pokoju), None)
        if pokoj:
            gracze_w_pokoju = pokoj.gracze
            emit('lista_graczy_w_pokoju', {'gracze': gracze_w_pokoju, 'Wlasciciel': pokoj.wlasciciel})
        else:
            emit('lista_graczy_w_pokoju', {'error': 'Pokój o podanej nazwie nie istnieje'})

    @staticmethod
    @socketio.on('ustaw_haslo')
    def ustaw_haslo(data):
        nazwa_pokoju = data.get('nazwa')
        haslo = data.get('haslo')
        gracz = data.get('gracz')

        pokoj = next((p for p in pokoje if p.nazwa == nazwa_pokoju), None)
        if pokoj and pokoj.czy_wlasciciel(gracz):
            pokoj.ustaw_haslo(haslo)
            emit('ustawienie_hasla', {'success': f'Hasło do pokoju {nazwa_pokoju} zostało ustawione'})

    @staticmethod
    @socketio.on('opusc_pokoj')
    def opusc_pokoj(data):
        nazwa_pokoju = data.get('nazwa')
        gracz = data.get('gracz')

        pokoj = next((p for p in pokoje if p.nazwa == nazwa_pokoju), None)
        if pokoj:
            if len(pokoj.gracze) > 1:
                nowy_wlasciciel = [g for g in pokoj.gracze if g != gracz]
                if nowy_wlasciciel:
                    nowy_wlasciciel = nowy_wlasciciel[0]
                    pokoj.wlasciciel = nowy_wlasciciel
                    emit('ustawienie_nazwy_wlasciciela', {'nazwa': nazwa_pokoju, 'wlasciciel': nowy_wlasciciel})
                    pokoj.usun_gracza(gracz)
                else:
                    pokoj.usun_gracza(gracz)
                    pokoje.remove(pokoj)
                    emit('opuszczanie_pokoju', {'success': f'Opuszczono pokój {nazwa_pokoju}'})
            else:
                pokoj.usun_gracza(gracz)
                pokoje.remove(pokoj)
                emit('opuszczanie_pokoju', {'success': f'Opuszczono pokój {nazwa_pokoju}'})
   

class Gra:
    @staticmethod
    def pierwsze_rozdanie(gracze):
        talia = Talia()
        karty_graczy = {}
        for gracz_name in gracze:
            reka = []
            for _ in range(5):
                karta = talia.rozdaj_karte()
                reka.append(karta)
            karty_graczy[gracz_name] = reka
        return karty_graczy

    @staticmethod
    def rozdaj_karty_na_stol(talia):
        return talia.rozdaj_karte(5)
    
    @staticmethod
    def determine_winner(hands):
        winners = []
        best_hand_rank = None
        for idx, hand in enumerate(hands):
            hand_rank = Gra.check_hand(hand)
            if best_hand_rank is None or hand_rank > best_hand_rank:
                best_hand_rank = hand_rank
                winners = [idx]
            elif hand_rank == best_hand_rank:
                winners.append(idx)

        if len(winners) > 1:
            best_pair_rank = 0
            best_card_rank = 0
            winning_player = None
            for winner_idx in winners:
                hand = hands[winner_idx]
                hand_ranks = [hierarchia.index(card.hierarchia) for card in hand]
                pair_rank = max(set(hand_ranks), key=hand_ranks.count)
                if pair_rank > best_pair_rank:
                    best_pair_rank = pair_rank
                    best_card_rank = max(hand_ranks)
                    winning_player = winner_idx
                elif pair_rank == best_pair_rank:
                    if max(hand_ranks) > best_card_rank:
                        best_card_rank = max(hand_ranks)
                        winning_player = winner_idx

            winners = [winning_player]

        return winners, best_hand_rank

    @staticmethod
    def check_hand(hand):
        counts = Counter(card.hierarchia for card in hand)
        if len(counts) == 5:
            return "High Card"
        if len(counts) == 4:
            return "One Pair"
        if len(counts) == 3:
            if 3 in counts.values():
                return "Three of a Kind"
            else:
                return "Two Pair"
        if len(counts) == 2:
            if 4 in counts.values():
                return "Four of a Kind"
            else:
                return "Full House"
        if len(counts) == 1:
            if "10" in counts.keys() and "J" in counts.keys() and "Q" in counts.keys() and "K" in counts.keys() and "A" in counts.keys():
                return "Royal Flush"
            elif all(rank in counts.keys() for rank in ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']):
                return "Straight Flush"
            else:
                return "Flush"
            
    @staticmethod
    @socketio.on('rezultat')
    def wynik(stan_gry):
        if stan_gry:
            hands = []
            for gracz in gracze:
                hands.append(gracz.pokaz_reke())
            zwyciezca, max_uklad = Gra.determine_winner(hands)

            if len(zwyciezca) == 1:
                zwyciezca = list(gracze)[zwyciezca[0]]
                emit('Wynik gry:', {" zwyciezcą jest: ": zwyciezca, " z układem: ": max_uklad })
            else:
                emit('Wynik gry:', {"remis": zwyciezca})
        else:
            emit('rezultat', {"błąd": "Brak danych o stanie gry."})
            return

class Menu:

    @staticmethod
    @socketio.on('rejestracja')
    def rejestracja(data):
        name = data.get('nazwa')
        if name:
            gracz = Gracz(name, 100)
            gracze[name] = gracz
            emit('rejestracja', {"komunikat": "Rejestracja zakończona pomyślnie."})
        else:
            emit('rejestracja', {"błąd": "Nazwa jest wymagana."})

    @staticmethod
    @socketio.on('stworz_pokoj')
    def stworz_pokoj(data):
        nazwa_pokoju = data.get('nazwa')
        haslo = data.get('haslo')
        wlasciciel = data.get('wlasciciel')

        if not nazwa_pokoju or not wlasciciel:
            emit('stworz_pokoj', {"error": "Brak wymaganych danych"})
        elif any(p.nazwa == nazwa_pokoju for p in pokoje):
            emit('stworz_pokoj', {"error": "Pokój o tej nazwie już istnieje"})
        else:
            pokoj = Pokoj(nazwa_pokoju, wlasciciel, haslo)
            pokoje.append(pokoj)
            emit('stworz_pokoj', {"success": "Pokój został utworzony pomyślnie"})

    @staticmethod
    @socketio.on('dolacz_do_pokoju')
    def dolacz_do_pokoju(data):
        nazwa_pokoju = data.get('nazwa')
        haslo = data.get('haslo')
        gracz = data.get('gracz')

        pokoj = next((p for p in pokoje if p.nazwa == nazwa_pokoju), None)
        if not pokoj:
            emit('dolacz_do_pokoju', {'error': 'Pokój o podanej nazwie nie istnieje'})
        elif pokoj.haslo and pokoj.haslo != haslo:
            emit('dolacz_do_pokoju', {'error': 'Nieprawidłowe hasło do pokoju'})
        else:
            pokoj.dodaj_gracza(gracz)
            emit('dolacz_do_pokoju', {'success': f'Dołączono do pokoju {nazwa_pokoju}'})

    @staticmethod
    @socketio.on('wyswietl_pokoje')
    def wyswietl_pokoje():
        if pokoje:
            lista_pokoi = [{'nazwa': p.nazwa, 'wlasciciel': p.wlasciciel, 'liczba_graczy': len(p.gracze)} for p in pokoje]
            emit('lista_pokoi', {'pokoje': lista_pokoi})
        else:
            emit('lista_pokoi', {'komunikat': 'Obecnie nie ma żadnych dostępnych pokojów.'})


pokoje = []

@app.route('/')
def index():
    return render_template('index.html')
    

if __name__ == "__main__":
    socketio.run(app, debug=True)
