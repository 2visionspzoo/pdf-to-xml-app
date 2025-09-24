"""
Test kompleksowy systemu PDF-to-XML
"""
import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from pdf_processor import PDFProcessor
from xml_generator import XMLGenerator
from comarch_mapper import ComarchMapper
import tempfile

def test_complete_flow():
    """Testuje cały przepływ od PDF do XML"""
    print("="*60)
    print("TEST KOMPLEKSOWY: PDF → Parser → XML")
    print("="*60)
    
    # Test z przykładowym tekstem symulującym różne faktury
    test_cases = [
        {
            'name': 'Faktura ATUT',
            'text': """
                FAKTURA VAT NR 2024/01/123
                Data wystawienia: 15.01.2024
                Data sprzedaży: 14.01.2024
                Termin płatności: 29.01.2024
                
                SPRZEDAWCA:
                ATUT Sp. z o.o.
                ul. Handlowa 15
                00-123 Warszawa
                NIP: 5252374228
                
                NABYWCA:
                2Vision Sp. z o.o.
                ul. Dąbska 20A/17
                31-572 Kraków
                NIP: 6751781780
                
                Lp. | Nazwa towaru/usługi | Ilość | Jedn. | Cena netto | Wartość netto | VAT% | Kwota VAT | Wartość brutto
                1 | Usługa konsultingowa | 1 | usł. | 1000.00 | 1000.00 | 23 | 230.00 | 1230.00
                2 | Materiały biurowe | 10 | szt. | 50.00 | 500.00 | 8 | 40.00 | 540.00
                
                RAZEM: Netto: 1500.00 | VAT: 270.00 | Brutto: 1770.00
                
                Sposób płatności: przelew
            """,
            'expected_type': 'ATUT',
            'expected_total': 1770.00
        },
        {
            'name': 'Faktura Bolt',
            'text': """
                BOLT OPERATIONS OÜ
                VAT ID: EE102054904
                
                INVOICE / FAKTURA
                Invoice number: RIDE-ABC123
                Date: 20.01.2024
                
                Customer:
                2Vision Sp. z o.o.
                NIP: 6751781780
                
                Service: Ride from Kraków Główny to Kraków Airport
                
                Net amount: 45.00 PLN
                VAT (23%): 10.35 PLN
                Total: 55.35 PLN
                
                Payment method: Card
            """,
            'expected_type': 'Bolt',
            'expected_total': 55.35
        },
        {
            'name': 'Faktura uniwersalna',
            'text': """
                Faktura VAT nr FV/2024/999
                Data wystawienia: 25.01.2024
                
                Sprzedawca:
                Firma XYZ Sp. z o.o.
                ul. Testowa 1
                01-234 Miasto
                NIP: 1234567890
                
                Nabywca:
                2Vision Sp. z o.o.
                ul. Dąbska 20A/17
                31-572 Kraków
                NIP: 6751781780
                
                Nazwa towaru | Ilość | Wartość netto | VAT 23% | Wartość brutto
                Produkt A | 5 | 500.00 | 115.00 | 615.00
                Produkt B | 2 | 200.00 | 46.00 | 246.00
                
                Razem netto: 700.00
                Razem VAT: 161.00
                Razem brutto: 861.00
            """,
            'expected_type': 'Unknown',
            'expected_total': 861.00
        }
    ]
    
    processor = PDFProcessor()
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        print(f"\n--- Test: {test_case['name']} ---")
        
        # Symulacja przetwarzania
        try:
            # Zapisz tekst do tymczasowego pliku
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(test_case['text'])
                temp_path = f.name
            
            # Przetwórz "PDF" (w rzeczywistości tekst)
            # Dla testu używamy bezpośrednio metody _parse_invoice_data
            from invoice_detector import InvoiceDetector
            detector = InvoiceDetector()
            invoice_type = detector.detect_type(test_case['text'])
            
            print(f"Wykryto typ: {invoice_type.value}")
            
            # Sprawdź typ
            if invoice_type.value == test_case['expected_type']:
                print(f"✓ Typ faktury: PASS")
                passed += 1
            else:
                print(f"✗ Typ faktury: FAIL (oczekiwano: {test_case['expected_type']})")
                failed += 1
            
            # Wybierz parser
            if invoice_type.value == 'ATUT':
                from parsers.atut_parser import ATUTParser
                parser = ATUTParser()
            elif invoice_type.value == 'Bolt':
                from parsers.bolt_parser import BoltParser
                parser = BoltParser()
            else:
                from parsers.universal_parser import UniversalParser
                parser = UniversalParser()
            
            # Parsuj
            result = parser.parse(test_case['text'])
            
            # Sprawdź wyniki
            if 'summary' in result:
                try:
                    total = float(result['summary']['gross_total'])
                    if abs(total - test_case['expected_total']) < 0.01:
                        print(f"✓ Kwota całkowita: PASS ({total:.2f})")
                        passed += 1
                    else:
                        print(f"✗ Kwota całkowita: FAIL (oczekiwano: {test_case['expected_total']:.2f}, otrzymano: {total:.2f})")
                        failed += 1
                except:
                    print(f"✗ Kwota całkowita: FAIL (błąd parsowania)")
                    failed += 1
            
            # Sprawdź NIP nabywcy
            if 'buyer' in result and result['buyer'].get('nip') == '6751781780':
                print(f"✓ NIP nabywcy: PASS")
                passed += 1
            else:
                print(f"✗ NIP nabywcy: FAIL")
                failed += 1
            
            # Usuń tymczasowy plik
            os.unlink(temp_path)
            
        except Exception as e:
            print(f"✗ Błąd podczas testu: {e}")
            failed += 3  # Wszystkie sprawdzenia failed
    
    print("\n" + "="*60)
    print(f"PODSUMOWANIE: {passed} passed, {failed} failed")
    if failed == 0:
        print("✓ WSZYSTKIE TESTY PRZESZŁY POMYŚLNIE!")
    else:
        print("✗ NIEKTÓRE TESTY NIE POWIODŁY SIĘ")
    print("="*60)
    
    return failed == 0

