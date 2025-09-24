"""
Test rozpoznawania typów faktur i parserów
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from invoice_detector import InvoiceDetector, InvoiceType
from parsers.atut_parser import ATUTParser
from parsers.universal_parser import UniversalParser

def test_invoice_detector():
    """Testuje rozpoznawanie typów faktur"""
    print("="*50)
    print("TEST: Rozpoznawanie typów faktur")
    print("="*50)
    
    detector = InvoiceDetector()
    
    # Przypadki testowe
    test_cases = [
        ("Faktura VAT 123/2024\nATUT Sp. z o.o.\nNIP: 5252374228", InvoiceType.ATUT),
        ("Invoice from Bolt Operations\nVAT: EU123456", InvoiceType.BOLT),
        ("FAKTURA SPRZEDAŻY\nTERG S.A.\nul. Przykładowa 1", InvoiceType.TERG),
        ("Dokument sprzedaży\nPKN ORLEN SA", InvoiceType.ORLEN),
        ("Faktura VAT\nNieznana Firma Sp. z o.o.", InvoiceType.UNKNOWN),
    ]
    
    passed = 0
    failed = 0
    
    for text, expected_type in test_cases:
        detected_type = detector.detect_type(text)
        confidence = detector.get_confidence_score(text, detected_type)
        
        if detected_type == expected_type:
            print(f"✓ PASS: Wykryto {detected_type.value} (pewność: {confidence:.2f})")
            passed += 1
        else:
            print(f"✗ FAIL: Oczekiwano {expected_type.value}, otrzymano {detected_type.value}")
            failed += 1
    
    print(f"\nPodsumowanie: {passed} passed, {failed} failed")
    return failed == 0

def test_multiple_invoices_detection():
    """Testuje wykrywanie wielu faktur w jednym dokumencie"""
    print("\n" + "="*50)
    print("TEST: Wykrywanie wielu faktur")
    print("="*50)
    
    detector = InvoiceDetector()
    
    # Symulacja dokumentu z wieloma fakturami
    multi_invoice_text = """
    FAKTURA VAT NR 123/2024
    ATUT Sp. z o.o.
    NIP: 5252374228
    Data wystawienia: 2024-01-15
    
    Pozycje faktury...
    
    Strona 1 z 2
    
    FAKTURA VAT NR 124/2024
    ATUT Sp. z o.o.
    NIP: 5252374228
    Data wystawienia: 2024-01-16
    
    Pozycje faktury...
    
    Strona 2 z 2
    """
    
    invoices = detector.detect_multiple_invoices(multi_invoice_text)
    
    if len(invoices) >= 2:
        print(f"✓ PASS: Wykryto {len(invoices)} faktury")
        for i, inv in enumerate(invoices, 1):
            print(f"  Faktura {i}: {inv['number']}, typ: {inv['type'].value}, pewność: {inv['confidence']:.2f}")
        return True
    else:
        print(f"✗ FAIL: Wykryto tylko {len(invoices)} faktur(y)")
        return False

def test_atut_parser():
    """Testuje parser ATUT"""
    print("\n" + "="*50)
    print("TEST: Parser ATUT")
    print("="*50)
    
    parser = ATUTParser()
    
    # Przykładowy tekst faktury ATUT
    sample_text = """
    FAKTURA VAT NR 123/2024
    Data wystawienia: 2024-01-15
    Data sprzedaży: 2024-01-14
    Termin płatności: 2024-01-29
    
    SPRZEDAWCA:
    ATUT Sp. z o.o.
    ul. Przykładowa 123
    00-001 Warszawa
    NIP: 5252374228
    
    NABYWCA:
    Firma Testowa Sp. z o.o.
    ul. Testowa 456
    02-002 Kraków
    NIP: 1234567890
    
    Lp. | Nazwa towaru | Ilość | Jedn. | Cena netto | Wartość netto | VAT% | VAT | Wartość brutto
    1   | Usługa A     | 1     | szt.  | 100.00     | 100.00       | 23   | 23.00 | 123.00
    2   | Usługa B     | 2     | szt.  | 50.00      | 100.00       | 8    | 8.00  | 108.00
    
    RAZEM: Netto: 200.00 | VAT: 31.00 | Brutto: 231.00
    """
    
    result = parser.parse(sample_text)
    
    # Sprawdzanie wyników
    checks = [
        ("Numer faktury", result['invoice_number'] == '123/2024'),
        ("Data wystawienia", result['invoice_date'] == '2024-01-15'),
        ("NIP sprzedawcy", result['seller']['nip'] == '5252374228'),
        ("NIP nabywcy", result['buyer']['nip'] == '1234567890'),
        ("Liczba pozycji", len(result['items']) == 2),
        ("Suma brutto", float(result['summary']['gross_total']) == 231.00)
    ]
    
    passed = 0
    failed = 0
    
    for check_name, check_result in checks:
        if check_result:
            print(f"✓ {check_name}: PASS")
            passed += 1
        else:
            print(f"✗ {check_name}: FAIL")
            failed += 1
    
    print(f"\nPodsumowanie: {passed} passed, {failed} failed")
    return failed == 0

def test_universal_parser():
    """Testuje parser uniwersalny"""
    print("\n" + "="*50)
    print("TEST: Parser uniwersalny")
    print("="*50)
    
    parser = UniversalParser()
    
    # Przykładowy tekst faktury ogólnej
    sample_text = """
    Faktura VAT nr FV/2024/001
    Data wystawienia: 15.01.2024
    Data sprzedaży: 14.01.2024
    
    Sprzedawca:
    Firma XYZ Sp. z o.o.
    ul. Handlowa 10
    01-234 Miasto
    NIP: 9876543210
    
    Nabywca:
    Klient ABC S.A.
    ul. Biznesowa 20
    05-678 Inne Miasto
    NIP: 1122334455
    
    Nazwa towaru | Ilość | Cena netto | Wartość netto | VAT 23% | Wartość brutto
    Produkt 1    | 5     | 20.00      | 100.00       | 23.00   | 123.00
    Produkt 2    | 3     | 30.00      | 90.00        | 20.70   | 110.70
    
    Razem netto: 190.00
    Razem VAT: 43.70
    Razem brutto: 233.70
    """
    
    result = parser.parse(sample_text)
    
    # Sprawdzanie wyników
    checks = [
        ("Numer faktury", 'FV/2024/001' in result['invoice_number']),
        ("Data wystawienia", '2024' in result['invoice_date']),
        ("Nazwa sprzedawcy", 'XYZ' in result['seller']['name']),
        ("NIP nabywcy", result['buyer']['nip'] == '1122334455'),
        ("Liczba pozycji", len(result['items']) >= 1),
        ("Suma brutto", float(result['summary']['gross_total']) > 0)
    ]
    
    passed = 0
    failed = 0
    
    for check_name, check_result in checks:
        if check_result:
            print(f"✓ {check_name}: PASS")
            passed += 1
        else:
            print(f"✗ {check_name}: FAIL")
            failed += 1
    
    print(f"\nPodsumowanie: {passed} passed, {failed} failed")
    return failed == 0

def main():
    """Główna funkcja testowa"""
    print("╔" + "="*48 + "╗")
    print("║    TESTY MODUŁU ROZPOZNAWANIA FAKTUR         ║")
    print("╚" + "="*48 + "╝")
    
    all_passed = True
    
    # Uruchom wszystkie testy
    tests = [
        test_invoice_detector,
        test_multiple_invoices_detection,
        test_atut_parser,
        test_universal_parser
    ]
    
    for test_func in tests:
        try:
            if not test_func():
                all_passed = False
        except Exception as e:
            print(f"\n✗ BŁĄD w {test_func.__name__}: {e}")
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("✓ WSZYSTKIE TESTY PRZESZŁY POMYŚLNIE!")
    else:
        print("✗ NIEKTÓRE TESTY NIE POWIODŁY SIĘ")
    print("="*50)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
