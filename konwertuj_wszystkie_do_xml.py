#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Konwertuje wszystkie faktury do jednego pliku XML
Obsługuje wielostronicowe PDF - każda strona jako osobna faktura
"""

import sys
import os
import glob
from pathlib import Path
from datetime import datetime
import codecs
import logging

sys.path.insert(0, r'C:\pdf-to-xml-app')
sys.path.insert(0, r'C:\pdf-to-xml-app\app')

from app.pdf_processor import PDFProcessor
from app.comarch_mapper import ComarchMapper
from app.xml_generator_multi import XMLGeneratorMulti

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

def convert_all_to_single_xml():
    """Konwertuje wszystkie faktury do jednego pliku XML - obsługa wielostronicowych PDF"""
    
    print("="*70)
    print("KONWERSJA WSZYSTKICH FAKTUR DO JEDNEGO PLIKU XML")
    print("Obsługa wielostronicowych PDF - każda strona osobno")
    print("="*70)
    
    # Znajdź faktury
    pdf_files = glob.glob(r'C:\pdf-to-xml-app\input\*.pdf')
    
    if not pdf_files:
        print("❌ Brak plików PDF w katalogu input/")
        return False
    
    print(f"\n📁 Znaleziono {len(pdf_files)} plików PDF")
    
    # Inicjalizacja
    processor = PDFProcessor(parser_type='universal')
    mapper = ComarchMapper()
    
    # Lista wszystkich faktur
    all_invoices = []
    total_invoices = 0
    total_pages_processed = 0
    files_with_invoices = 0
    files_without_invoices = 0
    
    # Przetwarzaj każdy plik PDF
    for i, pdf_path in enumerate(pdf_files, 1):
        pdf_name = os.path.basename(pdf_path)
        print(f"\n[{i}/{len(pdf_files)}] 📄 Przetwarzanie: {pdf_name}")
        print("-" * 50)
        
        try:
            # Ekstraktuj faktury z PDF (każda strona osobno)
            invoices_from_pdf = processor.extract_from_pdf_multipage(pdf_path)
            
            if invoices_from_pdf:
                files_with_invoices += 1
                print(f"   ✅ Znaleziono {len(invoices_from_pdf)} faktur(y)")
                
                # Przetwórz każdą fakturę
                for invoice_data in invoices_from_pdf:
                    try:
                        # Mapuj do formatu Comarch
                        comarch_data = mapper.map_invoice_data(invoice_data)
                        
                        # Dodaj do listy
                        all_invoices.append(comarch_data)
                        
                        # Informacje o fakturze
                        invoice_num = comarch_data.invoice_number or f"Strona_{invoice_data.get('source_page', '?')}"
                        source_page = invoice_data.get('source_page', '?')
                        
                        print(f"      📋 Faktura: {invoice_num} (strona {source_page})")
                        
                        # Pokaż szczegóły faktury
                        if comarch_data.seller_name:
                            print(f"         • Sprzedawca: {comarch_data.seller_name[:50]}...")
                        if comarch_data.buyer_name:
                            print(f"         • Nabywca: {comarch_data.buyer_name[:50]}...")
                        if hasattr(comarch_data, 'items') and comarch_data.items:
                            print(f"         • Pozycje: {len(comarch_data.items)}")
                        
                        total_invoices += 1
                        
                    except Exception as e:
                        logger.error(f"Błąd mapowania faktury ze strony {invoice_data.get('source_page', '?')}: {e}")
                
                total_pages_processed += len(invoices_from_pdf)
                
            else:
                files_without_invoices += 1
                print(f"   ⚠️ Nie znaleziono faktur w tym pliku")
                
        except Exception as e:
            print(f"   ❌ Błąd przetwarzania pliku: {e}")
            files_without_invoices += 1
    
    # Generuj jeden XML
    if all_invoices:
        print(f"\n📝 Generowanie zbiorczego XML...")
        print("-" * 50)
        
        generator = XMLGeneratorMulti()
        xml_content = generator.generate_multi_invoice_xml(all_invoices)
        
        # Zapisz z prawidłowym kodowaniem UTF-8 (bez BOM)
        output_path = Path(r'C:\pdf-to-xml-app\output') / 'wszystkie_faktury.xml'
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        print(f"✅ Zapisano XML: {output_path}")
        
        print(f"\n" + "="*70)
        print("📊 PODSUMOWANIE:")
        print("-" * 70)
        print(f"   • Przetworzono plików PDF: {len(pdf_files)}")
        print(f"   • Pliki z fakturami: {files_with_invoices}")
        print(f"   • Pliki bez faktur: {files_without_invoices}")
        print(f"   • Łącznie znaleziono faktur: {total_invoices}")
        print(f"   • Łącznie przetworzono stron: {total_pages_processed}")
        print(f"   • Plik XML: output\\wszystkie_faktury.xml")
        print("="*70)
        
        return True
    else:
        print("\n❌ Nie znaleziono żadnych faktur do zapisania")
        return False

if __name__ == "__main__":
    success = convert_all_to_single_xml()
    
    print("\n" + "="*70)
    if success:
        print("✅✅✅ KONWERSJA ZAKOŃCZONA POMYŚLNIE! ✅✅✅")
        print("\n🎯 Plik gotowy do importu: output\\wszystkie_faktury.xml")
    else:
        print("❌ KONWERSJA NIEUDANA")
    print("="*70)