def test_xml_generation():
    """Testuje generowanie XML"""
    print("\n" + "="*60)
    print("TEST: Generowanie XML")
    print("="*60)
    
    # Przykładowe dane faktury
    invoice_data = {
        'invoice_number': 'TEST/2024/001',
        'invoice_date': '2024-01-15',
        'sale_date': '2024-01-14',
        'seller': {
            'name': 'Test Seller Sp. z o.o.',
            'nip': '1234567890',
            'address': 'ul. Testowa 1',
            'city': 'Warszawa',
            'postal_code': '00-001'
        },
        'buyer': {
            'name': '2Vision Sp. z o.o.',
            'nip': '6751781780',
            'address': 'ul. Dąbska 20A/17',
            'city': 'Kraków',
            'postal_code': '31-572'
        },
        'items': [
            {
                'name': 'Usługa testowa',
                'quantity': '1',
                'unit': 'usł.',
                'net_amount': '1000.00',
                'vat_rate': '23%',
                'vat_amount': '230.00',
                'gross_amount': '1230.00'
            }
        ],
        'summary': {
            'net_total': '1000.00',
            'vat_total': '230.00',
            'gross_total': '1230.00'
        }
    }
    
    try:
        # Konwertuj do formatu Comarch
        mapper = ComarchMapper()
        from dataclasses import dataclass
        from typing import Optional, List, Dict
        
        @dataclass
        class InvoiceData:
            invoice_number: Optional[str] = None
            invoice_date: Optional[str] = None
            sale_date: Optional[str] = None
            seller_name: Optional[str] = None
            seller_nip: Optional[str] = None
            seller_address: Optional[str] = None
            seller_city: Optional[str] = None
            seller_postal_code: Optional[str] = None
            buyer_name: Optional[str] = None
            buyer_nip: Optional[str] = None
            buyer_address: Optional[str] = None
            items: List[Dict] = None
            net_total: Optional[float] = None
            vat_total: Optional[float] = None
            gross_total: Optional[float] = None
        
        # Konwersja dict do InvoiceData
        inv = InvoiceData()
        inv.invoice_number = invoice_data['invoice_number']
        inv.invoice_date = invoice_data['invoice_date']
        inv.sale_date = invoice_data['sale_date']
        inv.seller_name = invoice_data['seller']['name']
        inv.seller_nip = invoice_data['seller']['nip']
        inv.buyer_name = invoice_data['buyer']['name']
        inv.buyer_nip = invoice_data['buyer']['nip']
        inv.items = invoice_data['items']
        inv.net_total = float(invoice_data['summary']['net_total'])
        inv.vat_total = float(invoice_data['summary']['vat_total'])
        inv.gross_total = float(invoice_data['summary']['gross_total'])
        
        comarch_data = mapper.map_to_comarch(inv)
        
        # Generuj XML
        generator = XMLGenerator()
        xml_content = generator.generate_xml(comarch_data)
        
        # Sprawdź czy XML zawiera kluczowe elementy
        checks = [
            ('<NAGLOWEK>' in xml_content, "Nagłówek"),
            ('<ZAWARTOSC>' in xml_content, "Zawartość"),
            ('TEST/2024/001' in xml_content, "Numer faktury"),
            ('6751781780' in xml_content, "NIP nabywcy"),
            ('1230.00' in xml_content or '1230,00' in xml_content, "Kwota brutto")
        ]
        
        passed = 0
        failed = 0
        
        for check, name in checks:
            if check:
                print(f"✓ {name}: PASS")
                passed += 1
            else:
                print(f"✗ {name}: FAIL")
                failed += 1
        
        # Zapisz przykładowy XML
        test_output = os.path.join(os.path.dirname(__file__), 'test_output.xml')
        with open(test_output, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        print(f"\nPrzykładowy XML zapisany w: {test_output}")
        
        print(f"\nPodsumowanie: {passed} passed, {failed} failed")
        return failed == 0
        
    except Exception as e:
        print(f"✗ Błąd generowania XML: {e}")
        return False

def main():
    """Główna funkcja testowa"""
    print("╔" + "="*58 + "╗")
    print("║      KOMPLEKSOWE TESTY SYSTEMU PDF-TO-XML              ║")
    print("╚" + "="*58 + "╝")
    
    all_passed = True
    
    # Test 1: Przepływ kompletny
    if not test_complete_flow():
        all_passed = False
    
    # Test 2: Generowanie XML
    if not test_xml_generation():
        all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("✓✓✓ WSZYSTKIE TESTY SYSTEMOWE PRZESZŁY POMYŚLNIE! ✓✓✓")
    else:
        print("✗✗✗ NIEKTÓRE TESTY SYSTEMOWE NIE POWIODŁY SIĘ ✗✗✗")
    print("="*60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
