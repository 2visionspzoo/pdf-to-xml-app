# -*- coding: utf-8 -*-

import re
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from dataclasses import dataclass
from typing import Optional, List, Dict
import logging
import sys
import os

# Dodanie ścieżki do parserów
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_config
from invoice_detector import InvoiceDetector, InvoiceType
from parsers.atut_parser import ATUTParser
from parsers.bolt_parser import BoltParser
from parsers.universal_parser import UniversalParser

# Konfiguracja Tesseract
config = get_config()
pytesseract.pytesseract.tesseract_cmd = config.tesseract_path

logger = logging.getLogger(__name__)

@dataclass
class InvoiceData:
    """Struktura danych faktury"""
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    sale_date: Optional[str] = None
    seller_name: Optional[str] = None
    seller_nip: Optional[str] = None
    seller_address: Optional[str] = None
    seller_city: Optional[str] = None
    seller_postal_code: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_nip: Optional[str] = None
    buyer_address: Optional[str] = None
    items: List[Dict] = None
    net_total: Optional[float] = None
    vat_total: Optional[float] = None
    gross_total: Optional[float] = None
    payment_method: Optional[str] = None
    payment_date: Optional[str] = None

class PDFProcessor:
    def __init__(self, parser_type: str = 'auto'):
        self.parser_type = parser_type
        # Rozpoznawanie typu faktury
        self.invoice_types = {
            'ATUT': ['atut', 'comarch'],
            'SANFILM': ['sanfilm', 'san film'],
            'FIRMAO': ['firmao'],
            'BOLT': ['bolt', 'bolt.eu'],
            'TERG': ['terg', 'mediaexpert', 'media expert'],
            'ORLEN': ['orlen', 'pko bp'],
            'MY_MUSIC': ['my music', 'mymusic'],
            'PMH': ['pmh group', 'pmh']
        }
        
        self.invoice_patterns = {
            'invoice_number': [
                r'Faktura\s*(?:VAT\s*)?nr\s*[:.]?\s*([^\s\n]+)',
                r'Faktura\s*nr\s*[:.]?\s*([A-Z0-9\-/\.]+)',
                r'nr\s*[:.]?\s*([A-Z0-9\-/\.]+)',
                r'Numer\s*faktury\s*[:.]?\s*([A-Z0-9\-/\.]+)',
                r'Invoice\s*(?:no\.?)?\s*([A-Z0-9\-/\.]+)'
            ],
            'date': [
                r'Data\s*wystawienia\s*[:.]?\s*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4})',
                r'Data\s*wystawienia\s*[:.]?\s*(\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2})',
                r'Wystawiono\s*dnia\s*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4})',
                r'z\s*dnia\s*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4})'
            ],
            'sale_date': [
                r'Data\s*sprzedaży\s*[:.]?\s*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4})',
                r'Data\s*sprzedaży\s*[:.]?\s*(\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2})',
                r'Data\s*dostawy.*?[:.]?\s*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4})',
                r'Data\s*dostawy.*?[:.]?\s*(\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2})'
            ],
            'nip': [
                r'NIP\s*[:.]?\s*([PL]?\s*[\d\s\-]+)',
                r'Tax\s*ID\s*[:.]?\s*(\d{10})'
            ],
            'gross_amount': [
                r'Do\s*zapłaty\s*[:.]?\s*([\d\s]+[,.]?\d*)\s*(?:PLN|zł)?',
                r'Razem\s*do\s*zapłaty\s*[:.]?\s*([\d\s]+[,.]?\d*)\s*(?:PLN|zł)?',
                r'Pozostało\s*do\s*zapłaty\s*[:.]?\s*([\d\s]+[,.]?\d*)\s*(?:PLN|zł)?',
                r'Należność\s*ogółem\s*[:.]?\s*([\d\s]+[,.]?\d*)\s*(?:PLN|zł)?',
                r'Suma\s*brutto.*?[:.]?\s*([\d\s]+[,.]?\d*)',
                r'Wartość\s*brutto.*?([\d\s]+[,.]?\d*)\s*(?:PLN|zł)?',
                r'Razem.*?brutto.*?([\d\s]+[,.]?\d*)'
            ],
            'net_amount': [
                r'Wartość\s*netto\s*[:.]?\s*([\d\s]+[,.]?\d*)',
                r'Razem\s*netto\s*[:.]?\s*([\d\s]+[,.]?\d*)',
                r'Netto\s*[:.]?\s*([\d\s]+[,.]?\d*)',
                r'Suma\s*netto\s*[:.]?\s*([\d\s]+[,.]?\d*)'
            ],
            'vat_amount': [
                r'VAT\s*[:.]?\s*([\d\s]+[,.]?\d*)',
                r'Kwota\s*VAT\s*[:.]?\s*([\d\s]+[,.]?\d*)',
                r'Podatek\s*VAT\s*[:.]?\s*([\d\s]+[,.]?\d*)'
            ],
            'payment_method': [
                r'Sposób\s*(?:płatności|zapłaty)\s*[:.]?\s*([^\n]+)',
                r'Forma\s*płatności\s*[:.]?\s*([^\n]+)',
                r'Zapłacono\s*[:.]?\s*([^\n]+)'
            ],
            'payment_date': [
                r'Termin\s*płatności\s*[:.]?\s*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4})',
                r'Termin\s*płatności\s*[:.]?\s*(\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2})',
                r'Data\s*płatności\s*[:.]?\s*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4})'
            ]
        }
    
    def extract_from_pdf(self, pdf_path: str) -> Dict:
        """Ekstraktuje dane z PDF używając OCR jeśli potrzeba i odpowiedniego parsera"""
        text = ""
        all_tables = []
        
        try:
            # Próba ekstrakcji tekstu natywnego
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    
                    # Próba ekstrakcji tabel
                    tables = page.extract_tables()
                    if tables:
                        all_tables.extend(tables)
            
            # Jeśli brak tekstu, użyj OCR
            if len(text.strip()) < 100:
                logger.info("Używam OCR do ekstrakcji...")
                text = self._extract_with_ocr(pdf_path)
            
            # Wybierz parser według typu
            if self.parser_type == 'universal':
                parser = UniversalParser()
                logger.info("Używam uniwersalnego parsera")
            elif self.parser_type == 'atut':
                parser = ATUTParser()
                logger.info("Używam parsera ATUT")
            elif self.parser_type == 'bolt':
                parser = BoltParser()
                logger.info("Używam parsera Bolt")
            else:
                # Auto - rozpoznaj typ faktury
                detector = InvoiceDetector()
                invoice_type = detector.detect_type(text)
                confidence = detector.get_confidence_score(text, invoice_type)
                
                logger.info(f"Wykryto typ faktury: {invoice_type.value} (pewność: {confidence:.2f})")
                
                # Wybierz odpowiedni parser
                if invoice_type == InvoiceType.ATUT:
                    parser = ATUTParser()
                elif invoice_type == InvoiceType.BOLT:
                    parser = BoltParser()
                else:
                    # Użyj uniwersalnego parsera dla pozostałych typów
                    parser = UniversalParser()
            
            # Parsuj fakturę
            invoice_data = parser.parse(text, all_tables)
            
            # Dodaj informacje o typie faktury jeśli rozpoznano automatycznie
            if self.parser_type == 'auto':
                invoice_data['invoice_type'] = invoice_type.value
                invoice_data['confidence'] = confidence
            
            # Konwersja do InvoiceData jeśli potrzebna dla kompatybilności
            return self._convert_to_invoice_data(invoice_data)
            
        except Exception as e:
            logger.error(f"Błąd ekstrakcji PDF: {e}")
            return InvoiceData()
    
    def _convert_to_invoice_data(self, data: Dict) -> InvoiceData:
        """Konwertuje słownik do InvoiceData dla kompatybilności"""
        invoice_data = InvoiceData()
        
        # Podstawowe dane
        invoice_data.invoice_number = data.get('invoice_number')
        invoice_data.invoice_date = data.get('invoice_date')
        invoice_data.sale_date = data.get('sale_date')
        invoice_data.payment_date = data.get('payment_date')
        invoice_data.payment_method = data.get('payment_method')
        
        # Sprzedawca
        if 'seller' in data:
            invoice_data.seller_name = data['seller'].get('name')
            invoice_data.seller_nip = data['seller'].get('nip')
            invoice_data.seller_address = data['seller'].get('address')
            invoice_data.seller_city = data['seller'].get('city')
            invoice_data.seller_postal_code = data['seller'].get('postal_code')
        
        # Nabywca
        if 'buyer' in data:
            invoice_data.buyer_name = data['buyer'].get('name')
            invoice_data.buyer_nip = data['buyer'].get('nip')
            invoice_data.buyer_address = data['buyer'].get('address')
        
        # Pozycje
        invoice_data.items = data.get('items', [])
        
        # Podsumowanie
        if 'summary' in data:
            try:
                invoice_data.net_total = float(data['summary'].get('net_total', 0))
                invoice_data.vat_total = float(data['summary'].get('vat_total', 0))
                invoice_data.gross_total = float(data['summary'].get('gross_total', 0))
            except:
                pass
        
        return invoice_data
    
    def _extract_with_ocr(self, pdf_path: str) -> str:
        """OCR dla skanowanych PDF"""
        try:
            # Użyj poppler jeśli skonfigurowany
            kwargs = {'dpi': config.ocr_dpi}
            if config.poppler_path and os.path.exists(config.poppler_path):
                kwargs['poppler_path'] = config.poppler_path
            
            images = convert_from_path(pdf_path, **kwargs)
            text = ""
            
            for i, image in enumerate(images):
                logger.info(f"OCR strony {i+1}/{len(images)}...")
                # OCR z językami z konfiguracji
                page_text = pytesseract.image_to_string(
                    image, 
                    lang=config.ocr_languages,
                    config=config.get_tesseract_config()
                )
                text += page_text + "\n"
            
            return text
        except Exception as e:
            logger.error(f"Błąd OCR: {e}")
            logger.info("Sprawdź czy Tesseract jest zainstalowany w: C:\\Program Files\\Tesseract-OCR")
            logger.info("Jeśli używasz Windows, pobierz Poppler z: https://github.com/oschwartz10612/poppler-windows/releases")
            return ""
    
    def _parse_invoice_data(self, text: str, invoice_data: InvoiceData) -> InvoiceData:
        """Parsuje dane faktury z tekstu"""
        
        # Numer faktury
        for pattern in self.invoice_patterns['invoice_number']:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                invoice_data.invoice_number = match.group(1).strip()
                break
        
        # Data wystawienia
        for pattern in self.invoice_patterns['date']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice_data.invoice_date = match.group(1)
                break
        
        # Data sprzedaży
        for pattern in self.invoice_patterns['sale_date']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice_data.sale_date = match.group(1)
                break
        
        # Jeśli brak daty sprzedaży, użyj daty wystawienia
        if not invoice_data.sale_date and invoice_data.invoice_date:
            invoice_data.sale_date = invoice_data.invoice_date
        
        # Ekstrakcja sprzedawcy i nabywcy
        self._extract_parties(text, invoice_data)
        
        # Kwoty
        for pattern in self.invoice_patterns['gross_amount']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice_data.gross_total = self._parse_amount(match.group(1))
                break
        
        for pattern in self.invoice_patterns['net_amount']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice_data.net_total = self._parse_amount(match.group(1))
                break
        
        for pattern in self.invoice_patterns['vat_amount']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice_data.vat_total = self._parse_amount(match.group(1))
                break
        
        # Metoda płatności
        for pattern in self.invoice_patterns['payment_method']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice_data.payment_method = match.group(1).strip()
                break
        
        # Termin płatności
        for pattern in self.invoice_patterns['payment_date']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice_data.payment_date = match.group(1)
                break
        
        # Oblicz brakujące kwoty jeśli to możliwe
        if invoice_data.gross_total and invoice_data.net_total and not invoice_data.vat_total:
            invoice_data.vat_total = invoice_data.gross_total - invoice_data.net_total
        elif invoice_data.gross_total and invoice_data.vat_total and not invoice_data.net_total:
            invoice_data.net_total = invoice_data.gross_total - invoice_data.vat_total
        elif invoice_data.net_total and invoice_data.vat_total and not invoice_data.gross_total:
            invoice_data.gross_total = invoice_data.net_total + invoice_data.vat_total
        
        return invoice_data
    
    def _extract_parties(self, text: str, invoice_data: InvoiceData):
        """Ekstraktuje dane sprzedawcy i nabywcy"""
        
        # Wzorce dla sprzedawcy
        seller_section = re.search(
            r'(?:Sprzedawca|Wystawca|Dostawca)[:\s]*\n?(.*?)(?:Nabywca|Odbiorca|NIP|$)',
            text, 
            re.IGNORECASE | re.DOTALL
        )
        
        if seller_section:
            seller_text = seller_section.group(1)
            
            # Nazwa sprzedawcy - pierwsza linia
            lines = seller_text.strip().split('\n')
            if lines:
                invoice_data.seller_name = lines[0].strip()
            
            # NIP sprzedawcy
            nip_match = re.search(r'NIP\s*[:.]?\s*([PL]?\s*[\d\s\-]+)', seller_text, re.IGNORECASE)
            if nip_match:
                invoice_data.seller_nip = self._clean_nip(nip_match.group(1))
            
            # Adres
            address_match = re.search(r'(?:ul\.|ulica)?\s*([^\n]+\d+[^\n]*)', seller_text, re.IGNORECASE)
            if address_match:
                invoice_data.seller_address = address_match.group(1).strip()
            
            # Kod pocztowy i miasto
            postal_match = re.search(r'(\d{2}-\d{3})\s+([^\n]+)', seller_text)
            if postal_match:
                invoice_data.seller_postal_code = postal_match.group(1)
                invoice_data.seller_city = postal_match.group(2).strip()
        
        # Wzorce dla nabywcy
        buyer_section = re.search(
            r'(?:Nabywca|Odbiorca)[:\s]*\n?(.*?)(?:POZYCJE|Lp\.|L\.p\.|$)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        
        if buyer_section:
            buyer_text = buyer_section.group(1)
            
            # Nazwa nabywcy
            if '2vision' in buyer_text.lower() or '2Vision' in buyer_text:
                invoice_data.buyer_name = "2Vision Sp. z o.o."
                invoice_data.buyer_nip = "6751781780"
                invoice_data.buyer_address = "ul. Dąbska 20A/17, 31-572 Kraków"
            else:
                lines = buyer_text.strip().split('\n')
                if lines:
                    invoice_data.buyer_name = lines[0].strip()
                
                # NIP nabywcy
                nip_match = re.search(r'NIP\s*[:.]?\s*([PL]?\s*[\d\s\-]+)', buyer_text, re.IGNORECASE)
                if nip_match:
                    invoice_data.buyer_nip = self._clean_nip(nip_match.group(1))
    
    def _clean_nip(self, nip: str) -> str:
        """Czyści NIP z niepotrzebnych znaków"""
        cleaned = re.sub(r'[^\d]', '', nip)
        return cleaned
    
    def _parse_amount(self, amount_str: str) -> float:
        """Parsuje kwoty w formacie polskim"""
        amount_str = amount_str.strip()
        amount_str = re.sub(r'\s', '', amount_str)
        amount_str = amount_str.replace(',', '.')
        try:
            return float(re.sub(r'[^\d.]', '', amount_str))
        except:
            return 0.0
    
    def _extract_items_from_tables(self, tables: List) -> List[Dict]:
        """Ekstraktuje pozycje faktury z tabel"""
        items = []
        
        for table in tables:
            # Szukamy tabeli z pozycjami (zazwyczaj ma kolumny: Lp, Nazwa, Ilość, Cena, Wartość)
            if not table or len(table) < 2:
                continue
            
            # Sprawdź czy to tabela z pozycjami
            header = table[0] if table else []
            header_str = ' '.join(str(h) for h in header if h).lower()
            
            if any(word in header_str for word in ['nazwa', 'towar', 'usługa', 'opis', 'pozycja']):
                # To prawdopodobnie tabela z pozycjami
                for row in table[1:]:
                    if not row or all(not cell for cell in row):
                        continue
                    
                    item = {}
                    
                    # Próba identyfikacji kolumn
                    for i, cell in enumerate(row):
                        if not cell:
                            continue
                        
                        cell_str = str(cell).strip()
                        
                        # Nazwa towaru/usługi (zazwyczaj najdłuższa komórka)
                        if len(cell_str) > 10 and not re.match(r'^[\d\s,.-]+$', cell_str):
                            item['description'] = cell_str
                        
                        # Ilość (zazwyczaj małe liczby)
                        elif re.match(r'^\d+([.,]\d+)?\s*(szt|kg|l|m|h)?\.?$', cell_str, re.IGNORECASE):
                            item['quantity'] = self._parse_amount(cell_str)
                        
                        # Kwoty (większe liczby z przecinkami/kropkami)
                        elif re.match(r'^[\d\s]+[,.]?\d*$', cell_str):
                            amount = self._parse_amount(cell_str)
                            if amount > 0:
                                if 'unit_price' not in item:
                                    item['unit_price'] = amount
                                elif 'net_value' not in item:
                                    item['net_value'] = amount
                                elif 'gross_value' not in item:
                                    item['gross_value'] = amount
                    
                    if 'description' in item:
                        # Ustaw domyślne wartości jeśli brak
                        item.setdefault('quantity', 1)
                        item.setdefault('unit_price', 0)
                        item.setdefault('net_value', item['unit_price'] * item['quantity'])
                        item.setdefault('vat_rate', 23)
                        items.append(item)
        
        return items
