#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt testujący naprawiony mapper Comarch
"""

import sys
import os
import json
from pathlib import Path

# Dodaj katalog główny do ścieżki
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.parsers.universal_parser_v2 import UniversalParser
from app.comarch_mapper import ComarchMapper
from app.xml_generator import XMLGenerator
import pdfplumber


def test_mapper():
    """Test mappera Comarch po naprawie"""
    print("=" * 60)
    print("TEST NAPRAWIONEGO MAPPERA COMARCH")
    print("=" * 60)
    
    # Przygotuj dane testowe symulujące output z parsera
    test_data = {
        'invoice_number': 'FV/2025/01/001',
        'invoice_date': '11.07.2025',
        'sale_date': '11.07.2025',
        'seller_name': 'Test Firma Sp. z o.o.',
        'seller_nip': '1234567890',
        'items': [
            {
                'name': 'Wyklejenie samochodu IVECO',
                'quantity': 1,
                'unit': 'szt.',
                'unit_price_net': 427.00,
                'net_amount': 427.00,
                'vat_rate': '23%',  # Test parsowania z %
                'vat_amount': 0,
                'gross_amount': 525.21
            },
            {
                'description': 'Usługa transportowa',
                'quantity': 2,
                'unit': 'km',
                'unit_price': 100.00,
                'net_value': 200.00,
                'vat_rate': 8,  # Test parsowania liczby
                'vat_amount': 16.00,
                'gross_amount': 216.00
            }
        ],
        'net_total': 627.00,
        'vat_total': 114.21,
        'gross_total': 741.21,
        'payment_method': 'przelew',
        'payment_date': '25.07.2025'
    }
    
    # Konwertuj do obiektu z atrybutami
    class InvoiceData:
        def __init__(self, data):
            for key, value in data.items():
                setattr(self, key, value)
    
    invoice_data = InvoiceData(test_data)
    
    try:
        # Test mappera
        mapper = ComarchMapper()
        comarch_data = mapper.map_invoice_data(invoice_data)
        
        print("✅ Mapper wykonał się bez błędów!")
        print("\n📋 WYNIK MAPOWANIA:")
        print("-" * 60)
        print(f"📄 Numer faktury: {comarch_data.invoice_number}")
        print(f"📅 Data wystawienia: {comarch_data.issue_date}")
        print(f"🏢 Sprzedawca: {comarch_data.seller_name}")
        print(f"🏢 Nabywca: {comarch_data.buyer_name}")
        print(f"\n📦 Pozycje faktury:")
        
        for item in comarch_data.items:
            print(f"  {item['lp']}. {item['description']}")
            print(f"     Ilość: {item['quantity']} {item['unit']}")
            print(f"     Cena netto: {item['unit_price']:.2f} zł")
            print(f"     Wartość netto: {item['net_value']:.2f} zł")
            print(f"     Stawka VAT: {item['vat_rate']}%")
            print(f"     Kwota VAT: {item['vat_amount']:.2f} zł")
            print(f"     Wartość brutto: {item['gross_value']:.2f} zł")
        
        print(f"\n💰 PODSUMOWANIE:")
        print(f"   Netto: {comarch_data.net_total:.2f} zł")
        print(f"   VAT: {comarch_data.vat_total:.2f} zł")
        print(f"   Brutto: {comarch_data.gross_total:.2f} zł")
        
        print("\n🎉 Wszystkie testy przeszły pomyślnie!")
        
        return True
        
    except Exception as e:
        print(f"❌ Błąd podczas mapowania: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_pipeline():
    """Test pełnego pipeline'u PDF -> XML"""
    print("\n" + "=" * 60)
    print("TEST PEŁNEGO PROCESU KONWERSJI")
    print("=" * 60)
    
    input_dir = Path(r"C:\pdf-to-xml-app\input")
    test_file = input_dir / "Faktura 11_07_2025.pdf"
    
    if not test_file.exists():
        print(f"❌ Brak pliku testowego: {test_file}")
        return False
    
    try:
        print(f"📄 Przetwarzanie: {test_file.name}")
        
        # 1. Parsuj PDF
        with pdfplumber.open(test_file) as pdf:
            text = ""
            tables = []
            for page in pdf.pages:
                text += page.extract_text() or ""
                page_tables = page.extract_tables()
                if page_tables:
                    tables.extend(page_tables)
        
        parser = UniversalParser()
        invoice_dict = parser.parse(text, tables)
        
        print("✅ Parsing zakończony")
        
        # Konwertuj słownik na obiekt dla mappera
        class InvoiceData:
            def __init__(self, data):
                # Podstawowe dane
                self.invoice_number = data.get('invoice_number', '')
                self.invoice_date = data.get('invoice_date', '')
                self.sale_date = data.get('sale_date', '')
                self.payment_date = data.get('payment_date', '')
                self.payment_method = data.get('payment_method', '')
                
                # Sprzedawca
                seller = data.get('seller', {})
                self.seller_name = seller.get('name', '')
                self.seller_nip = seller.get('nip', '')
                
                # Nabywca
                buyer = data.get('buyer', {})
                self.buyer_name = buyer.get('name', '')
                self.buyer_nip = buyer.get('nip', '')
                
                # Pozycje
                self.items = data.get('items', [])
                
                # Podsumowanie
                summary = data.get('summary', {})
                self.net_total = summary.get('net_total', '0.00')
                self.vat_total = summary.get('vat_total', '0.00')
                self.gross_total = summary.get('gross_total', '0.00')
        
        invoice_data = InvoiceData(invoice_dict)
        
        # 2. Mapuj do Comarch
        mapper = ComarchMapper()
        comarch_data = mapper.map_invoice_data(invoice_data)
        
        print("✅ Mapowanie zakończone")
        
        # 3. Generuj XML
        generator = XMLGenerator()
        xml_content = generator.generate_xml(comarch_data)
        
        print("✅ Generowanie XML zakończone")
        
        # 4. Zapisz XML
        output_path = Path(r"C:\pdf-to-xml-app\skrypty_testowe\test_output.xml")
        output_path.write_text(xml_content, encoding='utf-8')
        
        print(f"✅ XML zapisany do: {output_path}")
        
        # Wyświetl fragment XML
        print("\n📄 Fragment wygenerowanego XML:")
        print("-" * 60)
        lines = xml_content.split('\n')[:30]
        for line in lines:
            print(line)
        if len(xml_content.split('\n')) > 30:
            print("...")
        
        return True
        
    except Exception as e:
        print(f"❌ Błąd podczas konwersji: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Rozpoczynam testy naprawionego systemu\n")
    
    # Test 1: Mapper
    test1_ok = test_mapper()
    
    # Test 2: Pełny pipeline
    test2_ok = test_full_pipeline()
    
    # Podsumowanie
    print("\n" + "=" * 60)
    print("PODSUMOWANIE TESTÓW")
    print("=" * 60)
    
    if test1_ok and test2_ok:
        print("✅ Wszystkie testy przeszły pomyślnie!")
        print("🎉 System jest gotowy do użycia!")
    else:
        print("⚠️ Niektóre testy nie przeszły")
        print("Sprawdź logi powyżej")
