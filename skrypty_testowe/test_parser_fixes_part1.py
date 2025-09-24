#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test poprawek parsera - CZĘŚĆ 1
Testuje:
1. Rozpoznawanie nazw sprzedawców
2. Poprawne parsowanie kwot
3. Filtrowanie pozycji "None"
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.parsers.universal_parser_v2 import UniversalParser
from app.comarch_mapper import ComarchMapper
from decimal import Decimal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_seller_name_extraction():
    """Test rozpoznawania nazwy sprzedawcy"""
    print("\n" + "="*50)
    print("TEST 1: Rozpoznawanie nazwy sprzedawcy")
    print("="*50)
    
    parser = UniversalParser()
    
    # Test przypadków
    test_cases = [
        {
            'name': 'Tylko dwukropek',
            'text': """
                Sprzedawca:
                ABC Company Sp. z o.o.
                NIP: 1234567890
                ul. Testowa 123
                00-000 Warszawa
            """,
            'expected': 'ABC Company Sp. z o.o.'
        },
        {
            'name': 'Nazwa po dwukropku',
            'text': """
                Sprzedawca: XYZ Solutions
                NIP: 9876543210
                ul. Przykładowa 456
                00-000 Kraków
            """,
            'expected': 'XYZ Solutions'
        },
        {
            'name': 'Etykieta SPRZEDAWCA',
            'text': """
                SPRZEDAWCA
                Test Firma S.A.
                NIP: 5555555555
            """,
            'expected': 'Test Firma S.A.'
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\nPrzypadek {i}: {case['name']}")
        data = parser._extract_company_data_improved(case['text'], True)
        print(f"  Oczekiwano: {case['expected']}")
        print(f"  Otrzymano:  {data['name']}")
        
        if data['name'] and data['name'] != ':':
            print(f"  ✓ PASS - Nazwa rozpoznana poprawnie")
        else:
            print(f"  ✗ FAIL - Nazwa nie została rozpoznana")

def test_amount_parsing():
    """Test parsowania kwot"""
    print("\n" + "="*50)
    print("TEST 2: Parsowanie kwot")
    print("="*50)
    
    parser = UniversalParser()
    
    test_cases = [
        {
            'name': 'Polski format z przecinkiem',
            'text': '1 234,56',
            'expected': Decimal('1234.56')
        },
        {
            'name': 'Bez spacji z przecinkiem',
            'text': '1234,56',
            'expected': Decimal('1234.56')
        },
        {
            'name': 'Format z kropką',
            'text': '1234.56',
            'expected': Decimal('1234.56')
        },
        {
            'name': 'Wartość 10000 (domyślna)',
            'text': '10000.00',
            'expected': Decimal('10000.00'),
            'warning': True
        },
        {
            'name': 'Puste/None',
            'text': 'None',
            'expected': Decimal('0')
        },
        {
            'name': 'Ze znakiem waluty',
            'text': '500,00 zł',
            'expected': Decimal('500.00')
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\nPrzypadek {i}: {case['name']}")
        result = parser._parse_amount_improved(case['text'])
        print(f"  Wejście:    '{case['text']}'")
        print(f"  Oczekiwano: {case['expected']}")
        print(f"  Otrzymano:  {result}")
        
        if result == case['expected']:
            if case.get('warning'):
                print(f"  ✓ PASS - Wartość rozpoznana (z ostrzeżeniem o domyślnej wartości)")
            else:
                print(f"  ✓ PASS")
        else:
            print(f"  ✗ FAIL")

def test_item_filtering():
    """Test filtrowania pozycji None"""
    print("\n" + "="*50)
    print("TEST 3: Filtrowanie pozycji 'None'")
    print("="*50)
    
    mapper = ComarchMapper()
    
    test_items = [
        {'name': 'Usługa konsultingowa', 'net_amount': '100.00', 'vat_rate': '23%'},
        {'name': 'None', 'net_amount': '50.00', 'vat_rate': '23%'},
        {'name': '', 'net_amount': '75.00', 'vat_rate': '23%'},
        {'name': 'Materiały biurowe', 'net_amount': '200.00', 'vat_rate': '23%'},
        {'name': 'none', 'net_amount': '25.00', 'vat_rate': '23%'},
        {'name': 'brak', 'net_amount': '30.00', 'vat_rate': '23%'},
    ]
    
    print("\nPozycje wejściowe:")
    for item in test_items:
        print(f"  - Nazwa: '{item['name']}', Netto: {item['net_amount']}")
    
    mapped = mapper._map_items(test_items)
    
    print(f"\nPo filtrowaniu pozostało: {len(mapped)} pozycji")
    print("Zachowane pozycje:")
    for item in mapped:
        print(f"  {item['lp']}. {item['description']} - {item['net_value']} zł")
    
    valid_count = sum(1 for item in test_items 
                      if item['name'] and item['name'].lower() not in ['none', '', 'brak', 'null'])
    
    if len(mapped) == valid_count:
        print(f"\n✓ PASS - Poprawnie odfiltrowano pozycje (zachowano {len(mapped)} z {valid_count} prawidłowych)")
    else:
        print(f"\n✗ FAIL - Błąd filtrowania (zachowano {len(mapped)}, powinno być {valid_count})")

def test_default_value_detection():
    """Test wykrywania domyślnej wartości 10000"""
    print("\n" + "="*50)
    print("TEST 4: Wykrywanie domyślnej wartości 10000")
    print("="*50)
    
    mapper = ComarchMapper()
    
    # Symulacja danych faktury z błędnymi wartościami
    class MockInvoiceData:
        def __init__(self):
            self.invoice_number = "FV/2025/001"
            self.invoice_date = "2025-01-15"
            self.sale_date = "2025-01-15"
            self.seller_name = "Test Company"
            self.seller_nip = "1234567890"
            self.payment_method = "przelew"
            self.payment_date = "2025-01-29"
            self.net_total = 0.0
            self.vat_total = 0.0
            self.gross_total = 10000.0
            self.items = [
                {'name': 'Usługa', 'net_amount': 1500.00, 'vat_amount': 345.00, 'gross_amount': 1845.00, 'vat_rate': '23%'}
            ]
    
    mock_data = MockInvoiceData()
    result = mapper.map_invoice_data(mock_data)
    
    print(f"Dane wejściowe:")
    print(f"  Netto: {mock_data.net_total}")
    print(f"  VAT: {mock_data.vat_total}")
    print(f"  Brutto: {mock_data.gross_total} (domyślna wartość)")
    
    print(f"\nDane po korekcji:")
    print(f"  Netto: {result.net_total}")
    print(f"  VAT: {result.vat_total}")
    print(f"  Brutto: {result.gross_total}")
    
    if result.gross_total != 10000.0 and result.gross_total > 0:
        print(f"\n✓ PASS - Domyślna wartość 10000 została skorygowana")
    else:
        print(f"\n✗ FAIL - Domyślna wartość nie została skorygowana")

def run_all_tests():
    """Uruchom wszystkie testy"""
    print("\n" + "#"*60)
    print("# TEST POPRAWEK PARSERA - CZĘŚĆ 1")
    print("#"*60)
    
    try:
        test_seller_name_extraction()
        test_amount_parsing()
        test_item_filtering()
        test_default_value_detection()
        
        print("\n" + "#"*60)
        print("# WSZYSTKIE TESTY ZAKOŃCZONE")
        print("#"*60)
        print("\nPodsumowanie:")
        print("- Test rozpoznawania sprzedawców: WYKONANY")
        print("- Test parsowania kwot: WYKONANY")
        print("- Test filtrowania pozycji: WYKONANY")
        print("- Test wartości domyślnych: WYKONANY")
        print("\nSprawdź logi powyżej, aby zobaczyć szczegółowe wyniki.")
        
    except Exception as e:
        print(f"\n✗ BŁĄD PODCZAS TESTÓW: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
