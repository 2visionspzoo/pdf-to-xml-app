"""
Bazowe klasy i interfejsy dla parserów faktur
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import re
from decimal import Decimal

class InvoiceItem:
    """Reprezentacja pojedynczej pozycji na fakturze"""
    
    def __init__(self):
        self.lp: Optional[int] = None
        self.name: str = ""
        self.description: str = ""  # Alias dla kompatybilności
        self.pkwiu: Optional[str] = None
        self.quantity: Decimal = Decimal('0')
        self.unit: str = ""
        self.unit_price_net: Decimal = Decimal('0')
        self.unit_price: Decimal = Decimal('0')  # Alias dla kompatybilności
        self.net_amount: Decimal = Decimal('0')
        self.vat_rate: str = "23%"
        self.vat_amount: Decimal = Decimal('0')
        self.gross_amount: Decimal = Decimal('0')
    
    def to_dict(self) -> Dict:
        """Konwertuje do słownika z kompatybilnością wsteczną"""
        # Używamy wartości z name lub description, zależnie która jest wypełniona
        name_value = self.name or self.description or ''
        unit_price_value = self.unit_price_net or self.unit_price or Decimal('0')
        
        return {
            'lp': self.lp,
            'name': name_value,
            'description': name_value,  # Dla kompatybilności wstecznej
            'pkwiu': self.pkwiu,
            'quantity': str(self.quantity),
            'unit': self.unit,
            'unit_price_net': str(unit_price_value),
            'unit_price': str(unit_price_value),  # Dla kompatybilności wstecznej
            'net_amount': str(self.net_amount),
            'vat_rate': self.vat_rate,
            'vat_amount': str(self.vat_amount),
            'gross_amount': str(self.gross_amount)
        }

class BaseInvoiceParser(ABC):
    """Abstrakcyjna klasa bazowa dla wszystkich parserów faktur"""
    
    def __init__(self):
        self.invoice_data = {
            'invoice_number': '',
            'invoice_date': '',
            'sale_date': '',
            'payment_date': '',
            'payment_method': '',
            
            # Sprzedawca
            'seller': {
                'name': '',
                'nip': '',
                'address': '',
                'city': '',
                'postal_code': '',
                'country': 'Polska'
            },
            
            # Nabywca
            'buyer': {
                'name': '',
                'nip': '',
                'address': '',
                'city': '',
                'postal_code': '',
                'country': 'Polska'
            },
            
            # Pozycje
            'items': [],
            
            # Podsumowanie
            'summary': {
                'net_total': '0.00',
                'vat_total': '0.00',
                'gross_total': '0.00',
                'vat_breakdown': {}  # Słownik: stawka VAT -> kwota
            }
        }
    
    @abstractmethod
    def parse(self, text: str, tables: List[List[List[str]]] = None) -> Dict:
        """
        Parsuje tekst faktury
        
        Args:
            text: Tekst wyekstrahowany z PDF
            tables: Opcjonalne tabele wyekstrahowane z PDF
            
        Returns:
            Słownik z danymi faktury
        """
        pass
    
    def extract_invoice_number(self, text: str) -> Optional[str]:
        """Ekstrahuje numer faktury"""
        patterns = [
            r'(?:Faktura\s+(?:VAT\s+)?(?:nr|Nr\.?)\s*[:\s]?)([A-Za-z0-9\-/]+)',
            r'(?:FAKTURA\s+(?:VAT\s+)?(?:NR|Nr\.?)\s*[:\s]?)([A-Za-z0-9\-/]+)',
            r'(?:Invoice\s+(?:number|no\.?)\s*[:\s]?)([A-Za-z0-9\-/]+)',
            r'(?:Numer\s+faktury\s*[:\s]?)([A-Za-z0-9\-/]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def extract_date(self, text: str, date_type: str = 'invoice') -> Optional[str]:
        """
        Ekstrahuje datę z tekstu
        
        Args:
            text: Tekst do przeszukania
            date_type: Typ daty ('invoice', 'sale', 'payment')
        """
        date_keywords = {
            'invoice': ['Data wystawienia', 'Data faktury', 'Invoice date', 'Data dokumentu'],
            'sale': ['Data sprzedaży', 'Data dostawy', 'Sale date', 'Data wykonania'],
            'payment': ['Termin płatności', 'Payment due', 'Data płatności']
        }
        
        keywords = date_keywords.get(date_type, [])
        
        # Wzorce dat
        date_patterns = [
            r'(\d{4}[-/.]\d{1,2}[-/.]\d{1,2})',  # YYYY-MM-DD
            r'(\d{1,2}[-/.]\d{1,2}[-/.]\d{4})',  # DD-MM-YYYY
            r'(\d{1,2}\s+\w+\s+\d{4})',          # DD Month YYYY
        ]
        
        for keyword in keywords:
            pattern = f'{keyword}.*?({"|".join(date_patterns)})'
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return self.normalize_date(match.group(1))
        
        return None
    
    def normalize_date(self, date_str: str) -> str:
        """Normalizuje datę do formatu YYYY-MM-DD"""
        # Słownik miesięcy
        months = {
            'stycznia': '01', 'styczeń': '01', 'january': '01', 'jan': '01',
            'lutego': '02', 'luty': '02', 'february': '02', 'feb': '02',
            'marca': '03', 'marzec': '03', 'march': '03', 'mar': '03',
            'kwietnia': '04', 'kwiecień': '04', 'april': '04', 'apr': '04',
            'maja': '05', 'maj': '05', 'may': '05',
            'czerwca': '06', 'czerwiec': '06', 'june': '06', 'jun': '06',
            'lipca': '07', 'lipiec': '07', 'july': '07', 'jul': '07',
            'sierpnia': '08', 'sierpień': '08', 'august': '08', 'aug': '08',
            'września': '09', 'wrzesień': '09', 'september': '09', 'sep': '09',
            'października': '10', 'październik': '10', 'october': '10', 'oct': '10',
            'listopada': '11', 'listopad': '11', 'november': '11', 'nov': '11',
            'grudnia': '12', 'grudzień': '12', 'december': '12', 'dec': '12'
        }
        
        # Próba różnych formatów
        try:
            # Format: DD Month YYYY
            for month_name, month_num in months.items():
                if month_name in date_str.lower():
                    parts = date_str.split()
                    day = parts[0].zfill(2)
                    year = parts[-1]
                    return f"{year}-{month_num}-{day}"
            
            # Format: YYYY-MM-DD lub YYYY/MM/DD
            if re.match(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', date_str):
                parts = re.split(r'[-/]', date_str)
                return f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
            
            # Format: DD-MM-YYYY lub DD/MM/YYYY
            if re.match(r'\d{1,2}[-/]\d{1,2}[-/]\d{4}', date_str):
                parts = re.split(r'[-/]', date_str)
                return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
            
        except:
            pass
        
        return date_str
    
    def extract_nip(self, text: str, context: str = '') -> Optional[str]:
        """Ekstrahuje NIP z tekstu"""
        # Wzorce NIP
        patterns = [
            r'NIP[\s:]*([0-9]{3}[-\s]?[0-9]{3}[-\s]?[0-9]{2}[-\s]?[0-9]{2})',
            r'NIP[\s:]*([0-9]{10})',
            r'VAT[\s:]*PL([0-9]{10})',
        ]
        
        search_text = context + text if context else text
        
        for pattern in patterns:
            match = re.search(pattern, search_text, re.IGNORECASE)
            if match:
                nip = re.sub(r'[-\s]', '', match.group(1))
                if len(nip) == 10:
                    return nip
        
        return None
    
    def parse_amount(self, text: str) -> Decimal:
        """Parsuje kwotę do Decimal"""
        try:
            # Usuń wszystko oprócz cyfr, przecinka i kropki
            cleaned = re.sub(r'[^\d,.-]', '', text)
            # Zamień przecinek na kropkę
            cleaned = cleaned.replace(',', '.')
            # Usuń spacje
            cleaned = cleaned.replace(' ', '')
            
            return Decimal(cleaned)
        except:
            return Decimal('0')
    
    def extract_vat_rate(self, text: str) -> str:
        """Ekstrahuje stawkę VAT"""
        # Wzorce stawek VAT
        patterns = [
            r'(\d+)\s*%',
            r'(\d+)%',
            r'VAT\s+(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                rate = match.group(1)
                return f"{rate}%"
        
        # Domyślnie 23%
        return "23%"
    
    def extract_company_data(self, text: str, is_seller: bool = True) -> Dict:
        """
        Ekstrahuje dane firmy (sprzedawca/nabywca)
        
        Args:
            text: Fragment tekstu z danymi firmy
            is_seller: True dla sprzedawcy, False dla nabywcy
        """
        data = {
            'name': '',
            'nip': '',
            'address': '',
            'city': '',
            'postal_code': '',
            'country': 'Polska'
        }
        
        # Ekstrakcja nazwy firmy
        lines = text.split('\n')
        if lines:
            data['name'] = lines[0].strip()
        
        # Ekstrakcja NIP
        data['nip'] = self.extract_nip(text) or ''
        
        # Ekstrakcja kodu pocztowego i miasta
        postal_pattern = r'(\d{2}[-\s]\d{3})\s+([A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż\s]+)'
        postal_match = re.search(postal_pattern, text)
        if postal_match:
            data['postal_code'] = postal_match.group(1).replace(' ', '-')
            data['city'] = postal_match.group(2).strip()
        
        # Ekstrakcja adresu (ulica)
        address_pattern = r'(ul\.?|ulica)\s+([A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż\s]+\s+\d+[A-Za-z]?(?:/\d+)?)'
        address_match = re.search(address_pattern, text, re.IGNORECASE)
        if address_match:
            data['address'] = address_match.group(2).strip()
        
        return data
