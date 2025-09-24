#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test systemu na rzeczywistych fakturach PDF
Testuje cały pipeline: PDF -> OCR -> Parse -> XML
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import glob
from pathlib import Path
from app.pdf_processor import PDFProcessor
from app.parsers.universal_parser_v2 import UniversalParser
from app.comarch_mapper import ComarchMapper
from app.xml_generator import XMLGenerator
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InvoiceTestRunner:
    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.parser = UniversalParser()
        self.mapper = ComarchMapper()
        self.xml_generator = XMLGenerator()
        self.results = []
        
    def test_single_invoice(self, pdf_path):
        """Testuje pojedynczą fakturę"""
        print(f"\n{'='*60}")
        print(f"Testowanie: {os.path.basename(pdf_path)}")
        print('='*60)
        
        result = {
            'file': os.path.basename(pdf_path),
            'status': 'FAILED',
            'details': {}
        }
        
        try:
            # Krok 1: OCR
            print("1. Wykonywanie OCR...")
            text, tables = self.pdf_processor.extract_text_from_pdf(pdf_path)
            
            if not text:
                print("   ✗ Błąd: Nie udało się wyekstrahować tekstu")
                result['details']['ocr'] = 'Brak tekstu'
                self.results.append(result)
                return False
            
            print(f"   ✓ Wyekstrahowano {len(text)} znaków tekstu")
            result['details']['text_length'] = len(text)
            
            # Krok 2: Parsowanie
            print("2. Parsowanie danych...")
            invoice_data = self.parser.parse(text, tables)
            
            # Sprawdzenie kluczowych pól
            checks = {
                'invoice_number': invoice_data.get('invoice_number', ''),
                'seller_name': invoice_data.get('seller', {}).get('name', ''),
                'seller_nip': invoice_data.get('seller', {}).get('nip', ''),
                'items_count': len(invoice_data.get('items', [])),
                'net_total': invoice_data.get('summary', {}).get('net_total', '0.00'),
                'gross_total': invoice_data.get('summary', {}).get('gross_total', '0.00')
            }
            
            print(f"   - Numer faktury: {checks['invoice_number'] or 'BRAK'}")
            print(f"   - Sprzedawca: {checks['seller_name'] or 'NIEROZPOZNANY'}")
            print(f"   - NIP: {checks['seller_nip'] or 'BRAK'}")
            print(f"   - Liczba pozycji: {checks['items_count']}")
            print(f"   - Kwota netto: {checks['net_total']} zł")
            print(f"   - Kwota brutto: {checks['gross_total']} zł")
            
            # Ocena jakości parsowania
            quality_score = 0
            if checks['invoice_number'] and checks['invoice_number'] != '':
                quality_score += 20
            if checks['seller_name'] and checks['seller_name'] not in [':', 'NIEZNANY DOSTAWCA', '']:
                quality_score += 30
            if checks['seller_nip'] and len(checks['seller_nip']) >= 10:
                quality_score += 20
            if checks['items_count'] > 0:
                quality_score += 15
            if float(checks['gross_total']) > 0 and float(checks['gross_total']) != 10000.0:
                quality_score += 15
                
            print(f"   - Jakość parsowania: {quality_score}%")
            result['details']['quality_score'] = quality_score
            result['details']['parsed_data'] = checks
            
            # Krok 3: Mapowanie do Comarch
            print("3. Mapowanie do formatu Comarch...")
            
            # Utworzenie obiektu z danymi faktury
            class InvoiceDataWrapper:
                def __init__(self, data):
                    self.invoice_number = data.get('invoice_number', '')
                    self.invoice_date = data.get('invoice_date', '')
                    self.sale_date = data.get('sale_date', '')
                    self.payment_date = data.get('payment_date', '')
                    self.payment_method = data.get('payment_method', '')
                    
                    seller = data.get('seller', {})
                    self.seller_name = seller.get('name', '')
                    self.seller_nip = seller.get('nip', '')
                    
                    buyer = data.get('buyer', {})
                    self.buyer_name = buyer.get('name', '')
                    self.buyer_nip = buyer.get('nip', '')
                    
                    self.items = data.get('items', [])
                    
                    summary = data.get('summary', {})
                    self.net_total = summary.get('net_total', '0.00')
                    self.vat_total = summary.get('vat_total', '0.00')
                    self.gross_total = summary.get('gross_total', '0.00')
            
            invoice_wrapper = InvoiceDataWrapper(invoice_data)
            comarch_data = self.mapper.map_invoice_data(invoice_wrapper)
            
            print(f"   ✓ Zmapowano do struktury Comarch")
            print(f"   - Kod sprzedawcy: {comarch_data.seller_code}")
            print(f"   - Metoda płatności: {comarch_data.payment_method}")
            
            # Krok 4: Generowanie XML (opcjonalne)
            # xml_content = self.xml_generator.generate_xml(comarch_data)
            # print(f"   ✓ Wygenerowano XML")
            
            # Podsumowanie
            if quality_score >= 60:
                result['status'] = 'SUCCESS'
                print(f"\n✅ SUKCES - Faktura przetworzona poprawnie (jakość: {quality_score}%)")
            elif quality_score >= 40:
                result['status'] = 'PARTIAL'
                print(f"\n⚠️ CZĘŚCIOWY SUKCES - Niektóre dane mogą wymagać korekty (jakość: {quality_score}%)")
            else:
                result['status'] = 'POOR'
                print(f"\n❌ SŁABA JAKOŚĆ - Wymaga ręcznej weryfikacji (jakość: {quality_score}%)")
                
            self.results.append(result)
            return result['status'] in ['SUCCESS', 'PARTIAL']
            
        except Exception as e:
            print(f"\n✗ BŁĄD: {str(e)}")
            result['details']['error'] = str(e)
            self.results.append(result)
            return False
    
    def run_tests(self, input_dir='input'):
        """Testuje wszystkie faktury w katalogu"""
        pdf_files = glob.glob(os.path.join(input_dir, '*.pdf'))
        
        if not pdf_files:
            print(f"Brak plików PDF w katalogu {input_dir}")
            return
        
        print(f"\n{'#'*60}")
        print(f"# TESTOWANIE RZECZYWISTYCH FAKTUR")
        print(f"# Znaleziono {len(pdf_files)} plików PDF")
        print(f"{'#'*60}")
        
        success_count = 0
        partial_count = 0
        failed_count = 0
        
        for pdf_path in pdf_files:
            try:
                if self.test_single_invoice(pdf_path):
                    if self.results[-1]['status'] == 'SUCCESS':
                        success_count += 1
                    else:
                        partial_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                print(f"Błąd podczas testowania {pdf_path}: {e}")
                failed_count += 1
        
        # Raport końcowy
        self.print_summary_report(success_count, partial_count, failed_count)
        
        # Zapis raportu do pliku
        self.save_report()
        
    def print_summary_report(self, success, partial, failed):
        """Drukuje raport podsumowujący"""
        total = success + partial + failed
        
        print(f"\n{'#'*60}")
        print(f"# RAPORT KOŃCOWY")
        print(f"{'#'*60}")
        print(f"\nPrzetestowano faktur: {total}")
        print(f"✅ Sukces (>60% jakości): {success} ({success/total*100:.1f}%)")
        print(f"⚠️  Częściowy sukces (40-60%): {partial} ({partial/total*100:.1f}%)")
        print(f"❌ Słaba jakość (<40%): {failed} ({failed/total*100:.1f}%)")
        
        print(f"\n{'='*60}")
        print("SZCZEGÓŁY DLA KAŻDEJ FAKTURY:")
        print(f"{'='*60}")
        
        for result in self.results:
            status_icon = {
                'SUCCESS': '✅',
                'PARTIAL': '⚠️',
                'POOR': '❌',
                'FAILED': '❌'
            }.get(result['status'], '?')
            
            print(f"\n{status_icon} {result['file']}")
            if 'parsed_data' in result['details']:
                data = result['details']['parsed_data']
                print(f"   - Jakość: {result['details'].get('quality_score', 0)}%")
                print(f"   - Sprzedawca: {data.get('seller_name', 'BRAK')}")
                print(f"   - Kwota brutto: {data.get('gross_total', '0.00')} zł")
            if 'error' in result['details']:
                print(f"   - Błąd: {result['details']['error']}")
    
    def save_report(self):
        """Zapisuje raport do pliku JSON"""
        report_path = 'skrypty_testowe/test_real_invoices_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\n📄 Raport szczegółowy zapisany do: {report_path}")

def main():
    """Główna funkcja"""
    tester = InvoiceTestRunner()
    
    # Sprawdź czy są faktury w katalogu input
    # Obsługa różnych lokalizacji uruchomienia
    if os.path.basename(os.getcwd()) == 'skrypty_testowe':
        input_dir = '../input'
    else:
        input_dir = 'input'
    
    if not os.path.exists(input_dir):
        print(f"Katalog {input_dir} nie istnieje!")
        print(f"Upewnij się, że katalog C:\\pdf-to-xml-app\\input\\ istnieje")
        return
    
    pdf_count = len(glob.glob(os.path.join(input_dir, '*.pdf')))
    if pdf_count == 0:
        print(f"Brak plików PDF w katalogu {input_dir}")
        print("Umieść faktury PDF w katalogu 'input' i uruchom test ponownie.")
        return
    
    print(f"Znaleziono {pdf_count} faktur do przetestowania.")
    print("Rozpoczynanie testów...")
    
    tester.run_tests(input_dir)

if __name__ == "__main__":
    main()
