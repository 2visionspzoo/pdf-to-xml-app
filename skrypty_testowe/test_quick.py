#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Szybki test pojedynczej faktury
Użycie: python test_quick.py [ścieżka_do_pdf]
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def quick_test(pdf_path=None):
    """Szybki test pojedynczej faktury"""
    
    # Importy wewnątrz funkcji dla szybszego startu
    from app.pdf_processor import PDFProcessor
    from app.parsers.universal_parser_v2 import UniversalParser
    from app.comarch_mapper import ComarchMapper
    import json
    
    # Jeśli nie podano ścieżki, szukaj pierwszej faktury
    if not pdf_path:
        import glob
        # Sprawdź czy jesteśmy w skrypty_testowe czy w głównym katalogu
        if os.path.basename(os.getcwd()) == 'skrypty_testowe':
            pdfs = glob.glob('../input/*.pdf')
        else:
            pdfs = glob.glob('input/*.pdf')
        
        if pdfs:
            pdf_path = pdfs[0]
            print(f"Używam pierwszej znalezionej faktury: {pdf_path}")
        else:
            print("Brak plików PDF w katalogu input/")
            print("Użycie: python test_quick.py [ścieżka_do_pdf]")
            print("Wskazówka: umieść pliki PDF w katalogu C:\\pdf-to-xml-app\\input\\")
            return False
    
    if not os.path.exists(pdf_path):
        print(f"Plik nie istnieje: {pdf_path}")
        return False
    
    print(f"\n{'='*60}")
    print(f"SZYBKI TEST: {os.path.basename(pdf_path)}")
    print('='*60)
    
    try:
        # 1. OCR
        print("\n📄 KROK 1: OCR")
        processor = PDFProcessor()
        text, tables = processor.extract_text_from_pdf(pdf_path)
        print(f"✓ Wyekstrahowano {len(text)} znaków")
        print(f"  Pierwsze 200 znaków: {text[:200]}...")
        
        # 2. Parsowanie
        print("\n🔍 KROK 2: PARSOWANIE")
        parser = UniversalParser()
        data = parser.parse(text, tables)
        
        print("Znalezione dane:")
        print(f"  📋 Numer: {data.get('invoice_number', 'BRAK')}")
        print(f"  📅 Data: {data.get('invoice_date', 'BRAK')}")
        
        seller = data.get('seller', {})
        print(f"\n  🏢 SPRZEDAWCA:")
        print(f"     Nazwa: {seller.get('name', 'BRAK')}")
        print(f"     NIP: {seller.get('nip', 'BRAK')}")
        
        items = data.get('items', [])
        print(f"\n  📦 POZYCJE: {len(items)}")
        for i, item in enumerate(items[:3], 1):  # Pokaż max 3 pozycje
            print(f"     {i}. {item.get('name', 'BRAK')} - {item.get('net_amount', 0)} zł netto")
        
        summary = data.get('summary', {})
        print(f"\n  💰 PODSUMOWANIE:")
        print(f"     Netto: {summary.get('net_total', '0.00')} zł")
        print(f"     VAT: {summary.get('vat_total', '0.00')} zł")
        print(f"     Brutto: {summary.get('gross_total', '0.00')} zł")
        
        # 3. Mapowanie
        print("\n🔄 KROK 3: MAPOWANIE DO COMARCH")
        
        # Wrapper dla danych
        class InvoiceWrapper:
            def __init__(self, d):
                self.invoice_number = d.get('invoice_number', '')
                self.invoice_date = d.get('invoice_date', '')
                self.sale_date = d.get('sale_date', '')
                self.payment_date = d.get('payment_date', '')
                self.payment_method = d.get('payment_method', '')
                self.seller_name = d.get('seller', {}).get('name', '')
                self.seller_nip = d.get('seller', {}).get('nip', '')
                self.buyer_name = d.get('buyer', {}).get('name', '')
                self.buyer_nip = d.get('buyer', {}).get('nip', '')
                self.items = d.get('items', [])
                self.net_total = d.get('summary', {}).get('net_total', '0')
                self.vat_total = d.get('summary', {}).get('vat_total', '0')
                self.gross_total = d.get('summary', {}).get('gross_total', '0')
        
        mapper = ComarchMapper()
        wrapper = InvoiceWrapper(data)
        comarch = mapper.map_invoice_data(wrapper)
        
        print(f"✓ Zmapowano do Comarch")
        print(f"  Kod sprzedawcy: {comarch.seller_code}")
        print(f"  Nazwa w systemie: {comarch.seller_name}")
        
        # Zapis do JSON dla analizy
        output_file = 'skrypty_testowe/test_quick_output.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Dane zapisane do: {output_file}")
        
        # Ocena jakości
        print(f"\n{'='*60}")
        print("📊 OCENA JAKOŚCI:")
        score = 0
        issues = []
        
        if data.get('invoice_number'):
            score += 25
        else:
            issues.append("- Brak numeru faktury")
            
        if seller.get('name') and seller.get('name') not in [':', 'NIEZNANY DOSTAWCA']:
            score += 25
        else:
            issues.append("- Nierozpoznany sprzedawca")
            
        if seller.get('nip'):
            score += 20
        else:
            issues.append("- Brak NIP sprzedawcy")
            
        if len(items) > 0:
            score += 15
        else:
            issues.append("- Brak pozycji faktury")
            
        if float(summary.get('gross_total', '0')) > 0:
            score += 15
        else:
            issues.append("- Brak kwoty brutto")
        
        print(f"\nWYNIK: {score}/100")
        
        if score >= 80:
            print("✅ ŚWIETNIE - Faktura rozpoznana bardzo dobrze!")
        elif score >= 60:
            print("✅ DOBRZE - Faktura rozpoznana poprawnie")
        elif score >= 40:
            print("⚠️ ŚREDNIO - Niektóre dane mogą wymagać korekty")
        else:
            print("❌ SŁABO - Wymaga ręcznej weryfikacji")
        
        if issues:
            print("\nProblemy do poprawy:")
            for issue in issues:
                print(issue)
        
        return score >= 40
        
    except Exception as e:
        print(f"\n❌ BŁĄD: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Sprawdź czy podano argument
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    success = quick_test(pdf_path)
    
    print(f"\n{'='*60}")
    if success:
        print("✅ TEST ZAKOŃCZONY POMYŚLNIE")
    else:
        print("❌ TEST ZAKOŃCZONY Z PROBLEMAMI")
    print('='*60)
