# -*- coding: utf-8 -*-
"""Test mappera - weryfikacja poprawek"""

import sys
import os
sys.path.append(r'C:\pdf-to-xml-app')

from app.comarch_mapper import ComarchMapper
from app.xml_generator_multi import XMLGeneratorMulti
from datetime import datetime

print("="*80)
print("TEST MAPPERA I GENERATORA XML")
print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# Testowa faktura
invoice = {
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
    'summary': {
        'net_total': 100.00,
        'vat_total': 23.00,
        'gross_total': 123.00
    }
}

try:
    # Mapowanie
    mapper = ComarchMapper()
    data = mapper.map_invoice_data(invoice)
    print("✅ Mapowanie OK")
    print(f"   Numer: {data.invoice_number}")
    print(f"   Sprzedawca: {data.seller_name}")
    
    # Generowanie XML
    generator = XMLGeneratorMulti()
    xml = generator.generate_multi_invoice_xml([data])
    print("✅ XML wygenerowany")
    
    # Sprawdź format
    if '<Dokumenty>' in xml and '<Dokument Typ="ZAKUP">' in xml:
        print("✅ FORMAT COMARCH ERP OPTIMA!")
    else:
        print("❌ Nieprawidłowy format")
    
    # Zapisz
    with open('test_mapper_output.xml', 'w', encoding='utf-8') as f:
        f.write(xml)
    print("💾 Zapisano: test_mapper_output.xml")
    
except Exception as e:
    print(f"❌ Błąd: {e}")
    import traceback
    traceback.print_exc()

print("="*80)
print("Test zakończony")
