#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import argparse
from pathlib import Path
from pdf_processor import PDFProcessor
from comarch_mapper import ComarchMapper
from xml_generator import XMLGenerator

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Główna funkcja aplikacji"""
    # Parser argumentów
    parser = argparse.ArgumentParser(description='Konwerter faktur PDF do XML')
    parser.add_argument('--input', '-i', help='Ścieżka do pliku PDF', 
                       default=r'C:\pdf-to-xml-app\input\faktura.pdf')
    parser.add_argument('--output', '-o', help='Ścieżka do pliku XML',
                       default=r'C:\pdf-to-xml-app\output\output.xml')
    args = parser.parse_args()
    
    try:
        # Ścieżki plików
        input_file = args.input
        output_file = args.output
        
        logger.info(f"Start przetwarzania PDF-to-XML")
        logger.info(f"Plik wejściowy: {input_file}")
        logger.info(f"Plik wyjściowy: {output_file}")
        
        # Sprawdzenie czy plik istnieje
        if not os.path.isfile(input_file):
            raise FileNotFoundError(f"Plik PDF nie istnieje: {input_file}")
        
        # Przetwarzanie PDF
        logger.info("Ekstrakcja danych z PDF...")
        processor = PDFProcessor()
        invoice_data = processor.extract_from_pdf(input_file)
        
        # Mapowanie danych do struktury Comarch
        logger.info("Mapowanie danych do formatu Comarch...")
        mapper = ComarchMapper()
        comarch_data = mapper.map_invoice_data(invoice_data)
        
        # Generowanie XML
        logger.info("Generowanie XML...")
        generator = XMLGenerator()
        xml_content = generator.generate_xml(comarch_data)
        
        # Zapis XML
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        logger.info(f"Sukces! XML zapisany do: {output_file}")
        
        # Wyświetl podsumowanie
        logger.info("=== PODSUMOWANIE ===")
        logger.info(f"Numer faktury: {comarch_data.invoice_number}")
        logger.info(f"Sprzedawca: {comarch_data.seller_name}")
        logger.info(f"NIP sprzedawcy: {comarch_data.seller_nip}")
        logger.info(f"Kwota netto: {comarch_data.net_total:.2f} PLN")
        logger.info(f"Kwota VAT: {comarch_data.vat_total:.2f} PLN")
        logger.info(f"Kwota brutto: {comarch_data.gross_total:.2f} PLN")
        
        return 0
        
    except Exception as e:
        logger.error(f"Błąd podczas przetwarzania: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
