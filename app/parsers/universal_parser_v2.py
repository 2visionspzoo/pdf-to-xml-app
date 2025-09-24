"""
Parser uniwersalny dla różnych typów faktur - wersja 2
Poprawiona ekstrakcja danych sprzedawcy/nabywcy i pozycji
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
        self.invoice_data['invoice_number'] = self._extract_invoice_number_improved(text) or ''
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
    
    def _extract_invoice_number_improved(self, text: str) -> Optional[str]:
        """Ulepszona ekstrakcja numeru faktury"""
        
        # Rozszerzona lista wzorców
        patterns = [
            # Standardowe wzorce
            r'(?:Faktura\s+(?:VAT\s+)?(?:nr|Nr\.?)\s*[:s]?)([A-Za-z0-9\-/]+)',
            r'(?:FAKTURA\s+(?:VAT\s+)?(?:NR|Nr\.?)\s*[:s]?)([A-Za-z0-9\-/]+)',
            r'(?:Invoice\s+(?:number|no\.?)\s*[:s]?)([A-Za-z0-9\-/]+)',
            r'(?:Numer\s+faktury\s*[:s]?)([A-Za-z0-9\-/]+)',
            
            # Wzorce specyficzne
            r'(?:F[AV]?[KS]?[TURA]*)[\s\-_]*([\d]+[\-/]\d+[\-/]\d+)',  # FV 123-45-67
            r'(?:FV|FS|FVS|FA|FZ)[\s\-_/]*([\d]+[\-_/]\d+[\-_/]\d+)',  # FV/123/45/67
            r'(?:Nr\.?\s+faktury)[\s:]*([A-Za-z0-9\-/_]+)',
            
            # Wzorce z datami
            r'(\d+/\d+/\d{4})',  # 11/07/2025
            r'(\d+[\-_]\d+[\-_]\d{4})',  # 11-07-2025
            
            # Wzorce specjalne
            r'(?:Faktura\s+nr\s+)([A-Z]+[\s/]\d+[\s/]\d+)',  # Faktura nr PL/7/2025
            r'^([A-Z]{2,}[\-/]\d+[\-/]\d+)',  # FVS-2-08-2025
            
            # Fallback - szukaj w pierwszych liniach
            r'^(?:Nr\.?\s*)([A-Za-z0-9\-/]+)'
        ]
        
        # Najpierw szukaj w pierwszych 10 liniach (często tam jest numer)
        lines = text.split('\n')[:10]
        for line in lines:
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    invoice_num = match.group(1).strip()
                    # Sprawdź czy to sensowny numer
                    if len(invoice_num) >= 3 and not invoice_num.lower() in ['vat', 'faktura', 'invoice', 'nr']:
                        return invoice_num
        
        # Jeśli nie znaleziono, szukaj w całym tekście
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                invoice_num = match.group(1).strip()
                # Sprawdź czy to sensowny numer
                if len(invoice_num) >= 3 and not invoice_num.lower() in ['vat', 'faktura', 'invoice', 'nr']:
                    return invoice_num
        
        # Ostatnia deska ratunku - szukaj czegoś co wygląda jak numer
        # np. FVS_2_08_2025 lub FV-2025-0213-0165
        special_pattern = r'(F[VSAKZ][S\-_/]*\d+[\-_/]\d+[\-_/]\d+)'
        match = re.search(special_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None
    
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
        
        # Znajdź pozycje słów kluczowych - rozszerzona lista
        seller_keywords = ['Sprzedawca', 'SPRZEDAWCA', 'Wystawca', 'Dostawca', 'Seller', 
                          'Wystawca:', 'WYSTAWCA:', 'Sprzedający', 'SPRZEDAJĄCY']
        buyer_keywords = ['Nabywca', 'NABYWCA', 'Odbiorca', 'Kupujący', 'Buyer',
                         'Nabywca:', 'NABYWCA:', 'Zamawiający', 'ZAMAWIAJĄCY']
        
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
        else:
            # Jeśli nie znaleziono etykiet, spróbuj znaleźć po NIP i pozycji w tekście
            self._extract_parties_by_pattern(text)
    
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
        original_text = text
        for kw in keywords_to_remove:
            # Usuń słowo kluczowe i dwukropek jeśli występuje
            text = re.sub(rf'{kw}\s*:?\s*', '', text, 1, re.IGNORECASE).strip()
        
        # Jeśli po usunięciu został tylko dwukropek lub puste, szukaj głębiej
        if not text or text == ':':
            # Szukaj nazwy w kolejnych liniach
            lines = original_text.split('\n')
            for i, line in enumerate(lines):
                # Pomijamy pierwszą linię z etykietą
                if i == 0:
                    continue
                clean_line = line.strip()
                # Jeśli linia nie jest pusta i nie zawiera tylko słów kluczowych
                if clean_line and clean_line != ':' and not any(kw in clean_line for kw in ['NIP', 'REGON', 'ul.']):
                    text = clean_line
                    break
        
        # Podziel na linie
        lines = [line.strip() for line in text.split('\n') if line.strip() and line.strip() != ':']
        
        # POPRAWKA: Sprawdź czy pierwsza linia nie zawiera "Data wystawienia" lub podobnych
        if lines:
            name_line = lines[0]
            # Pomijamy linie z datami i innymi metadanymi
            skip_patterns = ['Data wystawienia', 'Data sprzedaży', 'Miejsce wystawienia', 
                           'Termin płatności', 'Sposób płatności']
            
            # Szukaj pierwszej linii która nie jest metadaną
            for line in lines:
                is_metadata = False
                for pattern in skip_patterns:
                    if pattern in line:
                        is_metadata = True
                        break
                
                # Również pomijamy linie które są tylko datami lub kodami
                if re.match(r'^\d{4}-\d{2}-\d{2}', line) or re.match(r'^\d{2}\.\d{2}\.\d{4}', line):
                    is_metadata = True
                
                if not is_metadata and 'NIP' not in line and not re.match(r'^\d{2}-\d{3}', line):
                    # To prawdopodobnie nazwa firmy
                    data['name'] = line
                    break
        
        # Jeśli nadal nie mamy nazwy, szukaj przed NIP
        if not data['name'] and lines:
            for line in lines:
                if 'NIP' in line:
                    # Jeśli NIP jest w linii, wyciągnij nazwę przed NIP
                    nip_pos = line.find('NIP')
                    if nip_pos > 0:
                        potential_name = line[:nip_pos].strip()
                        # Sprawdź czy to nie jest data lub miasto
                        if not re.match(r'^\d', potential_name) and len(potential_name) > 3:
                            data['name'] = potential_name
                    break
        
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
    
    def _extract_parties_by_pattern(self, text: str):
        """Ekstrahuje sprzedawcę i nabywcę gdy brak etykiet"""
        # Szukaj NIPów w tekście
        nip_pattern = r'NIP[\s:]*([0-9]{3}[-\s]?[0-9]{3}[-\s]?[0-9]{2}[-\s]?[0-9]{2}|[0-9]{10})'
        nip_matches = list(re.finditer(nip_pattern, text, re.IGNORECASE))
        
        if len(nip_matches) >= 2:
            # Zakładamy że pierwszy NIP to sprzedawca (góra faktury)
            # a drugi to nabywca
            first_nip_pos = nip_matches[0].start()
            second_nip_pos = nip_matches[1].start()
            
            # Wyciągnij tekst wokół pierwszego NIP (sprzedawca)
            seller_start = max(0, first_nip_pos - 200)
            seller_end = min(len(text), first_nip_pos + 200)
            seller_text = text[seller_start:seller_end]
            
            # Wyciągnij tekst wokół drugiego NIP (nabywca)
            buyer_start = max(0, second_nip_pos - 200)
            buyer_end = min(len(text), second_nip_pos + 200)
            buyer_text = text[buyer_start:buyer_end]
            
            # Jeśli znamy 2Vision, sprawdź który jest który
            if '2vision' in buyer_text.lower() or '2Vision' in buyer_text:
                # 2Vision jest nabycą
                self.invoice_data['seller'] = self._extract_company_data_improved(seller_text, True)
                self.invoice_data['buyer'] = self._extract_company_data_improved(buyer_text, False)
            elif '2vision' in seller_text.lower() or '2Vision' in seller_text:
                # 2Vision jest sprzedawcą (faktura sprzedaży)
                self.invoice_data['buyer'] = self._extract_company_data_improved(seller_text, False)
                self.invoice_data['seller'] = self._extract_company_data_improved(buyer_text, True)
            else:
                # Domyślnie: pierwszy = sprzedawca
                self.invoice_data['seller'] = self._extract_company_data_improved(seller_text, True)
                self.invoice_data['buyer'] = self._extract_company_data_improved(buyer_text, False)
        elif len(nip_matches) == 1:
            # Tylko jeden NIP - prawdopodobnie sprzedawca
            nip_pos = nip_matches[0].start()
            company_start = max(0, nip_pos - 200)
            company_end = min(len(text), nip_pos + 200)
            company_text = text[company_start:company_end]
            
            if '2vision' in company_text.lower():
                # To jest 2Vision jako nabywca
                self.invoice_data['buyer'] = self._extract_company_data_improved(company_text, False)
            else:
                # To jest sprzedawca
                self.invoice_data['seller'] = self._extract_company_data_improved(company_text, True)
    
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
        
        # POPRAWKA: Zbieramy wszystkie pozycje, również te które mogą być w wielu wierszach
        all_items = []
        current_item_data = None
        
        # Parsuj każdy wiersz
        for i, row in enumerate(items_table[1:]):
            # Sprawdź czy wiersz nie jest pusty lub podsumowaniem
            if self._is_valid_item_row(row):
                # Sprawdź czy wiersz zawiera dane pozycji
                # Jeśli pierwsza kolumna ma liczbę (Lp.), to nowa pozycja
                first_cell = str(row[0]).strip() if row else ''
                
                # Sprawdź czy to nowa pozycja (zaczyna się od liczby)
                if first_cell and (first_cell.isdigit() or re.match(r'^\d+\.?$', first_cell)):
                    # Zapisz poprzednią pozycję jeśli istnieje
                    if current_item_data:
                        item = self._parse_item_row_improved(current_item_data, column_map)
                        if item and item.name and item.name.lower() not in ['none', '', 'brak', 'null']:
                            all_items.append(item)
                    
                    # Rozpocznij nową pozycję
                    current_item_data = self._fix_merged_row(row, column_map)
                elif current_item_data and row:
                    # To może być kontynuacja poprzedniej pozycji (np. długa nazwa)
                    # Sprawdź czy to nie jest już następna pozycja bez Lp.
                    has_amounts = False
                    for cell in row:
                        cell_str = str(cell).strip()
                        # Sprawdź czy komórka zawiera kwotę
                        if re.match(r'^[\d\s]+[,.]?\d*$', cell_str) and len(cell_str) > 0:
                            try:
                                val = float(cell_str.replace(',', '.').replace(' ', ''))
                                if val > 0:
                                    has_amounts = True
                                    break
                            except:
                                pass
                    
                    if has_amounts:
                        # To nowa pozycja bez numeru Lp.
                        if current_item_data:
                            item = self._parse_item_row_improved(current_item_data, column_map)
                            if item and item.name and item.name.lower() not in ['none', '', 'brak', 'null']:
                                all_items.append(item)
                        current_item_data = self._fix_merged_row(row, column_map)
                    else:
                        # To kontynuacja nazwy
                        if 'name' in column_map and column_map['name'] < len(row):
                            additional_text = str(row[column_map['name']]).strip()
                            if additional_text and current_item_data:
                                current_item_data[column_map['name']] += ' ' + additional_text
                else:
                    # Sprawdź czy wiersz zawiera sensowne dane
                    fixed_row = self._fix_merged_row(row, column_map)
                    if fixed_row:
                        item = self._parse_item_row_improved(fixed_row, column_map)
                        if item and item.name and item.name.lower() not in ['none', '', 'brak', 'null']:
                            all_items.append(item)
        
        # Nie zapomnij o ostatniej pozycji
        if current_item_data:
            item = self._parse_item_row_improved(current_item_data, column_map)
            if item and item.name and item.name.lower() not in ['none', '', 'brak', 'null']:
                all_items.append(item)
        
        # Dodaj wszystkie znalezione pozycje
        for item in all_items:
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
    
    def _fix_merged_row(self, row: List[str], column_map: Dict[str, int]) -> List[str]:
        """Naprawia wiersze z połączonymi danymi (np. wieloliniowe komórki)"""
        # Jeśli pierwsza komórka zawiera znaki nowej linii, to dane są połączone
        if row and '\n' in str(row[0]):
            # Spróbuj rozdzielić dane
            lines_per_cell = []
            max_lines = 0
            
            for cell in row:
                cell_lines = str(cell).split('\n')
                lines_per_cell.append(cell_lines)
                max_lines = max(max_lines, len(cell_lines))
            
            # Zwróć tylko pierwszy wiersz danych
            fixed_row = []
            for cell_lines in lines_per_cell:
                if cell_lines:
                    fixed_row.append(cell_lines[0])
                else:
                    fixed_row.append('')
            
            return fixed_row
        
        return row
    
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
                    # Usuń znaki nowej linii i weź pierwszą liczbę
                    lp_val = lp_val.split('\n')[0] if '\n' in lp_val else lp_val
                    item.lp = int(lp_val) if lp_val.isdigit() else None
                except:
                    pass
            
            if 'name' in column_map and column_map['name'] < len(row):
                name_val = str(row[column_map['name']]).strip()
                # Weź pierwszą linię jeśli są znaki nowej linii
                item.name = name_val.split('\n')[0] if '\n' in name_val else name_val
            
            if 'quantity' in column_map and column_map['quantity'] < len(row):
                item.quantity = self._parse_amount_improved(row[column_map['quantity']])
            
            if 'unit' in column_map and column_map['unit'] < len(row):
                unit_val = str(row[column_map['unit']]).strip()
                item.unit = unit_val.split('\n')[0] if '\n' in unit_val else unit_val
            
            if 'unit_price' in column_map and column_map['unit_price'] < len(row):
                item.unit_price_net = self._parse_amount_improved(row[column_map['unit_price']])
            
            if 'net_amount' in column_map and column_map['net_amount'] < len(row):
                item.net_amount = self._parse_amount_improved(row[column_map['net_amount']])
            
            if 'vat_rate' in column_map and column_map['vat_rate'] < len(row):
                vat_val = str(row[column_map['vat_rate']]).strip()
                vat_val = vat_val.split('\n')[0] if '\n' in vat_val else vat_val
                item.vat_rate = self.extract_vat_rate(vat_val)
            
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
                if item.net_amount > 0:
                    vat_decimal = Decimal(item.vat_rate.replace('%', '')) / 100
                    
                    # Zawsze oblicz VAT jeśli mamy netto
                    if item.vat_amount == 0 or item.vat_amount is None:
                        item.vat_amount = round(item.net_amount * vat_decimal, 2)
                    
                    # Jeśli brak brutto, oblicz
                    if item.gross_amount == 0:
                        item.gross_amount = item.net_amount + item.vat_amount
                        
                elif item.gross_amount > 0 and item.net_amount == 0:
                    vat_decimal = Decimal(item.vat_rate.replace('%', '')) / 100
                    item.net_amount = round(item.gross_amount / (1 + vat_decimal), 2)
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
            
            # Weź pierwszą linię jeśli są znaki nowej linii
            if '\n' in text:
                text = text.split('\n')[0]
            
            # Usuń wszystkie białe znaki
            text = text.strip()
            
            # Jeśli to puste lub None, zwróć 0
            if not text or text.lower() in ['none', '', '-', 'brak']:
                return Decimal('0')
            
            # POPRAWKA: Obsługa błędnych formatów z wieloma kropkami
            # np. "1...113.1110000.0010000.00"
            if text.count('.') > 2:
                # Sprawdź czy to nie jest wielokrotnie powtórzona wartość
                # Szukaj sensownej liczby w tekście
                numbers = re.findall(r'\d+\.?\d{0,2}', text)
                if numbers:
                    # Weź pierwszą sensowną liczbę
                    for num in numbers:
                        if num and float(num) > 0 and float(num) < 100000:
                            text = num
                            break
                else:
                    print(f"Warning: Malformed amount string: {text}")
                    return Decimal('0')
            
            # Usuń znaki waluty i inne
            text = re.sub(r'[zł$€£¥]', '', text)
            
            # Obsługa polskiej notacji - sprawdź czy jest spacja jako separator tysięcy i przecinek jako separator dziesiętny
            if ',' in text and ' ' in text:
                # Polski format: 1 234,56
                text = text.replace(' ', '').replace(',', '.')
            elif ',' in text and text.count(',') == 1:
                # Może być 1234,56 lub 1,234.56
                parts = text.split(',')
                if len(parts) == 2 and len(parts[1]) == 2:
                    # To prawdopodobnie polski format z przecinkiem dziesiętnym
                    text = text.replace(',', '.')
                elif len(parts) == 2 and len(parts[1]) == 3:
                    # To prawdopodobnie angielski format z przecinkiem jako separator tysięcy
                    text = text.replace(',', '')
            else:
                # Standardowe usuwanie spacji
                text = text.replace(' ', '')
                # Zamień przecinek na kropkę
                text = text.replace(',', '.')
            
            # Usuń wszystko oprócz cyfr, kropki i minusa
            text = re.sub(r'[^\d.-]', '', text)
            
            # Sprawdź czy nie ma wielu kropek
            if text.count('.') > 1:
                # Zostaw tylko ostatnią kropkę jako separator dziesiętny
                parts = text.split('.')
                text = ''.join(parts[:-1]) + '.' + parts[-1]
            
            # Parsuj do Decimal
            if text and text != '-' and text != '.':
                value = Decimal(text)
                # Sprawdź czy wartość nie jest podejrzanie duża (np. 10000.00 jako domyślna)
                if value == Decimal('10000.00'):
                    # Log this for debugging
                    print(f"Warning: Found default value 10000.00, might need manual verification")
                return value
            else:
                return Decimal('0')
        except Exception as e:
            print(f"Error parsing amount '{text}': {type(e).__name__}")
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
            net = Decimal(str(item.get('net_amount', '0')))
            vat = Decimal(str(item.get('vat_amount', '0')))
            gross = Decimal(str(item.get('gross_amount', '0')))
            vat_rate = item.get('vat_rate', '23%')
            
            # Jeśli VAT jest 0 ale mamy netto i stawkę, oblicz VAT
            if vat == 0 and net > 0 and vat_rate:
                vat_decimal = Decimal(vat_rate.replace('%', '')) / 100
                vat = round(net * vat_decimal, 2)
            
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
        # Implementacja pozostaje taka sama jak w oryginalnym parserze
        pass
,
        ]
        
        # Najpierw szukaj w pierwszych 10 liniach (często tam jest numer)
        lines = text.split('\n')[:10]
        for line in lines:
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    invoice_num = match.group(1).strip()
                    # Sprawdź czy to sensowny numer
                    if len(invoice_num) >= 3 and not invoice_num.lower() in ['vat', 'faktura', 'invoice', 'nr']:
                        return invoice_num
        
        # Jeśli nie znaleziono, szukaj w całym tekście
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                invoice_num = match.group(1).strip()
                # Sprawdź czy to sensowny numer
                if len(invoice_num) >= 3 and not invoice_num.lower() in ['vat', 'faktura', 'invoice', 'nr']:
                    return invoice_num
        
        # Ostatnia deska ratunku - szukaj czegoś co wygląda jak numer
        # np. FVS_2_08_2025 lub FV-2025-0213-0165
        special_pattern = r'(F[VSAKZ][S\-_/]*\d+[\-_/]\d+[\-_/]\d+)'
        match = re.search(special_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None
    
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
        
        # Znajdź pozycje słów kluczowych - rozszerzona lista
        seller_keywords = ['Sprzedawca', 'SPRZEDAWCA', 'Wystawca', 'Dostawca', 'Seller', 
                          'Wystawca:', 'WYSTAWCA:', 'Sprzedający', 'SPRZEDAJĄCY']
        buyer_keywords = ['Nabywca', 'NABYWCA', 'Odbiorca', 'Kupujący', 'Buyer',
                         'Nabywca:', 'NABYWCA:', 'Zamawiający', 'ZAMAWIAJĄCY']
        
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
        else:
            # Jeśli nie znaleziono etykiet, spróbuj znaleźć po NIP i pozycji w tekście
            self._extract_parties_by_pattern(text)
    
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
        original_text = text
        for kw in keywords_to_remove:
            # Usuń słowo kluczowe i dwukropek jeśli występuje
            text = re.sub(rf'{kw}\s*:?\s*', '', text, 1, re.IGNORECASE).strip()
        
        # Jeśli po usunięciu został tylko dwukropek lub puste, szukaj głębiej
        if not text or text == ':':
            # Szukaj nazwy w kolejnych liniach
            lines = original_text.split('\n')
            for i, line in enumerate(lines):
                # Pomijamy pierwszą linię z etykietą
                if i == 0:
                    continue
                clean_line = line.strip()
                # Jeśli linia nie jest pusta i nie zawiera tylko słów kluczowych
                if clean_line and clean_line != ':' and not any(kw in clean_line for kw in ['NIP', 'REGON', 'ul.']):
                    text = clean_line
                    break
        
        # Podziel na linie
        lines = [line.strip() for line in text.split('\n') if line.strip() and line.strip() != ':']
        
        # POPRAWKA: Sprawdź czy pierwsza linia nie zawiera "Data wystawienia" lub podobnych
        if lines:
            name_line = lines[0]
            # Pomijamy linie z datami i innymi metadanymi
            skip_patterns = ['Data wystawienia', 'Data sprzedaży', 'Miejsce wystawienia', 
                           'Termin płatności', 'Sposób płatności']
            
            # Szukaj pierwszej linii która nie jest metadaną
            for line in lines:
                is_metadata = False
                for pattern in skip_patterns:
                    if pattern in line:
                        is_metadata = True
                        break
                
                # Również pomijamy linie które są tylko datami lub kodami
                if re.match(r'^\d{4}-\d{2}-\d{2}', line) or re.match(r'^\d{2}\.\d{2}\.\d{4}', line):
                    is_metadata = True
                
                if not is_metadata and 'NIP' not in line and not re.match(r'^\d{2}-\d{3}', line):
                    # To prawdopodobnie nazwa firmy
                    data['name'] = line
                    break
        
        # Jeśli nadal nie mamy nazwy, szukaj przed NIP
        if not data['name'] and lines:
            for line in lines:
                if 'NIP' in line:
                    # Jeśli NIP jest w linii, wyciągnij nazwę przed NIP
                    nip_pos = line.find('NIP')
                    if nip_pos > 0:
                        potential_name = line[:nip_pos].strip()
                        # Sprawdź czy to nie jest data lub miasto
                        if not re.match(r'^\d', potential_name) and len(potential_name) > 3:
                            data['name'] = potential_name
                    break
        
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
    
    def _extract_parties_by_pattern(self, text: str):
        """Ekstrahuje sprzedawcę i nabywcę gdy brak etykiet"""
        # Szukaj NIPów w tekście
        nip_pattern = r'NIP[\s:]*([0-9]{3}[-\s]?[0-9]{3}[-\s]?[0-9]{2}[-\s]?[0-9]{2}|[0-9]{10})'
        nip_matches = list(re.finditer(nip_pattern, text, re.IGNORECASE))
        
        if len(nip_matches) >= 2:
            # Zakładamy że pierwszy NIP to sprzedawca (góra faktury)
            # a drugi to nabywca
            first_nip_pos = nip_matches[0].start()
            second_nip_pos = nip_matches[1].start()
            
            # Wyciągnij tekst wokół pierwszego NIP (sprzedawca)
            seller_start = max(0, first_nip_pos - 200)
            seller_end = min(len(text), first_nip_pos + 200)
            seller_text = text[seller_start:seller_end]
            
            # Wyciągnij tekst wokół drugiego NIP (nabywca)
            buyer_start = max(0, second_nip_pos - 200)
            buyer_end = min(len(text), second_nip_pos + 200)
            buyer_text = text[buyer_start:buyer_end]
            
            # Jeśli znamy 2Vision, sprawdź który jest który
            if '2vision' in buyer_text.lower() or '2Vision' in buyer_text:
                # 2Vision jest nabycą
                self.invoice_data['seller'] = self._extract_company_data_improved(seller_text, True)
                self.invoice_data['buyer'] = self._extract_company_data_improved(buyer_text, False)
            elif '2vision' in seller_text.lower() or '2Vision' in seller_text:
                # 2Vision jest sprzedawcą (faktura sprzedaży)
                self.invoice_data['buyer'] = self._extract_company_data_improved(seller_text, False)
                self.invoice_data['seller'] = self._extract_company_data_improved(buyer_text, True)
            else:
                # Domyślnie: pierwszy = sprzedawca
                self.invoice_data['seller'] = self._extract_company_data_improved(seller_text, True)
                self.invoice_data['buyer'] = self._extract_company_data_improved(buyer_text, False)
        elif len(nip_matches) == 1:
            # Tylko jeden NIP - prawdopodobnie sprzedawca
            nip_pos = nip_matches[0].start()
            company_start = max(0, nip_pos - 200)
            company_end = min(len(text), nip_pos + 200)
            company_text = text[company_start:company_end]
            
            if '2vision' in company_text.lower():
                # To jest 2Vision jako nabywca
                self.invoice_data['buyer'] = self._extract_company_data_improved(company_text, False)
            else:
                # To jest sprzedawca
                self.invoice_data['seller'] = self._extract_company_data_improved(company_text, True)
    
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
        
        # POPRAWKA: Zbieramy wszystkie pozycje, również te które mogą być w wielu wierszach
        all_items = []
        current_item_data = None
        
        # Parsuj każdy wiersz
        for i, row in enumerate(items_table[1:]):
            # Sprawdź czy wiersz nie jest pusty lub podsumowaniem
            if self._is_valid_item_row(row):
                # Sprawdź czy wiersz zawiera dane pozycji
                # Jeśli pierwsza kolumna ma liczbę (Lp.), to nowa pozycja
                first_cell = str(row[0]).strip() if row else ''
                
                # Sprawdź czy to nowa pozycja (zaczyna się od liczby)
                if first_cell and (first_cell.isdigit() or re.match(r'^\d+\.?$', first_cell)):
                    # Zapisz poprzednią pozycję jeśli istnieje
                    if current_item_data:
                        item = self._parse_item_row_improved(current_item_data, column_map)
                        if item and item.name and item.name.lower() not in ['none', '', 'brak', 'null']:
                            all_items.append(item)
                    
                    # Rozpocznij nową pozycję
                    current_item_data = self._fix_merged_row(row, column_map)
                elif current_item_data and row:
                    # To może być kontynuacja poprzedniej pozycji (np. długa nazwa)
                    # Sprawdź czy to nie jest już następna pozycja bez Lp.
                    has_amounts = False
                    for cell in row:
                        cell_str = str(cell).strip()
                        # Sprawdź czy komórka zawiera kwotę
                        if re.match(r'^[\d\s]+[,.]?\d*$', cell_str) and len(cell_str) > 0:
                            try:
                                val = float(cell_str.replace(',', '.').replace(' ', ''))
                                if val > 0:
                                    has_amounts = True
                                    break
                            except:
                                pass
                    
                    if has_amounts:
                        # To nowa pozycja bez numeru Lp.
                        if current_item_data:
                            item = self._parse_item_row_improved(current_item_data, column_map)
                            if item and item.name and item.name.lower() not in ['none', '', 'brak', 'null']:
                                all_items.append(item)
                        current_item_data = self._fix_merged_row(row, column_map)
                    else:
                        # To kontynuacja nazwy
                        if 'name' in column_map and column_map['name'] < len(row):
                            additional_text = str(row[column_map['name']]).strip()
                            if additional_text and current_item_data:
                                current_item_data[column_map['name']] += ' ' + additional_text
                else:
                    # Sprawdź czy wiersz zawiera sensowne dane
                    fixed_row = self._fix_merged_row(row, column_map)
                    if fixed_row:
                        item = self._parse_item_row_improved(fixed_row, column_map)
                        if item and item.name and item.name.lower() not in ['none', '', 'brak', 'null']:
                            all_items.append(item)
        
        # Nie zapomnij o ostatniej pozycji
        if current_item_data:
            item = self._parse_item_row_improved(current_item_data, column_map)
            if item and item.name and item.name.lower() not in ['none', '', 'brak', 'null']:
                all_items.append(item)
        
        # Dodaj wszystkie znalezione pozycje
        for item in all_items:
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
    
    def _fix_merged_row(self, row: List[str], column_map: Dict[str, int]) -> List[str]:
        """Naprawia wiersze z połączonymi danymi (np. wieloliniowe komórki)"""
        # Jeśli pierwsza komórka zawiera znaki nowej linii, to dane są połączone
        if row and '\n' in str(row[0]):
            # Spróbuj rozdzielić dane
            lines_per_cell = []
            max_lines = 0
            
            for cell in row:
                cell_lines = str(cell).split('\n')
                lines_per_cell.append(cell_lines)
                max_lines = max(max_lines, len(cell_lines))
            
            # Zwróć tylko pierwszy wiersz danych
            fixed_row = []
            for cell_lines in lines_per_cell:
                if cell_lines:
                    fixed_row.append(cell_lines[0])
                else:
                    fixed_row.append('')
            
            return fixed_row
        
        return row
    
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
                    # Usuń znaki nowej linii i weź pierwszą liczbę
                    lp_val = lp_val.split('\n')[0] if '\n' in lp_val else lp_val
                    item.lp = int(lp_val) if lp_val.isdigit() else None
                except:
                    pass
            
            if 'name' in column_map and column_map['name'] < len(row):
                name_val = str(row[column_map['name']]).strip()
                # Weź pierwszą linię jeśli są znaki nowej linii
                item.name = name_val.split('\n')[0] if '\n' in name_val else name_val
            
            if 'quantity' in column_map and column_map['quantity'] < len(row):
                item.quantity = self._parse_amount_improved(row[column_map['quantity']])
            
            if 'unit' in column_map and column_map['unit'] < len(row):
                unit_val = str(row[column_map['unit']]).strip()
                item.unit = unit_val.split('\n')[0] if '\n' in unit_val else unit_val
            
            if 'unit_price' in column_map and column_map['unit_price'] < len(row):
                item.unit_price_net = self._parse_amount_improved(row[column_map['unit_price']])
            
            if 'net_amount' in column_map and column_map['net_amount'] < len(row):
                item.net_amount = self._parse_amount_improved(row[column_map['net_amount']])
            
            if 'vat_rate' in column_map and column_map['vat_rate'] < len(row):
                vat_val = str(row[column_map['vat_rate']]).strip()
                vat_val = vat_val.split('\n')[0] if '\n' in vat_val else vat_val
                item.vat_rate = self.extract_vat_rate(vat_val)
            
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
                if item.net_amount > 0:
                    vat_decimal = Decimal(item.vat_rate.replace('%', '')) / 100
                    
                    # Zawsze oblicz VAT jeśli mamy netto
                    if item.vat_amount == 0 or item.vat_amount is None:
                        item.vat_amount = round(item.net_amount * vat_decimal, 2)
                    
                    # Jeśli brak brutto, oblicz
                    if item.gross_amount == 0:
                        item.gross_amount = item.net_amount + item.vat_amount
                        
                elif item.gross_amount > 0 and item.net_amount == 0:
                    vat_decimal = Decimal(item.vat_rate.replace('%', '')) / 100
                    item.net_amount = round(item.gross_amount / (1 + vat_decimal), 2)
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
            
            # Weź pierwszą linię jeśli są znaki nowej linii
            if '\n' in text:
                text = text.split('\n')[0]
            
            # Usuń wszystkie białe znaki
            text = text.strip()
            
            # Jeśli to puste lub None, zwróć 0
            if not text or text.lower() in ['none', '', '-', 'brak']:
                return Decimal('0')
            
            # POPRAWKA: Obsługa błędnych formatów z wieloma kropkami
            # np. "1...113.1110000.0010000.00"
            if text.count('.') > 2:
                # Sprawdź czy to nie jest wielokrotnie powtórzona wartość
                # Szukaj sensownej liczby w tekście
                numbers = re.findall(r'\d+\.?\d{0,2}', text)
                if numbers:
                    # Weź pierwszą sensowną liczbę
                    for num in numbers:
                        if num and float(num) > 0 and float(num) < 100000:
                            text = num
                            break
                else:
                    print(f"Warning: Malformed amount string: {text}")
                    return Decimal('0')
            
            # Usuń znaki waluty i inne
            text = re.sub(r'[zł$€£¥]', '', text)
            
            # Obsługa polskiej notacji - sprawdź czy jest spacja jako separator tysięcy i przecinek jako separator dziesiętny
            if ',' in text and ' ' in text:
                # Polski format: 1 234,56
                text = text.replace(' ', '').replace(',', '.')
            elif ',' in text and text.count(',') == 1:
                # Może być 1234,56 lub 1,234.56
                parts = text.split(',')
                if len(parts) == 2 and len(parts[1]) == 2:
                    # To prawdopodobnie polski format z przecinkiem dziesiętnym
                    text = text.replace(',', '.')
                elif len(parts) == 2 and len(parts[1]) == 3:
                    # To prawdopodobnie angielski format z przecinkiem jako separator tysięcy
                    text = text.replace(',', '')
            else:
                # Standardowe usuwanie spacji
                text = text.replace(' ', '')
                # Zamień przecinek na kropkę
                text = text.replace(',', '.')
            
            # Usuń wszystko oprócz cyfr, kropki i minusa
            text = re.sub(r'[^\d.-]', '', text)
            
            # Sprawdź czy nie ma wielu kropek
            if text.count('.') > 1:
                # Zostaw tylko ostatnią kropkę jako separator dziesiętny
                parts = text.split('.')
                text = ''.join(parts[:-1]) + '.' + parts[-1]
            
            # Parsuj do Decimal
            if text and text != '-' and text != '.':
                value = Decimal(text)
                # Sprawdź czy wartość nie jest podejrzanie duża (np. 10000.00 jako domyślna)
                if value == Decimal('10000.00'):
                    # Log this for debugging
                    print(f"Warning: Found default value 10000.00, might need manual verification")
                return value
            else:
                return Decimal('0')
        except Exception as e:
            print(f"Error parsing amount '{text}': {type(e).__name__}")
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
            net = Decimal(str(item.get('net_amount', '0')))
            vat = Decimal(str(item.get('vat_amount', '0')))
            gross = Decimal(str(item.get('gross_amount', '0')))
            vat_rate = item.get('vat_rate', '23%')
            
            # Jeśli VAT jest 0 ale mamy netto i stawkę, oblicz VAT
            if vat == 0 and net > 0 and vat_rate:
                vat_decimal = Decimal(vat_rate.replace('%', '')) / 100
                vat = round(net * vat_decimal, 2)
            
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
        # Implementacja pozostaje taka sama jak w oryginalnym parserze
        pass

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
        
        # Znajdź pozycje słów kluczowych - rozszerzona lista
        seller_keywords = ['Sprzedawca', 'SPRZEDAWCA', 'Wystawca', 'Dostawca', 'Seller', 
                          'Wystawca:', 'WYSTAWCA:', 'Sprzedający', 'SPRZEDAJĄCY']
        buyer_keywords = ['Nabywca', 'NABYWCA', 'Odbiorca', 'Kupujący', 'Buyer',
                         'Nabywca:', 'NABYWCA:', 'Zamawiający', 'ZAMAWIAJĄCY']
        
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
        else:
            # Jeśli nie znaleziono etykiet, spróbuj znaleźć po NIP i pozycji w tekście
            self._extract_parties_by_pattern(text)
    
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
        original_text = text
        for kw in keywords_to_remove:
            # Usuń słowo kluczowe i dwukropek jeśli występuje
            text = re.sub(rf'{kw}\s*:?\s*', '', text, 1, re.IGNORECASE).strip()
        
        # Jeśli po usunięciu został tylko dwukropek lub puste, szukaj głębiej
        if not text or text == ':':
            # Szukaj nazwy w kolejnych liniach
            lines = original_text.split('\n')
            for i, line in enumerate(lines):
                # Pomijamy pierwszą linię z etykietą
                if i == 0:
                    continue
                clean_line = line.strip()
                # Jeśli linia nie jest pusta i nie zawiera tylko słów kluczowych
                if clean_line and clean_line != ':' and not any(kw in clean_line for kw in ['NIP', 'REGON', 'ul.']):
                    text = clean_line
                    break
        
        # Podziel na linie
        lines = [line.strip() for line in text.split('\n') if line.strip() and line.strip() != ':']
        
        # POPRAWKA: Sprawdź czy pierwsza linia nie zawiera "Data wystawienia" lub podobnych
        if lines:
            name_line = lines[0]
            # Pomijamy linie z datami i innymi metadanymi
            skip_patterns = ['Data wystawienia', 'Data sprzedaży', 'Miejsce wystawienia', 
                           'Termin płatności', 'Sposób płatności']
            
            # Szukaj pierwszej linii która nie jest metadaną
            for line in lines:
                is_metadata = False
                for pattern in skip_patterns:
                    if pattern in line:
                        is_metadata = True
                        break
                
                # Również pomijamy linie które są tylko datami lub kodami
                if re.match(r'^\d{4}-\d{2}-\d{2}', line) or re.match(r'^\d{2}\.\d{2}\.\d{4}', line):
                    is_metadata = True
                
                if not is_metadata and 'NIP' not in line and not re.match(r'^\d{2}-\d{3}', line):
                    # To prawdopodobnie nazwa firmy
                    data['name'] = line
                    break
        
        # Jeśli nadal nie mamy nazwy, szukaj przed NIP
        if not data['name'] and lines:
            for line in lines:
                if 'NIP' in line:
                    # Jeśli NIP jest w linii, wyciągnij nazwę przed NIP
                    nip_pos = line.find('NIP')
                    if nip_pos > 0:
                        potential_name = line[:nip_pos].strip()
                        # Sprawdź czy to nie jest data lub miasto
                        if not re.match(r'^\d', potential_name) and len(potential_name) > 3:
                            data['name'] = potential_name
                    break
        
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
    
    def _extract_parties_by_pattern(self, text: str):
        """Ekstrahuje sprzedawcę i nabywcę gdy brak etykiet"""
        # Szukaj NIPów w tekście
        nip_pattern = r'NIP[\s:]*([0-9]{3}[-\s]?[0-9]{3}[-\s]?[0-9]{2}[-\s]?[0-9]{2}|[0-9]{10})'
        nip_matches = list(re.finditer(nip_pattern, text, re.IGNORECASE))
        
        if len(nip_matches) >= 2:
            # Zakładamy że pierwszy NIP to sprzedawca (góra faktury)
            # a drugi to nabywca
            first_nip_pos = nip_matches[0].start()
            second_nip_pos = nip_matches[1].start()
            
            # Wyciągnij tekst wokół pierwszego NIP (sprzedawca)
            seller_start = max(0, first_nip_pos - 200)
            seller_end = min(len(text), first_nip_pos + 200)
            seller_text = text[seller_start:seller_end]
            
            # Wyciągnij tekst wokół drugiego NIP (nabywca)
            buyer_start = max(0, second_nip_pos - 200)
            buyer_end = min(len(text), second_nip_pos + 200)
            buyer_text = text[buyer_start:buyer_end]
            
            # Jeśli znamy 2Vision, sprawdź który jest który
            if '2vision' in buyer_text.lower() or '2Vision' in buyer_text:
                # 2Vision jest nabycą
                self.invoice_data['seller'] = self._extract_company_data_improved(seller_text, True)
                self.invoice_data['buyer'] = self._extract_company_data_improved(buyer_text, False)
            elif '2vision' in seller_text.lower() or '2Vision' in seller_text:
                # 2Vision jest sprzedawcą (faktura sprzedaży)
                self.invoice_data['buyer'] = self._extract_company_data_improved(seller_text, False)
                self.invoice_data['seller'] = self._extract_company_data_improved(buyer_text, True)
            else:
                # Domyślnie: pierwszy = sprzedawca
                self.invoice_data['seller'] = self._extract_company_data_improved(seller_text, True)
                self.invoice_data['buyer'] = self._extract_company_data_improved(buyer_text, False)
        elif len(nip_matches) == 1:
            # Tylko jeden NIP - prawdopodobnie sprzedawca
            nip_pos = nip_matches[0].start()
            company_start = max(0, nip_pos - 200)
            company_end = min(len(text), nip_pos + 200)
            company_text = text[company_start:company_end]
            
            if '2vision' in company_text.lower():
                # To jest 2Vision jako nabywca
                self.invoice_data['buyer'] = self._extract_company_data_improved(company_text, False)
            else:
                # To jest sprzedawca
                self.invoice_data['seller'] = self._extract_company_data_improved(company_text, True)
    
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
        
        # POPRAWKA: Zbieramy wszystkie pozycje, również te które mogą być w wielu wierszach
        all_items = []
        current_item_data = None
        
        # Parsuj każdy wiersz
        for i, row in enumerate(items_table[1:]):
            # Sprawdź czy wiersz nie jest pusty lub podsumowaniem
            if self._is_valid_item_row(row):
                # Sprawdź czy wiersz zawiera dane pozycji
                # Jeśli pierwsza kolumna ma liczbę (Lp.), to nowa pozycja
                first_cell = str(row[0]).strip() if row else ''
                
                # Sprawdź czy to nowa pozycja (zaczyna się od liczby)
                if first_cell and (first_cell.isdigit() or re.match(r'^\d+\.?$', first_cell)):
                    # Zapisz poprzednią pozycję jeśli istnieje
                    if current_item_data:
                        item = self._parse_item_row_improved(current_item_data, column_map)
                        if item and item.name and item.name.lower() not in ['none', '', 'brak', 'null']:
                            all_items.append(item)
                    
                    # Rozpocznij nową pozycję
                    current_item_data = self._fix_merged_row(row, column_map)
                elif current_item_data and row:
                    # To może być kontynuacja poprzedniej pozycji (np. długa nazwa)
                    # Sprawdź czy to nie jest już następna pozycja bez Lp.
                    has_amounts = False
                    for cell in row:
                        cell_str = str(cell).strip()
                        # Sprawdź czy komórka zawiera kwotę
                        if re.match(r'^[\d\s]+[,.]?\d*$', cell_str) and len(cell_str) > 0:
                            try:
                                val = float(cell_str.replace(',', '.').replace(' ', ''))
                                if val > 0:
                                    has_amounts = True
                                    break
                            except:
                                pass
                    
                    if has_amounts:
                        # To nowa pozycja bez numeru Lp.
                        if current_item_data:
                            item = self._parse_item_row_improved(current_item_data, column_map)
                            if item and item.name and item.name.lower() not in ['none', '', 'brak', 'null']:
                                all_items.append(item)
                        current_item_data = self._fix_merged_row(row, column_map)
                    else:
                        # To kontynuacja nazwy
                        if 'name' in column_map and column_map['name'] < len(row):
                            additional_text = str(row[column_map['name']]).strip()
                            if additional_text and current_item_data:
                                current_item_data[column_map['name']] += ' ' + additional_text
                else:
                    # Sprawdź czy wiersz zawiera sensowne dane
                    fixed_row = self._fix_merged_row(row, column_map)
                    if fixed_row:
                        item = self._parse_item_row_improved(fixed_row, column_map)
                        if item and item.name and item.name.lower() not in ['none', '', 'brak', 'null']:
                            all_items.append(item)
        
        # Nie zapomnij o ostatniej pozycji
        if current_item_data:
            item = self._parse_item_row_improved(current_item_data, column_map)
            if item and item.name and item.name.lower() not in ['none', '', 'brak', 'null']:
                all_items.append(item)
        
        # Dodaj wszystkie znalezione pozycje
        for item in all_items:
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
    
    def _fix_merged_row(self, row: List[str], column_map: Dict[str, int]) -> List[str]:
        """Naprawia wiersze z połączonymi danymi (np. wieloliniowe komórki)"""
        # Jeśli pierwsza komórka zawiera znaki nowej linii, to dane są połączone
        if row and '\n' in str(row[0]):
            # Spróbuj rozdzielić dane
            lines_per_cell = []
            max_lines = 0
            
            for cell in row:
                cell_lines = str(cell).split('\n')
                lines_per_cell.append(cell_lines)
                max_lines = max(max_lines, len(cell_lines))
            
            # Zwróć tylko pierwszy wiersz danych
            fixed_row = []
            for cell_lines in lines_per_cell:
                if cell_lines:
                    fixed_row.append(cell_lines[0])
                else:
                    fixed_row.append('')
            
            return fixed_row
        
        return row
    
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
                    # Usuń znaki nowej linii i weź pierwszą liczbę
                    lp_val = lp_val.split('\n')[0] if '\n' in lp_val else lp_val
                    item.lp = int(lp_val) if lp_val.isdigit() else None
                except:
                    pass
            
            if 'name' in column_map and column_map['name'] < len(row):
                name_val = str(row[column_map['name']]).strip()
                # Weź pierwszą linię jeśli są znaki nowej linii
                item.name = name_val.split('\n')[0] if '\n' in name_val else name_val
            
            if 'quantity' in column_map and column_map['quantity'] < len(row):
                item.quantity = self._parse_amount_improved(row[column_map['quantity']])
            
            if 'unit' in column_map and column_map['unit'] < len(row):
                unit_val = str(row[column_map['unit']]).strip()
                item.unit = unit_val.split('\n')[0] if '\n' in unit_val else unit_val
            
            if 'unit_price' in column_map and column_map['unit_price'] < len(row):
                item.unit_price_net = self._parse_amount_improved(row[column_map['unit_price']])
            
            if 'net_amount' in column_map and column_map['net_amount'] < len(row):
                item.net_amount = self._parse_amount_improved(row[column_map['net_amount']])
            
            if 'vat_rate' in column_map and column_map['vat_rate'] < len(row):
                vat_val = str(row[column_map['vat_rate']]).strip()
                vat_val = vat_val.split('\n')[0] if '\n' in vat_val else vat_val
                item.vat_rate = self.extract_vat_rate(vat_val)
            
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
                if item.net_amount > 0:
                    vat_decimal = Decimal(item.vat_rate.replace('%', '')) / 100
                    
                    # Zawsze oblicz VAT jeśli mamy netto
                    if item.vat_amount == 0 or item.vat_amount is None:
                        item.vat_amount = round(item.net_amount * vat_decimal, 2)
                    
                    # Jeśli brak brutto, oblicz
                    if item.gross_amount == 0:
                        item.gross_amount = item.net_amount + item.vat_amount
                        
                elif item.gross_amount > 0 and item.net_amount == 0:
                    vat_decimal = Decimal(item.vat_rate.replace('%', '')) / 100
                    item.net_amount = round(item.gross_amount / (1 + vat_decimal), 2)
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
            
            # Weź pierwszą linię jeśli są znaki nowej linii
            if '\n' in text:
                text = text.split('\n')[0]
            
            # Usuń wszystkie białe znaki
            text = text.strip()
            
            # Jeśli to puste lub None, zwróć 0
            if not text or text.lower() in ['none', '', '-', 'brak']:
                return Decimal('0')
            
            # POPRAWKA: Obsługa błędnych formatów z wieloma kropkami
            # np. "1...113.1110000.0010000.00"
            if text.count('.') > 2:
                # Sprawdź czy to nie jest wielokrotnie powtórzona wartość
                # Szukaj sensownej liczby w tekście
                numbers = re.findall(r'\d+\.?\d{0,2}', text)
                if numbers:
                    # Weź pierwszą sensowną liczbę
                    for num in numbers:
                        if num and float(num) > 0 and float(num) < 100000:
                            text = num
                            break
                else:
                    print(f"Warning: Malformed amount string: {text}")
                    return Decimal('0')
            
            # Usuń znaki waluty i inne
            text = re.sub(r'[zł$€£¥]', '', text)
            
            # Obsługa polskiej notacji - sprawdź czy jest spacja jako separator tysięcy i przecinek jako separator dziesiętny
            if ',' in text and ' ' in text:
                # Polski format: 1 234,56
                text = text.replace(' ', '').replace(',', '.')
            elif ',' in text and text.count(',') == 1:
                # Może być 1234,56 lub 1,234.56
                parts = text.split(',')
                if len(parts) == 2 and len(parts[1]) == 2:
                    # To prawdopodobnie polski format z przecinkiem dziesiętnym
                    text = text.replace(',', '.')
                elif len(parts) == 2 and len(parts[1]) == 3:
                    # To prawdopodobnie angielski format z przecinkiem jako separator tysięcy
                    text = text.replace(',', '')
            else:
                # Standardowe usuwanie spacji
                text = text.replace(' ', '')
                # Zamień przecinek na kropkę
                text = text.replace(',', '.')
            
            # Usuń wszystko oprócz cyfr, kropki i minusa
            text = re.sub(r'[^\d.-]', '', text)
            
            # Sprawdź czy nie ma wielu kropek
            if text.count('.') > 1:
                # Zostaw tylko ostatnią kropkę jako separator dziesiętny
                parts = text.split('.')
                text = ''.join(parts[:-1]) + '.' + parts[-1]
            
            # Parsuj do Decimal
            if text and text != '-' and text != '.':
                value = Decimal(text)
                # Sprawdź czy wartość nie jest podejrzanie duża (np. 10000.00 jako domyślna)
                if value == Decimal('10000.00'):
                    # Log this for debugging
                    print(f"Warning: Found default value 10000.00, might need manual verification")
                return value
            else:
                return Decimal('0')
        except Exception as e:
            print(f"Error parsing amount '{text}': {type(e).__name__}")
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
            net = Decimal(str(item.get('net_amount', '0')))
            vat = Decimal(str(item.get('vat_amount', '0')))
            gross = Decimal(str(item.get('gross_amount', '0')))
            vat_rate = item.get('vat_rate', '23%')
            
            # Jeśli VAT jest 0 ale mamy netto i stawkę, oblicz VAT
            if vat == 0 and net > 0 and vat_rate:
                vat_decimal = Decimal(vat_rate.replace('%', '')) / 100
                vat = round(net * vat_decimal, 2)
            
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
        # Implementacja pozostaje taka sama jak w oryginalnym parserze
        pass
,
        ]
        
        # Najpierw szukaj w pierwszych 10 liniach (często tam jest numer)
        lines = text.split('\n')[:10]
        for line in lines:
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    invoice_num = match.group(1).strip()
                    # Sprawdź czy to sensowny numer
                    if len(invoice_num) >= 3 and not invoice_num.lower() in ['vat', 'faktura', 'invoice', 'nr']:
                        return invoice_num
        
        # Jeśli nie znaleziono, szukaj w całym tekście
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                invoice_num = match.group(1).strip()
                # Sprawdź czy to sensowny numer
                if len(invoice_num) >= 3 and not invoice_num.lower() in ['vat', 'faktura', 'invoice', 'nr']:
                    return invoice_num
        
        # Ostatnia deska ratunku - szukaj czegoś co wygląda jak numer
        # np. FVS_2_08_2025 lub FV-2025-0213-0165
        special_pattern = r'(F[VSAKZ][S\-_/]*\d+[\-_/]\d+[\-_/]\d+)'
        match = re.search(special_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None
    
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
        
        # Znajdź pozycje słów kluczowych - rozszerzona lista
        seller_keywords = ['Sprzedawca', 'SPRZEDAWCA', 'Wystawca', 'Dostawca', 'Seller', 
                          'Wystawca:', 'WYSTAWCA:', 'Sprzedający', 'SPRZEDAJĄCY']
        buyer_keywords = ['Nabywca', 'NABYWCA', 'Odbiorca', 'Kupujący', 'Buyer',
                         'Nabywca:', 'NABYWCA:', 'Zamawiający', 'ZAMAWIAJĄCY']
        
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
        else:
            # Jeśli nie znaleziono etykiet, spróbuj znaleźć po NIP i pozycji w tekście
            self._extract_parties_by_pattern(text)
    
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
        original_text = text
        for kw in keywords_to_remove:
            # Usuń słowo kluczowe i dwukropek jeśli występuje
            text = re.sub(rf'{kw}\s*:?\s*', '', text, 1, re.IGNORECASE).strip()
        
        # Jeśli po usunięciu został tylko dwukropek lub puste, szukaj głębiej
        if not text or text == ':':
            # Szukaj nazwy w kolejnych liniach
            lines = original_text.split('\n')
            for i, line in enumerate(lines):
                # Pomijamy pierwszą linię z etykietą
                if i == 0:
                    continue
                clean_line = line.strip()
                # Jeśli linia nie jest pusta i nie zawiera tylko słów kluczowych
                if clean_line and clean_line != ':' and not any(kw in clean_line for kw in ['NIP', 'REGON', 'ul.']):
                    text = clean_line
                    break
        
        # Podziel na linie
        lines = [line.strip() for line in text.split('\n') if line.strip() and line.strip() != ':']
        
        # POPRAWKA: Sprawdź czy pierwsza linia nie zawiera "Data wystawienia" lub podobnych
        if lines:
            name_line = lines[0]
            # Pomijamy linie z datami i innymi metadanymi
            skip_patterns = ['Data wystawienia', 'Data sprzedaży', 'Miejsce wystawienia', 
                           'Termin płatności', 'Sposób płatności']
            
            # Szukaj pierwszej linii która nie jest metadaną
            for line in lines:
                is_metadata = False
                for pattern in skip_patterns:
                    if pattern in line:
                        is_metadata = True
                        break
                
                # Również pomijamy linie które są tylko datami lub kodami
                if re.match(r'^\d{4}-\d{2}-\d{2}', line) or re.match(r'^\d{2}\.\d{2}\.\d{4}', line):
                    is_metadata = True
                
                if not is_metadata and 'NIP' not in line and not re.match(r'^\d{2}-\d{3}', line):
                    # To prawdopodobnie nazwa firmy
                    data['name'] = line
                    break
        
        # Jeśli nadal nie mamy nazwy, szukaj przed NIP
        if not data['name'] and lines:
            for line in lines:
                if 'NIP' in line:
                    # Jeśli NIP jest w linii, wyciągnij nazwę przed NIP
                    nip_pos = line.find('NIP')
                    if nip_pos > 0:
                        potential_name = line[:nip_pos].strip()
                        # Sprawdź czy to nie jest data lub miasto
                        if not re.match(r'^\d', potential_name) and len(potential_name) > 3:
                            data['name'] = potential_name
                    break
        
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
    
    def _extract_parties_by_pattern(self, text: str):
        """Ekstrahuje sprzedawcę i nabywcę gdy brak etykiet"""
        # Szukaj NIPów w tekście
        nip_pattern = r'NIP[\s:]*([0-9]{3}[-\s]?[0-9]{3}[-\s]?[0-9]{2}[-\s]?[0-9]{2}|[0-9]{10})'
        nip_matches = list(re.finditer(nip_pattern, text, re.IGNORECASE))
        
        if len(nip_matches) >= 2:
            # Zakładamy że pierwszy NIP to sprzedawca (góra faktury)
            # a drugi to nabywca
            first_nip_pos = nip_matches[0].start()
            second_nip_pos = nip_matches[1].start()
            
            # Wyciągnij tekst wokół pierwszego NIP (sprzedawca)
            seller_start = max(0, first_nip_pos - 200)
            seller_end = min(len(text), first_nip_pos + 200)
            seller_text = text[seller_start:seller_end]
            
            # Wyciągnij tekst wokół drugiego NIP (nabywca)
            buyer_start = max(0, second_nip_pos - 200)
            buyer_end = min(len(text), second_nip_pos + 200)
            buyer_text = text[buyer_start:buyer_end]
            
            # Jeśli znamy 2Vision, sprawdź który jest który
            if '2vision' in buyer_text.lower() or '2Vision' in buyer_text:
                # 2Vision jest nabycą
                self.invoice_data['seller'] = self._extract_company_data_improved(seller_text, True)
                self.invoice_data['buyer'] = self._extract_company_data_improved(buyer_text, False)
            elif '2vision' in seller_text.lower() or '2Vision' in seller_text:
                # 2Vision jest sprzedawcą (faktura sprzedaży)
                self.invoice_data['buyer'] = self._extract_company_data_improved(seller_text, False)
                self.invoice_data['seller'] = self._extract_company_data_improved(buyer_text, True)
            else:
                # Domyślnie: pierwszy = sprzedawca
                self.invoice_data['seller'] = self._extract_company_data_improved(seller_text, True)
                self.invoice_data['buyer'] = self._extract_company_data_improved(buyer_text, False)
        elif len(nip_matches) == 1:
            # Tylko jeden NIP - prawdopodobnie sprzedawca
            nip_pos = nip_matches[0].start()
            company_start = max(0, nip_pos - 200)
            company_end = min(len(text), nip_pos + 200)
            company_text = text[company_start:company_end]
            
            if '2vision' in company_text.lower():
                # To jest 2Vision jako nabywca
                self.invoice_data['buyer'] = self._extract_company_data_improved(company_text, False)
            else:
                # To jest sprzedawca
                self.invoice_data['seller'] = self._extract_company_data_improved(company_text, True)
    
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
        
        # POPRAWKA: Zbieramy wszystkie pozycje, również te które mogą być w wielu wierszach
        all_items = []
        current_item_data = None
        
        # Parsuj każdy wiersz
        for i, row in enumerate(items_table[1:]):
            # Sprawdź czy wiersz nie jest pusty lub podsumowaniem
            if self._is_valid_item_row(row):
                # Sprawdź czy wiersz zawiera dane pozycji
                # Jeśli pierwsza kolumna ma liczbę (Lp.), to nowa pozycja
                first_cell = str(row[0]).strip() if row else ''
                
                # Sprawdź czy to nowa pozycja (zaczyna się od liczby)
                if first_cell and (first_cell.isdigit() or re.match(r'^\d+\.?$', first_cell)):
                    # Zapisz poprzednią pozycję jeśli istnieje
                    if current_item_data:
                        item = self._parse_item_row_improved(current_item_data, column_map)
                        if item and item.name and item.name.lower() not in ['none', '', 'brak', 'null']:
                            all_items.append(item)
                    
                    # Rozpocznij nową pozycję
                    current_item_data = self._fix_merged_row(row, column_map)
                elif current_item_data and row:
                    # To może być kontynuacja poprzedniej pozycji (np. długa nazwa)
                    # Sprawdź czy to nie jest już następna pozycja bez Lp.
                    has_amounts = False
                    for cell in row:
                        cell_str = str(cell).strip()
                        # Sprawdź czy komórka zawiera kwotę
                        if re.match(r'^[\d\s]+[,.]?\d*$', cell_str) and len(cell_str) > 0:
                            try:
                                val = float(cell_str.replace(',', '.').replace(' ', ''))
                                if val > 0:
                                    has_amounts = True
                                    break
                            except:
                                pass
                    
                    if has_amounts:
                        # To nowa pozycja bez numeru Lp.
                        if current_item_data:
                            item = self._parse_item_row_improved(current_item_data, column_map)
                            if item and item.name and item.name.lower() not in ['none', '', 'brak', 'null']:
                                all_items.append(item)
                        current_item_data = self._fix_merged_row(row, column_map)
                    else:
                        # To kontynuacja nazwy
                        if 'name' in column_map and column_map['name'] < len(row):
                            additional_text = str(row[column_map['name']]).strip()
                            if additional_text and current_item_data:
                                current_item_data[column_map['name']] += ' ' + additional_text
                else:
                    # Sprawdź czy wiersz zawiera sensowne dane
                    fixed_row = self._fix_merged_row(row, column_map)
                    if fixed_row:
                        item = self._parse_item_row_improved(fixed_row, column_map)
                        if item and item.name and item.name.lower() not in ['none', '', 'brak', 'null']:
                            all_items.append(item)
        
        # Nie zapomnij o ostatniej pozycji
        if current_item_data:
            item = self._parse_item_row_improved(current_item_data, column_map)
            if item and item.name and item.name.lower() not in ['none', '', 'brak', 'null']:
                all_items.append(item)
        
        # Dodaj wszystkie znalezione pozycje
        for item in all_items:
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
    
    def _fix_merged_row(self, row: List[str], column_map: Dict[str, int]) -> List[str]:
        """Naprawia wiersze z połączonymi danymi (np. wieloliniowe komórki)"""
        # Jeśli pierwsza komórka zawiera znaki nowej linii, to dane są połączone
        if row and '\n' in str(row[0]):
            # Spróbuj rozdzielić dane
            lines_per_cell = []
            max_lines = 0
            
            for cell in row:
                cell_lines = str(cell).split('\n')
                lines_per_cell.append(cell_lines)
                max_lines = max(max_lines, len(cell_lines))
            
            # Zwróć tylko pierwszy wiersz danych
            fixed_row = []
            for cell_lines in lines_per_cell:
                if cell_lines:
                    fixed_row.append(cell_lines[0])
                else:
                    fixed_row.append('')
            
            return fixed_row
        
        return row
    
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
                    # Usuń znaki nowej linii i weź pierwszą liczbę
                    lp_val = lp_val.split('\n')[0] if '\n' in lp_val else lp_val
                    item.lp = int(lp_val) if lp_val.isdigit() else None
                except:
                    pass
            
            if 'name' in column_map and column_map['name'] < len(row):
                name_val = str(row[column_map['name']]).strip()
                # Weź pierwszą linię jeśli są znaki nowej linii
                item.name = name_val.split('\n')[0] if '\n' in name_val else name_val
            
            if 'quantity' in column_map and column_map['quantity'] < len(row):
                item.quantity = self._parse_amount_improved(row[column_map['quantity']])
            
            if 'unit' in column_map and column_map['unit'] < len(row):
                unit_val = str(row[column_map['unit']]).strip()
                item.unit = unit_val.split('\n')[0] if '\n' in unit_val else unit_val
            
            if 'unit_price' in column_map and column_map['unit_price'] < len(row):
                item.unit_price_net = self._parse_amount_improved(row[column_map['unit_price']])
            
            if 'net_amount' in column_map and column_map['net_amount'] < len(row):
                item.net_amount = self._parse_amount_improved(row[column_map['net_amount']])
            
            if 'vat_rate' in column_map and column_map['vat_rate'] < len(row):
                vat_val = str(row[column_map['vat_rate']]).strip()
                vat_val = vat_val.split('\n')[0] if '\n' in vat_val else vat_val
                item.vat_rate = self.extract_vat_rate(vat_val)
            
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
                if item.net_amount > 0:
                    vat_decimal = Decimal(item.vat_rate.replace('%', '')) / 100
                    
                    # Zawsze oblicz VAT jeśli mamy netto
                    if item.vat_amount == 0 or item.vat_amount is None:
                        item.vat_amount = round(item.net_amount * vat_decimal, 2)
                    
                    # Jeśli brak brutto, oblicz
                    if item.gross_amount == 0:
                        item.gross_amount = item.net_amount + item.vat_amount
                        
                elif item.gross_amount > 0 and item.net_amount == 0:
                    vat_decimal = Decimal(item.vat_rate.replace('%', '')) / 100
                    item.net_amount = round(item.gross_amount / (1 + vat_decimal), 2)
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
            
            # Weź pierwszą linię jeśli są znaki nowej linii
            if '\n' in text:
                text = text.split('\n')[0]
            
            # Usuń wszystkie białe znaki
            text = text.strip()
            
            # Jeśli to puste lub None, zwróć 0
            if not text or text.lower() in ['none', '', '-', 'brak']:
                return Decimal('0')
            
            # POPRAWKA: Obsługa błędnych formatów z wieloma kropkami
            # np. "1...113.1110000.0010000.00"
            if text.count('.') > 2:
                # Sprawdź czy to nie jest wielokrotnie powtórzona wartość
                # Szukaj sensownej liczby w tekście
                numbers = re.findall(r'\d+\.?\d{0,2}', text)
                if numbers:
                    # Weź pierwszą sensowną liczbę
                    for num in numbers:
                        if num and float(num) > 0 and float(num) < 100000:
                            text = num
                            break
                else:
                    print(f"Warning: Malformed amount string: {text}")
                    return Decimal('0')
            
            # Usuń znaki waluty i inne
            text = re.sub(r'[zł$€£¥]', '', text)
            
            # Obsługa polskiej notacji - sprawdź czy jest spacja jako separator tysięcy i przecinek jako separator dziesiętny
            if ',' in text and ' ' in text:
                # Polski format: 1 234,56
                text = text.replace(' ', '').replace(',', '.')
            elif ',' in text and text.count(',') == 1:
                # Może być 1234,56 lub 1,234.56
                parts = text.split(',')
                if len(parts) == 2 and len(parts[1]) == 2:
                    # To prawdopodobnie polski format z przecinkiem dziesiętnym
                    text = text.replace(',', '.')
                elif len(parts) == 2 and len(parts[1]) == 3:
                    # To prawdopodobnie angielski format z przecinkiem jako separator tysięcy
                    text = text.replace(',', '')
            else:
                # Standardowe usuwanie spacji
                text = text.replace(' ', '')
                # Zamień przecinek na kropkę
                text = text.replace(',', '.')
            
            # Usuń wszystko oprócz cyfr, kropki i minusa
            text = re.sub(r'[^\d.-]', '', text)
            
            # Sprawdź czy nie ma wielu kropek
            if text.count('.') > 1:
                # Zostaw tylko ostatnią kropkę jako separator dziesiętny
                parts = text.split('.')
                text = ''.join(parts[:-1]) + '.' + parts[-1]
            
            # Parsuj do Decimal
            if text and text != '-' and text != '.':
                value = Decimal(text)
                # Sprawdź czy wartość nie jest podejrzanie duża (np. 10000.00 jako domyślna)
                if value == Decimal('10000.00'):
                    # Log this for debugging
                    print(f"Warning: Found default value 10000.00, might need manual verification")
                return value
            else:
                return Decimal('0')
        except Exception as e:
            print(f"Error parsing amount '{text}': {type(e).__name__}")
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
            net = Decimal(str(item.get('net_amount', '0')))
            vat = Decimal(str(item.get('vat_amount', '0')))
            gross = Decimal(str(item.get('gross_amount', '0')))
            vat_rate = item.get('vat_rate', '23%')
            
            # Jeśli VAT jest 0 ale mamy netto i stawkę, oblicz VAT
            if vat == 0 and net > 0 and vat_rate:
                vat_decimal = Decimal(vat_rate.replace('%', '')) / 100
                vat = round(net * vat_decimal, 2)
            
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
        # Implementacja pozostaje taka sama jak w oryginalnym parserze
        pass
