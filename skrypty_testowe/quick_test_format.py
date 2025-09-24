#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Szybki test formatu XML"""

import sys
import os
sys.path.append(r'C:\pdf-to-xml-app')

from app.comarch_mapper import ComarchMapper
from app.xml_generator import XMLGenerator

# Dane testowe
test_invoice = {
    'invoice_number': 'TEST/001/2025',
    'invoice_date': '2025-09-24',
    'seller': {
        'name': 'Test Company Sp. z o.o.',
        'nip': '1234567890'
    },
    'payment': {
        'method': 'przelew',
        'due_date': '2025-10-01'
    },
    'items': [{
        'name': 'Usługa testowa',
        'quantity': 1,
        'unit_price_net': 100.00,
        'net_amount': 100.00,
        'vat_rate': 23,
        'vat_amount': 23.00,
        'gross_amount': 123.00
    }],
    'summary': {
        'net_total': 100.00,
        'vat_total': 23.00,
        'gross_total': 123.00
    }
}

print("="*60)
print("SZYBKI TEST FORMATU XML")
print("="*60)

try:
    # Mapowanie
    mapper = ComarchMapper()
    data = mapper.map_invoice_data(test_invoice)
    print("✅ Mapowanie OK")
    
    # Generowanie XML
    generator = XMLGenerator()
    xml = generator.generate_xml(data)
    print("✅ Generowanie XML OK")
    
    # Sprawdź strukturę
    if '<Dokumenty>' in xml and '<Dokument Typ="ZAKUP">' in xml:
        print("✅ Format Comarch ERP Optima!")
    else:
        print("❌ Nieprawidłowy format")
    
    # Zapisz
    with open('quick_test_output.xml', 'w', encoding='utf-8') as f:
        f.write(xml)
    
    # Wyświetl pierwsze linie
    print("\nPierwsze 30 linii XML:")
    print("-"*60)
    lines = xml.split('\n')[:30]
    for line in lines:
        print(line)
        
except Exception as e:
    print(f"❌ Błąd: {e}")
    import traceback
    traceback.print_exc()
