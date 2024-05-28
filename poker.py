import secrets
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
from collections import Counter
import time 
from json import dumps


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
    
    def to_json(self):
        return dumps(self.__dict__)

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
        if len(self.karty) < ilosc:
            raise ValueError("Brak wystarczającej liczby kart w talii")
        wydane_karty = []
        for _ in range(ilosc):
            karta = self.karty.pop()
            while karta in self.wydane_karty:
                karta = self.karty.pop()
            wydane_karty.append(karta)
            self.wydane_karty.add(karta)
        return wydane_karty
    
    def zbierz_karty_graczy(self, gracze):
        for gracz in gracze:
            self.karty.extend(gracz.reka)
            gracz.reka.clear()

class Gracz:
    def __init__(self, name, zetony):
        self.name = name
        self.zetony = zetony
        self.reka = []
        self.stawka = 0
        self.czy_pas = False

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
        self.czy_pas = True


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

    def podbicie(self, stawka):
        self.stawka += stawka
        self.zetony -= stawka

    def va_banque(self):
        self.stawka += self.zetony
        self.zetony = 0
    
    def czeka(self):
        if self.stawka < self.gra.aktualna_stawka:
            raise ValueError("Nie można czekać, gdy stawka została przebita")
        self.stawka = self.gra.aktualna_stawka

gracze = {}

class Pokoj:
    def __init__(self, id, nazwa, wlasciciel, haslo=None):
        self.id = str(id)
        self.nazwa = nazwa
        self.wlasciciel = wlasciciel
        self.haslo = haslo
        self.gracze = [wlasciciel]
        self.socket_id_wlasciciela = None
        self.game_started = False
        self.gra = None

    # Funkcja umożliwiająca właścicielowi zmianę ustawień pokoju
    
    @staticmethod
    @socketio.on('zmiana_ustawien')
    def zmien_ustawienia_pokoju(data):
        id = data.get('id')
        nowa_nazwa_pokoju=data.get('nazwa')
        nowe_haslo=data.get('haslo')
        wlasciciel=data.get('wlasciciel')
        pokoj = next((p for p in pokoje if p.id == id), None)
        if wlasciciel != pokoj.wlasciciel:
            return "Tylko właściciel pokoju może zmieniać ustawienia."
        if nowa_nazwa_pokoju:
            pokoj.nazwa = nowa_nazwa_pokoju
        if nowe_haslo:
            pokoj.haslo = nowe_haslo

        emit('zmiana_ustawien', {'success': f'Ustawienia pokoju {pokoj.nazwa} zostały zmienione!'})   
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
    def start_game(data):
        id = data.get('id')
        gracze_str = data.get('gracze')
        pokoj = next((p for p in pokoje if p.id == id), None)
        if gracze_str == pokoj.gracze:
            if len(pokoj.gracze) >= 2:
                pokoj.game_started = True
                print("Gra została rozpoczęta!")
                # Przekazanie żądania rozpoczęcia gry do klasy Gra
                ########## obiekt
                nowi_gracze = [ gracze[nick] for nick in gracze_str ]
                pokoj.gra = Gra(id, nowi_gracze)
                pokoj.gra.start_game()
                emit('start_game', {'success': f'Gra w pokoju {pokoj.nazwa} rozpoczęła się'}, room=pokoj.id)
            else:
                print("W grze muszą brać udział co najmniej dwaj gracze.")
        else:
            print("Tylko właściciel pokoju może rozpocząć grę.")


    @staticmethod
    @socketio.on('sprawdz_graczy_w_pokoju')
    def sprawdz_graczy_w_pokoju(data):
        id = data.get('id')
        pokoj = next((p for p in pokoje if p.id == id), None)
        if pokoj:
            gracze_w_pokoju = pokoj.gracze
            emit('lista_graczy_w_pokoju', {'gracze': gracze_w_pokoju, 'Wlasciciel': pokoj.wlasciciel, 'id': pokoj.id, 'nazwa': pokoj.nazwa})
        else:
            emit('lista_graczy_w_pokoju', {'error': 'Pokój o podanej nazwie nie istnieje'})

    @staticmethod
    @socketio.on('ustaw_haslo')
    def ustaw_haslo(data):
        id = data.get('id')
        nazwa_pokoju = data.get('nazwa')
        haslo = data.get('haslo')
        gracz = data.get('gracz')

        pokoj = next((p for p in pokoje if p.id == id), None)
        if pokoj and pokoj.czy_wlasciciel(gracz):
            pokoj.ustaw_haslo(haslo)
            emit('ustawienie_hasla', {'success': f'Hasło do pokoju {nazwa_pokoju} zostało ustawione'})

    @staticmethod
    @socketio.on('opusc_pokoj')
    def opusc_pokoj(data):
        id_pokoju = data.get('id')
        nazwa_pokoju = data.get('nazwa')
        gracz = data.get('gracz')
        leave_room(id_pokoju)
        pokoj = next((p for p in pokoje if p.id == id_pokoju), None)
        pokoj.usun_gracza(gracz)
        if pokoj:
            if len(pokoj.gracze) >= 1:
                nowy_wlasciciel = [g for g in pokoj.gracze if g != gracz]
                if nowy_wlasciciel:
                    nowy_wlasciciel = nowy_wlasciciel[0]
                    pokoj.wlasciciel = nowy_wlasciciel                    
                    emit('opuszczanie_pokoju', {'success': f'Opuszczono pokój {nazwa_pokoju}'}, room=id_pokoju)
                else:
                    pokoje.remove(pokoj)
                    emit('opuszczanie_pokoju', {'success': f'Opuszczono pokój {nazwa_pokoju}'}, room=id_pokoju)
            else:
                pokoje.remove(pokoj)
                emit('opuszczanie_pokoju', {'success': f'Opuszczono pokój {nazwa_pokoju}'}, room=id_pokoju)

   

