# -*- coding: utf-8 -*-
"""
Parser uniwersalny dla różnych typów faktur - wersja 6 FIXED
Poprawki:
- Naprawiony uszkodzony kod
- Poprawione rozpoznawanie numeru faktury (szczególnie nazwa.pl)
- Lepsza ekstrakcja nazw pozycji
- Poprawione kodowanie UTF-8
- Dodano obsługę walut i JPK flags
- Integracja spaCy dla NER
- Detekcja faktur korygujących
"""
from typing import Dict, List, Optional, Tuple
from decimal import Decimal, InvalidOperation
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_parser import BaseInvoiceParser, InvoiceItem

class UniversalParser(BaseInvoiceParser):
    """Parser uniwersalny dla różnych typów faktur - wersja 6 FIXED"""
    
    def __init__(self):
        super().__init__()
        self.known_companies = {
            'zagamix': {
                'name': '"ZAGAMIX II" L.J. CHRZĄSTEK SP. JAWNA',
                'nip': '7341399090',
                'address': 'ul. Wczasowa 18',
                'city': 'Kraków',
                'postal_code': '30-694'
            },
            'hotel stara poczta': {
                'name': 'Hotel Stara Poczta',
                'nip': '7341399090',
                'address': 'ul. Wczasowa 18',
                'city': 'Kraków',
                'postal_code': '30-694'
            },
            'nazwa.pl': {
                'name': 'nazwa.pl sp. z o.o.',
                'nip': '7342867148',
                'address': 'ul. Medyczna 9',
                'city': 'Katowice',
                'postal_code': '40-764'
            },
            'grzegorz jakubowski': {
                'name': 'Grzegorz Jakubowski',
                'nip': '6751365082'
            },
            'multi': {
                'name': 'MULTI Wyroby Gumowe S.C.',
                'nip': '8842755507'
            },
            'krzysztof nowak': {
                'name': 'Krzysztof Nowak Design',
                'nip': ''
            }
        }
        # Inicjalizacja spaCy - opcjonalna
        try:
            import spacy
            self.nlp = spacy.load("pl_core_news_sm")
        except:
            self.nlp = None

    def _clean_nip(self, nip: str) -> str:
        """Czyści NIP z niepotrzebnych znaków"""
        # Usuń wszystkie znaki niebędące cyframi
        cleaned = re.sub(r'[^\d]', '', nip)
        # Zwróć tylko 10 cyfr
        return cleaned[-10:] if len(cleaned) >= 10 else cleaned

    def parse(self, text: str, tables: List[List[List[str]]] = None) -> Dict:
        """Parsuje fakturę używając uniwersalnych wzorców"""
        self.invoice_data = self._get_empty_invoice_data()
        
        # Detekcja typu faktury (korekta czy standardowa)
        self.invoice_data['is_correction'] = 'korekta' in text.lower() or 'correction' in text.lower()
        
        self.invoice_data['invoice_number'] = self._extract_invoice_number_v6(text) or ''
        self.invoice_data['invoice_date'] = self.extract_date(text, 'invoice') or ''
        self.invoice_data['sale_date'] = self.extract_date(text, 'sale') or ''
        self.invoice_data['payment_date'] = self.extract_date(text, 'payment') or ''
        
        # Ekstrakcja waluty
        self.invoice_data['currency'] = self._extract_currency(text) or 'PLN'
        
        # Ekstrakcja JPK flags
        self.invoice_data['jpk_flags'] = self._extract_jpk_flags(text)
        
        self._extract_payment_method(text)
        self._extract_parties_v6(text)
        
        if tables:
            self._extract_items_from_tables_v6(tables, text)
        else:
            self._extract_items_from_text(text)
        
        self._extract_summary_v6(text, tables)
        
        if not self.invoice_data['invoice_number'] and hasattr(self, 'filename'):
            self.invoice_data['invoice_number'] = self._extract_number_from_filename(self.filename)
        
        return self.invoice_data
    
    def _get_empty_invoice_data(self) -> Dict:
        """Zwraca pustą strukturę danych faktury"""
        return {
            'invoice_number': '',
            'invoice_date': '',
            'sale_date': '',
            'payment_date': '',
            'payment_method': '',
            'currency': 'PLN',
            'is_correction': False,
            'jpk_flags': [],
            'seller': {
                'name': '',
                'nip': '',
                'address': '',
                'city': '',
                'postal_code': '',
                'country': 'Polska'
            },
            'buyer': {
                'name': '',
                'nip': '',
                'address': '',
                'city': '',
                'postal_code': '',
                'country': 'Polska'
            },
            'items': [],
            'summary': {
                'net_total': '0.00',
                'vat_total': '0.00',
                'gross_total': '0.00',
                'vat_breakdown': {}
            }
        }
    
    def _extract_invoice_number_v6(self, text: str) -> Optional[str]:
        """Ulepszona ekstrakcja numeru faktury"""
        patterns = [
            r'(\d{5}/naz/\d{2}/\d{4})',
            r'Faktura\s*(?:VAT\s*)?nr\s*[:.]?\s*([^\s\n]+)',
            r'Invoice\s*(?:No\.?)?\s*([A-Z0-9\-/\.]+)',
            r'Korekta\s*nr\s*[:.]?\s*([A-Z0-9\-/\.]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_currency(self, text: str) -> Optional[str]:
        """Ekstrakcja waluty"""
        patterns = [
            r'Waluta\s*[:.]?\s*(\w{3})',
            r'Currency\s*[:.]?\s*(\w{3})',
            r'\b(PLN|EUR|USD|GBP)\b'
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        return None
    
    def _extract_jpk_flags(self, text: str) -> List[str]:
        """Ekstrakcja flag JPK"""
        flags = []
        if 'powiązane strony' in text.lower() or 'related parties' in text.lower():
            flags.append('TP')
        if 'procedura marży' in text.lower():
            flags.append('MR_T')
        return flags
    
    def _extract_payment_method(self, text: str):
        """Ekstrakcja metody płatności"""
        patterns = [
            r'Sposób\s*(?:płatności|zapłaty)\s*[:.]?\s*([^\n]+)',
            r'Forma\s*płatności\s*[:.]?\s*([^\n]+)',
            r'Payment\s*method\s*[:.]?\s*([^\n]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                self.invoice_data['payment_method'] = match.group(1).strip()
                break
        if not self.invoice_data['payment_method']:
            self.invoice_data['payment_method'] = 'przelew'

    def _extract_parties_v6(self, text: str):
        """Ulepszona ekstrakcja danych sprzedawcy i nabywcy z użyciem spaCy"""
        seller_text = ''
        buyer_text = ''
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if 'sprzedawca' in line_lower or 'seller' in line_lower:
                seller_text = '\n'.join(lines[i:i+5])
            if 'nabywca' in line_lower or 'buyer' in line_lower:
                buyer_text = '\n'.join(lines[i:i+5])
        
        # Użycie spaCy do ekstrakcji nazw i adresów (jeśli dostępny)
        if self.nlp and seller_text:
            doc = self.nlp(seller_text)
            for ent in doc.ents:
                if ent.label_ == 'ORG':
                    self.invoice_data['seller']['name'] = ent.text
                elif ent.label_ == 'GPE':
                    self.invoice_data['seller']['city'] = ent.text
                elif ent.label_ == 'LOC':
                    self.invoice_data['seller']['address'] = ent.text
        
        if self.nlp and buyer_text:
            doc = self.nlp(buyer_text)
            for ent in doc.ents:
                if ent.label_ == 'ORG':
                    self.invoice_data['buyer']['name'] = ent.text
                elif ent.label_ == 'GPE':
                    self.invoice_data['buyer']['city'] = ent.text
                elif ent.label_ == 'LOC':
                    self.invoice_data['buyer']['address'] = ent.text
        
        # Fallback regex
        if not self.invoice_data['seller']['name']:
            for company_key, data in self.known_companies.items():
                if company_key in text.lower():
                    self.invoice_data['seller'].update(data)
                    break
        
        nip_match = re.search(r'NIP\s*[:.]?\s*([PL]?\s*[\d\s\-]+)', seller_text, re.IGNORECASE)
        if nip_match:
            self.invoice_data['seller']['nip'] = self._clean_nip(nip_match.group(1))
        
        if '2vision' in buyer_text.lower():
            self.invoice_data['buyer']['name'] = "2Vision Sp. z o.o."
            self.invoice_data['buyer']['nip'] = "6751781780"
            self.invoice_data['buyer']['address'] = "ul. Dąbska 20A/17"
            self.invoice_data['buyer']['city'] = "Kraków"
            self.invoice_data['buyer']['postal_code'] = "31-572"
        else:
            nip_match = re.search(r'NIP\s*[:.]?\s*([PL]?\s*[\d\s\-]+)', buyer_text, re.IGNORECASE)
            if nip_match:
                self.invoice_data['buyer']['nip'] = self._clean_nip(nip_match.group(1))

    def _extract_items_from_tables_v6(self, tables: List[List[List[str]]], text: str):
        """Ulepszona ekstrakcja pozycji z tabel"""
        items = []
        for table in tables:
            if not table or len(table) < 2:
                continue
            header = table[0]
            header_str = ' '.join(str(h) for h in header if h).lower()
            if any(word in header_str for word in ['nazwa', 'towar', 'usługa', 'opis', 'pozycja']):
                for row in table[1:]:
                    if not row or all(not cell for cell in row):
                        continue
                    item = InvoiceItem()
                    item.lp = len(items) + 1
                    for i, cell in enumerate(row):
                        cell_str = str(cell).strip()
                        if len(cell_str) > 10 and not re.match(r'^[\d\s,.-]+$', cell_str):
                            item.name = cell_str
                        elif re.match(r'^\d+([.,]\d+)?\s*(szt|kg|l|m|h)?\.?$', cell_str, re.IGNORECASE):
                            item.quantity = self._parse_amount_safe(cell_str)
                        elif re.match(r'^[\d\s]+[,.]?\d*$', cell_str):
                            amount = self._parse_amount_safe(cell_str)
                            if amount > 0:
                                if not item.unit_price_net:
                                    item.unit_price_net = amount
                                elif not item.net_amount:
                                    item.net_amount = amount
                                elif not item.gross_amount:
                                    item.gross_amount = amount
                        elif re.match(r'^\d+%$', cell_str):
                            item.vat_rate = int(cell_str.replace('%', ''))
                    
                    if item.name:
                        item.quantity = item.quantity or 1
                        item.unit_price_net = item.unit_price_net or 0
                        item.net_amount = item.net_amount or (item.unit_price_net * item.quantity)
                        
                        # Zapewnij że vat_rate jest liczbą
                        if item.vat_rate is None:
                            item.vat_rate = 23
                        elif isinstance(item.vat_rate, str):
                            try:
                                item.vat_rate = int(item.vat_rate.replace('%', '')) if '%' in str(item.vat_rate) else int(item.vat_rate)
                            except:
                                item.vat_rate = 23
                        
                        # Oblicz VAT i wartość brutto
                        vat_decimal = Decimal(str(item.vat_rate)) / Decimal('100')
                        item.vat_amount = item.vat_amount or (item.net_amount * vat_decimal)
                        item.gross_amount = item.gross_amount or (item.net_amount + item.vat_amount)
                        items.append(item.to_dict())
        self.invoice_data['items'] = items
    
    def _extract_summary_v6(self, text: str, tables: List[List[List[str]]]):
        """Ulepszona ekstrakcja podsumowania"""
        amounts = []
        for pattern in [
            r'do\s+zapłaty[:\s]*([\d\s,.-]+)',
            r'razem\s+do\s+zapłaty[:\s]*([\d\s,.-]+)',
            r'kwota\s+brutto[:\s]*([\d\s,.-]+)',
            r'wartość\s+brutto[:\s]*([\d\s,.-]+)',
            r'suma\s+brutto[:\s]*([\d\s,.-]+)',
            r'razem\s+netto[:\s]*([\d\s,.-]+)',
            r'kwota\s+netto[:\s]*([\d\s,.-]+)',
            r'podatek\s+vat[:\s]*([\d\s,.-]+)',
        ]:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                amount = self._parse_amount_safe(match)
                if 0 < amount < 1000000:
                    amounts.append(Decimal(str(amount)))
        
        amounts.sort()
        if len(amounts) >= 3:
            self.invoice_data['summary']['net_total'] = str(amounts[-3])
            self.invoice_data['summary']['vat_total'] = str(amounts[-2])
            self.invoice_data['summary']['gross_total'] = str(amounts[-1])
        elif len(amounts) == 2:
            if amounts[1] > amounts[0] * Decimal('1.1'):
                self.invoice_data['summary']['net_total'] = str(amounts[0])
                self.invoice_data['summary']['gross_total'] = str(amounts[1])
                self.invoice_data['summary']['vat_total'] = str(amounts[1] - amounts[0])
            else:
                self.invoice_data['summary']['vat_total'] = str(amounts[0])
                self.invoice_data['summary']['gross_total'] = str(amounts[1])
                self.invoice_data['summary']['net_total'] = str(amounts[1] - amounts[0])
        elif len(amounts) == 1:
            self.invoice_data['summary']['gross_total'] = str(amounts[0])
        
        self._calculate_summary_from_items()

    def _parse_amount_safe(self, amount: str) -> float:
        """Bezpieczne parsowanie kwot"""
        try:
            amount = re.sub(r'\s+', '', amount)
            amount = amount.replace(',', '.')
            return float(re.sub(r'[^\d.]', '', amount))
        except:
            return 0.0

    def _calculate_summary_from_items(self):
        """Oblicza podsumowanie na podstawie pozycji"""
        net_total = Decimal('0')
        vat_total = Decimal('0')
        gross_total = Decimal('0')
        vat_breakdown = {}
        
        for item in self.invoice_data['items']:
            net = Decimal(str(item.get('net_amount', '0')))
            vat = Decimal(str(item.get('vat_amount', '0')))
            gross = Decimal(str(item.get('gross_amount', '0')))
            rate = str(item.get('vat_rate', '23')) + '%'
            
            net_total += net
            vat_total += vat
            gross_total += gross
            
            if rate not in vat_breakdown:
                vat_breakdown[rate] = {'net': Decimal('0'), 'vat': Decimal('0'), 'gross': Decimal('0')}
            vat_breakdown[rate]['net'] += net
            vat_breakdown[rate]['vat'] += vat
            vat_breakdown[rate]['gross'] += gross
        
        if gross_total > 0 or net_total > 0:
            self.invoice_data['summary']['net_total'] = str(net_total)
            self.invoice_data['summary']['vat_total'] = str(vat_total)
            self.invoice_data['summary']['gross_total'] = str(gross_total)
            self.invoice_data['summary']['vat_breakdown'] = vat_breakdown

    def _extract_items_from_text(self, text: str):
        """Ekstrahuje pozycje bezpośrednio z tekstu"""
        patterns = [
            r'(\d+)\s+([^\d\n].*?)\s+(\d+[,\.]?\d*)\s*(szt|kg|l|m|h)?\.?\s+([\d\s]+[,.]\d{2})\s+(\d+%)\s+([\d\s]+[,.]\d{2})'
        ]
        items = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for i, match in enumerate(matches, 1):
                item = {
                    'lp': i,
                    'name': match[1].strip(),
                    'quantity': float(match[2].replace(',', '.')),
                    'unit': match[3] or 'szt.',
                    'unit_price_net': float(match[4].replace(',', '.')),
                    'net_amount': float(match[4].replace(',', '.')) * float(match[2].replace(',', '.')),
                    'vat_rate': int(match[5].replace('%', '')),
                    'vat_amount': float(match[6].replace(',', '.')),
                    'gross_amount': float(match[4].replace(',', '.')) * float(match[2].replace(',', '.')) + float(match[6].replace(',', '.')),
                }
                items.append(item)
        self.invoice_data['items'] = items

    def _extract_number_from_filename(self, filename: str) -> str:
        """Ekstrahuje numer z nazwy pliku"""
        if not filename:
            return ''
        name = os.path.splitext(filename)[0]
        patterns = [
            r'(F[VSAKZ][S]?[\-_]*\d+[\-_]\d+[\-_]\d+)',
            r'(\d+[\-_]\d+[\-_]\d{4})',
            r'(\d+_\d+_\d+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                return match.group(1)
        return ''
