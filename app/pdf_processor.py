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
import warnings

# Filtruj ostrzeżenia z pdfplumber o brakującym module dla kolorów
warnings.filterwarnings('ignore', message='.*Cannot import pdfplumber.*', category=UserWarning)
warnings.filterwarnings('ignore', message='.*Error importing pdfplumber.*', category=UserWarning)

# Dodanie ścieżki do parserów
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_config
from invoice_detector import InvoiceDetector, InvoiceType
from parsers.atut_parser import ATUTParser
from parsers.bolt_parser import BoltParser
from parsers.universal_parser_v6 import UniversalParser

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
        self.invoice_keywords = [
            'faktura', 'invoice', 'vat', 'sprzedawca', 'nabywca',
            'nip', 'razem', 'suma', 'brutto', 'netto',
            'do zapłaty', 'wartość', 'kwota', 'pozycje'
        ]
        self.min_keywords_count = 3
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

    def _extract_with_ocr(self, pdf_path: str) -> str:
        """Ekstraktuje tekst z PDF używając OCR z optymalizacją dla tabel"""
        try:
            images = convert_from_path(pdf_path)
            text = ""
            for image in images:
                # Optymalizacja Tesseract: PSM 6 dla tabel, OEM 3 dla LSTM, obsługa języka polskiego i angielskiego
                page_text = pytesseract.image_to_string(
                    image,
                    lang='pol+eng',
                    config='--psm 6 --oem 3'
                )
                text += page_text + "\n"
            return text
        except Exception as e:
            logger.error(f"Błąd OCR: {e}")
            return ""

    def _is_invoice(self, text: str) -> bool:
        """Sprawdza, czy tekst zawiera wystarczającą liczbę słów kluczowych"""
        text_lower = text.lower()
        keyword_count = sum(1 for keyword in self.invoice_keywords if keyword in text_lower)
        return keyword_count >= self.min_keywords_count

    def _detect_invoice_type(self, text: str) -> str:
        """Rozpoznaje typ faktury na podstawie słów kluczowych"""
        text_lower = text.lower()
        for inv_type, keywords in self.invoice_types.items():
            if any(keyword in text_lower for keyword in keywords):
                return inv_type
        return 'UNIVERSAL'

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
            if not table or len(table) < 2:
                continue

            header = table[0] if table else []
            header_str = ' '.join(str(h) for h in header if h).lower()

            if any(word in header_str for word in ['nazwa', 'towar', 'usługa', 'opis', 'pozycja']):
                for row in table[1:]:
                    if not row or all(not cell for cell in row):
                        continue

                    item = {}
                    for i, cell in enumerate(row):
                        if not cell:
                            continue

                        cell_str = str(cell).strip()

                        if len(cell_str) > 10 and not re.match(r'^[\d\s,.-]+$', cell_str):
                            item['description'] = cell_str
                        elif re.match(r'^\d+([.,]\d+)?\s*(szt|kg|l|m|h)?\.?$', cell_str, re.IGNORECASE):
                            item['quantity'] = self._parse_amount(cell_str)
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
                        item.setdefault('quantity', 1)
                        item.setdefault('unit_price', 0)
                        item.setdefault('net_value', item['unit_price'] * item['quantity'])
                        item.setdefault('vat_rate', 23)
                        items.append(item)

        return items

    def extract_text_and_tables(self, pdf_path: str):
        """Ekstraktuje tekst i tabele z PDF"""
        text = ""
        all_tables = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

                    tables = page.extract_tables()
                    if tables:
                        all_tables.extend(tables)

            if len(text.strip()) < 100:
                logger.info("Używam OCR do ekstrakcji...")
                text = self._extract_with_ocr(pdf_path)

            return text, all_tables

        except Exception as e:
            logger.error(f"Błąd ekstrakcji tekstu i tabel: {e}")
            return "", []

    def extract_from_pdf(self, pdf_path: str) -> InvoiceData:
        """Główna metoda ekstrakcji danych z PDF"""
        text, tables = self.extract_text_and_tables(pdf_path)
        if not self._is_invoice(text):
            logger.warning(f"Plik {pdf_path} nie zawiera faktury")
            return InvoiceData()

        invoice_type = self._detect_invoice_type(text)
        logger.info(f"Wykryto typ faktury: {invoice_type}")

        if self.parser_type == 'auto':
            parser_type = invoice_type.lower()
        else:
            parser_type = self.parser_type

        if parser_type == 'atut':
            parser = ATUTParser()
        elif parser_type == 'bolt':
            parser = BoltParser()
        else:
            parser = UniversalParser()

        parser.filename = os.path.basename(pdf_path)
        invoice_data = parser.parse(text, tables)

        return InvoiceData(
            invoice_number=invoice_data.get('invoice_number'),
            invoice_date=invoice_data.get('invoice_date'),
            sale_date=invoice_data.get('sale_date'),
            seller_name=invoice_data.get('seller', {}).get('name'),
            seller_nip=invoice_data.get('seller', {}).get('nip'),
            seller_address=invoice_data.get('seller', {}).get('address'),
            seller_city=invoice_data.get('seller', {}).get('city'),
            seller_postal_code=invoice_data.get('seller', {}).get('postal_code'),
            buyer_name=invoice_data.get('buyer', {}).get('name'),
            buyer_nip=invoice_data.get('buyer', {}).get('nip'),
            buyer_address=invoice_data.get('buyer', {}).get('address'),
            items=invoice_data.get('items', []),
            net_total=float(invoice_data.get('summary', {}).get('net_total', 0)),
            vat_total=float(invoice_data.get('summary', {}).get('vat_total', 0)),
            gross_total=float(invoice_data.get('summary', {}).get('gross_total', 0)),
            payment_method=invoice_data.get('payment_method'),
            payment_date=invoice_data.get('payment_date')
        )