class Gra:
    def __init__(self, id, gracze):
        self.id = id 
        self.gracze = gracze
        self.kolejka: list[Gracz] = gracze
        self.talia = Talia()
        self.stol = []
        self.aktualny_gracz = None
        self.aktualny_gracz_bilans = 0
        self.poczatkowy_bilans = 100
        self.aktualna_stawka = 0
        self.runda = 1
        self.koniec_gry = False
        self.hierarchia = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        self.wygrana = 0 

        
    def start_game(self):
        # Tasowanie talii i rozdanie początkowych kart
        self.talia.tasuj()
        for gracz in self.gracze:
            gracz.reka = self.talia.rozdaj_karte(5)
            gracz.zetony = self.poczatkowy_bilans
        # Ustawienie pierwszego gracza jako aktualnego gracza
        self.aktualny_gracz = self.gracze[0]

    def kolejna_runda(self):
        # Sprawdzenie czy wszyscy gracze wykonali ruch
        if all(gracz.stawka == self.aktualna_stawka for gracz in self.gracze if not gracz.czy_pas):
            # Jeśli tak, zakończ rundę
            self.zakoncz_runde()
            # Sprawdzenie czy gra powinna się zakończyć
            self.sprawdz_koniec_gry()
        else:
            # W przeciwnym razie, przejdź do kolejnego gracza
            self.kolejny_gracz()

    
    def wykonaj_ruch(self, ruch, stawka=0, karty_do_wymiany=None):
        if ruch == "czekanie":
            if self.aktualna_stawka > 0:
                self.aktualny_gracz.czeka()
            self.aktualny_gracz_bilans = self.aktualny_gracz.zetony
            self.kolejna_runda()
        elif ruch == "dobierz":
            self.aktualny_gracz.dobierz_karte(karty_do_wymiany, self.talia)
            self.aktualny_gracz_bilans = self.aktualny_gracz.zetony
            self.kolejna_runda()
        elif ruch == "postawienie":
            self.aktualny_gracz.postawienie(stawka)
            self.aktualna_stawka += stawka
            self.aktualny_gracz_bilans = self.aktualny_gracz.zetony
            self.kolejna_runda()
        elif ruch == "sprawdzenie":
            roznica = self.aktualna_stawka - self.aktualny_gracz.stawka
            self.aktualny_gracz.sprawdzenie(roznica)
            self.aktualny_gracz_bilans = self.aktualny_gracz.zetony
            self.kolejna_runda()
        elif ruch == "pas":
            self.aktualny_gracz.pas()
            self.aktualny_gracz.stawka = 0
            self.aktualny_gracz_bilans = self.aktualny_gracz.zetony
            self.kolejna_runda()
        elif ruch == "podbicie":
            self.aktualna_stawka += stawka  
            self.aktualny_gracz.podbicie(stawka)  
            self.aktualny_gracz_bilans = self.aktualny_gracz.zetony
            self.kolejna_runda()
        elif ruch == "va_banque":
            self.aktualny_gracz.va_banque()
            self.aktualna_stawka += self.aktualny_gracz.stawka
            self.aktualny_gracz_bilans = self.aktualny_gracz.zetony
            self.kolejna_runda()

    @staticmethod
    @socketio.on('start_gry')
    def handle_start_gry(data):
        id_pokoju = data.get('id')
        gracz = data.get('gracz')
        pokoj = next((p for p in pokoje if p.id == id_pokoju), None)
        gracz = pokoj.gra.gracze[pokoj.gracze.index(gracz)]

        karty = []
        for karta in gracz.reka:
            karty.append({'kolor': karta.kolory, 'znak': karta.hierarchia})

        gracze = [g.name for g in pokoj.gra.gracze]
        emit('aktualizacja', {'message': 'Start gry', 'reka': karty, 'gracze': gracze, 'nastepny_gracz': pokoj.gra.aktualny_gracz.name })

    @staticmethod
    @socketio.on('dobierz')
    def handle_dobierz(data):
        id_pokoju = data.get('id')
        pokoj = next((p for p in pokoje if p.id == id_pokoju), None)
        gra = pokoj.gra
        karty_do_wymiany = data.get('karty_do_wymiany')
        gra.wykonaj_ruch('dobierz', karty_do_wymiany=karty_do_wymiany)
        
        gracz = pokoj.gra.gracze[pokoj.gracze.index(gracz)]
        karty = []
        for karta in gracz.reka:
            karty.append({'kolor': karta.kolory, 'znak': karta.hierarchia})
        emit('aktualizacja', {'message': 'Karty', 'reka': karty})
        
        # FIXME: Może wywalić testy
        emit('aktualizacja', {'message': 'Gracz dobrał karty', 'nastepny_gracz': pokoj.gra.aktualny_gracz.name }, room=id_pokoju)
        # emit('aktualizacja', {'message': 'Gracz dobrał karty'})


    @staticmethod
    @socketio.on('postawienie')
    def handle_postawienie(data):
        id_pokoju = data.get('id')
        stawka = int(data.get('stawka'))
        pokoj = next((p for p in pokoje if p.id == id_pokoju), None)
        stary_gracz = pokoj.gra.aktualny_gracz.name
        pokoj.gra.wykonaj_ruch('postawienie', stawka=stawka)
        bilans_gracza = pokoj.gra.aktualny_gracz_bilans
        wygrana = sum(gracz.stawka for gracz in pokoj.gra.gracze)
        emit('aktualizacja', {'obecny_gracz': stary_gracz, 'bilans': bilans_gracza, 'message': 'Gracz postawił stawkę', 'stawka': stawka, 'nastepny_gracz': pokoj.gra.aktualny_gracz.name, 'stawka_total': wygrana}, room=id_pokoju)

    @staticmethod
    @socketio.on('sprawdzenie')
    def handle_sprawdzenie(data):
        id_pokoju = data.get('id')
        pokoj = next((p for p in pokoje if p.id == id_pokoju), None)
        stary_gracz = pokoj.gra.aktualny_gracz.name
        pokoj.gra.wykonaj_ruch('sprawdzenie')
        bilans_gracza = pokoj.gra.aktualny_gracz_bilans
        wygrana = sum(gracz.stawka for gracz in pokoj.gra.gracze)
        emit('aktualizacja', {'obecny_gracz': stary_gracz, 'bilans': bilans_gracza, 'message': 'Gracz sprawdził', 'nastepny_gracz': pokoj.gra.aktualny_gracz.name, 'stawka_total': wygrana}, room=id_pokoju)

    @staticmethod
    @socketio.on('pas')
    def handle_pas(data):
        id_pokoju = data.get('id')
        pokoj = next((p for p in pokoje if p.id == id_pokoju), None)
        stary_gracz = pokoj.gra.aktualny_gracz.name
        pokoj.gra.wykonaj_ruch('pas')
        bilans_gracza = pokoj.gra.aktualny_gracz_bilans
        wygrana = sum(gracz.stawka for gracz in pokoj.gra.gracze)
        emit('aktualizacja', {'obecny_gracz': stary_gracz, 'bilans': bilans_gracza, 'message': 'Gracz spasował', 'nastepny_gracz': pokoj.gra.aktualny_gracz.name, 'stawka_total': wygrana}, room=id_pokoju)

    @staticmethod
    @socketio.on('podbicie')
    def handle_podbicie(data):
        stawka = int(data.get('stawka'))
        id_pokoju = data.get('id')
        pokoj = next((p for p in pokoje if p.id == id_pokoju), None)
        stary_gracz = pokoj.gra.aktualny_gracz.name
        pokoj.gra.wykonaj_ruch('podbicie', stawka=stawka)
        bilans_gracza = pokoj.gra.aktualny_gracz_bilans
        wygrana = sum(gracz.stawka for gracz in pokoj.gra.gracze)
        emit('aktualizacja', {'obecny_gracz': stary_gracz, 'bilans': bilans_gracza,  'message': 'Gracz podbił stawkę', 'stawka': stawka, 'nastepny_gracz': pokoj.gra.aktualny_gracz.name, 'stawka_total': wygrana}, room=id_pokoju)

    @staticmethod
    @socketio.on('va_banque')
    def handle_va_banque(data):
        id_pokoju = data.get('id')
        pokoj = next((p for p in pokoje if p.id == id_pokoju), None)
        stary_gracz = pokoj.gra.aktualny_gracz.name
        pokoj.gra.wykonaj_ruch('va_banque')
        bilans_gracza = pokoj.gra.aktualny_gracz_bilans
        wygrana = sum(gracz.stawka for gracz in pokoj.gra.gracze)
        emit('aktualizacja', {'obecny_gracz': stary_gracz, 'bilans': bilans_gracza, 'message': 'Gracz zagrał va banque', 'nastepny_gracz': pokoj.gra.aktualny_gracz.name, 'stawka_total': wygrana}, room=id_pokoju)

    @staticmethod
    @socketio.on('czekanie')
    def handle_czekanie(data):
        id_pokoju = data.get('id')
        pokoj = next((p for p in pokoje if p.id == id_pokoju), None)
        stary_gracz = pokoj.gra.aktualny_gracz.name
        pokoj.gra.wykonaj_ruch('czekanie')
        bilans_gracza = pokoj.gra.aktualny_gracz_bilans
        wygrana = sum(gracz.stawka for gracz in pokoj.gra.gracze)
        emit('aktualizacja', {'obecny_gracz': stary_gracz, 'bilans': bilans_gracza, 'message': 'Gracz czeka', 'nastepny_gracz': pokoj.gra.aktualny_gracz.name, 'stawka_total': wygrana}, room=id_pokoju)

    def kolejny_gracz(self):
        # Obecny gracz na koniec
        temp = self.kolejka.pop(0)
        self.kolejka.append(temp)
        # Ustawienie następnego gracza jako aktualny
        self.aktualny_gracz = self.kolejka[0]
 
    def determine_winner(self, hands):
        winners = []
        best_hand_rank = None
        for idx, hand in enumerate(hands):
            hand_rank = self.check_hand(hand)  # Wywołanie metody klasy Gra
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
                hand_ranks = [self.hierarchia.index(card.hierarchia) for card in hand]
                pair_rank = max(set(hand_ranks), key=hand_ranks.count)
                print("pair_rank:", pair_rank)
                print("best_pair_rank:", best_pair_rank)
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

    def check_hand(self, hand):
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
            
    def zakoncz_runde(self):
        hands = [gracz.reka + self.stol for gracz in self.gracze if not gracz.czy_pas]
        winners, best_hand_rank = self.determine_winner(hands)
        winning_hand = hands[winners[0]]  # Pobranie układu zwycięzcy
        wygrana = sum(gracz.stawka for gracz in self.gracze)
        if len(winners) == 1:
            gracze_aktywni = [gracz for gracz in self.gracze if not gracz.czy_pas]
            winning_player = gracze_aktywni[winners[0]]
            winning_player.zetony += wygrana
        else:
            for idx in winners:
                gracze_aktywni = [gracz for gracz in self.gracze if not gracz.czy_pas]
                winning_player = gracze_aktywni[idx]
                winning_player.zetony += wygrana // len(winners)
        
        emit('rezultat', {
            'message': 'Runda zakończona',
            'zwyciezca': [self.gracze[idx].name for idx in winners],
            'uklad_zwyciezcy': self.check_hand(winning_hand),
            'bilans_gracza': [self.gracze[idx].zetony for idx in winners]
        }, room=self.id)

    def sprawdz_koniec_gry(self):
        if any(gracz.zetony >= 200 for gracz in self.gracze):  # Na przykład, jeśli ktoś ma 200 żetonów, wygrywa
            self.koniec_gry = True
            zwyciezca = max(self.gracze, key=lambda gracz: gracz.zetony)
            emit('rezultatkoniecgry', {'message': 'Gra zakończona', 'zwyciezca': zwyciezca.name}, room=self.id)
        elif all(gracz.zetony == 0 for gracz in self.gracze if gracz != self.aktualny_gracz):
            self.koniec_gry = True
            zwyciezca = self.aktualny_gracz
            emit('rezultatkoniecgry', {'message': 'Gra zakończona, wszyscy gracze poza jednym zbankrutowali', 'zwyciezca': zwyciezca.name}, room=self.id)
        elif self.runda >= 3:  # Na przykład gra kończy się po 5 rundach
            self.koniec_gry = True
            zwyciezca = max(self.gracze, key=lambda gracz: gracz.zetony)
            emit('rezultatkoniecgry', {'message': 'Gra zakończona', 'zwyciezca': zwyciezca.name}, room=self.id)
        else:
            self.runda=+1
                    # Resetowanie stawek graczy
            self.aktualna_stawka = 0
            for gracz in self.gracze:
                gracz.stawka = 0
                self.talia.zbierz_karty_graczy(self.gracze)
                gracz.reka = self.talia.rozdaj_karte(5)
                self.wygrana = 0
                gracz.czy_pas = False
            # Resetowanie stołu
            self.stol = []


                



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
        id = time.time()
        nazwa_pokoju = data.get('nazwa')
        haslo = data.get('haslo')
        wlasciciel = data.get('wlasciciel')
        join_room(id.__str__())

        if not nazwa_pokoju or not wlasciciel:
            emit('stworz_pokoj', {"error": "Brak wymaganych danych"})
        elif any(p.nazwa == nazwa_pokoju for p in pokoje):
            emit('stworz_pokoj', {"error": "Pokój o tej nazwie już istnieje"})
        else:
            pokoj = Pokoj(id, nazwa_pokoju, wlasciciel, haslo)
            pokoje.append(pokoj)
            emit('stworz_pokoj', {"success": "Pokój został utworzony pomyślnie", "ID": id})

    @staticmethod
    @socketio.on('dolacz_do_pokoju')
    def dolacz_do_pokoju(data):
        id_pokoju = data.get('id')
        nazwa_pokoju = data.get('nazwa')
        haslo = data.get('haslo')
        gracz = data.get('gracz')
        join_room(id_pokoju)

        pokoj = next((p for p in pokoje if p.id == id_pokoju), None)
        if not pokoj:
            emit('dolacz_do_pokoju', {'error': 'Pokój o podanej nazwie nie istnieje'})
        elif pokoj.haslo and pokoj.haslo != haslo:
            emit('dolacz_do_pokoju', {'error': 'Nieprawidłowe hasło do pokoju'})
        else:
            pokoj.dodaj_gracza(gracz)
            emit('dolacz_do_pokoju', {'success': f'Dołączono do pokoju {pokoj.nazwa}'}, room=id_pokoju)

    @staticmethod
    @socketio.on('szybka_gra')
    def szybka_gra(data):
        gracz = data.get('gracz')

        pokoj = next((p for p in pokoje if len(p.gracze) < 4), None)

        if pokoj is None:
            emit('znaleziono_wolny_pokoj', {'error': f'Nie udało się znaleźć pokoju', 'id': None})
        else:
            emit('znaleziono_wolny_pokoj', {'success': f'Znaleziono wolny pokój {pokoj.nazwa}', 'id': pokoj.id})

    @staticmethod
    @socketio.on('wyswietl_pokoje')
    def wyswietl_pokoje():
        if pokoje:
            lista_pokoi = [{'ID': p.id, 'nazwa': p.nazwa, 'wlasciciel': p.wlasciciel, 'liczba_graczy': len(p.gracze)} for p in pokoje]
            emit('lista_pokoi', {'pokoje': lista_pokoi})
        else:
            emit('lista_pokoi', {'komunikat': 'Obecnie nie ma żadnych dostępnych pokojów.'})


pokoje = []

@app.route('/')
def index():
    return render_template('index.html')
    

if __name__ == "__main__":
    socketio.run(app, debug=True)