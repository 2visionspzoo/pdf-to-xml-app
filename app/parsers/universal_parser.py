"""
Parser uniwersalny dla różnych typów faktur
"""
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import re
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_parser import BaseInvoiceParser, InvoiceItem

class UniversalParser(BaseInvoiceParser):
    """Parser uniwersalny dla różnych typów faktur - wersja ulepszona"""
    
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
        
        # POPRAWIONA ekstrakcja danych sprzedawcy i nabywcy
        self._extract_parties_improved(text)
        
        # POPRAWIONA ekstrakcja pozycji faktury
        if tables:
            self._extract_items_from_tables_improved(tables, text)
        else:
            self._extract_items_from_text(text)
        
        # POPRAWIONA ekstrakcja podsumowania
        self._extract_summary_improved(text, tables)
        
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
    
    def _extract_parties_improved(self, text: str):
        """Ulepszona ekstrakcja danych sprzedawcy i nabywcy"""
        
        # Znajdź pozycje słów kluczowych
        seller_keywords = ['Sprzedawca', 'SPRZEDAWCA', 'Wystawca', 'Dostawca', 'Seller']
        buyer_keywords = ['Nabywca', 'NABYWCA', 'Odbiorca', 'Kupujący', 'Buyer']
        
        seller_pos = -1
        buyer_pos = -1
        
        for kw in seller_keywords:
            pos = text.find(kw)
            if pos != -1:
                seller_pos = pos
                break
        
        for kw in buyer_keywords:
            pos = text.find(kw)
            if pos != -1:
                buyer_pos = pos
                break
        
        # Jeśli znaleziono oba
        if seller_pos != -1 and buyer_pos != -1:
            # Określ kolejność
            if seller_pos < buyer_pos:
                # Sprzedawca pierwszy
                seller_text = text[seller_pos:buyer_pos]
                # Znajdź koniec sekcji nabywcy
                end_keywords = ['Lp', 'L.p.', 'Pozycje', 'Santander', 'Razem', 'PKO']
                buyer_end = len(text)
                for kw in end_keywords:
                    pos = text.find(kw, buyer_pos)
                    if pos != -1:
                        buyer_end = min(buyer_end, pos)
                buyer_text = text[buyer_pos:buyer_end]
            else:
                # Nabywca pierwszy
                buyer_text = text[buyer_pos:seller_pos]
                end_keywords = ['Lp', 'L.p.', 'Pozycje', 'Santander', 'Razem', 'PKO']
                seller_end = len(text)
                for kw in end_keywords:
                    pos = text.find(kw, seller_pos)
                    if pos != -1:
                        seller_end = min(seller_end, pos)
                seller_text = text[seller_pos:seller_end]
            
            # Ekstrahuj dane
            self.invoice_data['seller'] = self._extract_company_data_improved(seller_text, True)
            self.invoice_data['buyer'] = self._extract_company_data_improved(buyer_text, False)
    
    def _extract_company_data_improved(self, text: str, is_seller: bool) -> Dict:
        """Ulepszona ekstrakcja danych firmy"""
        data = {
            'name': '',
            'nip': '',
            'address': '',
            'city': '',
            'postal_code': '',
            'country': 'Polska'
        }
        
        # Usuń słowo kluczowe z początku
        keywords_to_remove = ['Sprzedawca', 'SPRZEDAWCA', 'Nabywca', 'NABYWCA', 
                             'Wystawca', 'Odbiorca', 'Kupujący', 'Dostawca']
        for kw in keywords_to_remove:
            text = text.replace(kw, '', 1).strip()
        
        # Podziel na linie
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Pierwsza linia to zwykle nazwa
        if lines:
            # Usuń NIP jeśli jest w nazwie
            name_line = lines[0]
            if 'NIP' not in name_line:
                data['name'] = name_line
            else:
                # Jeśli NIP jest w pierwszej linii, wyciągnij nazwę przed NIP
                nip_pos = name_line.find('NIP')
                if nip_pos > 0:
                    data['name'] = name_line[:nip_pos].strip()
        
        # Szukaj NIP
        nip_pattern = r'NIP[\s:]*([0-9]{3}[-\s]?[0-9]{3}[-\s]?[0-9]{2}[-\s]?[0-9]{2}|[0-9]{10})'
        nip_match = re.search(nip_pattern, text, re.IGNORECASE)
        if nip_match:
            data['nip'] = re.sub(r'[-\s]', '', nip_match.group(1))
        
        # Szukaj kodu pocztowego i miasta
        postal_pattern = r'(\d{2}[-\s]\d{3})\s+([A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż\s]+?)(?:\n|$|NIP)'
        postal_match = re.search(postal_pattern, text)
        if postal_match:
            data['postal_code'] = postal_match.group(1).replace(' ', '-')
            data['city'] = postal_match.group(2).strip()
        
        # Szukaj ulicy
        # Prostsza metoda - szukaj linii z numerem
        for line in lines:
            # Pomijamy linię z nazwą i NIP
            if line == data['name'] or 'NIP' in line:
                continue
            # Szukamy linii z numerem domu/mieszkania
            if re.search(r'\d+[A-Za-z]?(?:/\d+)?(?:\s|$)', line):
                # Sprawdzamy czy to nie kod pocztowy
                if not re.match(r'\d{2}[-\s]\d{3}', line):
                    # To prawdopodobnie adres
                    # Usuń "ul." jeśli jest
                    address = re.sub(r'^ul\.?\s*', '', line, flags=re.IGNORECASE)
                    # Usuń część z kodem pocztowym jeśli jest
                    address = re.split(r'\d{2}[-\s]\d{3}', address)[0].strip()
                    if address:
                        data['address'] = address
                        break
        
        return data
    
    def _extract_items_from_tables_improved(self, tables: List[List[List[str]]], text: str):
        """Ulepszona ekstrakcja pozycji z tabel"""
        
        # Najpierw szukamy tabeli z pozycjami
        items_table = None
        for table in tables:
            if self._is_items_table_improved(table):
                items_table = table
                break
        
        if not items_table:
            return
        
        # Parsuj tabelę
        header = items_table[0] if items_table else []
        column_map = self._identify_columns(header)
        
        # Obsługa połączonych wierszy
        # Sprawdź czy dane są w jednym wierszu czy wielu
        if len(items_table) > 1:
            first_data_row = items_table[1]
            # Jeśli pierwsza komórka zawiera \n, to dane są połączone
            if first_data_row and '\n' in str(first_data_row[0]):
                # Rozdziel połączone dane
                self._parse_merged_table(items_table, column_map)
                return
        
        # Standardowe parsowanie wiersz po wierszu
        for row in items_table[1:]:
            if self._is_valid_item_row(row):
                item = self._parse_item_row_improved(row, column_map)
                if item and item.name:
                    self.invoice_data['items'].append(item.to_dict())
    
    def _parse_merged_table(self, table: List[List[str]], column_map: Dict[str, int]):
        """Parsuje tabelę z połączonymi wierszami"""
        if len(table) < 2:
            return
        
        # Weź pierwszy wiersz z danymi
        data_row = table[1]
        
        # Rozdziel każdą komórkę na linie
        split_cells = []
        max_lines = 0
        
        for cell in data_row:
            lines = str(cell).split('\n')
            split_cells.append(lines)
            max_lines = max(max_lines, len(lines))
        
        # Teraz parsuj każdy "wirtualny" wiersz
        for i in range(max_lines):
            virtual_row = []
            for cell_lines in split_cells:
                if i < len(cell_lines):
                    virtual_row.append(cell_lines[i])
                else:
                    virtual_row.append('')
            
            # Parsuj wirtualny wiersz
            if self._is_valid_item_row(virtual_row):
                item = self._parse_item_row_improved(virtual_row, column_map)
                if item and item.name:
                    self.invoice_data['items'].append(item.to_dict())
    
    def _is_items_table_improved(self, table: List[List[str]]) -> bool:
        """Ulepszone sprawdzanie czy tabela zawiera pozycje"""
        if not table or len(table) < 2:
            return False
        
        header = ' '.join(str(cell).lower() for cell in table[0])
        
        # Kluczowe słowa dla tabeli pozycji
        required_keywords = ['nazwa', 'wartość', 'ilość']
        optional_keywords = ['lp', 'cena', 'netto', 'brutto', 'vat', 'stawka', 'kwota']
        
        required_matches = sum(1 for kw in required_keywords if kw in header)
        optional_matches = sum(1 for kw in optional_keywords if kw in header)
        
        # Tabela pozycji powinna mieć przynajmniej 2 wymagane słowa
        # lub 1 wymagane i 2 opcjonalne
        return required_matches >= 2 or (required_matches >= 1 and optional_matches >= 2)
    
    def _is_valid_item_row(self, row: List[str]) -> bool:
        """Sprawdza czy wiersz zawiera prawidłową pozycję"""
        # Pomijamy puste wiersze
        if not row or all(not str(cell).strip() for cell in row):
            return False
        
        # Pomijamy wiersze z podsumowaniem
        first_cell = str(row[0]).lower() if row else ''
        skip_words = ['razem', 'suma', 'ogółem', 'total', 'podsumowanie', 'stawka vat']
        
        for word in skip_words:
            if word in first_cell:
                return False
        
        return True
    
    def _identify_columns(self, header: List[str]) -> Dict[str, int]:
        """Identyfikuje indeksy kolumn na podstawie nagłówka"""
        column_map = {}
        
        patterns = {
            'lp': [r'lp\.?', r'l\.p\.?', r'nr', r'no\.?', r'poz'],
            'name': [r'nazwa', r'towar', r'usługa', r'opis', r'description'],
            'quantity': [r'ilość', r'ilosc', r'quantity', r'qty', r'liczba'],
            'unit': [r'j\.?m\.?', r'jedn', r'unit', r'miara'],
            'unit_price': [r'cena\s*jedn', r'cena\s*netto', r'unit\s*price'],
            'net_amount': [r'wartość\s*netto', r'netto', r'net'],
            'vat_rate': [r'stawka', r'vat\s*%', r'%\s*vat', r'tax\s*rate'],
            'vat_amount': [r'kwota\s*vat', r'vat(?!\s*%)', r'podatek'],
            'gross_amount': [r'wartość\s*brutto', r'brutto', r'gross']
        }
        
        for i, cell in enumerate(header):
            cell_lower = str(cell).lower().strip()
            for col_name, col_patterns in patterns.items():
                for pattern in col_patterns:
                    if re.search(pattern, cell_lower):
                        column_map[col_name] = i
                        break
        
        return column_map
    
    def _parse_item_row_improved(self, row: List[str], column_map: Dict[str, int]) -> Optional[InvoiceItem]:
        """Ulepszone parsowanie wiersza pozycji"""
        item = InvoiceItem()
        
        try:
            # Pobierz wartości według mapy kolumn
            if 'lp' in column_map and column_map['lp'] < len(row):
                try:
                    lp_val = str(row[column_map['lp']]).strip()
                    item.lp = int(lp_val) if lp_val.isdigit() else None
                except:
                    pass
            
            if 'name' in column_map and column_map['name'] < len(row):
                item.name = str(row[column_map['name']]).strip()
            
            if 'quantity' in column_map and column_map['quantity'] < len(row):
                item.quantity = self._parse_amount_improved(row[column_map['quantity']])
            
            if 'unit' in column_map and column_map['unit'] < len(row):
                item.unit = str(row[column_map['unit']]).strip()
            
            if 'unit_price' in column_map and column_map['unit_price'] < len(row):
                item.unit_price_net = self._parse_amount_improved(row[column_map['unit_price']])
            
            if 'net_amount' in column_map and column_map['net_amount'] < len(row):
                item.net_amount = self._parse_amount_improved(row[column_map['net_amount']])
            
            if 'vat_rate' in column_map and column_map['vat_rate'] < len(row):
                item.vat_rate = self.extract_vat_rate(row[column_map['vat_rate']])
            
            if 'vat_amount' in column_map and column_map['vat_amount'] < len(row):
                item.vat_amount = self._parse_amount_improved(row[column_map['vat_amount']])
            
            if 'gross_amount' in column_map and column_map['gross_amount'] < len(row):
                item.gross_amount = self._parse_amount_improved(row[column_map['gross_amount']])
            
            # Uzupełnij brakujące wartości
            if item.name and (item.net_amount > 0 or item.gross_amount > 0):
                # Jeśli brak stawki VAT, domyślnie 23%
                if not item.vat_rate:
                    item.vat_rate = "23%"
                
                # Oblicz brakujące wartości
                if item.net_amount > 0 and item.gross_amount == 0:
                    vat_decimal = Decimal(item.vat_rate.replace('%', '')) / 100
                    item.vat_amount = item.net_amount * vat_decimal
                    item.gross_amount = item.net_amount + item.vat_amount
                elif item.gross_amount > 0 and item.net_amount == 0:
                    vat_decimal = Decimal(item.vat_rate.replace('%', '')) / 100
                    item.net_amount = item.gross_amount / (1 + vat_decimal)
                    item.vat_amount = item.gross_amount - item.net_amount
                
                return item
            
        except Exception as e:
            print(f"Błąd parsowania wiersza: {e}")
        
        return None
    
    def _parse_amount_improved(self, text: str) -> Decimal:
        """Ulepszone parsowanie kwot - obsługa polskiej notacji"""
        try:
            # Konwertuj do stringa
            text = str(text)
            
            # Usuń wszystkie białe znaki
            text = text.strip()
            
            # Usuń znaki waluty i inne
            text = re.sub(r'[zł$€£¥]', '', text)
            
            # Usuń spacje używane jako separatory tysięcy
            text = text.replace(' ', '')
            
            # Zamień przecinek na kropkę (polska notacja)
            text = text.replace(',', '.')
            
            # Usuń wszystko oprócz cyfr, kropki i minusa
            text = re.sub(r'[^\d.-]', '', text)
            
            # Parsuj do Decimal
            if text:
                return Decimal(text)
            else:
                return Decimal('0')
        except:
            return Decimal('0')
    
    def _extract_summary_improved(self, text: str, tables: List[List[List[str]]]):
        """Ulepszona ekstrakcja podsumowania"""
        
        # Najpierw szukamy tabeli z podsumowaniem VAT
        vat_summary_table = None
        for table in tables:
            if self._is_vat_summary_table(table):
                vat_summary_table = table
                break
        
        if vat_summary_table:
            self._extract_summary_from_table(vat_summary_table)
        
        # Dodatkowo szukamy sum w tekście
        summary_patterns = {
            'net_total': [
                r'razem\s*netto[:\s]*([\d\s,.-]+)',
                r'suma\s*netto[:\s]*([\d\s,.-]+)',
                r'wartość\s*netto[:\s]*([\d\s,.-]+)',
                r'netto\s*razem[:\s]*([\d\s,.-]+)'
            ],
            'vat_total': [
                r'razem\s*vat[:\s]*([\d\s,.-]+)',
                r'suma\s*vat[:\s]*([\d\s,.-]+)',
                r'kwota\s*vat[:\s]*([\d\s,.-]+)',
                r'vat\s*razem[:\s]*([\d\s,.-]+)'
            ],
            'gross_total': [
                r'razem\s*brutto[:\s]*([\d\s,.-]+)',
                r'do\s*zapłaty[:\s]*([\d\s,.-]+)',
                r'suma\s*brutto[:\s]*([\d\s,.-]+)',
                r'wartość\s*brutto[:\s]*([\d\s,.-]+)',
                r'brutto\s*razem[:\s]*([\d\s,.-]+)',
                r'razem\s*do\s*zapłaty[:\s]*([\d\s,.-]+)'
            ]
        }
        
        for field, patterns in summary_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    amount = self._parse_amount_improved(match.group(1))
                    if amount > 0:
                        self.invoice_data['summary'][field] = str(amount)
                        break
        
        # Jeśli nie znaleziono, oblicz na podstawie pozycji
        if self.invoice_data['items'] and self.invoice_data['summary']['net_total'] == '0.00':
            self._calculate_summary()
    
    def _is_vat_summary_table(self, table: List[List[str]]) -> bool:
        """Sprawdza czy tabela zawiera podsumowanie VAT"""
        if not table:
            return False
        
        header = ' '.join(str(cell).lower() for cell in table[0])
        keywords = ['stawka vat', 'stawka', 'wartość netto', 'kwota vat', 'wartość brutto']
        
        matches = sum(1 for kw in keywords if kw in header)
        return matches >= 3
    
    def _extract_summary_from_table(self, table: List[List[str]]):
        """Ekstrahuje podsumowanie z tabeli VAT"""
        if not table or len(table) < 2:
            return
        
        # Identyfikuj kolumny
        header = table[0]
        column_map = {}
        
        for i, cell in enumerate(header):
            cell_lower = str(cell).lower()
            if 'stawka' in cell_lower:
                column_map['rate'] = i
            elif 'netto' in cell_lower:
                column_map['net'] = i
            elif 'kwota vat' in cell_lower or 'vat' in cell_lower:
                column_map['vat'] = i
            elif 'brutto' in cell_lower:
                column_map['gross'] = i
        
        # Parsuj wiersze
        total_net = Decimal('0')
        total_vat = Decimal('0')
        total_gross = Decimal('0')
        vat_breakdown = {}
        
        for row in table[1:]:
            if row and len(row) > max(column_map.values() if column_map else 0):
                # Sprawdź czy to nie wiersz "Razem"
                first_cell = str(row[0]).lower()
                
                if 'razem' in first_cell or 'suma' in first_cell:
                    # To wiersz z podsumowaniem
                    if 'net' in column_map:
                        total_net = self._parse_amount_improved(row[column_map['net']])
                    if 'vat' in column_map:
                        total_vat = self._parse_amount_improved(row[column_map['vat']])
                    if 'gross' in column_map:
                        total_gross = self._parse_amount_improved(row[column_map['gross']])
                else:
                    # To wiersz ze stawką VAT
                    if 'rate' in column_map:
                        rate = self.extract_vat_rate(row[column_map['rate']])
                        if rate and rate not in vat_breakdown:
                            vat_breakdown[rate] = {}
                            if 'net' in column_map:
                                vat_breakdown[rate]['net'] = str(
                                    self._parse_amount_improved(row[column_map['net']])
                                )
                            if 'vat' in column_map:
                                vat_breakdown[rate]['vat'] = str(
                                    self._parse_amount_improved(row[column_map['vat']])
                                )
                            if 'gross' in column_map:
                                vat_breakdown[rate]['gross'] = str(
                                    self._parse_amount_improved(row[column_map['gross']])
                                )
        
        # Aktualizuj dane
        if total_net > 0:
            self.invoice_data['summary']['net_total'] = str(total_net)
        if total_vat > 0:
            self.invoice_data['summary']['vat_total'] = str(total_vat)
        if total_gross > 0:
            self.invoice_data['summary']['gross_total'] = str(total_gross)
        if vat_breakdown:
            self.invoice_data['summary']['vat_breakdown'] = vat_breakdown
    
    def _calculate_summary(self):
        """Oblicza podsumowanie na podstawie pozycji"""
        net_total = Decimal('0')
        vat_total = Decimal('0')
        gross_total = Decimal('0')
        vat_breakdown = {}
        
        for item in self.invoice_data['items']:
            net = Decimal(item.get('net_amount', '0'))
            vat = Decimal(item.get('vat_amount', '0'))
            gross = Decimal(item.get('gross_amount', '0'))
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
        
        # Aktualizuj
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
    
    def _extract_items_from_text(self, text: str):
        """Ekstrahuje pozycje bezpośrednio z tekstu"""
        # Ta metoda jest zapasowa, gdy nie ma tabel
        # Implementacja pozostaje pusta, bo używamy tabel
        pass
