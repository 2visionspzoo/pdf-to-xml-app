#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test uniwersalny - automatycznie dostosowuje ścieżki
Może być uruchomiony z dowolnej lokalizacji
"""

import sys
import os

# Znajdź główny katalog projektu
current_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(current_dir) == 'skrypty_testowe':
    project_root = os.path.dirname(current_dir)
else:
    project_root = current_dir

# Dodaj do ścieżki
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'app'))

# Zmień katalog roboczy na główny katalog projektu
os.chdir(project_root)

print(f"Katalog projektu: {project_root}")
print(f"Katalog roboczy: {os.getcwd()}")

def run_test():
    """Uruchom test na pierwszej znalezionej fakturze"""
    from app.pdf_processor import PDFProcessor
    from app.parsers.universal_parser_v2 import UniversalParser
    from app.comarch_mapper import ComarchMapper
    import glob
    import json
    
    # Znajdź faktury
    pdf_files = glob.glob('input/*.pdf')
    
    if not pdf_files:
        print("\n❌ Brak plików PDF w katalogu input/")
        print("Umieść faktury PDF w katalogu: C:\\pdf-to-xml-app\\input\\")
        return False
    
    print(f"\n✅ Znaleziono {len(pdf_files)} faktur w katalogu input/")
    
    # Wybierz pierwszą fakturę
    test_file = pdf_files[0]
    print(f"\nTestowanie: {os.path.basename(test_file)}")
    print("="*60)
    
    try:
        # Inicjalizacja
        processor = PDFProcessor()
        parser = UniversalParser()
        mapper = ComarchMapper()
        
        # OCR i Parsowanie
        print("\n1️⃣ Ekstrakcja i parsowanie PDF...")
        invoice_data_obj = processor.extract_from_pdf(test_file)
        
        # Konwertuj do słownika jeśli to InvoiceData
        if hasattr(invoice_data_obj, '__dict__'):
            data = {
                'invoice_number': invoice_data_obj.invoice_number,
                'invoice_date': invoice_data_obj.invoice_date,
                'sale_date': invoice_data_obj.sale_date,
                'payment_date': invoice_data_obj.payment_date,
                'payment_method': invoice_data_obj.payment_method,
                'seller': {
                    'name': invoice_data_obj.seller_name,
                    'nip': invoice_data_obj.seller_nip,
                    'address': invoice_data_obj.seller_address,
                    'city': invoice_data_obj.seller_city,
                    'postal_code': invoice_data_obj.seller_postal_code
                },
                'buyer': {
                    'name': invoice_data_obj.buyer_name,
                    'nip': invoice_data_obj.buyer_nip,
                    'address': invoice_data_obj.buyer_address
                },
                'items': invoice_data_obj.items or [],
                'summary': {
                    'net_total': str(invoice_data_obj.net_total or 0),
                    'vat_total': str(invoice_data_obj.vat_total or 0),
                    'gross_total': str(invoice_data_obj.gross_total or 0)
                }
            }
        else:
            data = invoice_data_obj
        
        print(f"   ✓ Dane faktury wyekstrahowane")
        
        # Pokaż wyniki
        print("\n📄 WYNIKI:")
        print(f"   Numer: {data.get('invoice_number', 'BRAK')}")
        
        seller = data.get('seller', {})
        seller_name = seller.get('name', '')
        print(f"   Sprzedawca: {seller_name if seller_name and seller_name != ':' else 'NIEROZPOZNANY'}")
        
        if seller_name == ':':
            print("   ⚠️ Nazwa sprzedawcy to ':' - sprawdź poprawki!")
        
        items = data.get('items', [])
        print(f"   Pozycje: {len(items)}")
        
        # Sprawdź czy są pozycje None
        none_items = [item for item in items if item.get('name', '').lower() in ['none', '']]
        if none_items:
            print(f"   ⚠️ Znaleziono {len(none_items)} pozycji 'None' - powinny być odfiltrowane!")
        
        summary = data.get('summary', {})
        gross = float(summary.get('gross_total', '0'))
        print(f"   Brutto: {gross:.2f} zł")
        
        if gross == 10000.0:
            print("   ⚠️ Wykryto domyślną wartość 10000!")
        
        # Mapowanie
        print("\n3️⃣ Mapowanie do Comarch...")
        
        # Wrapper
        class Wrapper:
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
        
        comarch = mapper.map_invoice_data(Wrapper(data))
        print(f"   ✓ Kod kontrahenta: {comarch.seller_code}")
        
        # Ocena
        print("\n📊 OCENA:")
        score = 0
        
        if data.get('invoice_number'):
            score += 25
        if seller_name and seller_name not in [':', 'NIEZNANY DOSTAWCA', '']:
            score += 25
        if seller.get('nip'):
            score += 20
        if len(items) > 0:
            score += 15
        if gross > 0 and gross != 10000.0:
            score += 15
        
        print(f"   Wynik: {score}/100")
        
        if score >= 80:
            print("   ✅ ŚWIETNIE!")
        elif score >= 60:
            print("   ✅ DOBRZE")
        elif score >= 40:
            print("   ⚠️ ŚREDNIO")
        else:
            print("   ❌ SŁABO")
        
        # Zapis
        output = 'skrypty_testowe/test_universal_output.json'
        os.makedirs(os.path.dirname(output), exist_ok=True)
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Zapisano: {output}")
        
        return score >= 40
        
    except Exception as e:
        print(f"\n❌ BŁĄD: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("TEST UNIWERSALNY - PDF TO XML CONVERTER")
    print("="*60)
    
    success = run_test()
    
    print("\n" + "="*60)
    if success:
        print("✅ TEST ZAKOŃCZONY POMYŚLNIE")
    else:
        print("❌ TEST ZAKOŃCZONY Z PROBLEMAMI")
    print("="*60)
