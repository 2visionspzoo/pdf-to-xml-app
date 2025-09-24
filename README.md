# PDF to XML Converter for Comarch ERP Optima

System automatycznej konwersji faktur PDF do formatu XML zgodnego z Comarch ERP Optima.

## 📋 Opis projektu

Aplikacja automatycznie przetwarza faktury w formacie PDF, ekstraktuje z nich dane za pomocą OCR (Tesseract) i generuje pliki XML gotowe do importu w systemie Comarch ERP Optima.

### Główne funkcjonalności:
- 🔍 **OCR faktur PDF** - automatyczne rozpoznawanie tekstu ze skanów
- 📊 **Inteligentny parser** - wyciąganie kluczowych danych (sprzedawca, nabywca, pozycje, kwoty)
- 🔄 **Konwersja do formatu Comarch** - generowanie struktury zgodnej z Comarch ERP Optima
- 🛠️ **Obsługa błędów** - automatyczna korekcja i walidacja danych
- 📁 **Przetwarzanie wsadowe** - obsługa wielu faktur w jednym pliku XML
- ✅ **Zgodność z Comarch ERP Optima 2025.5** - pełna kompatybilność z najnowszą wersją

## 🚀 Szybki start

### Wymagania systemowe
- Python 3.8+
- Tesseract OCR 5.0+
- Poppler (do konwersji PDF)
- Windows 10/11 (testowane)

### Instalacja

1. **Sklonuj repozytorium**
```bash
git clone https://github.com/your-username/pdf-to-xml-app.git
cd pdf-to-xml-app
```

2. **Zainstaluj zależności Python**
```bash
pip install -r requirements.txt
```

3. **Zainstaluj Tesseract OCR**
   - Pobierz instalator z: https://github.com/UB-Mannheim/tesseract/wiki
   - Lub użyj dołączonego instalatora: `tesseract-ocr-w64-setup-5.5.0.20241111.exe`
   - Dodaj do PATH: `C:\Program Files\Tesseract-OCR`

4. **Zainstaluj Poppler**
   - Pobierz z: https://github.com/oschwartz10612/poppler-windows/releases/
   - Rozpakuj do `C:\poppler`
   - Dodaj do PATH: `C:\poppler\Library\bin`

### Użycie

#### Konwersja wszystkich PDF w katalogu input:
```bash
python konwertuj_wszystkie_do_xml.py
```

#### Pojedyncza faktura:
```bash
python app/main.py
```

#### Wiele faktur w jednym XML:
```bash
python app/main_multi.py
```

## 📁 Struktura projektu

```
pdf-to-xml-app/
├── app/                            # Główna aplikacja
│   ├── parsers/                   # Parsery różnych typów faktur
│   │   ├── universal_parser_v2.py # Główny parser (najnowszy)
│   │   ├── google_cloud_parser.py # Parser dla Google Cloud
│   │   └── ...
│   ├── comarch_mapper.py          # Mapowanie do formatu Comarch
│   ├── pdf_processor.py           # Przetwarzanie PDF i OCR
│   ├── xml_generator.py           # Generator XML (pojedyncze faktury)
│   ├── xml_generator_multi.py     # Generator XML (wiele faktur)
│   ├── invoice_detector.py        # Detektor faktur w PDF
│   └── main.py                    # Główny punkt wejścia
├── input/                         # Katalog na faktury PDF do przetworzenia
├── output/                        # Wygenerowane pliki XML
├── skrypty_testowe/              # Skrypty testowe i diagnostyczne
│   ├── test_comarch_format.py   # Test formatu Comarch
│   ├── test_mapper_fix.py       # Test mapowania danych
│   └── ...
├── wzór_xml/                     # Przykładowe XML dla Comarch Optima
├── instrukcja wzoru xml.txt      # Dokumentacja formatu XML Comarch
├── config.ini                    # Konfiguracja aplikacji
└── requirements.txt              # Zależności Python
```

## 🔧 Format XML - Comarch ERP Optima

Aplikacja generuje XML zgodny ze strukturą Comarch ERP Optima:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Dokumenty>
  <Dokument Typ="ZAKUP">
    <Naglowek>
      <Numer>FA/123/2025</Numer>
      <DataWystawienia>2025-08-01</DataWystawienia>
      <DataSprzedazy>2025-08-01</DataSprzedazy>
      <Kontrahent>
        <NIP>5252822767</NIP>
        <Nazwa>GOOGLE CLOUD POLAND SP. Z O.O.</Nazwa>
        <Adres>ul. Emilii Plater 53, Warszawa, 00-113</Adres>
      </Kontrahent>
      <FormaPlatnosci>przelew</FormaPlatnosci>
      <TerminPlatnosci>2025-08-08</TerminPlatnosci>
    </Naglowek>
    <Pozycje>
      <Pozycja>
        <Opis>Usługi informatyczne</Opis>
        <Ilosc>1</Ilosc>
        <CenaNetto>511.42</CenaNetto>
        <StawkaVAT>23</StawkaVAT>
        <KwotaVAT>117.63</KwotaVAT>
        <WartoscBrutto>629.05</WartoscBrutto>
      </Pozycja>
    </Pozycje>
    <RejestrVAT>
      <Typ>Rejestr zakupu</Typ>
      <StawkaVAT>23</StawkaVAT>
      <Netto>511.42</Netto>
      <VAT>117.63</VAT>
      <Brutto>629.05</Brutto>
      <Odliczalny>Tak</Odliczalny>
    </RejestrVAT>
    <Platnosc>
      <Kwota>629.05</Kwota>
      <Waluta>PLN</Waluta>
      <DataPlatnosci>2025-08-08</DataPlatnosci>
      <Status>rozchód</Status>
    </Platnosc>
  </Dokument>
