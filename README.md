# PDF to XML Converter for Comarch ERP Optima

System automatycznej konwersji faktur PDF do formatu XML zgodnego z Comarch ERP Optima.

## 📋 Opis projektu

Aplikacja automatycznie przetwarza faktury w formacie PDF, ekstraktuje z nich dane za pomocą OCR (Tesseract) i generuje pliki XML gotowe do importu w systemie Comarch ERP Optima.

### Główne funkcjonalności:
- 🔍 **OCR faktur PDF** - automatyczne rozpoznawanie tekstu ze skanów
- 📊 **Inteligentny parser** - wyciąganie kluczowych danych (sprzedawca, nabywca, pozycje, kwoty)
- 🔄 **Mapowanie do XML** - generowanie struktury zgodnej z Comarch ERP Optima
- 🛠️ **Obsługa błędów** - automatyczna korekcja i walidacja danych
- 📁 **Przetwarzanie wsadowe** - obsługa wielu faktur jednocześnie

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

#### Pojedyncza faktura:
```bash
python app/main.py
```

#### Przetwarzanie wsadowe:
```bash
python konwertuj_faktury.py
```

#### GUI (w rozwoju):
```bash
python gui_konwerter.py
```

## 📁 Struktura projektu

```
pdf-to-xml-app/
├── app/                      # Główna aplikacja
│   ├── parsers/             # Parsery różnych typów faktur
│   │   ├── universal_parser_v2.py  # Główny parser (ulepszony)
│   │   └── ...
│   ├── comarch_mapper.py    # Mapowanie do formatu Comarch
│   ├── pdf_processor.py     # Przetwarzanie PDF i OCR
│   ├── xml_generator.py     # Generowanie XML
│   └── main.py              # Główny punkt wejścia
├── input/                   # Katalog na faktury PDF
├── output/                  # Wygenerowane pliki XML
├── skrypty_testowe/        # Skrypty testowe i diagnostyczne
├── wzór_xml/               # Wzorce XML dla Comarch Optima
└── requirements.txt        # Zależności Python
```

## 🔧 Konfiguracja

Edytuj plik `config.ini`:
```ini
[settings]
ocr_lang=pol
xml_template_path=wzór_xml/plik od ksiegowej wzór zaimportowanych faktur.xml
```

## 📝 Ostatnie poprawki (styczeń 2025)

### ✅ Rozwiązane problemy:
1. **Nazwy sprzedawców** - poprawione rozpoznawanie, gdy parser zwracał tylko ":"
2. **Błędne kwoty** - usunięte domyślne wartości 10000, lepsze parsowanie polskiej notacji
3. **Pozycje "None"** - automatyczne filtrowanie pustych pozycji

### 🔄 Wprowadzone ulepszenia:
- Inteligentniejsze wykrywanie sekcji sprzedawcy/nabywcy
- Obsługa różnych formatów kwot (1 234,56 / 1234.56)
- Automatyczna walidacja i korekcja danych
- Lepsza obsługa błędów OCR

## 🧪 Testowanie

Uruchom testy jednostkowe:
```bash
python skrypty_testowe/test_parser_fixes_part1.py
```

Test pełnego systemu:
```bash
python skrypty_testowe/test_full_system.py
```

## 📊 Wspierane formaty faktur

- ✅ Faktury standardowe (FV)
- ✅ Faktury zakupu (FZ) 
- ✅ Faktury korygujące
- ✅ Różni dostawcy (uniwersalny parser)

## 🤝 Współpraca

1. Fork repozytorium
2. Stwórz branch (`git checkout -b feature/AmazingFeature`)
3. Commit zmiany (`git commit -m 'Add some AmazingFeature'`)
4. Push do branch (`git push origin feature/AmazingFeature`)
5. Otwórz Pull Request

## 📜 Licencja

Projekt na licencji MIT - zobacz plik [LICENSE](LICENSE) dla szczegółów.

## 👥 Autorzy

- **2Vision Sp. z o.o.** - główny rozwój

## 🙏 Podziękowania

- Tesseract OCR za świetne narzędzie OCR
- Poppler za konwersję PDF
- Comarch za dokumentację formatu XML

## 📞 Kontakt

W razie pytań lub problemów:
- Otwórz Issue na GitHub
- Email: support@2vision.pl

## 🔄 Status projektu

**Aktywnie rozwijany** - ostatnia aktualizacja: styczeń 2025

### TODO:
- [ ] Ulepszone GUI
- [ ] Wsparcie dla większej liczby formatów faktur
- [ ] Automatyczne uczenie się nowych szablonów
- [ ] API REST dla integracji
- [ ] Dockeryzacja aplikacji
