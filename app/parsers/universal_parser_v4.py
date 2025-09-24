"""
Parser uniwersalny dla różnych typów faktur - wersja 4
Poprawiona ekstrakcja danych z rozwiązaniem problemów:
- Brak NIP sprzedawcy
- Nierozpoznany sprzedawca
- Brak numeru faktury
- Brak pozycji faktury
- VAT = 0
"""
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import re
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_parser import BaseInvoiceParser, InvoiceItem

class UniversalParser(BaseInvoiceParser):
    """Parser uniwersalny dla różnych typów faktur - wersja 4 ulepszona"""
    
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
        
        # Fallback dla numeru faktury z nazwy pliku
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
        """Ulepszona ekstrakcja numeru faktury - obsługa różnych formatów"""
        
        # Rozszerzona lista wzorców
        patterns = [
            # Standardowe wzorce
            r'(?:Faktura\s+(?:VAT\s+)?(?:nr|Nr\.?)\s*[:s]?)([A-Za-z0-9\-/_]+)',
            r'(?:FAKTURA\s+(?:VAT\s+)?(?:NR|Nr\.?)\s*[:s]?)([A-Za-z0-9\-/_]+)',
            r'(?:Invoice\s+(?:number|no\.?)\s*[:s]?)([A-Za-z0-9\-/_]+)',
            r'(?:Numer\s+faktury\s*[:s]?)([A-Za-z0-9\-/_]+)',
            
            # Wzorce specyficzne - obsługa FVS, FS itp.
            r'(F[VSAKZ][S]?[\-_/]*\d+[\-_/]\d+[\-_/]\d+)',  # FVS_2_08_2025, FS_4447_08_2025
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
        special_patterns = [
            r'(F[VSAKZ][S]?[\-_/]*\d+[\-_/]\d+[\-_/]\d+)',
            r'(FV[\-_/]\d{4}[\-_/]\d+[\-_/]\d+)',
            r'(\d+[\-_/]\d+[\-_/]\d{4})'  # Prosty format daty jako numer
        ]
        
        for pattern in special_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_number_from_filename(self, filename: str) -> str:
        """Ekstrahuje numer faktury z nazwy pliku jako ostatni fallback"""
        if not filename:
            return ''
        
        # Usuń rozszerzenie
        name = os.path.splitext(filename)[0]
        
        # Szukaj wzorców w nazwie pliku
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
                          'Wystawca:', 'WYSTAWCA:', 'Sprzedający', 'SPRZEDAJĄCY', 'Vendor']
        buyer_keywords = ['Nabywca', 'NABYWCA', 'Odbiorca', 'Kupujący', 'Buyer',
                         'Nabywca:', 'NABYWCA:', 'Zamawiający', 'ZAMAWIAJĄCY', 'Customer']
        
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
            # Określ kolejność i wyciągnij sekcje
            if seller_pos < buyer_pos:
                seller_text = text[seller_pos:buyer_pos]
                buyer_text = self._extract_buyer_section(text, buyer_pos)
            else:
                buyer_text = text[buyer_pos:seller_pos]
                seller_text = self._extract_seller_section(text, seller_pos)
            
            self.invoice_data['seller'] = self._extract_company_data_improved(seller_text, True)
            self.invoice_data['buyer'] = self._extract_company_data_improved(buyer_text, False)
        else:
            # Jeśli nie znaleziono etykiet, szukaj po NIP
            self._extract_parties_by_nip(text)
    
    def _extract_seller_section(self, text: str, start_pos: int) -> str:
        """Wyciąga sekcję sprzedawcy"""
        end_keywords = ['Lp', 'L.p.', 'Pozycje', 'Santander', 'Razem', 'PKO', 'Items']
        end_pos = len(text)
        
        for kw in end_keywords:
            pos = text.find(kw, start_pos)
            if pos != -1:
                end_pos = min(end_pos, pos)
        
        return text[start_pos:end_pos]
    
    def _extract_buyer_section(self, text: str, start_pos: int) -> str:
        """Wyciąga sekcję nabywcy"""
        end_keywords = ['Lp', 'L.p.', 'Pozycje', 'Santander', 'Razem', 'PKO', 'Items']
        end_pos = len(text)
        
        for kw in end_keywords:
            pos = text.find(kw, start_pos)
            if pos != -1:
                end_pos = min(end_pos, pos)
        
        return text[start_pos:end_pos]
    
    def _extract_parties_by_nip(self, text: str):
        """Ekstrahuje sprzedawcę i nabywcę po NIP gdy brak etykiet"""
        # Szukaj wszystkich NIPów w tekście
        nip_pattern = r'NIP[\s:]*([0-9]{3}[-\s]?[0-9]{3}[-\s]?[0-9]{2}[-\s]?[0-9]{2}|[0-9]{10})'
        nip_matches = list(re.finditer(nip_pattern, text, re.IGNORECASE))
        
        if len(nip_matches) >= 2:
            # Pierwszy NIP to zazwyczaj sprzedawca (góra faktury)
            first_nip_pos = nip_matches[0].start()
            second_nip_pos = nip_matches[1].start()
            
            # Wyciągnij kontekst wokół NIPów
            seller_text = text[max(0, first_nip_pos - 200):min(len(text), first_nip_pos + 200)]
            buyer_text = text[max(0, second_nip_pos - 200):min(len(text), second_nip_pos + 200)]
            
            # Sprawdź czy 2Vision jest w którymś z tekstów
            if '2vision' in buyer_text.lower():
                # 2Vision jest nabywcą
                self.invoice_data['buyer'] = self._extract_company_data_improved(buyer_text, False)
                self.invoice_data['seller'] = self._extract_company_data_improved(seller_text, True)
            elif '2vision' in seller_text.lower():
                # 2Vision jest sprzedawcą (rzadko, ale możliwe)
                self.invoice_data['seller'] = self._extract_company_data_improved(seller_text, True)
                self.invoice_data['buyer'] = self._extract_company_data_improved(buyer_text, False)
            else:
                # Domyślnie pierwszy NIP = sprzedawca
                self.invoice_data['seller'] = self._extract_company_data_improved(seller_text, True)
                self.invoice_data['buyer'] = self._extract_company_data_improved(buyer_text, False)
        elif len(nip_matches) == 1:
            # Tylko jeden NIP - prawdopodobnie sprzedawca
            nip_pos = nip_matches[0].start()
            company_text = text[max(0, nip_pos - 200):min(len(text), nip_pos + 200)]
            
            # Sprawdź czy to 2Vision
            if '2vision' in company_text.lower():
                self.invoice_data['buyer'] = self._extract_company_data_improved(company_text, False)
                # Spróbuj znaleźć sprzedawcę w inny sposób
                self._find_seller_without_nip(text)
            else:
                self.invoice_data['seller'] = self._extract_company_data_improved(company_text, True)
                # Ustaw domyślne dane nabywcy (2Vision)
                self._set_default_buyer()
    
    def _find_seller_without_nip(self, text: str):
        """Próbuje znaleźć sprzedawcę gdy nie ma NIP"""
        # Szukaj charakterystycznych nazw firm
        known_sellers = [
            ('nazwa.pl', {'name': 'nazwa.pl sp. z o.o.', 'nip': '7342867148'}),
            ('Zagamix', {'name': 'Zagamix', 'nip': ''}),
            ('MULTI', {'name': 'MULTI', 'nip': ''}),
            ('Hotel Stara Poczta', {'name': 'Hotel Stara Poczta', 'nip': ''}),
            ('Grzegorz Jakubowski', {'name': 'Grzegorz Jakubowski', 'nip': ''})
        ]
        
        for company_name, company_data in known_sellers:
            if company_name.lower() in text.lower():
                self.invoice_data['seller'].update(company_data)
                break
    
    def _set_default_buyer(self):
        """Ustawia domyślne dane nabywcy (2Vision)"""
        self.invoice_data['buyer'] = {
            'name': '2Vision Sp. z o.o.',
            'nip': '6751781780',
            'address': 'ul. Dąbska 20A/17',
            'city': 'Kraków',
            'postal_code': '31-572',
            'country': 'Polska'
        }
    
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
        
        # Usuń słowa kluczowe
        keywords_to_remove = ['Sprzedawca', 'SPRZEDAWCA', 'Nabywca', 'NABYWCA', 
                             'Wystawca', 'Odbiorca', 'Kupujący', 'Dostawca', 'Vendor', 'Customer']
        
        for kw in keywords_to_remove:
            text = re.sub(rf'{kw}\s*:?\s*', '', text, 1, re.IGNORECASE).strip()
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Znajdź nazwę firmy (pierwsza linia która nie jest metadaną)
        skip_patterns = ['Data wystawienia', 'Data sprzedaży', 'Miejsce wystawienia', 
                        'Termin płatności', 'Sposób płatności', 'NIP', 'REGON']
        
        for line in lines:
            is_metadata = False
            for pattern in skip_patterns:
                if pattern in line:
                    is_metadata = True
                    break
            
            # Pomijamy linie będące datami lub kodami
            if re.match(r'^\d{4}-\d{2}-\d{2}', line) or re.match(r'^\d{2}\.\d{2}\.\d{4}', line):
                is_metadata = True
            
            if not is_metadata and not re.match(r'^\d{2}-\d{3}', line):
                data['name'] = line
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
        for line in lines:
            if line == data['name'] or 'NIP' in line:
                continue
            
            # Szukamy linii z numerem domu/mieszkania
            if re.search(r'\d+[A-Za-z]?(?:/\d+)?(?:\s|$)', line):
                # Sprawdzamy czy to nie kod pocztowy
                if not re.match(r'\d{2}[-\s]\d{3}', line):
                    # Usuń "ul." jeśli jest
                    address = re.sub(r'^ul\.?\s*', '', line, flags=re.IGNORECASE)
                    # Usuń część z kodem pocztowym
                    address = re.split(r'\d{2}[-\s]\d{3}', address)[0].strip()
                    if address:
                        data['address'] = address
                        break
        
        return data
    
    def _extract_items_from_tables_improved(self, tables: List[List[List[str]]], text: str):
        """Ulepszona ekstrakcja pozycji z tabel"""
        
        # Znajdź tabelę z pozycjami
        items_table = None
        for table in tables:
            if self._is_items_table_improved(table):
                items_table = table
                break
        
        if not items_table:
            return
        
        # Identyfikuj kolumny
        header = items_table[0] if items_table else []
        column_map = self._identify_columns(header)
        
        # Parsuj pozycje
        for i, row in enumerate(items_table[1:]):
            if self._is_valid_item_row(row):
                item = self._parse_item_row_improved(row, column_map)
                if item and item.name:
                    self.invoice_data['items'].append(item.to_dict())
    
    def _is_items_table_improved(self, table: List[List[str]]) -> bool:
        """Ulepszone sprawdzanie czy tabela zawiera pozycje"""
        if not table or len(table) < 2:
            return False
        
        header = ' '.join(str(cell).lower() for cell in table[0])
        
        # Kluczowe słowa dla tabeli pozycji
        required_keywords = ['nazwa', 'wartość', 'ilość', 'towar', 'usługa']
        optional_keywords = ['lp', 'cena', 'netto', 'brutto', 'vat', 'stawka', 'kwota']
        
        required_matches = sum(1 for kw in required_keywords if kw in header)
        optional_matches = sum(1 for kw in optional_keywords if kw in header)
        
        # Tabela pozycji powinna mieć przynajmniej 2 wymagane słowa
        # lub 1 wymagane i 2 opcjonalne
        return required_matches >= 2 or (required_matches >= 1 and optional_matches >= 2)
    
    def _is_valid_item_row(self, row: List[str]) -> bool:
        """Sprawdza czy wiersz zawiera prawidłową pozycję"""
        if not row or all(not str(cell).strip() for cell in row):
            return False
        
        first_cell = str(row[0]).lower() if row else ''
        skip_words = ['razem', 'suma', 'ogółem', 'total', 'podsumowanie', 'stawka vat', 'według stawek']
        
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
                vat_val = str(row[column_map['vat_rate']]).strip()
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
                    
                    if item.vat_amount == 0 or item.vat_amount is None:
                        item.vat_amount = round(item.net_amount * vat_decimal, 2)
                    
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
        """Ulepszone parsowanie kwot - obsługa różnych formatów"""
        try:
            text = str(text).strip()
            
            if not text or text.lower() in ['none', '', '-', 'brak']:
                return Decimal('0')
            
            # Obsługa błędnych formatów z wieloma kropkami
            if text.count('.') > 2:
                # Szukaj sensownej liczby
                numbers = re.findall(r'\d+\.?\d{0,2}', text)
                for num in numbers:
                    if num and 0 < float(num) < 100000:
                        text = num
                        break
                else:
                    return Decimal('0')
            
            # Usuń znaki waluty
            text = re.sub(r'[zł$€£¥]', '', text)
            
            # Obsługa polskiej notacji (spacja jako separator tysięcy, przecinek dziesiętny)
            if ',' in text:
                if ' ' in text:
                    # Polski format: 1 234,56
                    text = text.replace(' ', '').replace(',', '.')
                else:
                    parts = text.split(',')
                    if len(parts) == 2 and len(parts[1]) == 2:
                        # Polski format: 1234,56
                        text = text.replace(',', '.')
                    elif len(parts) == 2 and len(parts[1]) == 3:
                        # Angielski format: 1,234.56
                        text = text.replace(',', '')
            else:
                text = text.replace(' ', '')
            
            # Usuń wszystko oprócz cyfr, kropki i minusa
            text = re.sub(r'[^\d.-]', '', text)
            
            # Normalizuj kropki
            if text.count('.') > 1:
                parts = text.split('.')
                text = ''.join(parts[:-1]) + '.' + parts[-1]
            
            if text and text not in ['-', '.']:
                return Decimal(text)
            else:
                return Decimal('0')
                
        except Exception as e:
            print(f"Error parsing amount '{text}': {e}")
            return Decimal('0')
    
    def _extract_summary_improved(self, text: str, tables: List[List[List[str]]]):
        """Ulepszona ekstrakcja podsumowania"""
        
        # Szukaj tabeli z podsumowaniem VAT
        vat_summary_table = None
        for table in tables:
            if self._is_vat_summary_table(table):
                vat_summary_table = table
                break
        
        if vat_summary_table:
            self._extract_summary_from_table(vat_summary_table)
        
        # Szukaj sum w tekście
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
        keywords = ['stawka vat', 'stawka', 'wartość netto', 'kwota vat', 'wartość brutto', 'według stawek']
        
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
                first_cell = str(row[0]).lower()
                
                if 'razem' in first_cell or 'suma' in first_cell:
                    # Wiersz z podsumowaniem
                    if 'net' in column_map:
                        total_net = self._parse_amount_improved(row[column_map['net']])
                    if 'vat' in column_map:
                        total_vat = self._parse_amount_improved(row[column_map['vat']])
                    if 'gross' in column_map:
                        total_gross = self._parse_amount_improved(row[column_map['gross']])
                else:
                    # Wiersz ze stawką VAT
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
        """Ekstrahuje pozycje bezpośrednio z tekstu gdy brak tabel"""
        # Różne wzorce dla różnych formatów
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
                item.quantity = self._parse_amount_improved(groups[2])
                item.unit = groups[3]
                item.unit_price_net = self._parse_amount_improved(groups[4])
                item.net_amount = self._parse_amount_improved(groups[5])
                item.vat_rate = f"{groups[6]}%"
                item.vat_amount = self._parse_amount_improved(groups[7])
                item.gross_amount = self._parse_amount_improved(groups[8])
            elif len(groups) == 5:  # Uproszczony format
                item.name = groups[0].strip()
                item.quantity = self._parse_amount_improved(groups[1])
                item.net_amount = self._parse_amount_improved(groups[2])
                item.vat_amount = self._parse_amount_improved(groups[3])
                item.gross_amount = self._parse_amount_improved(groups[4])
                # Oblicz stawkę VAT
                if item.net_amount > 0:
                    vat_rate = (item.vat_amount / item.net_amount * 100)
                    item.vat_rate = f"{int(vat_rate)}%"
            
            if item.name and item.gross_amount > 0:
                return item
                
        except Exception as e:
            print(f"Błąd parsowania dopasowania: {e}")
        
        return None