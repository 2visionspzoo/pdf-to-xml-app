#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test bezpośredni na fakturze - najprostszy możliwy
"""

import sys
import os

# Dodaj ścieżki
sys.path.insert(0, r'C:\pdf-to-xml-app')
sys.path.insert(0, r'C:\pdf-to-xml-app\app')

print("="*60)
print("TEST BEZPOŚREDNI NA FAKTURZE")
print("="*60)

try:
    from app.pdf_processor import PDFProcessor
    from app.comarch_mapper import ComarchMapper
    
    # Znajdź pierwszą fakturę
    import glob
    pdfs = glob.glob(r'C:\pdf-to-xml-app\input\*.pdf')
    
    if not pdfs:
        print("❌ Brak faktur w input/")
        sys.exit(1)
    
    test_pdf = pdfs[0]
    print(f"\n📄 Testuję: {os.path.basename(test_pdf)}")
    print("-"*60)
    
    # Przetwórz
    print("\n⚙️ Przetwarzanie...")
    processor = PDFProcessor()
    data = processor.extract_from_pdf(test_pdf)
    
    # Wyświetl wyniki
    print("\n✅ WYNIKI:")
    print(f"   Numer faktury: {data.invoice_number or 'BRAK'}")
    print(f"   Data: {data.invoice_date or 'BRAK'}")
    print(f"   Sprzedawca: {data.seller_name or 'BRAK'}")
    
    # Sprawdź problem z ":"
    if data.seller_name == ':':
        print("   ⚠️ UWAGA: Nazwa to tylko ':' - wymaga poprawki!")
    
    print(f"   NIP: {data.seller_nip or 'BRAK'}")
    print(f"   Kwota brutto: {data.gross_total or 0:.2f} zł")
    
    # Sprawdź problem z 10000
    if data.gross_total == 10000.0:
        print("   ⚠️ UWAGA: Domyślna wartość 10000!")
    
    # Pozycje
    if data.items:
        print(f"   Pozycje: {len(data.items)}")
        for i, item in enumerate(data.items[:3], 1):
            name = item.get('description', item.get('name', '?'))
            print(f"      {i}. {name}")
    else:
        print("   Pozycje: BRAK")
    
    # Ocena
    score = 0
    if data.invoice_number:
        score += 30
    if data.seller_name and data.seller_name != ':':
        score += 30
    if data.seller_nip:
        score += 20
    if data.gross_total and data.gross_total > 0 and data.gross_total != 10000:
        score += 20
        
    print(f"\n📊 OCENA: {score}/100")
    
    if score >= 60:
        print("   ✅ Faktura rozpoznana poprawnie!")
    else:
        print("   ⚠️ Faktura wymaga poprawek")
        
except Exception as e:
    print(f"\n❌ BŁĄD: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
