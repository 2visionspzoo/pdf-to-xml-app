"""
Parser dla faktur ATUT Sp. z o.o.
"""
from typing import Dict, List, Optional
from decimal import Decimal
import re
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_parser import BaseInvoiceParser, InvoiceItem

class ATUTParser(BaseInvoiceParser):
    """Parser specyficzny dla faktur ATUT"""
    
    def __init__(self):
        super().__init__()
        self.company_nip = '5252374228'
        self.company_name = 'ATUT Sp. z o.o.'
    
    def parse(self, text: str, tables: List[List[List[str]]] = None) -> Dict:
        """Parsuje fakturę ATUT"""
        
        # Wyczyść dane
        self.invoice_data = {
            'invoice_number': '',
            'invoice_date': '',
            'sale_date': '',
            'payment_date': '',
            'payment_method': '',
            'seller': {
                'name': self.company_name,
                'nip': self.company_nip,
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
        
        # Ekstrakcja podstawowych danych
        self.invoice_data['invoice_number'] = self.extract_invoice_number(text) or ''
        self.invoice_data['invoice_date'] = self.extract_date(text, 'invoice') or ''
        self.invoice_data['sale_date'] = self.extract_date(text, 'sale') or ''
        self.invoice_data['payment_date'] = self.extract_date(text, 'payment') or ''
        
        # Ekstrakcja danych sprzedawcy (ATUT)
        self._extract_seller_data(text)
        
        # Ekstrakcja danych nabywcy
        self._extract_buyer_data(text)
        
        # Ekstrakcja pozycji faktury
        if tables:
            self._extract_items_from_tables(tables)
        else:
            self._extract_items_from_text(text)
        
        # Oblicz podsumowanie
        self._calculate_summary()
        
        return self.invoice_data
    
    def _extract_seller_data(self, text: str):
        """Ekstrahuje dane sprzedawcy ATUT"""
        # Szukamy bloku ze sprzedawcą
        seller_patterns = [
            r'Sprzedawca[:\s]*(.*?)(?:Nabywca|Odbiorca|$)',
            r'SPRZEDAWCA[:\s]*(.*?)(?:NABYWCA|ODBIORCA|$)',
            r'Wystawca[:\s]*(.*?)(?:Nabywca|Odbiorca|$)'
        ]
        
        for pattern in seller_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                seller_text = match.group(1)
                
                # Szukamy adresu ATUT
                address_match = re.search(r'ul\.?\s+([^,\n]+)', seller_text, re.IGNORECASE)
                if address_match:
                    self.invoice_data['seller']['address'] = address_match.group(1).strip()
                
                # Kod pocztowy i miasto
                postal_match = re.search(r'(\d{2}[-\s]\d{3})\s+([A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż\s]+)', seller_text)
                if postal_match:
                    self.invoice_data['seller']['postal_code'] = postal_match.group(1).replace(' ', '-')
                    self.invoice_data['seller']['city'] = postal_match.group(2).strip()
                
                break
    
    def _extract_buyer_data(self, text: str):
        """Ekstrahuje dane nabywcy"""
        # Szukamy bloku z nabywcą
        buyer_patterns = [
            r'Nabywca[:\s]*(.*?)(?:Pozycje|Lp\.|Nr\.|$)',
            r'NABYWCA[:\s]*(.*?)(?:POZYCJE|LP\.|NR\.|$)',
            r'Odbiorca[:\s]*(.*?)(?:Pozycje|Lp\.|Nr\.|$)'
        ]
        
        for pattern in buyer_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                buyer_text = match.group(1)
                lines = buyer_text.strip().split('\n')
                
                if lines:
                    # Pierwsza linia to zazwyczaj nazwa
                    self.invoice_data['buyer']['name'] = lines[0].strip()
                
                # NIP
                nip = self.extract_nip(buyer_text)
                if nip:
                    self.invoice_data['buyer']['nip'] = nip
                
                # Adres
                address_match = re.search(r'ul\.?\s+([^,\n]+)', buyer_text, re.IGNORECASE)
                if address_match:
                    self.invoice_data['buyer']['address'] = address_match.group(1).strip()
                
                # Kod pocztowy i miasto
                postal_match = re.search(r'(\d{2}[-\s]\d{3})\s+([A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż\s]+)', buyer_text)
                if postal_match:
                    self.invoice_data['buyer']['postal_code'] = postal_match.group(1).replace(' ', '-')
                    self.invoice_data['buyer']['city'] = postal_match.group(2).strip()
                
                break
    
    def _extract_items_from_tables(self, tables: List[List[List[str]]]):
        """Ekstrahuje pozycje z tabel"""
        for table in tables:
            # Sprawdzamy czy to tabela z pozycjami
            if self._is_items_table(table):
                for row in table[1:]:  # Pomijamy nagłówek
                    item = self._parse_item_row(row)
                    if item:
                        self.invoice_data['items'].append(item.to_dict())
    
    def _is_items_table(self, table: List[List[str]]) -> bool:
        """Sprawdza czy tabela zawiera pozycje faktury"""
        if not table:
            return False
        
        header = ' '.join(str(cell).lower() for cell in table[0])
        keywords = ['lp', 'nazwa', 'ilość', 'cena', 'vat', 'netto', 'brutto']
        
        matches = sum(1 for keyword in keywords if keyword in header)
        return matches >= 3
    
    def _parse_item_row(self, row: List[str]) -> Optional[InvoiceItem]:
        """Parsuje wiersz tabeli do InvoiceItem"""
        if len(row) < 5:
            return None
        
        item = InvoiceItem()
        
        try:
            # Zakładamy standardową kolejność kolumn dla ATUT
            # Lp | Nazwa | Ilość | Jedn. | Cena netto | Wartość netto | VAT% | VAT | Wartość brutto
            
            col_idx = 0
            
            # Lp
            if col_idx < len(row):
                try:
                    item.lp = int(row[col_idx])
                    col_idx += 1
                except:
                    col_idx += 1
            
            # Nazwa
            if col_idx < len(row):
                item.name = row[col_idx].strip()
                col_idx += 1
            
            # Ilość
            if col_idx < len(row):
                item.quantity = self.parse_amount(row[col_idx])
                col_idx += 1
            
            # Jednostka
            if col_idx < len(row):
                item.unit = row[col_idx].strip()
                col_idx += 1
            
            # Cena jednostkowa netto
            if col_idx < len(row):
                item.unit_price_net = self.parse_amount(row[col_idx])
                col_idx += 1
            
            # Wartość netto
            if col_idx < len(row):
                item.net_amount = self.parse_amount(row[col_idx])
                col_idx += 1
            
            # Stawka VAT
            if col_idx < len(row):
                item.vat_rate = self.extract_vat_rate(row[col_idx])
                col_idx += 1
            
            # Kwota VAT
            if col_idx < len(row):
                item.vat_amount = self.parse_amount(row[col_idx])
                col_idx += 1
            
            # Wartość brutto
            if col_idx < len(row):
                item.gross_amount = self.parse_amount(row[col_idx])
            
            # Walidacja - czy mamy wystarczające dane
            if item.name and (item.net_amount > 0 or item.gross_amount > 0):
                return item
            
        except Exception as e:
            print(f"Błąd parsowania wiersza: {e}")
        
        return None
    
    def _extract_items_from_text(self, text: str):
        """Ekstrahuje pozycje bezpośrednio z tekstu (fallback)"""
        # Wzorzec dla pozycji ATUT
        item_pattern = r'(\d+)\s+(.*?)\s+(\d+[,.]?\d*)\s+(\w+)\s+(\d+[,.]?\d*)\s+(\d+[,.]?\d*)\s+(\d+)%?\s+(\d+[,.]?\d*)\s+(\d+[,.]?\d*)'
        
        matches = re.finditer(item_pattern, text)
        for match in matches:
            item = InvoiceItem()
            item.lp = int(match.group(1))
            item.name = match.group(2).strip()
            item.quantity = self.parse_amount(match.group(3))
            item.unit = match.group(4)
            item.unit_price_net = self.parse_amount(match.group(5))
            item.net_amount = self.parse_amount(match.group(6))
            item.vat_rate = f"{match.group(7)}%"
            item.vat_amount = self.parse_amount(match.group(8))
            item.gross_amount = self.parse_amount(match.group(9))
            
            self.invoice_data['items'].append(item.to_dict())
    
    def _calculate_summary(self):
        """Oblicza podsumowanie faktury"""
        net_total = Decimal('0')
        vat_total = Decimal('0')
        gross_total = Decimal('0')
        vat_breakdown = {}
        
        for item in self.invoice_data['items']:
            net = Decimal(item['net_amount'])
            vat = Decimal(item['vat_amount'])
            gross = Decimal(item['gross_amount'])
            vat_rate = item['vat_rate']
            
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
