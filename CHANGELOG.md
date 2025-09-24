# Changelog

Wszystkie znaczące zmiany w tym projekcie będą dokumentowane w tym pliku.

Format oparty na [Keep a Changelog](https://keepachangelog.com/pl/1.0.0/),
projekt stosuje [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-09-24

### 🔄 Zmienione (BREAKING CHANGES)
- **Format XML zmieniony z JPK na Comarch ERP Optima** - całkowita zmiana struktury XML
- Przepisanie `xml_generator.py` - generuje format `<Dokumenty>` zamiast `<JPK>`
- Przepisanie `xml_generator_multi.py` - obsługa wielu faktur w formacie Comarch
- Struktura XML zgodna z wymogami Comarch ERP Optima 2025.5

### ✅ Dodane
- Plik `instrukcja wzoru xml.txt` z dokumentacją formatu Comarch
- Test `test_comarch_format.py` - weryfikacja struktury XML
- Test `quick_test_format.py` - szybkie testowanie pojedynczej faktury
- Sekcja `<RejestrVAT>` w generowanych XML
- Sekcja `<Platnosc>` z informacjami o płatnościach
- Pole `<Kontrahent>` z pełnymi danymi sprzedawcy
- Obsługa waluty w płatnościach

### 🐛 Naprawione
- Problem z formatem XML niezgodnym z Comarch ERP Optima
- Błędna struktura namespace JPK
- Brakujące wymagane sekcje w XML

## [1.5.0] - 2025-08-31

### ✅ Dodane
- Uniwersalny parser v2 (`universal_parser_v2.py`)
- Obsługa faktur wielostronicowych
- Dedykowane parsery dla różnych dostawców
- System wykrywania typu faktury

### 🐛 Naprawione
- Błędne rozpoznawanie nazw sprzedawców (zwracał ":")
- Domyślne wartości 10000 w kwotach
- Pozycje "None" w fakturach
- Problemy z polską notacją liczb (1 234,56)

## [1.4.0] - 2025-07-15

### ✅ Dodane
- Przetwarzanie wsadowe (`konwertuj_wszystkie_do_xml.py`)
- Generator wielu faktur w jednym XML
- Invoice detector - wykrywanie granic faktur w PDF

### 🔄 Zmienione
- Ulepszony OCR z Tesseract 5.5
- Lepsza obsługa błędów
- Optymalizacja wydajności

## [1.3.0] - 2025-06-01

### ✅ Dodane
- Obsługa faktur korygujących
- Parser dla Google Cloud Poland
- Automatyczna walidacja NIP
- Konfiguracja poprzez `config.ini`

### 🐛 Naprawione
- Błędy w rozpoznawaniu dat
- Problem z kodowaniem UTF-8
- Błędy parsowania kwot VAT

## [1.2.0] - 2025-04-20

### ✅ Dodane
- Mapowanie do formatu Comarch (`comarch_mapper.py`)
- Obsługa różnych stawek VAT
- Automatyczne obliczanie terminów płatności
- Kategorie księgowe dla pozycji

### 🔄 Zmienione
- Struktura projektu - podział na moduły
- Lepsza organizacja parserów
- Rozszerzone logowanie

## [1.1.0] - 2025-03-10

### ✅ Dodane
- OCR z użyciem Tesseract
- Podstawowy parser faktur
- Generowanie XML w formacie JPK
- Obsługa pojedynczych faktur

### 🐛 Naprawione
- Problemy z instalacją Poppler
- Błędy konwersji PDF do obrazów
- Problemy z PATH w Windows

## [1.0.0] - 2025-02-01

### ✅ Początkowe wydanie
- Podstawowa funkcjonalność konwersji PDF do XML
- Obsługa prostych faktur
- Struktura projektu
- Dokumentacja README

---

## Legenda

- ✅ **Dodane** - nowe funkcjonalności
- 🔄 **Zmienione** - zmiany w istniejących funkcjonalnościach  
- 🗑️ **Usunięte** - usunięte funkcjonalności
- 🐛 **Naprawione** - poprawki błędów
- 🔒 **Bezpieczeństwo** - poprawki bezpieczeństwa
- ⚠️ **Przestarzałe** - funkcje które zostaną usunięte
