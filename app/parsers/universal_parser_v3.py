"""
Parser uniwersalny dla różnych typów faktur
"""
from typing import Dict, List, Optional
from decimal import Decimal
import re
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_parser import BaseInvoiceParser, InvoiceItem

class UniversalParser(BaseInvoiceParser):
    """Parser uniwersalny dla różnych typów faktur"""
    
    def __init__(self):
        super().__init__()
    
    def parse(self, text: str, tables: List[List[List[str]]] = None) -> Dict:
        """Parsuje fakturę używając uniwersalnych wzorców"""
        
        # Resetuj dane
        self.invoice_data = self._get_empty_invoice_data()
        
        # Ekstrakcja podstawowych danych
        self.invoice_data['invoice_number'] = self.extract_invoice_number(text) or ''
        self.invoice_data['invoice_date'] = self.extract_date(text, 'invoice') or ''
        self.invoice_data['sale_date'] = self.extract_date(text, 'sale') or ''
        self.invoice_data['payment_date'] = self.extract_date(text, 'payment') or ''
        
        # Ekstrakcja metody płatności
        self._extract_payment_method(text)
        
        # Ekstrakcja danych sprzedawcy i nabywcy
        self._extract_parties(text)
        
        # Ekstrakcja pozycji faktury
        if tables:
            self._extract_items_from_tables(tables)
        else:
            self._extract_items_from_text(text)
        
        # Ekstrakcja lub obliczenie podsumowania
        self._extract_or_calculate_summary(text)
        
        return self.invoice_data
    
    def _get_empty_invoice_data(self) -> Dict:
        """Zwraca pustą strukturę danych faktury"""
        return {
            'invoice_number': '',
            'invoice_date': '',
            'sale_date': '',
            'payment_date': '',
            'payment_method': '',
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
    
    def _extract_payment_method(self, text: str):
        """Ekstrahuje metodę płatności"""
        payment_patterns = [
            (r'przelew|transfer', 'przelew'),
            (r'gotówka|cash', 'gotówka'),
            (r'karta|card', 'karta'),
            (r'pobranie', 'pobranie'),
            (r'kompensata', 'kompensata')
        ]
        
        text_lower = text.lower()
        for pattern, method in payment_patterns:
            if re.search(pattern, text_lower):
                self.invoice_data['payment_method'] = method
                break
    
    def _extract_parties(self, text: str):
        """Ekstrahuje dane sprzedawcy i nabywcy"""
        # Podział tekstu na sekcje
        seller_section = self._extract_section(text, 
            ['Sprzedawca', 'SPRZEDAWCA', 'Wystawca', 'Dostawca', 'Seller', 'Vendor'],
            ['Nabywca', 'NABYWCA', 'Odbiorca', 'Kupujący', 'Buyer', 'Pozycje', 'Lp.'])
        
        buyer_section = self._extract_section(text,
            ['Nabywca', 'NABYWCA', 'Odbiorca', 'Kupujący', 'Buyer', 'Customer'],
            ['Pozycje', 'Lp.', 'L.p.', 'Nr', 'Razem', 'Suma', 'Items'])
        
        if seller_section:
            self.invoice_data['seller'] = self.extract_company_data(seller_section, True)
        
        if buyer_section:
            self.invoice_data['buyer'] = self.extract_company_data(buyer_section, False)
    
    def _extract_section(self, text: str, start_keywords: List[str], end_keywords: List[str]) -> Optional[str]:
        """Ekstrahuje sekcję tekstu między słowami kluczowymi"""
        # Tworzenie wzorca regex
        start_pattern = '|'.join(re.escape(kw) for kw in start_keywords)
        end_pattern = '|'.join(re.escape(kw) for kw in end_keywords)
        
        pattern = f'({start_pattern})[:\s]*(.*?)(?={end_pattern}|$)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        
        if match:
            return match.group(2)
        return None
    
    def _extract_items_from_tables(self, tables: List[List[List[str]]]):
        """Ekstrahuje pozycje z tabel"""
        for table in tables:
            if self._is_items_table(table):
                # Identyfikacja kolumn
                column_map = self._identify_columns(table[0] if table else [])
                
                # Parsowanie wierszy
                for row in table[1:]:
                    item = self._parse_item_row_universal(row, column_map)
                    if item and item.name:
                        self.invoice_data['items'].append(item.to_dict())
    
    def _is_items_table(self, table: List[List[str]]) -> bool:
        """Sprawdza czy tabela zawiera pozycje faktury"""
        if not table or len(table) < 2:
            return False
        
        header = ' '.join(str(cell).lower() for cell in table[0])
        keywords = ['nazwa', 'towar', 'usługa', 'ilość', 'quantity', 'netto', 'net', 
                   'vat', 'brutto', 'gross', 'cena', 'price', 'wartość', 'amount']
        
        matches = sum(1 for keyword in keywords if keyword in header)
        return matches >= 3
    
    def _identify_columns(self, header: List[str]) -> Dict[str, int]:
        """Identyfikuje indeksy kolumn na podstawie nagłówka"""
        column_map = {}
        
        patterns = {
            'lp': [r'lp\.?', r'l\.p\.?', r'nr', r'no\.?', r'poz'],
            'name': [r'nazwa', r'towar', r'usługa', r'opis', r'description', r'name'],
            'quantity': [r'ilość', r'ilosc', r'quantity', r'qty', r'liczba'],
            'unit': [r'j\.?m\.?', r'jedn', r'unit', r'miara'],
            'unit_price': [r'cena\s*jedn', r'unit\s*price', r'cena\s*netto', r'price'],
            'net_amount': [r'wartość\s*netto', r'netto', r'net\s*amount', r'net'],
            'vat_rate': [r'stawka\s*vat', r'vat\s*%', r'%\s*vat', r'tax\s*rate'],
            'vat_amount': [r'kwota\s*vat', r'vat\s*amount', r'podatek', r'tax'],
            'gross_amount': [r'wartość\s*brutto', r'brutto', r'gross', r'razem']
        }
        
        for i, cell in enumerate(header):
            cell_lower = str(cell).lower()
            for col_name, col_patterns in patterns.items():
                for pattern in col_patterns:
                    if re.search(pattern, cell_lower):
                        column_map[col_name] = i
                        break
        
        return column_map
    
    def _parse_item_row_universal(self, row: List[str], column_map: Dict[str, int]) -> Optional[InvoiceItem]:
        """Parsuje wiersz używając mapy kolumn"""
        item = InvoiceItem()
        
        try:
            # Pobieranie wartości według mapy kolumn
            if 'lp' in column_map and column_map['lp'] < len(row):
                try:
                    item.lp = int(row[column_map['lp']])
                except:
                    pass
            
            if 'name' in column_map and column_map['name'] < len(row):
                item.name = row[column_map['name']].strip()
            
            if 'quantity' in column_map and column_map['quantity'] < len(row):
                item.quantity = self.parse_amount(row[column_map['quantity']])
            
            if 'unit' in column_map and column_map['unit'] < len(row):
                item.unit = row[column_map['unit']].strip()
            
            if 'unit_price' in column_map and column_map['unit_price'] < len(row):
                item.unit_price_net = self.parse_amount(row[column_map['unit_price']])
            
            if 'net_amount' in column_map and column_map['net_amount'] < len(row):
                item.net_amount = self.parse_amount(row[column_map['net_amount']])
            
            if 'vat_rate' in column_map and column_map['vat_rate'] < len(row):
                item.vat_rate = self.extract_vat_rate(row[column_map['vat_rate']])
            
            if 'vat_amount' in column_map and column_map['vat_amount'] < len(row):
                item.vat_amount = self.parse_amount(row[column_map['vat_amount']])
            
            if 'gross_amount' in column_map and column_map['gross_amount'] < len(row):
                item.gross_amount = self.parse_amount(row[column_map['gross_amount']])
            
            # Walidacja i obliczenia uzupełniające
            if item.name and (item.net_amount > 0 or item.gross_amount > 0):
                # Uzupełnij brakujące wartości jeśli to możliwe
                if item.net_amount > 0 and item.vat_rate and item.gross_amount == 0:
                    vat_decimal = Decimal(item.vat_rate.replace('%', '')) / 100
                    item.vat_amount = item.net_amount * vat_decimal
                    item.gross_amount = item.net_amount + item.vat_amount
                
                return item
            
        except Exception as e:
            print(f"Błąd parsowania wiersza: {e}")
        
        return None
    
    def _extract_items_from_text(self, text: str):
        """Ekstrahuje pozycje bezpośrednio z tekstu"""
        # Różne wzorce dla różnych formatów faktur
        patterns = [
            # Format: nr | nazwa | ilość | jedn | cena | netto | vat% | vat | brutto
            r'(\d+)[\s\|]+([\w\s\-]+?)[\s\|]+(\d+[,.]?\d*)[\s\|]+(\w+)[\s\|]+(\d+[,.]?\d*)[\s\|]+(\d+[,.]?\d*)[\s\|]+(\d+)%?[\s\|]+(\d+[,.]?\d*)[\s\|]+(\d+[,.]?\d*)',
            # Format: nazwa | ilość | netto | vat | brutto
            r'([\w\s\-]{3,50})[\s\|]+(\d+[,.]?\d*)[\s\|]+(\d+[,.]?\d*)[\s\|]+(\d+[,.]?\d*)[\s\|]+(\d+[,.]?\d*)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                item = self._parse_text_match(match, pattern)
                if item:
                    self.invoice_data['items'].append(item.to_dict())
    
    def _parse_text_match(self, match: re.Match, pattern: str) -> Optional[InvoiceItem]:
        """Parsuje dopasowanie regex do InvoiceItem"""
        item = InvoiceItem()
        groups = match.groups()
        
        try:
            if len(groups) == 9:  # Pełny format
                item.lp = int(groups[0])
                item.name = groups[1].strip()
                item.quantity = self.parse_amount(groups[2])
                item.unit = groups[3]
                item.unit_price_net = self.parse_amount(groups[4])
                item.net_amount = self.parse_amount(groups[5])
                item.vat_rate = f"{groups[6]}%"
                item.vat_amount = self.parse_amount(groups[7])
                item.gross_amount = self.parse_amount(groups[8])
            elif len(groups) == 5:  # Uproszczony format
                item.name = groups[0].strip()
                item.quantity = self.parse_amount(groups[1])
                item.net_amount = self.parse_amount(groups[2])
                item.vat_amount = self.parse_amount(groups[3])
                item.gross_amount = self.parse_amount(groups[4])
                # Oblicz stawkę VAT
                if item.net_amount > 0:
                    vat_rate = (item.vat_amount / item.net_amount * 100)
                    item.vat_rate = f"{int(vat_rate)}%"
            
            if item.name and item.gross_amount > 0:
                return item
                
        except Exception as e:
            print(f"Błąd parsowania dopasowania: {e}")
        
        return None
    
    def _extract_or_calculate_summary(self, text: str):
        """Ekstrahuje podsumowanie z tekstu lub oblicza na podstawie pozycji"""
        # Próba ekstrakcji sum z tekstu
        summary_patterns = {
            'net_total': [r'razem\s*netto[:\s]*([\d\s,.-]+)', r'suma\s*netto[:\s]*([\d\s,.-]+)'],
            'vat_total': [r'razem\s*vat[:\s]*([\d\s,.-]+)', r'suma\s*vat[:\s]*([\d\s,.-]+)'],
            'gross_total': [r'razem\s*brutto[:\s]*([\d\s,.-]+)', r'do\s*zapłaty[:\s]*([\d\s,.-]+)']
        }
        
        for field, patterns in summary_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    self.invoice_data['summary'][field] = str(self.parse_amount(match.group(1)))
                    break
        
        # Jeśli nie znaleziono, oblicz na podstawie pozycji
        if self.invoice_data['items']:
            self._calculate_summary()
    
    def _calculate_summary(self):
        """Oblicza podsumowanie na podstawie pozycji"""
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
        
        # Aktualizuj tylko jeśli obliczone wartości są większe od zero
        if net_total > 0:
            self.invoice_data['summary']['net_total'] = str(net_total)
        if vat_total > 0:
            self.invoice_data['summary']['vat_total'] = str(vat_total)
        if gross_total > 0:
            self.invoice_data['summary']['gross_total'] = str(gross_total)
        
        # Konwersja vat_breakdown
        for rate, values in vat_breakdown.items():
            vat_breakdown[rate] = {
                'net': str(values['net']),
                'vat': str(values['vat']),
                'gross': str(values['gross'])
            }
        
        if vat_breakdown:
            self.invoice_data['summary']['vat_breakdown'] = vat_breakdown