</Dokumenty>
```

## 📝 Ostatnie poprawki (wrzesień 2025)

### ✅ Najnowsze zmiany:
1. **Format XML** - zmiana z JPK na format Comarch ERP Optima
2. **Struktura dokumentów** - prawidłowa hierarchia: Dokumenty → Dokument → Sekcje
3. **Nowe generatory XML** - xml_generator.py i xml_generator_multi.py dla formatu Comarch
4. **Rozszerzone testy** - test_comarch_format.py weryfikuje zgodność z formatem

### 🔄 Wprowadzone ulepszenia:
- Pełna zgodność z formatem importu Comarch ERP Optima
- Obsługa wszystkich wymaganych sekcji: Nagłówek, Pozycje, RejestrVAT, Płatność
- Automatyczne mapowanie kontrahentów (NIP, nazwa, adres)
- Inteligentne rozpoznawanie stawek VAT
- Obsługa wielu faktur w jednym pliku XML
- Walidacja struktury XML przed zapisem

## 🧪 Testowanie

### Testy jednostkowe:
```bash
# Test formatu Comarch
python skrypty_testowe/test_comarch_format.py

# Test mapowania danych
python skrypty_testowe/test_mapper_fix.py

# Szybki test formatu
python skrypty_testowe/quick_test_format.py
```

### Test pełnego systemu:
```bash
# Przetwórz wszystkie PDF z katalogu input
python konwertuj_wszystkie_do_xml.py
```

## 📊 Wspierane formaty faktur

- ✅ Faktury standardowe (FV)
- ✅ Faktury zakupu (FZ) - format Comarch "ZAKUP"
- ✅ Faktury korygujące
- ✅ Różni dostawcy (uniwersalny parser)
- ✅ Faktury wielostronicowe
- ✅ Faktury z wieloma pozycjami

## 🔍 Parsery specjalistyczne

System zawiera dedykowane parsery dla:
- Google Cloud Poland
- Techrebal Giordano Mancinelli
- CO2 sp. z o.o.
- Grzegorz Jakubowski
- Uniwersalny parser dla pozostałych dostawców

## 📈 Wydajność

- ⚡ Przetwarzanie PDF: ~2-5 sekund/stronę
- 📄 Obsługa plików: do 100+ stron
- 🔄 Batch processing: 10+ faktur jednocześnie
- 💾 Rozmiar XML: ~2KB/faktura

## 🛠️ Rozwiązywanie problemów

### Problem: Błędne rozpoznawanie tekstu
**Rozwiązanie:** Upewnij się, że Tesseract ma zainstalowany pakiet języka polskiego (pol).

### Problem: Brak danych sprzedawcy
**Rozwiązanie:** System automatycznie przypisuje "NIEZNANY DOSTAWCA" jeśli nie może rozpoznać nazwy.

### Problem: Błędne kwoty
**Rozwiązanie:** Parser automatycznie wykrywa i koryguje domyślne wartości (10000.00).

## 🤝 Współpraca

1. Fork repozytorium
2. Stwórz branch (`git checkout -b feature/NoweFunkcje`)
3. Commit zmiany (`git commit -m 'Dodaj nowe funkcje'`)
4. Push do branch (`git push origin feature/NoweFunkcje`)
5. Otwórz Pull Request

## 📜 Licencja

Projekt na licencji MIT - zobacz plik [LICENSE](LICENSE) dla szczegółów.

## 👥 Autorzy

- **2Vision Sp. z o.o.** - główny rozwój
- NIP: 6751781780
- Adres: ul. Dąbska 20A/17, 31-572 Kraków

## 🙏 Podziękowania

- Tesseract OCR za świetne narzędzie OCR
- Poppler za konwersję PDF
- Comarch za dokumentację formatu XML
- Społeczność Python za wspaniałe biblioteki

## 📞 Kontakt

W razie pytań lub problemów:
- Otwórz Issue na GitHub
- Email: support@2vision.pl

## 🔄 Status projektu

**Aktywnie rozwijany** - ostatnia aktualizacja: wrzesień 2025

### ✅ Zrealizowane:
- [x] Format XML zgodny z Comarch ERP Optima
- [x] Parsowanie wielu typów faktur
- [x] Obsługa błędów i walidacja
- [x] Przetwarzanie wsadowe
- [x] Testy jednostkowe

### 🚀 Planowane funkcje:
- [ ] GUI z podglądem XML
- [ ] Wsparcie dla faktur w języku angielskim
- [ ] Automatyczne uczenie się nowych szablonów
- [ ] API REST dla integracji
- [ ] Dockeryzacja aplikacji
- [ ] Eksport do innych formatów (CSV, JSON)
- [ ] Integracja z bazą danych

## 📚 Dokumentacja

Szczegółowa dokumentacja formatu XML znajduje się w pliku:
`instrukcja wzoru xml.txt`

Przykładowe pliki XML w katalogu:
`wzór_xml/`

## ⚙️ Wymagania techniczne

### Minimalne:
- CPU: 2 rdzenie
- RAM: 4 GB
- Dysk: 1 GB wolnego miejsca
- OS: Windows 10/11

### Zalecane:
- CPU: 4+ rdzeni (dla przetwarzania równoległego)
- RAM: 8+ GB
- Dysk: SSD dla szybszego przetwarzania
- OS: Windows 11 Pro

---

💡 **Wskazówka:** Zawsze sprawdź wygenerowany XML przed importem do Comarch ERP Optima!
:)
