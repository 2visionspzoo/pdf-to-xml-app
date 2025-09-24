# -*- coding: utf-8 -*-
"""
Parser uniwersalny dla różnych typów faktur - wersja 6 FIXED
Poprawki:
- Naprawiony uszkodzony kod
- Poprawione rozpoznawanie numeru faktury (szczególnie nazwa.pl)
- Lepsza ekstrakcja nazw pozycji
- Poprawione kodowanie UTF-8
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
        # Znane firmy bez NIP lub ze specyficznymi danymi
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
    
    def parse(self, text: str, tables: List[List[List[str]]] = None) -> Dict:
        """Parsuje fakturę używając uniwersalnych wzorców"""
        
        # Resetuj dane
        self.invoice_data = self._get_empty_invoice_data()
        
        # Ekstrakcja podstawowych danych
        self.invoice_data['invoice_number'] = self._extract_invoice_number_v6(text) or ''
        self.invoice_data['invoice_date'] = self.extract_date(text, 'invoice') or ''
        self.invoice_data['sale_date'] = self.extract_date(text, 'sale') or ''
        self.invoice_data['payment_date'] = self.extract_date(text, 'payment') or ''
        
        # Ekstrakcja metody płatności
        self._extract_payment_method(text)
        
        # ULEPSZONA ekstrakcja danych sprzedawcy i nabywcy
        self._extract_parties_v6(text)
        
        # ULEPSZONA ekstrakcja pozycji faktury
        if tables:
            self._extract_items_from_tables_v6(tables, text)
        else:
            self._extract_items_from_text(text)
        
        # ULEPSZONA ekstrakcja podsumowania z lepszą ekstrakcją kwot
        self._extract_summary_v6(text, tables)
        
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
    
    def _extract_invoice_number_v6(self, text: str) -> Optional[str]:
        """Wersja 6 FIXED - ulepszona ekstrakcja numeru faktury"""
        
        # Specjalny przypadek dla nazwa.pl - szukaj wzorca 23373/naz/07/2025
        if 'nazwa.pl' in text.lower() or 'faktura vat' in text.lower():
            # Szukaj numeru w formacie XXXXX/naz/MM/YYYY
            patterns = [
                r'(\d{5}/naz/\d{2}/\d{4})',
                r'Faktura\s+Vat\s+(\d{5}[\s/\-_]naz[\s/\-_]\d{2}[\s/\-_]\d{4})',
                r'nr\s+(\d{5}[\s/\-_]naz[\s/\-_]\d{2}[\s/\-_]\d{4})',
                r'(\d{5}[\s_\-/]naz[\s_\-/]\d{2}[\s_\-/]\d{4})'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text[:1000], re.IGNORECASE)
                if match:
                    number = match.group(1)
                    # Normalizuj separatory
                    number = re.sub(r'[\s_\-]+', '/', number)
                    return number
        
        # Najpierw sprawdź pierwszą linię
        lines = text.split('\n')
        if lines and len(lines) > 0:
            first_line = lines[0].strip()
            # Jeśli pierwsza linia to np. "FVS/2/08/2025" lub "FS 4447/08/2025"
            if re.match(r'^F[VSAKZ][S]?[\s/\-_]\d+', first_line):
                # Usuń ewentualne "Faktura sprzedaży" z początku
                number = re.sub(r'^Faktura\s+sprzedaży\s+', '', first_line, flags=re.IGNORECASE).strip()
                # Dla FS dodaj prefix
                if 'FS' in first_line.upper() and not number.startswith('FS'):
                    return f"FS_{number.replace('/', '_').replace('-', '_')}"
                return number
        
        # Specjalne wzorce dla różnych formatów
        patterns = [
            # Wzorzec dla FS 4447/08/2025
            r'(?:FS|Faktura\s+sprzedaży)\s+(\d+[/\-_]\d+[/\-_]\d+)',
            r'(FS[\s\-_]*\d+[/\-_]\d+[/\-_]\d+)',
            
            # Wzorzec dla FVS/2/08/2025
            r'(FVS[/\-_]\d+[/\-_]\d+[/\-_]\d+)',
            
            # Standardowe wzorce
            r'(?:Faktura\s+(?:VAT\s+)?(?:nr|Nr\.?)\s*[:.\s]?)([A-Za-z0-9\-/_]+)',
            r'(?:FAKTURA\s+(?:VAT\s+)?(?:NR|Nr\.?)\s*[:.\s]?)([A-Za-z0-9\-/_]+)',
            r'(?:Numer\s+faktury\s*[:.\s]?)([A-Za-z0-9\-/_]+)',
            
            # Faktura VAT z numerem
            r'Faktura\s+VAT\s+nr\s+([A-Za-z0-9\-/_]+)',
            r'Faktura\s+Vat\s+([0-9]+[\-/_][A-Za-z0-9\-/_]+)',
            
            # Wzorzec dla numeru w formacie daty
            r'Nr[:.\s]*(\d+[/\-]\d+[/\-]\d{4})',
            
            # Prosty numer na początku linii
            r'^([A-Z]{2,}[/\-]\d+[/\-]\d+)',
        ]
        
        # Szukaj w pierwszych 15 liniach
        search_text = '\n'.join(lines[:15]) if len(lines) > 15 else text[:1500]
        
        for pattern in patterns:
            match = re.search(pattern, search_text, re.IGNORECASE | re.MULTILINE)
            if match:
                invoice_num = match.group(1).strip()
                # Walidacja i czyszczenie
                invoice_num = invoice_num.replace('sprzedaży', '').strip()
                invoice_num = re.sub(r'^[\s/\-_]+', '', invoice_num)
                
                if len(invoice_num) >= 3 and not invoice_num.lower() in ['vat', 'faktura', 'invoice', 'nr', 'sprzeda']:
                    # Dla FS dodaj prefix jeśli go nie ma
                    if re.match(r'^\d+[/\-_]\d+[/\-_]\d+$', invoice_num) and 'FS' in text[:100].upper():
                        return f"FS_{invoice_num.replace('/', '_').replace('-', '_')}"
                    return invoice_num
        
        # Fallback - szukaj czegokolwiek co wygląda jak numer faktury
        fallback_patterns = [
            r'(F[VSAKZ][S]?[\s\-_/]*\d+[\s\-_/]*\d+[\s\-_/]*\d+)',
            r'(\d+[/\-_]\d+[/\-_]\d{4})'
        ]
        
        for pattern in fallback_patterns:
            match = re.search(pattern, text[:1000], re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
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
    
    def _extract_parties_v6(self, text: str):
        """Wersja 6 - ulepszona ekstrakcja sprzedawcy i nabywcy"""
        
        # Najpierw sprawdź znane firmy
        text_lower = text.lower()
        seller_found = False
        
        for key, company_data in self.known_companies.items():
            if key in text_lower:
                # Znaleziono znaną firmę - sprawdź czy to sprzedawca czy nabywca
                if '2vision' in text_lower:
                    # Jeśli jest 2Vision, to znana firma jest sprzedawcą
                    self.invoice_data['seller'].update(company_data)
                    seller_found = True
                    break
        
        # Standardowa ekstrakcja
        seller_keywords = ['Sprzedawca', 'SPRZEDAWCA', 'Wystawca', 'WYSTAWCA', 'Dostawca', 
                          'Seller', 'Vendor', 'Sprzedający', 'SPRZEDAJĄCY']
        buyer_keywords = ['Nabywca', 'NABYWCA', 'Odbiorca', 'ODBIORCA', 'Kupujący', 
                         'Buyer', 'Customer', 'Zamawiający', 'ZAMAWIAJĄCY']
        
        # Znajdź sekcje
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
        
        # Ekstrakcja danych
        if seller_pos != -1 and buyer_pos != -1:
            if seller_pos < buyer_pos:
                seller_text = text[seller_pos:buyer_pos]
                buyer_text = text[buyer_pos:buyer_pos+500]
            else:
                buyer_text = text[buyer_pos:seller_pos]
                seller_text = text[seller_pos:seller_pos+500]
            
            if not seller_found:
                self.invoice_data['seller'] = self._extract_company_data_v6(seller_text, True)
            self.invoice_data['buyer'] = self._extract_company_data_v6(buyer_text, False)
            
        elif seller_pos != -1:
            # Tylko sprzedawca
            seller_text = text[seller_pos:seller_pos+500]
            if not seller_found:
                self.invoice_data['seller'] = self._extract_company_data_v6(seller_text, True)
            # Ustaw domyślnego nabywcę
            self._set_default_buyer()
            
        elif buyer_pos != -1:
            # Tylko nabywca
            buyer_text = text[buyer_pos:buyer_pos+500]
            self.invoice_data['buyer'] = self._extract_company_data_v6(buyer_text, False)
            # Spróbuj znaleźć sprzedawcę inaczej
            if not seller_found:
                self._find_seller_by_position(text)
        else:
            # Brak etykiet - szukaj po pozycji i NIP
            self._extract_parties_by_position(text)
    
    def _find_seller_by_position(self, text: str):
        """Znajduje sprzedawcę na podstawie pozycji w dokumencie"""
        lines = text.split('\n')
        
        # Sprzedawca zazwyczaj jest w pierwszych 20 liniach
        for i in range(min(20, len(lines))):
            line = lines[i].strip()
            
            # Pomijaj puste linie i metadane
            if not line or any(skip in line.lower() for skip in 
                              ['faktura', 'invoice', 'data wystawienia', 'miejsce']):
                continue
            
            # Jeśli linia zawiera NIP, to prawdopodobnie sprzedawca
            if 'NIP' in line or re.search(r'\d{10}', line):
                # Weź kilka linii kontekstu
                context = '\n'.join(lines[max(0, i-2):min(len(lines), i+3)])
                self.invoice_data['seller'] = self._extract_company_data_v6(context, True)
                break
    
    def _extract_parties_by_position(self, text: str):
        """Ekstrahuje strony na podstawie pozycji w tekście"""
        lines = text.split('\n')
        
        # Pierwsze wystąpienie NIP to zazwyczaj sprzedawca
        nip_pattern = r'NIP[\s:]*([0-9]{3}[-\s]?[0-9]{3}[-\s]?[0-9]{2}[-\s]?[0-9]{2}|[0-9]{10})'
        
        first_nip_found = False
        for i, line in enumerate(lines[:30]):  # Pierwsze 30 linii
            if re.search(nip_pattern, line, re.IGNORECASE):
                if not first_nip_found:
                    # Pierwszy NIP - sprzedawca
                    context = '\n'.join(lines[max(0, i-3):min(len(lines), i+3)])
                    self.invoice_data['seller'] = self._extract_company_data_v6(context, True)
                    first_nip_found = True
                else:
                    # Drugi NIP - nabywca
                    context = '\n'.join(lines[max(0, i-3):min(len(lines), i+3)])
                    self.invoice_data['buyer'] = self._extract_company_data_v6(context, False)
                    break
        
        # Jeśli nie znaleziono nabywcy, ustaw domyślnego
        if not self.invoice_data['buyer']['name']:
            if '2vision' in text.lower():
                self._set_default_buyer()
    
    def _extract_company_data_v6(self, text: str, is_seller: bool) -> Dict:
        """Wersja 6 - ulepszona ekstrakcja danych firmy"""
        data = {
            'name': '',
            'nip': '',
            'address': '',
            'city': '',
            'postal_code': '',
            'country': 'Polska'
        }
        
        # Usuń etykiety
        keywords_to_remove = ['Sprzedawca', 'SPRZEDAWCA', 'Nabywca', 'NABYWCA', 
                             'Wystawca', 'WYSTAWCA', 'Odbiorca', 'ODBIORCA']
        
        for kw in keywords_to_remove:
            text = re.sub(rf'{kw}\s*:?\s*', '', text, 1, re.IGNORECASE).strip()
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Znajdź nazwę firmy
        for line in lines:
            # Pomijaj metadane
            if any(skip in line.lower() for skip in ['data', 'termin', 'sposób', 'miejsce', 'nip:', 'regon']):
                continue
            
            # Pomijaj daty i kody
            if re.match(r'^\d{4}-\d{2}-\d{2}', line) or re.match(r'^\d{2}\.\d{2}\.\d{4}', line):
                continue
            
            # To prawdopodobnie nazwa firmy
            if len(line) > 3 and not re.match(r'^\d{2}-\d{3}', line):
                data['name'] = line
                break
        
        # Znajdź NIP
        nip_pattern = r'NIP[\s:]*([0-9]{3}[-\s]?[0-9]{3}[-\s]?[0-9]{2}[-\s]?[0-9]{2}|[0-9]{10})'
        nip_match = re.search(nip_pattern, text, re.IGNORECASE)
        if nip_match:
            data['nip'] = re.sub(r'[-\s]', '', nip_match.group(1))
        
        # Znajdź adres
        address_pattern = r'(?:ul\.|ulica)?\s*([A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż\s]+\s+\d+[A-Za-z]?(?:/\d+)?)'
        address_match = re.search(address_pattern, text)
        if address_match:
            data['address'] = address_match.group(1).strip()
        
        # Znajdź kod pocztowy i miasto
        postal_pattern = r'(\d{2}[-\s]\d{3})\s+([A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż\s]+)'
        postal_match = re.search(postal_pattern, text)
        if postal_match:
            data['postal_code'] = postal_match.group(1).replace(' ', '-')
            data['city'] = postal_match.group(2).strip()
        
        return data
    
    def _set_default_buyer(self):
        """Ustawia domyślne dane nabywcy (2Vision)"""
        self.invoice_data['buyer'] = {
            'name': '2VISION SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ',
            'nip': '6751781780',
            'address': 'ul. Dąbska 20A/17',
            'city': 'Kraków',
            'postal_code': '31-572',
            'country': 'Polska'
        }
    
    def _extract_items_from_tables_v6(self, tables: List[List[List[str]]], text: str):
        """Wersja 6 - ulepszona ekstrakcja pozycji z poprawioną ekstrakcją nazw"""
        
        items_found = False
        
        for table in tables:
            if self._is_items_table_v6(table):
                items = self._parse_items_table_v6(table, text)
                if items:
                    self.invoice_data['items'].extend([item.to_dict() for item in items])
                    items_found = True
                    break
        
        # Jeśli nie znaleziono pozycji w tabelach, spróbuj z tekstu
        if not items_found:
            self._extract_items_from_text_patterns(text)
    
    def _is_items_table_v6(self, table: List[List[str]]) -> bool:
        """Wersja 6 - lepsza identyfikacja tabeli z pozycjami"""
        if not table or len(table) < 2:
            return False
        
        # Sprawdź nagłówek
        header_text = ' '.join(str(cell).lower() for cell in table[0] if cell)
        
        # Musi zawierać przynajmniej jedno z tych słów
        must_have = ['nazwa', 'towar', 'usługa', 'opis', 'przedmiot']
        has_required = any(word in header_text for word in must_have)
        
        # Opcjonalne słowa
        optional = ['wartość', 'kwota', 'netto', 'brutto', 'cena', 'ilość']
        optional_count = sum(1 for word in optional if word in header_text)
        
        return has_required or optional_count >= 2
    
    def _parse_items_table_v6(self, table: List[List[str]], text: str) -> List[InvoiceItem]:
        """Wersja 6 - ulepszone parsowanie tabeli pozycji z lepszą ekstrakcją nazw"""
        items = []
        
        if not table or len(table) < 2:
            return items
        
        # Identyfikuj kolumny
        header = table[0]
        column_map = self._identify_columns_v6(header)
        
        # Parsuj wiersze
        for row in table[1:]:
            if self._is_valid_item_row_v6(row):
                item = self._parse_item_row_v6(row, column_map, text)
                if item:
                    items.append(item)
        
        return items
    
    def _identify_columns_v6(self, header: List[str]) -> Dict[str, int]:
        """Wersja 6 - lepsza identyfikacja kolumn"""
        column_map = {}
        
        for i, cell in enumerate(header):
            if not cell:
                continue
            
            cell_lower = str(cell).lower().strip()
            
            # Mapowanie kolumn
            if any(word in cell_lower for word in ['lp', 'l.p', 'nr', 'poz']):
                column_map['lp'] = i
            elif any(word in cell_lower for word in ['nazwa', 'towar', 'usługa', 'opis', 'przedmiot']):
                column_map['name'] = i
            elif any(word in cell_lower for word in ['ilość', 'ilosc', 'szt', 'quantity']):
                column_map['quantity'] = i
            elif 'j.m' in cell_lower or 'jedn' in cell_lower:
                column_map['unit'] = i
            elif 'cena' in cell_lower and any(word in cell_lower for word in ['jedn', 'netto']):
                column_map['unit_price'] = i
            elif 'netto' in cell_lower and any(word in cell_lower for word in ['wartość', 'kwota']):
                column_map['net_amount'] = i
            elif 'stawka' in cell_lower and 'vat' in cell_lower:
                column_map['vat_rate'] = i
            elif 'vat' in cell_lower and any(word in cell_lower for word in ['kwota', 'wartość']):
                column_map['vat_amount'] = i
            elif 'brutto' in cell_lower:
                column_map['gross_amount'] = i
        
        return column_map
    
    def _is_valid_item_row_v6(self, row: List[str]) -> bool:
        """Wersja 6 - sprawdzanie poprawności wiersza"""
        if not row or all(not str(cell).strip() for cell in row):
            return False
        
        # Pomijaj wiersze z podsumowaniem
        first_cells = ' '.join(str(cell).lower() for cell in row[:2] if cell)
        skip_words = ['razem', 'suma', 'ogółem', 'total', 'podsumowanie', 
                     'stawka vat', 'według stawek', 'do zapłaty']
        
        for word in skip_words:
            if word in first_cells:
                return False
        
        return True
    
    def _parse_item_row_v6(self, row: List[str], column_map: Dict[str, int], text: str) -> Optional[InvoiceItem]:
        """Wersja 6 FIXED - parsowanie wiersza z pozycją i lepszą ekstrakcją nazw"""
        item = InvoiceItem()
        
        try:
            # Jeśli brak mapy kolumn, spróbuj zgadnąć
            if not column_map:
                return self._parse_item_row_guess(row)
            
            # Nazwa (wymagana) - POPRAWIONE
            if 'name' in column_map and column_map['name'] < len(row):
                cell_value = str(row[column_map['name']]).strip()
                # Sprawdź czy to nie jest pusta wartość lub None
                if cell_value and cell_value.lower() not in ['none', '', '-', 'brak']:
                    item.name = cell_value
            
            # Jeśli nie znaleziono nazwy przez mapę, szukaj w całym wierszu
            if not item.name or item.name.lower() in ['none', 'brak']:
                # Szukaj najdłuższej niepustej komórki która nie jest liczbą
                for cell in row:
                    cell_str = str(cell).strip() if cell else ''
                    # Sprawdź czy to może być nazwa (dłuższa niż 3 znaki i nie tylko liczby)
                    if cell_str and len(cell_str) > 3 and not re.match(r'^[\d\s,.-]+$', cell_str):
                        # Upewnij się że to nie jest stawka VAT lub jednostka
                        if not re.match(r'^\d+[%]?$', cell_str) and cell_str.lower() not in ['szt', 'szt.', 'kg', 'l', 'm', 'vat', '23%', '8%', '5%', '0%']:
                            item.name = cell_str
                            break
            
            # Jeśli nadal nie ma nazwy, spróbuj znaleźć w tekście faktury
            if not item.name or item.name.lower() in ['none', 'brak', '']:
                # Szukaj opisów pozycji w tekście
                item.name = self._extract_item_name_from_text(text, row)
            
            # Ilość
            if 'quantity' in column_map and column_map['quantity'] < len(row):
                item.quantity = self._parse_amount_safe(row[column_map['quantity']])
            else:
                item.quantity = 1
            
            # Jednostka
            if 'unit' in column_map and column_map['unit'] < len(row):
                item.unit = str(row[column_map['unit']]).strip()
            
            # Cena jednostkowa
            if 'unit_price' in column_map and column_map['unit_price'] < len(row):
                item.unit_price_net = self._parse_amount_safe(row[column_map['unit_price']])
            
            # Wartość netto
            if 'net_amount' in column_map and column_map['net_amount'] < len(row):
                item.net_amount = self._parse_amount_safe(row[column_map['net_amount']])
            
            # Stawka VAT
            if 'vat_rate' in column_map and column_map['vat_rate'] < len(row):
                item.vat_rate = self.extract_vat_rate(row[column_map['vat_rate']])
            else:
                item.vat_rate = "23%"  # Domyślna stawka
            
            # Kwota VAT
            if 'vat_amount' in column_map and column_map['vat_amount'] < len(row):
                item.vat_amount = self._parse_amount_safe(row[column_map['vat_amount']])
            
            # Wartość brutto
            if 'gross_amount' in column_map and column_map['gross_amount'] < len(row):
                item.gross_amount = self._parse_amount_safe(row[column_map['gross_amount']])
            
            # Oblicz brakujące wartości
            self._calculate_missing_item_values(item)
            
            return item if item.name else None
            
        except Exception as e:
            print(f"Błąd parsowania wiersza: {e}")
            return None
    
    def _extract_item_name_from_text(self, text: str, row: List[str]) -> str:
        """Ekstrahuje nazwę pozycji z tekstu faktury na podstawie kontekstu"""
        # Szukaj wzorców pozycji w tekście
        patterns = [
            r'(?:Usługa|Towar|Produkt):\s*([^,\n]{5,50})',
            r'(?:Opis|Nazwa):\s*([^,\n]{5,50})',
            r'(?:\d+\.\s+)([A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż\s]{5,50})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Jeśli nic nie znaleziono, zwróć ogólny opis
        return "Towar/usługa"
    
    def _parse_item_row_guess(self, row: List[str]) -> Optional[InvoiceItem]:
        """Próbuje zgadnąć strukturę wiersza bez mapy kolumn"""
        item = InvoiceItem()
        
        # Znajdź nazwę - najdłuższa niepusta komórka nie będąca liczbą
        for cell in row:
            cell_str = str(cell).strip()
            if cell_str and len(cell_str) > 5 and not re.match(r'^[\d\s,.-]+$', cell_str):
                item.name = cell_str
                break
        
        if not item.name:
            return None
        
        # Znajdź liczby
        amounts = []
        for cell in row:
            amount = self._parse_amount_safe(cell)
            if amount > 0 and amount < 1000000:
                amounts.append(amount)
        
        # Zgadnij co to za kwoty
        if len(amounts) >= 3:
            # Prawdopodobnie: ilość, netto, brutto lub ilość, cena, wartość
            if amounts[0] < 100:  # Prawdopodobnie ilość
                item.quantity = amounts[0]
                if len(amounts) >= 4:
                    item.net_amount = amounts[-2]
                    item.gross_amount = amounts[-1]
                else:
                    item.net_amount = amounts[1]
                    item.gross_amount = amounts[2] if len(amounts) > 2 else amounts[1]
            else:
                item.net_amount = amounts[-2] if len(amounts) > 1 else amounts[0]
                item.gross_amount = amounts[-1]
        elif len(amounts) == 2:
            item.net_amount = amounts[0]
            item.gross_amount = amounts[1]
        elif len(amounts) == 1:
            item.gross_amount = amounts[0]
        
        # Oblicz brakujące
        self._calculate_missing_item_values(item)
        
        return item
    
    def _calculate_missing_item_values(self, item: InvoiceItem):
        """Oblicza brakujące wartości pozycji"""
        if not item.vat_rate:
            item.vat_rate = "23%"
        
        vat_decimal = Decimal(item.vat_rate.replace('%', '')) / 100
        
        # Oblicz brakujące wartości
        if item.net_amount > 0:
            if item.vat_amount == 0:
                item.vat_amount = round(item.net_amount * vat_decimal, 2)
            if item.gross_amount == 0:
                item.gross_amount = item.net_amount + item.vat_amount
        elif item.gross_amount > 0:
            if item.net_amount == 0:
                item.net_amount = round(item.gross_amount / (1 + vat_decimal), 2)
            if item.vat_amount == 0:
                item.vat_amount = item.gross_amount - item.net_amount
    
    def _extract_items_from_text_patterns(self, text: str):
        """Ekstrahuje pozycje z tekstu gdy brak tabel"""
        # Szukaj wzorców pozycji
        patterns = [
            # Format: nazwa usługi... kwota
            r'([A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż\s]+(?:usługa|towar|produkt)[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż\s]*)\s+([\d\s,.-]+)',
            # Format z numeracją
            r'\d+\.\s*([A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż\s]+)\s+([\d\s,.-]+)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                item = InvoiceItem()
                item.name = match.group(1).strip()
                item.gross_amount = self._parse_amount_safe(match.group(2))
                if item.name and item.gross_amount > 0:
                    item.quantity = 1
                    item.vat_rate = "23%"
                    self._calculate_missing_item_values(item)
                    self.invoice_data['items'].append(item.to_dict())
    
    def _parse_amount_safe(self, text: str) -> Decimal:
        """Bezpieczne parsowanie kwot - zapobiega astronomicznym wartościom"""
        try:
            if not text:
                return Decimal('0')
            
            text = str(text).strip()
            
            if not text or text.lower() in ['none', '', '-', 'brak', '–']:
                return Decimal('0')
            
            # Usuń znaki waluty
            text = re.sub(r'[zł$€£¥PLN]', '', text, flags=re.IGNORECASE).strip()
            
            # Obsługa polskiej notacji
            if ',' in text and '.' in text:
                # Określ który jest separatorem tysięcy
                if text.rfind(',') > text.rfind('.'):
                    # Przecinek jest separatorem dziesiętnym
                    text = text.replace('.', '').replace(',', '.')
                else:
                    # Kropka jest separatorem dziesiętnym
                    text = text.replace(',', '')
            elif ',' in text:
                # Tylko przecinek - sprawdź czy to separator dziesiętny
                parts = text.split(',')
                if len(parts) == 2 and len(parts[1]) <= 2:
                    text = text.replace(',', '.')
                else:
                    text = text.replace(',', '')
            
            # Usuń spacje
            text = text.replace(' ', '')
            
            # Usuń wszystko oprócz cyfr, kropki i minusa
            text = re.sub(r'[^\d.-]', '', text)
            
            # Sprawdź czy nie ma wielu kropek
            if text.count('.') > 1:
                # Zostaw tylko ostatnią kropkę jako separator dziesiętny
                parts = text.split('.')
                text = ''.join(parts[:-1]) + '.' + parts[-1]
            
            if text and text not in ['-', '.', '-.']:
                value = Decimal(text)
                
                # Sprawdź czy wartość jest sensowna (max 10 mln)
                if value > 10000000:
                    return Decimal('0')
                
                return abs(value)  # Zawsze wartość dodatnia
            else:
                return Decimal('0')
                
        except (InvalidOperation, ValueError) as e:
            return Decimal('0')
    
    def _extract_summary_v6(self, text: str, tables: List[List[List[str]]]):
        """Wersja 6 - ulepszona ekstrakcja podsumowania z lepszą ekstrakcją kwot netto/VAT"""
        
        # Najpierw szukaj w tabelach
        for table in tables:
            if self._is_summary_table(table):
                self._parse_summary_table_v6(table)
                
        # Jeśli nie znaleziono w tabelach, szukaj w tekście
        if self.invoice_data['summary']['gross_total'] == '0.00':
            self._extract_summary_from_text_v6(text)
        
        # Jeśli mamy brutto ale brak netto/VAT, oblicz je
        if self.invoice_data['summary']['gross_total'] != '0.00':
            if self.invoice_data['summary']['net_total'] == '0.00':
                # Spróbuj obliczyć z pozycji
                if self.invoice_data['items']:
                    self._calculate_summary_from_items()
                else:
                    # Oblicz zakładając 23% VAT
                    gross = Decimal(self.invoice_data['summary']['gross_total'])
                    net = round(gross / Decimal('1.23'), 2)
                    vat = gross - net
                    self.invoice_data['summary']['net_total'] = str(net)
                    self.invoice_data['summary']['vat_total'] = str(vat)
    
    def _is_summary_table(self, table: List[List[str]]) -> bool:
        """Sprawdza czy to tabela podsumowania"""
        if not table:
            return False
        
        text = ' '.join(' '.join(str(cell) for cell in row if cell) for row in table).lower()
        
        keywords = ['razem', 'suma', 'total', 'ogółem', 'do zapłaty', 'stawka vat', 
                   'według stawek', 'podsumowanie']
        matches = sum(1 for kw in keywords if kw in text)
        
        return matches >= 2
    
    def _parse_summary_table_v6(self, table: List[List[str]]):
        """Parsuje tabelę podsumowania z lepszą ekstrakcją kwot"""
        for row in table:
            if not row:
                continue
            
            row_text = ' '.join(str(cell).lower() for cell in row if cell)
            
            # Szukaj sum
            if any(word in row_text for word in ['razem', 'suma', 'ogółem', 'do zapłaty']):
                # Znajdź kwoty w wierszu
                amounts = []
                for cell in row:
                    amount = self._parse_amount_safe(cell)
                    if amount > 0 and amount < 1000000:
                        amounts.append(amount)
                
                # Sortuj kwoty rosnąco (zazwyczaj: netto < VAT < brutto)
                amounts.sort()
                
                # Zgadnij co to za kwoty
                if len(amounts) >= 3:
                    # Mamy netto, VAT, brutto
                    self.invoice_data['summary']['net_total'] = str(amounts[-3])
                    self.invoice_data['summary']['vat_total'] = str(amounts[-2])
                    self.invoice_data['summary']['gross_total'] = str(amounts[-1])
                elif len(amounts) == 2:
                    # Prawdopodobnie netto i brutto
                    if amounts[1] > amounts[0] * Decimal('1.1'):  # Różnica > 10%
                        self.invoice_data['summary']['net_total'] = str(amounts[0])
                        self.invoice_data['summary']['gross_total'] = str(amounts[1])
                        self.invoice_data['summary']['vat_total'] = str(amounts[1] - amounts[0])
                    else:
                        # Może VAT i brutto
                        self.invoice_data['summary']['vat_total'] = str(amounts[0])
                        self.invoice_data['summary']['gross_total'] = str(amounts[1])
                        self.invoice_data['summary']['net_total'] = str(amounts[1] - amounts[0])
                elif len(amounts) == 1:
                    # Tylko brutto
                    self.invoice_data['summary']['gross_total'] = str(amounts[0])
    
    def _extract_summary_from_text_v6(self, text: str):
        """Ekstrahuje podsumowanie z tekstu z lepszymi wzorcami"""
        patterns = {
            'gross_total': [
                r'do\s+zapłaty[:\s]*([\d\s,.-]+)',
                r'razem\s+do\s+zapłaty[:\s]*([\d\s,.-]+)',
                r'kwota\s+brutto[:\s]*([\d\s,.-]+)',
                r'wartość\s+brutto[:\s]*([\d\s,.-]+)',
                r'suma\s+brutto[:\s]*([\d\s,.-]+)',
                r'razem\s+brutto[:\s]*([\d\s,.-]+)',
                r'łącznie[:\s]*([\d\s,.-]+)',
                r'do\s+zapłaty\s+PLN[:\s]*([\d\s,.-]+)',
            ],
            'net_total': [
                r'razem\s+netto[:\s]*([\d\s,.-]+)',
                r'suma\s+netto[:\s]*([\d\s,.-]+)',
                r'wartość\s+netto[:\s]*([\d\s,.-]+)',
                r'kwota\s+netto[:\s]*([\d\s,.-]+)',
                r'netto\s+razem[:\s]*([\d\s,.-]+)',
                r'podstawa\s+opodatkowania[:\s]*([\d\s,.-]+)',
            ],
            'vat_total': [
                r'razem\s+vat[:\s]*([\d\s,.-]+)',
                r'suma\s+vat[:\s]*([\d\s,.-]+)',
                r'kwota\s+vat[:\s]*([\d\s,.-]+)',
                r'podatek\s+vat[:\s]*([\d\s,.-]+)',
                r'vat\s+razem[:\s]*([\d\s,.-]+)',
                r'należny\s+podatek[:\s]*([\d\s,.-]+)',
            ]
        }
        
        for field, field_patterns in patterns.items():
            for pattern in field_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    amount = self._parse_amount_safe(match.group(1))
                    if amount > 0 and amount < 1000000:
                        self.invoice_data['summary'][field] = str(amount)
                        break
    
    def _calculate_summary_from_items(self):
        """Oblicza podsumowanie na podstawie pozycji"""
        net_total = Decimal('0')
        vat_total = Decimal('0')
        gross_total = Decimal('0')
        
        for item in self.invoice_data['items']:
            net = Decimal(str(item.get('net_amount', '0')))
            vat = Decimal(str(item.get('vat_amount', '0')))
            gross = Decimal(str(item.get('gross_amount', '0')))
            
            net_total += net
            vat_total += vat
            gross_total += gross
        
        if gross_total > 0 or net_total > 0:
            self.invoice_data['summary']['net_total'] = str(net_total)
            self.invoice_data['summary']['vat_total'] = str(vat_total)
            self.invoice_data['summary']['gross_total'] = str(gross_total)
    
    def _extract_items_from_text(self, text: str):
        """Ekstrahuje pozycje bezpośrednio z tekstu"""
        self._extract_items_from_text_patterns(text)
    
    def _extract_number_from_filename(self, filename: str) -> str:
        """Ekstrahuje numer z nazwy pliku"""
        if not filename:
            return ''
        
        name = os.path.splitext(filename)[0]
        
        # Wzorce numerów w nazwach plików
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
