#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test diagnostyczny parsowania faktur
=====================================
Szczegółowa analiza procesu parsowania
"""

import os
import sys
from pathlib import Path
import re

# Dodaj ścieżkę do aplikacji
sys.path.insert(0, r'C:\pdf-to-xml-app')
sys.path.insert(0, r'C:\pdf-to-xml-app\app')

def test_invoice_parsing():
    """Test parsowania faktury krok po kroku"""
    
    print("="*60)
    print("TEST PARSOWANIA FAKTURY - SZCZEGÓŁOWA DIAGNOZA")
    print("="*60)
    
    # Importy
    from pdf_processor import PDFProcessor
    from invoice_detector import InvoiceDetector, InvoiceType
    from parsers.universal_parser import UniversalParser
    import pdfplumber
    
    # Wybór pliku testowego
    test_file = Path(r'C:\pdf-to-xml-app\input\Faktura 11_07_2025.pdf')
    
    if not test_file.exists():
        print(f"❌ Nie znaleziono pliku: {test_file}")
        return
    
    print(f"📄 Analizowany plik: {test_file.name}")
    print("-"*60)
    
    # KROK 1: Ekstrakcja tekstu
    print("\n[KROK 1] EKSTRAKCJA TEKSTU")
    text = ""
    tables = []
    
    with pdfplumber.open(test_file) as pdf:
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
            
            page_tables = page.extract_tables()
            if page_tables:
                tables.extend(page_tables)
    
    print(f"✅ Wyekstraktowano {len(text)} znaków tekstu")
    print(f"✅ Znaleziono {len(tables)} tabel")
    
    # Pokaż fragment tekstu
    print("\n📋 Fragment tekstu (pierwsze 500 znaków):")
    print("-"*40)
    print(text[:500])
    print("-"*40)
    
    # KROK 2: Detekcja typu faktury
    print("\n[KROK 2] DETEKCJA TYPU FAKTURY")
    detector = InvoiceDetector()
    invoice_type = detector.detect_type(text)
    confidence = detector.get_confidence_score(text, invoice_type)
    
    print(f"🔍 Wykryty typ: {invoice_type.value}")
    print(f"🎯 Pewność: {confidence:.2%}")
    
    # KROK 3: Analiza kluczowych pól
    print("\n[KROK 3] ANALIZA KLUCZOWYCH PÓL")
    
    # Numer faktury
    print("\n📌 Numer faktury:")
    invoice_patterns = [
        r'Faktura\s*(?:VAT\s*)?nr\s*[:.]?\s*([^\s\n]+)',
        r'nr\s*[:.]?\s*([A-Z0-9\-/\.]+)',
        r'Numer\s*faktury\s*[:.]?\s*([A-Z0-9\-/\.]+)',
    ]
    
    for pattern in invoice_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            print(f"  ✅ Znaleziono: '{match.group(1)}'")
            print(f"     Pattern: {pattern}")
            print(f"     Pozycja: {match.start()}-{match.end()}")
            break
    else:
        print("  ❌ Nie znaleziono numeru faktury")
    
    # Sprzedawca
    print("\n📌 Sprzedawca:")
    seller_pattern = r'(?:Sprzedawca|Wystawca)[:\s]*\n?(.*?)(?:Nabywca|Odbiorca|$)'
    seller_match = re.search(seller_pattern, text, re.IGNORECASE | re.DOTALL)
    if seller_match:
        seller_text = seller_match.group(1)[:200]
        print(f"  ✅ Znaleziono sekcję sprzedawcy:")
        print(f"  {seller_text}")
        
        # Szukaj NIP
        nip_match = re.search(r'NIP\s*[:.]?\s*([PL]?\s*[\d\s\-]+)', seller_text, re.IGNORECASE)
        if nip_match:
            print(f"  NIP: {nip_match.group(1)}")
    else:
        print("  ❌ Nie znaleziono sekcji sprzedawcy")
    
    # Nabywca
    print("\n📌 Nabywca:")
    buyer_pattern = r'(?:Nabywca|Odbiorca)[:\s]*\n?(.*?)(?:Pozycje|Lp\.|$)'
    buyer_match = re.search(buyer_pattern, text, re.IGNORECASE | re.DOTALL)
    if buyer_match:
        buyer_text = buyer_match.group(1)[:200]
        print(f"  ✅ Znaleziono sekcję nabywcy:")
        print(f"  {buyer_text}")
    else:
        print("  ❌ Nie znaleziono sekcji nabywcy")
    
    # Kwoty
    print("\n📌 Kwoty:")
    amount_patterns = {
        'Brutto': [
            r'Do\s*zapłaty\s*[:.]?\s*([\d\s,.-]+)',
            r'Razem\s*brutto\s*[:.]?\s*([\d\s,.-]+)',
            r'Suma\s*brutto\s*[:.]?\s*([\d\s,.-]+)',
            r'Wartość\s*brutto\s*[:.]?\s*([\d\s,.-]+)'
        ],
        'Netto': [
            r'Razem\s*netto\s*[:.]?\s*([\d\s,.-]+)',
            r'Suma\s*netto\s*[:.]?\s*([\d\s,.-]+)',
            r'Wartość\s*netto\s*[:.]?\s*([\d\s,.-]+)'
        ],
        'VAT': [
            r'Razem\s*VAT\s*[:.]?\s*([\d\s,.-]+)',
            r'Kwota\s*VAT\s*[:.]?\s*([\d\s,.-]+)',
            r'Podatek\s*VAT\s*[:.]?\s*([\d\s,.-]+)'
        ]
    }
    
    for field, patterns in amount_patterns.items():
        print(f"\n  {field}:")
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1)
                # Czyszczenie kwoty
                clean_amount = amount_str.replace(' ', '').replace(',', '.')
                print(f"    ✅ Znaleziono: '{amount_str}' -> {clean_amount}")
                print(f"       Pattern: {pattern[:40]}...")
                break
        else:
            print(f"    ❌ Nie znaleziono")
    
    # KROK 4: Test parsera
    print("\n[KROK 4] TEST PARSERA UNIWERSALNEGO")
    parser = UniversalParser()
    
    # Użyj parsera
    result = parser.parse(text, tables)
    
    print("\n📊 Wyniki parsowania:")
    print(f"  Numer faktury: {result.get('invoice_number', 'BRAK')}")
    print(f"  Data wystawienia: {result.get('invoice_date', 'BRAK')}")
    print(f"  Data sprzedaży: {result.get('sale_date', 'BRAK')}")
    
    if 'seller' in result:
        print(f"\n  Sprzedawca:")
        print(f"    Nazwa: {result['seller'].get('name', 'BRAK')}")
        print(f"    NIP: {result['seller'].get('nip', 'BRAK')}")
        print(f"    Adres: {result['seller'].get('address', 'BRAK')}")
    
    if 'buyer' in result:
        print(f"\n  Nabywca:")
        print(f"    Nazwa: {result['buyer'].get('name', 'BRAK')}")
        print(f"    NIP: {result['buyer'].get('nip', 'BRAK')}")
        print(f"    Adres: {result['buyer'].get('address', 'BRAK')}")
    
    if 'summary' in result:
        print(f"\n  Podsumowanie:")
        print(f"    Netto: {result['summary'].get('net_total', '0.00')}")
        print(f"    VAT: {result['summary'].get('vat_total', '0.00')}")
        print(f"    Brutto: {result['summary'].get('gross_total', '0.00')}")
    
    if 'items' in result and result['items']:
        print(f"\n  Pozycje: {len(result['items'])} szt.")
        for i, item in enumerate(result['items'][:3], 1):  # Pierwsze 3 pozycje
            print(f"    {i}. {item.get('name', 'BRAK')[:50]} - {item.get('gross_amount', '0.00')}")
    else:
        print(f"\n  Pozycje: BRAK")
    
    # KROK 5: Analiza tabel
    if tables:
        print("\n[KROK 5] ANALIZA TABEL")
        for i, table in enumerate(tables):
            print(f"\n  Tabela {i+1}:")
            if table and len(table) > 0:
                print(f"    Wymiary: {len(table)} wierszy x {len(table[0])} kolumn")
                print(f"    Nagłówek: {table[0] if table else 'BRAK'}")
                if len(table) > 1:
                    print(f"    Pierwszy wiersz danych: {table[1][:5]}...")  # Pierwsze 5 kolumn
    
    print("\n" + "="*60)
    print("KONIEC DIAGNOZY")
    print("="*60)

if __name__ == "__main__":
    test_invoice_parsing()
