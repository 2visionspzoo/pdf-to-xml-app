#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test demonstracyjny systemu na przykładowej fakturze
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.pdf_processor import PDFProcessor
from app.parsers.universal_parser_v2 import UniversalParser
from app.comarch_mapper import ComarchMapper
import json

def test_sample_invoice():
    """Test na przykładowej fakturze"""
    
    # Obsługa różnych lokalizacji uruchomienia
    if os.path.basename(os.getcwd()) == 'skrypty_testowe':
        test_file = "../input/Faktura_Vat_23373_naz_07_2025.pdf"
    else:
        test_file = "input/Faktura_Vat_23373_naz_07_2025.pdf"
    
    if not os.path.exists(test_file):
        print(f"Plik testowy nie istnieje: {test_file}")
        return False
    
    print("\n" + "="*70)
    print("TEST DEMONSTRACYJNY SYSTEMU PDF TO XML")
    print("="*70)
    print(f"\nTestowany plik: {test_file}")
    
    try:
        # Inicjalizacja
        processor = PDFProcessor()
        parser = UniversalParser()
        mapper = ComarchMapper()
        
        # KROK 1: OCR
        print("\n[KROK 1] Ekstrakcja tekstu z PDF (OCR)...")
        print("-" * 50)
        text, tables = processor.extract_text_from_pdf(test_file)
        
        print(f"✓ Wyekstrahowano tekst ({len(text)} znaków)")
        print(f"✓ Znaleziono tabel: {len(tables) if tables else 0}")
        
        # Pokaż fragment tekstu
        print("\nFragment rozpoznanego tekstu (pierwsze 300 znaków):")
        print("-" * 30)
        print(text[:300])
        print("-" * 30)
        
        # KROK 2: PARSOWANIE
        print("\n[KROK 2] Parsowanie danych faktury...")
        print("-" * 50)
        invoice_data = parser.parse(text, tables)
        
        # Wyświetl kluczowe dane
        print("\n📋 DANE FAKTURY:")
        print(f"   Numer: {invoice_data.get('invoice_number', 'BRAK')}")
        print(f"   Data wystawienia: {invoice_data.get('invoice_date', 'BRAK')}")
        print(f"   Data sprzedaży: {invoice_data.get('sale_date', 'BRAK')}")
        
        seller = invoice_data.get('seller', {})
        print(f"\n🏢 SPRZEDAWCA:")
        print(f"   Nazwa: {seller.get('name', 'NIEROZPOZNANY')}")
        if seller.get('name') and seller.get('name') == ':':
            print("   ⚠️ UWAGA: Nazwa rozpoznana jako ':' - poprawka działa!")
        print(f"   NIP: {seller.get('nip', 'BRAK')}")
        print(f"   Adres: {seller.get('address', 'BRAK')}")
        print(f"   Miasto: {seller.get('postal_code', '')} {seller.get('city', '')}")
        
        buyer = invoice_data.get('buyer', {})
        print(f"\n🏢 NABYWCA:")
        print(f"   Nazwa: {buyer.get('name', 'NIEROZPOZNANY')}")
        print(f"   NIP: {buyer.get('nip', 'BRAK')}")
        
        items = invoice_data.get('items', [])
        print(f"\n📦 POZYCJE FAKTURY: (znaleziono: {len(items)})")
        if items:
            for i, item in enumerate(items[:5], 1):  # Max 5 pozycji
                name = item.get('name', 'BRAK NAZWY')
                if name.lower() == 'none':
                    print(f"   {i}. ⚠️ Pozycja 'None' - powinna być odfiltrowana!")
                else:
                    print(f"   {i}. {name}")
                    print(f"      Ilość: {item.get('quantity', 1)}, Netto: {item.get('net_amount', 0)} zł")
        else:
            print("   ⚠️ Brak rozpoznanych pozycji")
        
        summary = invoice_data.get('summary', {})
        print(f"\n💰 PODSUMOWANIE:")
        net = float(summary.get('net_total', '0'))
        vat = float(summary.get('vat_total', '0'))
        gross = float(summary.get('gross_total', '0'))
        
        print(f"   Netto: {net:.2f} zł")
        print(f"   VAT: {vat:.2f} zł")
        print(f"   Brutto: {gross:.2f} zł")
        
        if gross == 10000.0 and net == 0:
            print("   ⚠️ UWAGA: Wykryto domyślną wartość 10000 - wymaga korekcji!")
        
        # KROK 3: MAPOWANIE
        print("\n[KROK 3] Mapowanie do formatu Comarch ERP Optima...")
        print("-" * 50)
        
        # Wrapper dla zgodności
        class InvoiceWrapper:
            def __init__(self, data):
                self.invoice_number = data.get('invoice_number', '')
                self.invoice_date = data.get('invoice_date', '')
                self.sale_date = data.get('sale_date', '')
                self.payment_date = data.get('payment_date', '')
                self.payment_method = data.get('payment_method', '')
                self.seller_name = data.get('seller', {}).get('name', '')
                self.seller_nip = data.get('seller', {}).get('nip', '')
                self.buyer_name = data.get('buyer', {}).get('name', '')
                self.buyer_nip = data.get('buyer', {}).get('nip', '')
                self.items = data.get('items', [])
                self.net_total = data.get('summary', {}).get('net_total', '0')
                self.vat_total = data.get('summary', {}).get('vat_total', '0')
                self.gross_total = data.get('summary', {}).get('gross_total', '0')
        
        wrapper = InvoiceWrapper(invoice_data)
        comarch_data = mapper.map_invoice_data(wrapper)
        
        print(f"✓ Dane zmapowane do struktury Comarch")
        print(f"   Typ dokumentu: {comarch_data.document_type}")
        print(f"   Kod kontrahenta: {comarch_data.seller_code}")
        print(f"   Metoda płatności: {comarch_data.payment_method}")
        print(f"   Termin płatności: {comarch_data.payment_date}")
        
        # ANALIZA JAKOŚCI
        print("\n" + "="*70)
        print("📊 ANALIZA JAKOŚCI ROZPOZNANIA")
        print("="*70)
        
        score = 0
        max_score = 100
        checks = []
        
        # Sprawdzanie poszczególnych elementów
        if invoice_data.get('invoice_number'):
            score += 20
            checks.append("✓ Numer faktury rozpoznany")
        else:
            checks.append("✗ Brak numeru faktury")
        
        # Sprzedawca
        if seller.get('name') and seller.get('name') not in [':', 'NIEZNANY DOSTAWCA', '']:
            score += 25
            checks.append("✓ Nazwa sprzedawcy rozpoznana")
        else:
            checks.append("✗ Nazwa sprzedawcy nierozpoznana")
        
        if seller.get('nip'):
            score += 15
            checks.append("✓ NIP sprzedawcy rozpoznany")
        else:
            checks.append("✗ Brak NIP sprzedawcy")
        
        # Pozycje
        if len(items) > 0:
            score += 20
            checks.append(f"✓ Rozpoznano {len(items)} pozycji")
            # Sprawdź czy nie ma 'None'
            none_items = [item for item in items if item.get('name', '').lower() == 'none']
            if none_items:
                checks.append(f"⚠️ Znaleziono {len(none_items)} pozycji 'None'")
        else:
            checks.append("✗ Brak pozycji faktury")
        
        # Kwoty
        if gross > 0 and gross != 10000.0:
            score += 20
            checks.append("✓ Kwoty rozpoznane poprawnie")
        elif gross == 10000.0:
            checks.append("⚠️ Wykryto domyślną wartość 10000")
        else:
            checks.append("✗ Brak kwot")
        
        # Wyświetl wyniki
        print("\nWYNIKI SPRAWDZENIA:")
        for check in checks:
            print(f"   {check}")
        
        print(f"\n🏆 WYNIK KOŃCOWY: {score}/{max_score} punktów")
        
        if score >= 80:
            print("   ✅ ŚWIETNIE! Faktura rozpoznana bardzo dobrze")
        elif score >= 60:
            print("   ✅ DOBRZE - większość danych rozpoznana poprawnie")
        elif score >= 40:
            print("   ⚠️ ŚREDNIO - wymaga weryfikacji")
        else:
            print("   ❌ SŁABO - wymaga ręcznego wprowadzenia danych")
        
        # Zapis do JSON
        output_file = 'skrypty_testowe/test_demo_output.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(invoice_data, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Dane faktury zapisane do: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ BŁĄD: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_sample_invoice()
    
    print("\n" + "="*70)
    if success:
        print("✅ TEST DEMONSTRACYJNY ZAKOŃCZONY POMYŚLNIE")
    else:
        print("❌ TEST ZAKOŃCZONY Z BŁĘDAMI")
    print("="*70)