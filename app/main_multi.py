#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Główny program - zbiera wszystkie faktury do jednego pliku XML
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from pdf_processor import PDFProcessor
from comarch_mapper import ComarchMapper
from xml_generator_multi import XMLGeneratorMulti

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_all_to_single_xml(input_dir, output_file, parser_type='universal'):
    """Przetwarza wszystkie pliki PDF i zapisuje do jednego XML"""
    
    input_path = Path(input_dir)
    output_path = Path(output_file)
    
    # Tworzenie katalogu wyjściowego
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Znajdź wszystkie pliki PDF
    pdf_files = list(input_path.glob("*.pdf"))
    
    if not pdf_files:
        logger.warning(f"Brak plików PDF w katalogu: {input_dir}")
        return 0
    
    logger.info(f"Znaleziono {len(pdf_files)} plików PDF do przetworzenia")
    
    # Inicjalizuj komponenty
    processor = PDFProcessor(parser_type=parser_type)
    mapper = ComarchMapper()
    
    # Lista do przechowywania wszystkich faktur
    all_invoices = []
    successful = 0
    failed = 0
    
    # Przetwarzaj każdy plik PDF
    for pdf_file in pdf_files:
        try:
            logger.info(f"Przetwarzanie: {pdf_file.name}")
            
            # 1. Ekstrahuj dane z PDF
            invoice_data = processor.extract_from_pdf(str(pdf_file))
            
            # 2. Mapuj do formatu Comarch
            comarch_data = mapper.map_invoice_data(invoice_data)
            
            # Dodaj nazwę pliku źródłowego dla identyfikacji
            comarch_data.source_file = pdf_file.name
            
            # 3. Dodaj do listy wszystkich faktur
            all_invoices.append(comarch_data)
            successful += 1
            logger.info(f"  ✅ Sukces: {pdf_file.name}")
            
        except Exception as e:
            logger.error(f"  ❌ Błąd dla {pdf_file.name}: {e}")
            failed += 1
    
    # Generuj zbiorczy XML
    if all_invoices:
        logger.info(f"Generowanie zbiorczego XML z {len(all_invoices)} fakturami...")
        generator = XMLGeneratorMulti()
        xml_content = generator.generate_multi_invoice_xml(all_invoices)
        
        # Zapisz XML
        with open(output_path, 'w', encoding='utf-8-sig') as f:
            f.write(xml_content)
        
        logger.info(f"✅ XML zapisany do: {output_path}")
        
        # Oblicz podsumowanie
        total_net = sum(inv.net_total for inv in all_invoices)
        total_vat = sum(inv.vat_total for inv in all_invoices)
        total_gross = sum(inv.gross_total for inv in all_invoices)
        
        logger.info("=" * 50)
        logger.info("PODSUMOWANIE:")
        logger.info(f"📄 Liczba faktur: {len(all_invoices)}")
        logger.info(f"✅ Przetworzone pomyślnie: {successful}")
        logger.info(f"❌ Niepowodzenia: {failed}")
        logger.info(f"💰 Suma netto: {total_net:.2f} PLN")
        logger.info(f"💰 Suma VAT: {total_vat:.2f} PLN")
        logger.info(f"💰 Suma brutto: {total_gross:.2f} PLN")
        logger.info(f"📁 Plik XML: {output_path}")
        logger.info("=" * 50)
    else:
        logger.error("Nie udało się przetworzyć żadnego pliku PDF")
        return 0
    
    return successful

def main():
    """Główna funkcja aplikacji"""
    # Parser argumentów
    parser = argparse.ArgumentParser(description='Konwerter wielu faktur PDF do jednego XML')
    parser.add_argument('--input-dir', help='Katalog z plikami PDF',
                       default=r'C:\pdf-to-xml-app\input')
    parser.add_argument('--output', '-o', help='Plik wyjściowy XML',
                       default=r'C:\pdf-to-xml-app\output\wszystkie_faktury.xml')
    parser.add_argument('--parser', help='Parser do użycia (universal, atut, bolt)',
                       default='universal')
    
    args = parser.parse_args()
    
    try:
        logger.info("=" * 50)
        logger.info("START - Konwersja wielu PDF do jednego XML")
        logger.info("=" * 50)
        
        count = process_all_to_single_xml(
            args.input_dir,
            args.output,
            args.parser
        )
        
        return 0 if count > 0 else 1
            
    except Exception as e:
        logger.error(f"Krytyczny błąd: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
