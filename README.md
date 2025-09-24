# 📄 PDF-to-XML Converter for Comarch Optima

System do automatycznej konwersji faktur PDF do formatu XML zgodnego z Comarch Optima.

## 🚀 SZYBKI START

### ⚡ DWA TRYBY PRACY:

#### 1️⃣ **JEDEN PLIK XML DLA WSZYSTKICH FAKTUR** (ZALECANE!)
```bash
# Skrypt Python
python konwertuj_do_jednego_xml.py

# Lub batch Windows  
uruchom_jeden_xml.bat

# Lub bezpośrednio
python app\main_multi.py
```
**Rezultat:** `output\wszystkie_faktury.xml` zawierający wszystkie faktury

#### 2️⃣ **OSOBNY XML DLA KAŻDEJ FAKTURY**
```bash
# GUI
python gui_konwerter.py

# Lub batch
uruchom_konwerter.bat

# Lub bezpośrednio
python app\main.py
```
**Rezultat:** Osobny plik XML dla każdego PDF

## 📁 STRUKTURA FOLDERÓW

```
C:\pdf-to-xml-app\
├── input\                      # ← Tutaj umieść faktury PDF
├── output\                     # ← Tutaj pojawią się pliki XML
│   └── wszystkie_faktury.xml   # ← Zbiorczy XML (tryb 1)
├── app\                        # Kod aplikacji
│   ├── main_multi.py          # NOWY - wszystkie faktury → jeden XML
│   └── main.py                # Osobne XML dla każdej faktury
├── konwertuj_do_jednego_xml.py # NOWY - prosty skrypt
├── uruchom_jeden_xml.bat       # NOWY - batch dla Windows
└── skrypty_testowe\            # Skrypty testowe
```

## 📋 JAK UŻYWAĆ

### Tryb 1: Wszystkie faktury w jednym XML (ZALECANY)
1. **Umieść faktury PDF** w folderze `input\`
2. **Uruchom:** `python konwertuj_do_jednego_xml.py`
3. **Odbierz plik:** `output\wszystkie_faktury.xml`

### Tryb 2: Osobny XML dla każdej faktury
1. **Umieść faktury PDF** w folderze `input\`
2. **Uruchom:** `python gui_konwerter.py`
3. **Odbierz pliki:** osobne XML w `output\`

## ✅ FUNKCJONALNOŚCI

- ✅ **NOWE:** Generowanie jednego XML ze wszystkich faktur
- ✅ **NOWE:** Podsumowanie finansowe wszystkich faktur
- ✅ Automatyczna ekstrakcja danych z PDF (83% skuteczności)
- ✅ Rozpoznawanie sprzedawcy i nabywcy
- ✅ Parsowanie pozycji faktury
- ✅ Obliczanie sum i VAT
- ✅ Format zgodny z Comarch Optima / JPK
- ✅ Obsługa polskich znaków (UTF-8)
- ✅ Interfejs graficzny GUI
- ✅ Przetwarzanie wsadowe

## 🧪 TESTOWANIE

```bash
# Test nowego systemu (jeden XML)
python skrypty_testowe\test_single_xml.py

# Diagnostyka
python skrypty_testowe\diagnoza_systemu.py

# Test przetwarzania wsadowego
python skrypty_testowe\test_batch_processing.py
```

## 📊 PRZYKŁAD WYNIKU (JEDEN XML)

```xml
<?xml version='1.0' encoding='UTF-8'?>
<JPK>
  <Naglowek>
    <KodFormularza>JPK_FA</KodFormularza>
    <DataWytworzeniaJPK>2025-09-24</DataWytworzeniaJPK>
  </Naglowek>
  <Podmiot>
    <NIP>6751781780</NIP>
    <PelnaNazwa>2VISION SPÓŁKA Z O.O.</PelnaNazwa>
  </Podmiot>
  <Faktury>
    <FakturaZakup>
      <LpFaktury>1</LpFaktury>
      <NrFaktury>11/07/2025</NrFaktury>
      <!-- dane faktury 1 -->
    </FakturaZakup>
    <FakturaZakup>
      <LpFaktury>2</LpFaktury>
      <NrFaktury>FS_4447_08_2025</NrFaktury>
      <!-- dane faktury 2 -->
    </FakturaZakup>
    <!-- kolejne faktury -->
  </Faktury>
  <Podsumowanie>
    <LiczbaFaktur>7</LiczbaFaktur>
    <SumaNetto>5432.10</SumaNetto>
    <SumaVAT>1249.38</SumaVAT>
    <SumaBrutto>6681.48</SumaBrutto>
  </Podsumowanie>
</JPK>
```

## 🔧 ROZWIĄZYWANIE PROBLEMÓW

### Błąd: "ModuleNotFoundError"
```bash
pip install pdfplumber lxml python-dateutil
```

### Błąd: "Brak plików PDF"
Upewnij się, że faktury są w: `C:\pdf-to-xml-app\input\`

### Niepełne dane w XML
Parser ma 83% skuteczności. Niektóre faktury mogą wymagać ręcznej korekty.

## 📝 UWAGI

- System automatycznie przypisuje nabywcę jako **2VISION Sp. z o.o.**
- Domyślna stawka VAT to **23%** (jeśli nie rozpoznano)
- Pliki XML są zapisywane w kodowaniu **UTF-8-SIG**
- **NOWE:** Tryb zbiorczy sumuje wszystkie faktury

## 🆘 POMOC

W przypadku problemów:
1. Uruchom diagnostykę: `python skrypty_testowe\diagnoza_systemu.py`
2. Sprawdź logi w konsoli
3. Upewnij się, że PDF nie jest zeskanowanym obrazem

---
© 2025 PDF-to-XML Converter for Comarch Optima
Wersja 2.0 - Obsługa wielu faktur w jednym XML
