#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST POJEDYNCZEJ FAKTURY Z DEBUGOWANIEM
"""

import os
import sys
import logging
from pathlib import Path

# Ścieżki
sys.path.insert(0, r'C:\pdf-to-xml-app')
sys.path.insert(0, r'C:\pdf-to-xml-app\app')

# Bardzo szczegółowe logowanie
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)8s] %(filename)s:%(lineno)d - %(funcName)s() - %(message)s'
)

def test_single_invoice(pdf_path):
    """Test konwersji pojedynczej faktury z pełnym debugowaniem"""
    
    print(f"\n{'='*60}")
    print(f"TEST FAKTURY: {Path(pdf_path).name}")
    print(f"{'='*60}\n")
    
    try:
        # 1. Test odczytu PDF
        print("[KROK 1] Odczyt PDF...")
        import pdfplumber
        
        with pdfplumber.open(pdf_path) as pdf:
            print(f"  Liczba stron: {len(pdf.pages)}")
            
            # Odczytaj tekst z pierwszej strony
            page = pdf.pages[0]
            text = page.extract_text()
            
            if text:
                print(f"  Odczytano {len(text)} znaków tekstu")
                print(f"\n  Pierwsze 500 znaków:")
                print("-" * 40)
                print(text[:500])
                print("-" * 40)
            else:
                print("  ⚠ Brak tekstu - może być skan, próbuję OCR...")
        
        # 2. Test detekcji typu faktury
        print("\n[KROK 2] Detekcja typu faktury...")
        from invoice_detector import InvoiceDetector
        
        detector = InvoiceDetector()
        invoice_type = detector.detect_type(text if text else "")
        print(f"  Wykryty typ: {invoice_type}")
        
        # 3. Test parsowania
        print("\n[KROK 3] Parsowanie danych...")
        from pdf_processor import PDFProcessor
        
        processor = PDFProcessor()
        invoice_data = processor.extract_from_pdf(pdf_path)
        
        if invoice_data:
            print("  ✓ Dane wyekstraktowane")
            
            # Wyświetl wszystkie wykryte pola
            if hasattr(invoice_data, '__dict__'):
                print("\n  Wykryte pola:")
                for key, value in invoice_data.__dict__.items():
                    if value and not key.startswith('_'):
                        print(f"    • {key}: {value}")
        else:
            print("  ✗ Brak danych")
            return False
        
        # 4. Test mapowania do Comarch
        print("\n[KROK 4] Mapowanie do formatu Comarch...")
        from comarch_mapper import ComarchMapper
        
        mapper = ComarchMapper()
        comarch_data = mapper.map_invoice_data(invoice_data)
        
        if comarch_data:
            print("  ✓ Dane zmapowane")
            print(f"    • Numer faktury: {getattr(comarch_data, 'invoice_number', 'BRAK')}")
            print(f"    • Sprzedawca: {getattr(comarch_data, 'seller_name', 'BRAK')}")
            print(f"    • NIP: {getattr(comarch_data, 'seller_nip', 'BRAK')}")
            print(f"    • Kwota netto: {getattr(comarch_data, 'net_total', 0):.2f} PLN")
            print(f"    • VAT: {getattr(comarch_data, 'vat_total', 0):.2f} PLN")
            print(f"    • Brutto: {getattr(comarch_data, 'gross_total', 0):.2f} PLN")
        else:
            print("  ✗ Błąd mapowania")
            return False
        
        # 5. Test generowania XML
        print("\n[KROK 5] Generowanie XML...")
        from xml_generator import XMLGenerator
        
        generator = XMLGenerator()
        xml_content = generator.generate_xml(comarch_data)
        
        if xml_content:
            print(f"  ✓ XML wygenerowany ({len(xml_content)} znaków)")
            
            # Zapisz XML
            output_path = Path(r'C:\pdf-to-xml-app\output') / f"debug_{Path(pdf_path).stem}.xml"
            output_path.write_text(xml_content, encoding='utf-8')
            print(f"  ✓ Zapisano: {output_path}")
            
            # Pokaż fragment XML
            print("\n  Fragment XML:")
            print("-" * 40)
            lines = xml_content.split('\n')[:20]
            print('\n'.join(lines))
            print("-" * 40)
        else:
            print("  ✗ Błąd generowania XML")
            return False
        
        print(f"\n{'='*60}")
        print("✓ TEST ZAKOŃCZONY SUKCESEM!")
        print(f"{'='*60}")
        return True
        
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"✗ BŁĄD PODCZAS TESTU: {e}")
        print(f"{'='*60}")
        
        import traceback
        print("\nSzczegóły błędu:")
        print(traceback.format_exc())
        return False

def main():
    """Główna funkcja"""
    print("\n╔══════════════════════════════════════════╗")
    print("║   TEST POJEDYNCZEJ FAKTURY Z DEBUGIEM   ║")
    print("╚══════════════════════════════════════════╝")
    
    # Lista plików PDF
    input_dir = Path(r'C:\pdf-to-xml-app\input')
    pdf_files = list(input_dir.glob('*.pdf'))
    
    if not pdf_files:
        print("\n✗ Brak plików PDF w katalogu input/")
        return 1
    
    print("\nDostępne faktury:")
    for i, pdf in enumerate(pdf_files, 1):
        print(f"  [{i}] {pdf.name}")
    
    # Wybór pliku
    choice = input("\nWybierz numer faktury (lub Enter dla pierwszej): ").strip()
    
    if choice.isdigit() and 1 <= int(choice) <= len(pdf_files):
        selected_pdf = pdf_files[int(choice) - 1]
    else:
        selected_pdf = pdf_files[0]
    
    # Uruchom test
    success = test_single_invoice(str(selected_pdf))
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
