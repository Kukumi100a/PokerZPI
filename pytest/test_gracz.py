from poker import Gracz, Karta

def test_pas():
    gracz = Gracz("Testowy gracz", 100)
    gracz.stawka = 50
    gracz.pas()
    assert gracz.zetony == 50  # Sprawdzenie czy gracz stracił stawkę i ma odpowiednią liczbę żetonów
    assert gracz.stawka == 0  # Sprawdzenie czy stawka gracza została wyzerowana po pasowaniu

def test_sprawdzenie():
    gracz = Gracz("Testowy gracz", 100)
    gracz.stawka = 30
    gracz.sprawdzenie(50)
    assert gracz.zetony == 50  # Sprawdzenie czy gracz wyrównał stawkę i stracił odpowiednią liczbę żetonów
    assert gracz.stawka == 80  # Sprawdzenie czy stawka gracza została zwiększona o wartość stawki

def test_postawienie():
    gracz = Gracz("Testowy gracz", 100)
    gracz.postawienie(20)
    assert gracz.zetony == 80  # Sprawdzenie czy gracz postawił odpowiednią liczbę żetonów
    assert gracz.stawka == 20  # Sprawdzenie czy stawka gracza została odpowiednio zwiększona

def test_podbicie():
    gracz = Gracz("Testowy gracz", 100)
    gracz.stawka = 30
    gracz.podbicie(30, 40)
    assert gracz.zetony == 60  # Sprawdzenie czy gracz podbił stawkę i stracił odpowiednią liczbę żetonów
    assert gracz.stawka == 70  # Sprawdzenie czy stawka gracza została podbita o odpowiednią kwotę

def test_va_banque():
    gracz = Gracz("Testowy gracz", 100)
    gracz.va_banque()
    assert gracz.zetony == 0  # Sprawdzenie czy gracz postawił wszystkie dostępne żetony
    assert gracz.stawka == 100  # Sprawdzenie czy stawka gracza została odpowiednio zwiększona o wszystkie jego żetony

def test_dobierz_karte():
    gracz = Gracz("Testowy gracz", 100)
    karta1 = Karta("Kier", "As")
    karta2 = Karta("Trefl", "Dwójka")
    gracz.dobierz_karte(karta1)
    gracz.dobierz_karte(karta2)
    assert len(gracz.reka) == 2  # Sprawdzenie czy gracz ma dwie karty po dołożeniu dwóch kart

def test_pokaz_reke():
    gracz = Gracz("Testowy gracz", 100)
    karta1 = Karta("Kier", "As")
    karta2 = Karta("Trefl", "Dwójka")
    gracz.dobierz_karte(karta1)
    gracz.dobierz_karte(karta2)
    reka = gracz.pokaz_reke()
    assert len(reka) == 2  # Sprawdzenie czy gracz ma dwie karty w reku
    assert str(karta1) in reka  # Sprawdzenie czy pierwsza karta jest w reku
    assert str(karta2) in reka  # Sprawdzenie czy druga karta jest w reku
