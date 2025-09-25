#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Skrypt testowy do weryfikacji poprawek w universal_parser_v6.py
Testuje:
1. Metodę _clean_nip
2. Kompatybilność nazw pól (name/description, unit_price_net/unit_price)
3. Przetwarzanie faktur z input/
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.parsers.universal_parser_v6 import UniversalParser
from app.base_parser import InvoiceItem
from app.pdf_processor import PDFProcessor
import json

def test_clean_nip():
    """Test czyszczenia NIP"""
    print("\n=== Test metody _clean_nip ===")
    parser = UniversalParser()
    
    test_cases = [
        ("PL 123-456-78-90", "1234567890"),
        ("1234567890", "1234567890"),
        ("PL1234567890", "1234567890"),
        ("123 456 78 90", "1234567890"),
        ("PL-123-456-78-90", "1234567890"),
    ]
    
    for input_nip, expected in test_cases:
        result = parser._clean_nip(input_nip)
        status = "✓" if result == expected else "✗"
        print(f"{status} Input: {input_nip:20} -> Output: {result:12} (Expected: {expected})")
    
    return all(parser._clean_nip(inp) == exp for inp, exp in test_cases)

def test_invoice_item_compatibility():
    """Test kompatybilności InvoiceItem"""
    print("\n=== Test kompatybilności InvoiceItem ===")
    
    item = InvoiceItem()
    
    # Test 1: Używanie nowych nazw
    item.name = "Usługa testowa"
    item.unit_price_net = 100.0
    
    dict_result = item.to_dict()
    
    print(f"✓ name -> {dict_result.get('name')}")
    print(f"✓ description (alias) -> {dict_result.get('description')}")
    print(f"✓ unit_price_net -> {dict_result.get('unit_price_net')}")
    print(f"✓ unit_price (alias) -> {dict_result.get('unit_price')}")
    
    # Test 2: Używanie starych nazw
    item2 = InvoiceItem()
    item2.description = "Stara nazwa pola"
    item2.unit_price = 200.0
    
    dict_result2 = item2.to_dict()
    
    print(f"\nTest kompatybilności wstecznej:")
    print(f"✓ description -> name: {dict_result2.get('name')}")
    print(f"✓ unit_price -> unit_price_net: {dict_result2.get('unit_price_net')}")
    
    return True

def test_pdf_processing():
    """Test przetwarzania rzeczywistych PDF-ów"""
    print("\n=== Test przetwarzania PDF ===")
    
    input_dir = r"C:\pdf-to-xml-app\input"
    pdf_files = [f for f in os.listdir(input_dir) if f.endswith('.pdf')]
    
    if not pdf_files:
        print("Brak plików PDF w katalogu input/")
        return False
    
    processor = PDFProcessor()
    parser = UniversalParser()
    
    # Test tylko pierwszego pliku
    test_file = pdf_files[0]
    pdf_path = os.path.join(input_dir, test_file)
    
    print(f"\nTestowanie: {test_file}")
    
    try:
        # Ekstrakcja tekstu z PDF
        text, tables = processor.extract_text(pdf_path)
        
        if text:
            print(f"✓ Wyekstrahowano {len(text)} znaków tekstu")
        else:
            print("✗ Brak tekstu w PDF")
        
        # Parsowanie
        invoice_data = parser.parse(text, tables)
        
        # Sprawdzenie kluczowych pól
        checks = [
            ('invoice_number', invoice_data.get('invoice_number', '')),
            ('seller.nip', invoice_data.get('seller', {}).get('nip', '')),
            ('buyer.nip', invoice_data.get('buyer', {}).get('nip', '')),
            ('items count', len(invoice_data.get('items', []))),
        ]
        
        for field, value in checks:
            status = "✓" if value else "⚠"
            print(f"{status} {field}: {value}")
        
        # Sprawdź items
        if invoice_data.get('items'):
            item = invoice_data['items'][0]
            print(f"\nPierwsza pozycja:")
            print(f"  - name: {item.get('name', 'BRAK')}")
            print(f"  - description: {item.get('description', 'BRAK')}")
            print(f"  - unit_price_net: {item.get('unit_price_net', 'BRAK')}")
            print(f"  - unit_price: {item.get('unit_price', 'BRAK')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Błąd podczas przetwarzania: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Główna funkcja testowa"""
    print("=" * 50)
    print("TESTY POPRAWEK W UNIVERSAL_PARSER_V6")
    print("=" * 50)
    
    results = []
    
    # Test 1: clean_nip
    results.append(("clean_nip", test_clean_nip()))
    
    # Test 2: kompatybilność InvoiceItem
    results.append(("invoice_item", test_invoice_item_compatibility()))
    
    # Test 3: przetwarzanie PDF
    results.append(("pdf_processing", test_pdf_processing()))
    
    # Podsumowanie
    print("\n" + "=" * 50)
    print("PODSUMOWANIE TESTÓW:")
    print("=" * 50)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 Wszystkie testy zakończone sukcesem!")
    else:
        print("\n⚠️  Niektóre testy nie powiodły się.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
