# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
import re

logger = logging.getLogger(__name__)

@dataclass  
class ComarchInvoiceData:
    """Struktura danych zgodna z Comarch ERP Optima"""
    document_type: str = "FZ"
    invoice_number: str = ""
    issue_date: str = ""
    sale_date: str = ""
    
    # Sprzedawca
    seller_code: str = ""
    seller_name: str = ""
    seller_nip: str = ""
    seller_regon: str = ""
    seller_address: Dict = None
    
    # Nabywca
    buyer_code: str = ""
    buyer_name: str = ""
    buyer_nip: str = ""
    buyer_address: Dict = None
    
    # Płatność
    payment_method: str = "przelew"
    payment_date: str = ""
    
    # Pozycje
    items: List[Dict] = None
    
    # Sumy
    net_total: float = 0.0
    vat_total: float = 0.0
    gross_total: float = 0.0
    vat_summary: Dict[str, Dict] = None

class ComarchMapper:
    def __init__(self):
        self.default_buyer = {
            'name': '2VISION SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ',
            'nip': '6751781780',
            'code': 'FIRMA_2VISION',
            'address': {
                'street': 'Dąbska',
                'building': '20A',
                'apartment': '17',
                'postal_code': '31-572',
                'city': 'Kraków'
            }
        }
    
    def map_invoice_data(self, invoice_data) -> ComarchInvoiceData:
        """Mapuje dane z PDF do struktury Comarch"""
        
        comarch_data = ComarchInvoiceData()
        
        # Obsługa zarówno słowników jak i obiektów
        if isinstance(invoice_data, dict):
            # Dla słowników
            invoice_number = invoice_data.get('invoice_number')
            invoice_date = invoice_data.get('invoice_date')
            sale_date = invoice_data.get('sale_date')
            
            seller_info = invoice_data.get('seller', {})
            seller_name = seller_info.get('name')
            seller_nip = seller_info.get('nip')
            
            payment_info = invoice_data.get('payment', {})
            payment_method = payment_info.get('method')
            payment_date = payment_info.get('due_date')
            
            items = invoice_data.get('items', [])
            
            summary = invoice_data.get('summary', {})
            net_total = summary.get('net_total', 0)
            vat_total = summary.get('vat_total', 0)
            gross_total = summary.get('gross_total', 0)
        else:
            # Dla obiektów z atrybutami
            invoice_number = getattr(invoice_data, 'invoice_number', None)
            invoice_date = getattr(invoice_data, 'invoice_date', None)
            sale_date = getattr(invoice_data, 'sale_date', None)
            
            seller_name = getattr(invoice_data, 'seller_name', None)
            seller_nip = getattr(invoice_data, 'seller_nip', None)
            
            payment_method = getattr(invoice_data, 'payment_method', None)
            payment_date = getattr(invoice_data, 'payment_date', None)
            
            items = getattr(invoice_data, 'items', [])
            
            net_total = getattr(invoice_data, 'net_total', 0)
            vat_total = getattr(invoice_data, 'vat_total', 0)
            gross_total = getattr(invoice_data, 'gross_total', 0)
        
        # Mapowanie podstawowych danych
        comarch_data.invoice_number = self._clean_invoice_number(invoice_number)
        comarch_data.issue_date = self._format_date(invoice_date)
        comarch_data.sale_date = self._format_date(sale_date) if sale_date else comarch_data.issue_date
        
        # Mapowanie sprzedawcy
        comarch_data.seller_name = self._clean_company_name(seller_name)
        comarch_data.seller_nip = self._format_nip(seller_nip)
        comarch_data.seller_code = self._generate_seller_code(seller_name, seller_nip)
        
        # Mapowanie nabywcy (zawsze 2Vision)
        comarch_data.buyer_name = self.default_buyer['name']
        comarch_data.buyer_nip = self.default_buyer['nip']
        comarch_data.buyer_code = self.default_buyer['code']
        comarch_data.buyer_address = self.default_buyer['address']
        
        # Mapowanie płatności
        comarch_data.payment_method = self._map_payment_method(payment_method)
        comarch_data.payment_date = self._format_date(payment_date) if payment_date else self._calculate_payment_date(comarch_data.issue_date)
        
        # Mapowanie pozycji
        if items:
            comarch_data.items = self._map_items(items)
        else:
            comarch_data.items = self._create_single_item_from_dict(invoice_data) if isinstance(invoice_data, dict) else self._create_single_item(invoice_data)
        
        # Mapowanie sum - sprawdzenie wartości 10000
        net = float(net_total or 0)
        vat = float(vat_total or 0)
        gross = float(gross_total or 0)
        
        # Jeśli wartości to 10000, spróbuj obliczyć z pozycji
        if gross == 10000.0 and net == 0.0:
            if comarch_data.items:
                net = sum(item['net_value'] for item in comarch_data.items)
                vat = sum(item['vat_amount'] for item in comarch_data.items)
                gross = sum(item['gross_value'] for item in comarch_data.items)
                logger.warning(f"Detected default value 10000.00, recalculated from items: net={net}, vat={vat}, gross={gross}")
        
        comarch_data.net_total = net
        comarch_data.vat_total = vat
        comarch_data.gross_total = gross
        
        # Podsumowanie VAT
        comarch_data.vat_summary = self._calculate_vat_summary(comarch_data.items)
        
        return comarch_data
    
    def _clean_invoice_number(self, number: Optional[str]) -> str:
        """Czyści numer faktury"""
        if not number:
            return f"FZ/{datetime.now().strftime('%Y%m%d')}/001"
        return re.sub(r'\s+', ' ', number).strip()
    
    def _clean_company_name(self, name: Optional[str]) -> str:
        """Czyści nazwę firmy"""
        if not name or name.strip() in ['', ':', 'None', 'none', 'null', 'brak']:
            return "NIEZNANY DOSTAWCA"
        
        # Usuń nadmiarowe białe znaki
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Jeśli nazwa zawiera tylko znaki specjalne, zwróć domyślną
        if re.match(r'^[^a-zA-Z0-9ĄĆĘŁŃÓŚŹŻąćęłńóśźż]+$', name):
            return "NIEZNANY DOSTAWCA"
        
        # Jeśli cała nazwa jest wielkimi literami, zamień na Title Case
        if name.upper() == name and len(name) > 10:
            name = name.title()
        
        return name
    
    def _format_date(self, date_str: Optional[str]) -> str:
        """Formatuje datę do formatu YYYY-MM-DD"""
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d')
        
        date_str = date_str.strip()
        
        formats = [
            '%d.%m.%Y', '%d-%m-%Y', '%d/%m/%Y',
            '%Y-%m-%d', '%Y.%m.%d', '%Y/%m/%d'
        ]
        
        for fmt in formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime('%Y-%m-%d')
            except:
                continue
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def _format_nip(self, nip: Optional[str]) -> str:
        """Formatuje NIP"""
        if not nip:
            return ""
        nip_digits = ''.join(filter(str.isdigit, str(nip)))
        return nip_digits
    
    def _generate_seller_code(self, name: Optional[str], nip: Optional[str]) -> str:
        """Generuje kod sprzedawcy"""
        if nip:
            return f"K_{nip[:6]}"
        elif name:
            code = ''.join(word[0] for word in name.split()[:3] if word).upper()
            if not code:
                code = "NIEZNANY"
            return f"K_{code}"
        return "K_NIEZNANY"
    
    def _map_payment_method(self, method: Optional[str]) -> str:
        """Mapuje metodę płatności"""
        if not method:
            return "przelew"
        
        method_lower = method.lower()
        
        if 'przelew' in method_lower:
            return "przelew"
        elif 'gotówka' in method_lower:
            return "gotówka"
        elif 'karta' in method_lower:
            return "karta"
        return "przelew"
    
    def _calculate_payment_date(self, issue_date: str, days: int = 14) -> str:
        """Oblicza datę płatności"""
        try:
            date_obj = datetime.strptime(issue_date, '%Y-%m-%d')
            payment_date = date_obj + timedelta(days=days)
            return payment_date.strftime('%Y-%m-%d')
        except:
            return issue_date
    
    def _map_items(self, items: List[Dict]) -> List[Dict]:
        """Mapuje pozycje faktury"""
        mapped_items = []
        
        for i, item in enumerate(items, 1):
            # Filtruj pozycje z nazwą "None"
            item_name = item.get('name') or item.get('description', '')
            if not item_name or item_name.lower() in ['none', 'null', 'brak', '']:
                continue
                
            # Parsuj stawkę VAT - może być jako '23%', '23', lub liczba
            vat_rate_raw = item.get('vat_rate', 23)
            if isinstance(vat_rate_raw, str):
                # Usuń znak % i konwertuj na int
                vat_rate_str = vat_rate_raw.replace('%', '').strip()
                vat_rate = int(vat_rate_str) if vat_rate_str.isdigit() else 23
            else:
                vat_rate = int(vat_rate_raw)
            
            unit_price = float(item.get('unit_price_net') or item.get('unit_price', 0))
            net_value = float(item.get('net_amount') or item.get('net_value', 0))
            
            # Sprawdź czy wartość nie jest domyślna 10000
            if net_value == 10000.0:
                logger.warning(f"Detected default net value 10000.00 for item {i}, setting to 0")
                net_value = 0.0
            
            mapped_item = {
                'lp': len(mapped_items) + 1,  # Używamy aktualnej długości listy
                'description': item_name,
                'quantity': float(item.get('quantity', 1)),
                'unit': item.get('unit', 'szt.'),
                'unit_price': unit_price,
                'net_value': net_value,
                'vat_rate': vat_rate,
                'vat_amount': 0,
                'gross_value': 0
            }
            
            # Oblicz VAT i brutto
            vat_amount = float(item.get('vat_amount', 0))
            gross_amount = float(item.get('gross_amount', 0))
            
            # Sprawdź czy wartość brutto nie jest domyślna 10000
            if gross_amount == 10000.0 and net_value == 0.0:
                logger.warning(f"Detected default gross value 10000.00 for item {i}, recalculating")
                gross_amount = 0.0
            
            # Jeśli VAT jest 0 ale brutto różne od netto, oblicz VAT
            if vat_amount == 0 and gross_amount > net_value:
                vat_amount = gross_amount - net_value
            
            # Jeśli nadal brak wartości, oblicz standardowo
            if vat_amount == 0 and vat_rate > 0 and net_value > 0:
                vat_decimal = vat_rate / 100
                vat_amount = round(net_value * vat_decimal, 2)
            
            if gross_amount == 0:
                gross_amount = round(net_value + vat_amount, 2)
            
            mapped_item['vat_amount'] = vat_amount
            mapped_item['gross_value'] = gross_amount
            
            mapped_items.append(mapped_item)
        
        return mapped_items
    
    def _create_single_item(self, invoice_data) -> List[Dict]:
        """Tworzy pojedynczą pozycję gdy brak szczegółów"""
        net_value = float(invoice_data.net_total or 0)
        vat_value = float(invoice_data.vat_total or 0)
        gross_value = float(invoice_data.gross_total or 0)
        
        # Sprawdź czy wartości nie są domyślne 10000
        if gross_value == 10000.0 and net_value == 0.0:
            logger.warning("Detected default values in single item, resetting to 0")
            net_value = 0.0
            vat_value = 0.0
            gross_value = 0.0
        
        vat_rate = 23
        if net_value > 0 and vat_value > 0:
            vat_rate = round((vat_value / net_value) * 100)
        
        description = "Zakup towaru/usługi"
        if invoice_data.seller_name and invoice_data.seller_name not in [':', 'None', '']:
            description = f"Faktura od {invoice_data.seller_name}"
        
        return [{
            'lp': 1,
            'description': description,
            'quantity': 1,
            'unit': 'szt.',
            'unit_price': net_value,
            'net_value': net_value,
            'vat_rate': vat_rate,
            'vat_amount': vat_value,
            'gross_value': gross_value
        }]
    
    def _create_single_item_from_dict(self, invoice_data: Dict) -> List[Dict]:
        """Tworzy pojedynczą pozycję dla słownika danych"""
        summary = invoice_data.get('summary', {})
        net_value = float(summary.get('net_total', 0))
        vat_value = float(summary.get('vat_total', 0))
        gross_value = float(summary.get('gross_total', 0))
        
        # Sprawdź czy wartości nie są domyślne 10000
        if gross_value == 10000.0 and net_value == 0.0:
            logger.warning("Detected default values in single item from dict, resetting to 0")
            net_value = 0.0
            vat_value = 0.0
            gross_value = 0.0
        
        vat_rate = 23
        if net_value > 0 and vat_value > 0:
            vat_rate = round((vat_value / net_value) * 100)
        
        description = "Zakup towaru/usługi"
        seller_info = invoice_data.get('seller', {})
        seller_name = seller_info.get('name')
        if seller_name and seller_name not in [':', 'None', '']:
            description = f"Faktura od {seller_name}"
        
        return [{
            'lp': 1,
            'description': description,
            'quantity': 1,
            'unit': 'szt.',
            'unit_price': net_value,
            'net_value': net_value,
            'vat_rate': vat_rate,
            'vat_amount': vat_value,
            'gross_value': gross_value
        }]
    
    def _calculate_vat_summary(self, items: List[Dict]) -> Dict:
        """Oblicza podsumowanie według stawek VAT"""
        vat_summary = {}
        
        for item in items:
            vat_rate = str(item['vat_rate']) + '%'
            
            if vat_rate not in vat_summary:
                vat_summary[vat_rate] = {
                    'net': 0.0,
                    'vat': 0.0,
                    'gross': 0.0
                }
            
            vat_summary[vat_rate]['net'] += item['net_value']
            vat_summary[vat_rate]['vat'] += item['vat_amount']
            vat_summary[vat_rate]['gross'] += item['gross_value']
        
        for rate in vat_summary:
            vat_summary[rate]['net'] = round(vat_summary[rate]['net'], 2)
            vat_summary[rate]['vat'] = round(vat_summary[rate]['vat'], 2)
            vat_summary[rate]['gross'] = round(vat_summary[rate]['gross'], 2)
        
        return vat_summary
