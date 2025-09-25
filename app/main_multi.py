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
from multiprocessing import Pool
from pdf_processor import PDFProcessor
from comarch_mapper import ComarchMapper
from xml_generator_multi import XMLGeneratorMulti

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_single_pdf(pdf_file: Path, parser_type: str) -> tuple:
    """Przetwarza pojedynczy plik PDF i zwraca dane oraz metryki"""
    try:
        logger.info(f"Przetwarzanie: {pdf_file.name}")
        processor = PDFProcessor(parser_type=parser_type)
        invoice_data = processor.extract_from_pdf(str(pdf_file))
        mapper = ComarchMapper()
        comarch_data = mapper.map_invoice_data(invoice_data)
        comarch_data.source_file = pdf_file.name
        
        # Metryki dokładności
        confidence = 1.0
        if not invoice_data.invoice_number:
            confidence -= 0.2
        if not invoice_data.seller_name or not invoice_data.seller_nip:
            confidence -= 0.2
        if not invoice_data.items:
            confidence -= 0.3
        if not invoice_data.net_total or not invoice_data.gross_total:
            confidence -= 0.2
        
        return comarch_data, confidence, None
    except Exception as e:
        logger.error(f"  ❌ Błąd dla {pdf_file.name}: {e}")
        return None, 0.0, str(e)

def process_all_to_single_xml(input_dir, output_file, parser_type='universal'):
    """Przetwarza wszystkie pliki PDF i zapisuje do jednego XML"""
    input_path = Path(input_dir)
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    pdf_files = list(input_path.glob("*.pdf"))
    if not pdf_files:
        logger.warning(f"Brak plików PDF w katalogu: {input_dir}")
        return 0
    
    logger.info(f"Znaleziono {len(pdf_files)} plików PDF do przetworzenia")
    
    all_invoices = []
    successful = 0
    failed = 0
    confidence_scores = []
    
    # Równoległe przetwarzanie
    with Pool() as pool:
        results = pool.starmap(process_single_pdf, [(pdf_file, parser_type) for pdf_file in pdf_files])
    
    for comarch_data, confidence, error in results:
        if comarch_data:
            all_invoices.append(comarch_data)
            successful += 1
            confidence_scores.append(confidence)
            logger.info(f"  ✅ Sukces: {comarch_data.source_file} (dokładność: {confidence:.2%})")
        else:
            failed += 1
            logger.error(f"  ❌ Błąd: {error}")
    
    if all_invoices:
        logger.info(f"Generowanie zbiorczego XML z {len(all_invoices)} fakturami...")
        generator = XMLGeneratorMulti()
        try:
            xml_content = generator.generate_multi_invoice_xml(all_invoices)
            with open(output_path, 'w', encoding='utf-8-sig') as f:
                f.write(xml_content)
            
            logger.info(f"✅ XML zapisany do: {output_path}")
            
            total_net = sum(inv.net_total for inv in all_invoices)
            total_vat = sum(inv.vat_total for inv in all_invoices)
            total_gross = sum(inv.gross_total for inv in all_invoices)
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
            
            logger.info("=" * 50)
            logger.info("PODSUMOWANIE:")
            logger.info(f"📄 Liczba faktur: {len(all_invoices)}")
            logger.info(f"✅ Przetworzone pomyślnie: {successful}")
            logger.info(f"❌ Niepowodzenia: {failed}")
            logger.info(f"📊 Średnia dokładność: {avg_confidence:.2%}")
            logger.info(f"💰 Suma netto: {total_net:.2f} {all_invoices[0].currency if all_invoices else 'PLN'}")
            logger.info(f"💰 Suma VAT: {total_vat:.2f} {all_invoices[0].currency if all_invoices else 'PLN'}")
            logger.info(f"💰 Suma brutto: {total_gross:.2f} {all_invoices[0].currency if all_invoices else 'PLN'}")
            logger.info(f"📁 Plik XML: {output_path}")
            logger.info("=" * 50)
        except ValueError as e:
            logger.error(f"Błąd generowania XML: {e}")
            return 0
    else:
        logger.error("Nie udało się przetworzyć żadnego pliku PDF")
        return 0
    
    return successful

def main():
    """Główna funkcja aplikacji"""
    parser = argparse.ArgumentParser(description='Konwerter wielu faktur PDF do jednego XML')
    parser.add_argument('--input-dir', help='Katalog z plikami PDF',
                       default=r'input')
    parser.add_argument('--output', '-o', help='Plik wyjściowy XML',
                       default=r'output/wszystkie_faktury.xml')
    parser.add_argument('--parser', help='Parser do użycia (universal, atut, bolt)',
                       default='universal')
    
    args = parser.parse_args()
    
    process_all_to_single_xml(args.input_dir, args.output, args.parser)

if __name__ == '__main__':
    main()