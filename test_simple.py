#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test uproszczony - używa PDFProcessor który sam parsuje
"""

import sys
import os

# Znajdź główny katalog projektu
current_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(current_dir) == 'skrypty_testowe':
    project_root = os.path.dirname(current_dir)
else:
    project_root = current_dir

sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'app'))
os.chdir(project_root)

print(f"Katalog projektu: {project_root}")

def test_invoice():
    """Testuj fakturę używając PDFProcessor"""
    from app.pdf_processor import PDFProcessor
    from app.comarch_mapper import ComarchMapper
    import glob
    import json
    
    # Znajdź faktury
    pdf_files = glob.glob('input/*.pdf')
    
    if not pdf_files:
        print("\n❌ Brak plików PDF w katalogu input/")
        return False
    
    print(f"\n✅ Znaleziono {len(pdf_files)} faktur")
    test_file = pdf_files[0]
    print(f"\n📄 Testowanie: {os.path.basename(test_file)}")
    print("="*60)
    
    try:
        # PDFProcessor sam wykonuje OCR i parsowanie
        print("\n1️⃣ Przetwarzanie PDF (OCR + parsowanie)...")
        processor = PDFProcessor(parser_type='universal')  # Użyj uniwersalnego parsera
        invoice_data = processor.extract_from_pdf(test_file)
        
        print("   ✓ PDF przetworzony")
        
        # Wyświetl dane
        print("\n📋 WYNIKI ROZPOZNANIA:")
        print(f"   Numer faktury: {invoice_data.invoice_number or 'BRAK'}")
        print(f"   Data: {invoice_data.invoice_date or 'BRAK'}")
        
        print(f"\n🏢 SPRZEDAWCA:")
        if invoice_data.seller_name and invoice_data.seller_name != ':':
            print(f"   ✓ {invoice_data.seller_name}")
        else:
            print(f"   ✗ Nierozpoznany (otrzymano: '{invoice_data.seller_name}')")
        print(f"   NIP: {invoice_data.seller_nip or 'BRAK'}")
        
        print(f"\n💰 KWOTY:")
        print(f"   Netto: {invoice_data.net_total or 0:.2f} zł")
        print(f"   VAT: {invoice_data.vat_total or 0:.2f} zł")
        print(f"   Brutto: {invoice_data.gross_total or 0:.2f} zł")
        
        if invoice_data.gross_total == 10000.0 and invoice_data.net_total == 0:
            print("   ⚠️ Wykryto domyślną wartość 10000!")
        
        items_count = len(invoice_data.items) if invoice_data.items else 0
        print(f"\n📦 POZYCJE: {items_count}")
        if invoice_data.items:
            for i, item in enumerate(invoice_data.items[:3], 1):
                desc = item.get('description', item.get('name', 'BRAK'))
                if desc.lower() in ['none', '']:
                    print(f"   {i}. ⚠️ Pusta pozycja")
                else:
                    print(f"   {i}. {desc}")
        
        # Mapowanie do Comarch
        print("\n2️⃣ Mapowanie do formatu Comarch...")
        mapper = ComarchMapper()
        comarch_data = mapper.map_invoice_data(invoice_data)
        
        print(f"   ✓ Kod kontrahenta: {comarch_data.seller_code}")
        print(f"   ✓ Metoda płatności: {comarch_data.payment_method}")
        
        # Ocena jakości
        print("\n📊 OCENA JAKOŚCI:")
        score = 0
        checks = []
        
        if invoice_data.invoice_number:
            score += 25
            checks.append("✓ Numer faktury")
        else:
            checks.append("✗ Brak numeru")
            
        if invoice_data.seller_name and invoice_data.seller_name not in [':', '', 'NIEZNANY DOSTAWCA']:
            score += 25
            checks.append("✓ Nazwa sprzedawcy")
        else:
            checks.append("✗ Nazwa sprzedawcy")
            
        if invoice_data.seller_nip:
            score += 20
            checks.append("✓ NIP sprzedawcy")
        else:
            checks.append("✗ NIP sprzedawcy")
            
        if items_count > 0:
            score += 15
            checks.append(f"✓ Pozycje ({items_count})")
        else:
            checks.append("✗ Brak pozycji")
            
        if invoice_data.gross_total and invoice_data.gross_total > 0 and invoice_data.gross_total != 10000.0:
            score += 15
            checks.append("✓ Kwoty")
        else:
            checks.append("✗ Kwoty")
        
        for check in checks:
            print(f"   {check}")
        
        print(f"\n🏆 WYNIK: {score}/100 punktów")
        
        if score >= 80:
            print("   🟢 ŚWIETNIE!")
        elif score >= 60:
            print("   🟡 DOBRZE")
        elif score >= 40:
            print("   🟠 ŚREDNIO")
        else:
            print("   🔴 SŁABO")
        
        # Zapisz do JSON
        # Konwertuj InvoiceData do dict
        output_data = {
            'invoice_number': invoice_data.invoice_number,
            'invoice_date': invoice_data.invoice_date,
            'sale_date': invoice_data.sale_date,
            'seller': {
                'name': invoice_data.seller_name,
                'nip': invoice_data.seller_nip,
                'address': invoice_data.seller_address,
                'city': invoice_data.seller_city,
                'postal_code': invoice_data.seller_postal_code
            },
            'buyer': {
                'name': invoice_data.buyer_name,
                'nip': invoice_data.buyer_nip,
                'address': invoice_data.buyer_address
            },
            'items': invoice_data.items or [],
            'payment_method': invoice_data.payment_method,
            'payment_date': invoice_data.payment_date,
            'summary': {
                'net_total': invoice_data.net_total,
                'vat_total': invoice_data.vat_total,
                'gross_total': invoice_data.gross_total
            }
        }
        
        output_file = 'skrypty_testowe/test_simple_output.json'
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Dane zapisane: {output_file}")
        
        return score >= 40
        
    except Exception as e:
        print(f"\n❌ BŁĄD: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("TEST UPROSZCZONY - PDF TO XML")
    print("="*60)
    
    success = test_invoice()
    
    print("\n" + "="*60)
    if success:
        print("✅ TEST ZAKOŃCZONY POMYŚLNIE")
    else:
        print("❌ TEST ZAKOŃCZONY Z PROBLEMAMI")
    print("="*60)
