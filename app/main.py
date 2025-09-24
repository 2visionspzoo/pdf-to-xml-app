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

def process_single_file(input_file, output_file, parser_type='universal'):
    """Przetwarza pojedynczy plik PDF"""
    try:
        logger.info(f"Przetwarzanie: {Path(input_file).name}")
        
        # Sprawdzenie czy plik istnieje
        if not os.path.isfile(input_file):
            raise FileNotFoundError(f"Plik PDF nie istnieje: {input_file}")
        
        # Przetwarzanie PDF
        processor = PDFProcessor(parser_type=parser_type)
        invoice_data = processor.extract_from_pdf(input_file)
        
        # Mapowanie danych do struktury Comarch
        mapper = ComarchMapper()
        comarch_data = mapper.map_invoice_data(invoice_data)
        
        # Generowanie XML
        generator = XMLGenerator()
        xml_content = generator.generate_xml(comarch_data)
        
        # Zapis XML z poprawnym kodowaniem
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8-sig') as f:  # utf-8-sig dla lepszej kompatybilności
            f.write(xml_content)
        
        logger.info(f"✅ Sukces! XML zapisany: {Path(output_file).name}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Błąd dla {Path(input_file).name}: {e}")
        return False

def process_batch(input_dir, output_dir, parser_type='universal'):
    """Przetwarza wszystkie pliki PDF z katalogu"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Tworzenie katalogu wyjściowego
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Znajdź wszystkie pliki PDF
    pdf_files = list(input_path.glob("*.pdf"))
    
    if not pdf_files:
        logger.warning(f"Brak plików PDF w katalogu: {input_dir}")
        return 0
    
    logger.info(f"Znaleziono {len(pdf_files)} plików PDF do przetworzenia")
    
    successful = 0
    failed = 0
    
    for pdf_file in pdf_files:
        # Generuj nazwę pliku wyjściowego
        output_file = output_path / (pdf_file.stem + ".xml")
        
        # Przetwórz plik
        if process_single_file(str(pdf_file), str(output_file), parser_type):
            successful += 1
        else:
            failed += 1
    
    # Podsumowanie
    logger.info("=" * 50)
    logger.info(f"PODSUMOWANIE:")
    logger.info(f"✅ Przetworzone pomyślnie: {successful}")
    logger.info(f"❌ Niepowodzenia: {failed}")
    logger.info(f"📁 Pliki XML zapisane w: {output_dir}")
    logger.info("=" * 50)
    
    return successful

def main():
    """Główna funkcja aplikacji"""
    # Parser argumentów
    parser = argparse.ArgumentParser(description='Konwerter faktur PDF do XML')
    parser.add_argument('--input', '-i', help='Ścieżka do pliku PDF')
    parser.add_argument('--output', '-o', help='Ścieżka do pliku XML')
    parser.add_argument('--input-dir', help='Katalog z plikami PDF',
                       default=r'C:\pdf-to-xml-app\input')
    parser.add_argument('--output-dir', help='Katalog wyjściowy dla XML',
                       default=r'C:\pdf-to-xml-app\output')
    parser.add_argument('--parser', help='Parser do użycia (universal, atut, bolt)',
                       default='universal')
    parser.add_argument('--batch', action='store_true', 
                       help='Przetwarzaj wszystkie pliki z katalogu input')
    
    args = parser.parse_args()
    
    try:
        logger.info("Start przetwarzania PDF-to-XML")
        
        # Tryb pojedynczego pliku
        if args.input and args.output:
            logger.info("Tryb: pojedynczy plik")
            success = process_single_file(args.input, args.output, args.parser)
            return 0 if success else 1
        
        # Tryb wsadowy (domyślny lub z flagą --batch)
        else:
            logger.info("Tryb: przetwarzanie wsadowe")
            count = process_batch(args.input_dir, args.output_dir, args.parser)
            return 0 if count > 0 else 1
            
    except Exception as e:
        logger.error(f"Krytyczny błąd: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
