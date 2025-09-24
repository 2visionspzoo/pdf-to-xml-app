"""
Parser dla faktur Bolt
"""
from typing import Dict, List, Optional
from decimal import Decimal
import re
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_parser import BaseInvoiceParser, InvoiceItem

class BoltParser(BaseInvoiceParser):
    """Parser specyficzny dla faktur Bolt"""
    
    def __init__(self):
        super().__init__()
        self.company_patterns = ['Bolt Operations', 'Bolt Technology', 'Bolt Services']
    
    def parse(self, text: str, tables: List[List[List[str]]] = None) -> Dict:
        """Parsuje fakturę Bolt"""
        
        # Resetuj dane
        self.invoice_data = self._get_empty_invoice_data()
        
        # Ekstrakcja podstawowych danych
        self._extract_basic_info(text)
        
        # Ekstrakcja danych stron
        self._extract_bolt_parties(text)
        
        # Ekstrakcja pozycji
        if tables:
            self._extract_items_from_tables(tables)
        else:
            self._extract_bolt_items(text)
        
        # Oblicz podsumowanie
        self._calculate_summary()
        
        return self.invoice_data
    
    def _get_empty_invoice_data(self) -> Dict:
        """Zwraca pustą strukturę danych faktury"""
        return {
            'invoice_number': '',
            'invoice_date': '',
            'sale_date': '',
            'payment_date': '',
            'payment_method': 'karta',  # Bolt zazwyczaj karta
            'seller': {
                'name': '',
                'nip': '',
                'address': '',
                'city': '',
                'postal_code': '',
                'country': ''
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
    
    def _extract_basic_info(self, text: str):
        """Ekstrahuje podstawowe informacje faktury Bolt"""
        # Numer faktury - często w formacie RIDE-xxxx
        patterns = [
            r'(?:Invoice|Faktura)\s*(?:number|nr|Nr)?\s*[:\s]*([A-Z0-9\-]+)',
            r'RIDE[-\s]([A-Z0-9]+)',
            r'Trip\s*ID[:\s]*([A-Z0-9\-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                self.invoice_data['invoice_number'] = match.group(1)
                break
        
        # Data - Bolt używa różnych formatów
        date_patterns = [
            r'Date[:\s]*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4})',
            r'(\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2})',
            r'(\d{1,2}\s+\w+\s+\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                self.invoice_data['invoice_date'] = self.normalize_date(match.group(1))
                self.invoice_data['sale_date'] = self.invoice_data['invoice_date']
                break
    
    def _extract_bolt_parties(self, text: str):
        """Ekstrahuje dane stron dla Bolt"""
        # Bolt jako sprzedawca
        for pattern in self.company_patterns:
            if pattern in text:
                self.invoice_data['seller']['name'] = pattern
                break
        
        # VAT ID dla Bolt (często estoński)
        vat_match = re.search(r'VAT\s*(?:ID|number)[:\s]*([A-Z]{2}\d+)', text, re.IGNORECASE)
        if vat_match:
            self.invoice_data['seller']['nip'] = vat_match.group(1)
        
        # Adres Bolt (często Estonia)
        if 'Estonia' in text or 'Tallinn' in text:
            self.invoice_data['seller']['country'] = 'Estonia'
            city_match = re.search(r'Tallinn[,\s]+(\d{5})', text)
            if city_match:
                self.invoice_data['seller']['city'] = 'Tallinn'
                self.invoice_data['seller']['postal_code'] = city_match.group(1)
        
        # Nabywca - szukamy polskiej firmy
        self._extract_buyer_from_text(text)
    
    def _extract_buyer_from_text(self, text: str):
        """Ekstrahuje dane nabywcy"""
        buyer_section = re.search(
            r'(?:Customer|Client|Nabywca|Bill to)[:\s]*(.*?)(?:Items|Services|Trip|$)',
            text, 
            re.IGNORECASE | re.DOTALL
        )
        
        if buyer_section:
            buyer_text = buyer_section.group(1)
            
            # Nazwa firmy
            lines = buyer_text.strip().split('\n')
            if lines:
                self.invoice_data['buyer']['name'] = lines[0].strip()
            
            # NIP
            nip = self.extract_nip(buyer_text)
            if nip:
                self.invoice_data['buyer']['nip'] = nip
    
    def _extract_bolt_items(self, text: str):
        """Ekstrahuje pozycje z faktury Bolt"""
        # Bolt ma zazwyczaj jedną pozycję - przejazd
        item = InvoiceItem()
        
        # Opis usługi
        service_patterns = [
            r'(?:Ride|Trip|Przejazd)\s+(?:from|z)\s+(.*?)(?:to|do)\s+(.*?)(?:\n|$)',
            r'(?:Service|Usługa)[:\s]*(.*?)(?:\n|$)'
        ]
        
        for pattern in service_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if match.lastindex == 2:
                    item.name = f"Przejazd: {match.group(1)} - {match.group(2)}"
                else:
                    item.name = match.group(1)
                break
        
        if not item.name:
            item.name = "Usługa transportowa Bolt"
        
        item.quantity = Decimal('1')
        item.unit = 'usł.'
        
        # Kwoty
        amount_patterns = [
            (r'(?:Total|Razem|Amount)[:\s]*([\d.,]+)', 'gross'),
            (r'(?:Net|Netto)[:\s]*([\d.,]+)', 'net'),
            (r'(?:VAT|Tax)[:\s]*([\d.,]+)', 'vat')
        ]
        
        amounts = {}
        for pattern, amount_type in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amounts[amount_type] = self.parse_amount(match.group(1))
        
        # Przypisz kwoty
        if 'gross' in amounts:
            item.gross_amount = amounts['gross']
        if 'net' in amounts:
            item.net_amount = amounts['net']
        if 'vat' in amounts:
            item.vat_amount = amounts['vat']
        
        # Oblicz brakujące wartości
        if item.gross_amount > 0 and item.net_amount > 0:
            item.vat_amount = item.gross_amount - item.net_amount
            if item.net_amount > 0:
                vat_rate = (item.vat_amount / item.net_amount * 100)
                item.vat_rate = f"{int(vat_rate)}%"
        elif item.gross_amount > 0:
            # Zakładamy 23% VAT
            item.vat_rate = "23%"
            item.net_amount = item.gross_amount / Decimal('1.23')
            item.vat_amount = item.gross_amount - item.net_amount
        
        item.unit_price_net = item.net_amount
        
        if item.gross_amount > 0:
            self.invoice_data['items'].append(item.to_dict())
    
    def _extract_items_from_tables(self, tables: List[List[List[str]]]):
        """Ekstrahuje pozycje z tabel"""
        for table in tables:
            if self._is_items_table(table):
                for row in table[1:]:
                    item = self._parse_item_row(row)
                    if item:
                        self.invoice_data['items'].append(item.to_dict())
    
    def _is_items_table(self, table: List[List[str]]) -> bool:
        """Sprawdza czy tabela zawiera pozycje"""
        if not table or len(table) < 2:
            return False
        
        header = ' '.join(str(cell).lower() for cell in table[0])
        keywords = ['service', 'ride', 'amount', 'total', 'vat']
        
        matches = sum(1 for keyword in keywords if keyword in header)
        return matches >= 2
    
    def _parse_item_row(self, row: List[str]) -> Optional[InvoiceItem]:
        """Parsuje wiersz tabeli"""
        if len(row) < 2:
            return None
        
        item = InvoiceItem()
        
        # Pierwsza kolumna to zazwyczaj opis
        item.name = row[0].strip() if row[0] else "Usługa Bolt"
        item.quantity = Decimal('1')
        item.unit = 'usł.'
        
        # Szukaj kwot w pozostałych kolumnach
        for cell in row[1:]:
            if cell:
                amount = self.parse_amount(cell)
                if amount > 0:
                    if item.gross_amount == 0:
                        item.gross_amount = amount
                    elif item.net_amount == 0:
                        item.net_amount = amount
                    elif item.vat_amount == 0:
                        item.vat_amount = amount
        
        # Oblicz brakujące wartości
        if item.gross_amount > 0 and item.net_amount == 0:
            item.net_amount = item.gross_amount / Decimal('1.23')
            item.vat_amount = item.gross_amount - item.net_amount
            item.vat_rate = "23%"
        
        if item.gross_amount > 0:
            return item
        
        return None
    
    def _calculate_summary(self):
        """Oblicza podsumowanie faktury"""
        net_total = Decimal('0')
        vat_total = Decimal('0')
        gross_total = Decimal('0')
        vat_breakdown = {}
        
        for item in self.invoice_data['items']:
            net = Decimal(item.get('net_amount', 0))
            vat = Decimal(item.get('vat_amount', 0))
            gross = Decimal(item.get('gross_amount', 0))
            vat_rate = item.get('vat_rate', '23%')
            
            net_total += net
            vat_total += vat
            gross_total += gross
            
            if vat_rate not in vat_breakdown:
                vat_breakdown[vat_rate] = {
                    'net': Decimal('0'),
                    'vat': Decimal('0'),
                    'gross': Decimal('0')
                }
            
            vat_breakdown[vat_rate]['net'] += net
            vat_breakdown[vat_rate]['vat'] += vat
            vat_breakdown[vat_rate]['gross'] += gross
        
        # Konwersja do stringów
        self.invoice_data['summary']['net_total'] = str(net_total)
        self.invoice_data['summary']['vat_total'] = str(vat_total)
        self.invoice_data['summary']['gross_total'] = str(gross_total)
        
        # Konwersja vat_breakdown
        for rate, values in vat_breakdown.items():
            vat_breakdown[rate] = {
                'net': str(values['net']),
                'vat': str(values['vat']),
                'gross': str(values['gross'])
            }
        
        self.invoice_data['summary']['vat_breakdown'] = vat_breakdown
