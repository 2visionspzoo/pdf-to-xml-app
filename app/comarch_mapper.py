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
        
        # Mapowanie podstawowych danych
        comarch_data.invoice_number = self._clean_invoice_number(invoice_data.invoice_number)
        comarch_data.issue_date = self._format_date(invoice_data.invoice_date)
        comarch_data.sale_date = self._format_date(invoice_data.sale_date) if invoice_data.sale_date else comarch_data.issue_date
        
        # Mapowanie sprzedawcy
        comarch_data.seller_name = self._clean_company_name(invoice_data.seller_name)
        comarch_data.seller_nip = self._format_nip(invoice_data.seller_nip)
        comarch_data.seller_code = self._generate_seller_code(invoice_data.seller_name, invoice_data.seller_nip)
        
        # Mapowanie nabywcy (zawsze 2Vision)
        comarch_data.buyer_name = self.default_buyer['name']
        comarch_data.buyer_nip = self.default_buyer['nip']
        comarch_data.buyer_code = self.default_buyer['code']
        comarch_data.buyer_address = self.default_buyer['address']
        
        # Mapowanie płatności
        comarch_data.payment_method = self._map_payment_method(invoice_data.payment_method)
        comarch_data.payment_date = self._format_date(invoice_data.payment_date) if invoice_data.payment_date else self._calculate_payment_date(comarch_data.issue_date)
        
        # Mapowanie pozycji
        if invoice_data.items:
            comarch_data.items = self._map_items(invoice_data.items)
        else:
            comarch_data.items = self._create_single_item(invoice_data)
        
        # Mapowanie sum
        comarch_data.net_total = float(invoice_data.net_total or 0)
        comarch_data.vat_total = float(invoice_data.vat_total or 0)
        comarch_data.gross_total = float(invoice_data.gross_total or 0)
        
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
        if not name:
            return "NIEZNANY DOSTAWCA"
        name = re.sub(r'\s+', ' ', name).strip()
        if name.upper() == name:
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
            code = ''.join(word[0] for word in name.split()[:3]).upper()
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
            mapped_item = {
                'lp': i,
                'description': item.get('description', f'Towar/Usługa {i}'),
                'quantity': float(item.get('quantity', 1)),
                'unit': item.get('unit', 'szt.'),
                'unit_price': float(item.get('unit_price', 0)),
                'net_value': float(item.get('net_value', 0)),
                'vat_rate': int(item.get('vat_rate', 23)),
                'vat_amount': 0,
                'gross_value': 0
            }
            
            # Oblicz VAT i brutto
            vat_decimal = mapped_item['vat_rate'] / 100
            mapped_item['vat_amount'] = round(mapped_item['net_value'] * vat_decimal, 2)
            mapped_item['gross_value'] = round(mapped_item['net_value'] + mapped_item['vat_amount'], 2)
            
            mapped_items.append(mapped_item)
        
        return mapped_items
    
    def _create_single_item(self, invoice_data) -> List[Dict]:
        """Tworzy pojedynczą pozycję gdy brak szczegółów"""
        net_value = float(invoice_data.net_total or 0)
        vat_value = float(invoice_data.vat_total or 0)
        gross_value = float(invoice_data.gross_total or 0)
        
        vat_rate = 23
        if net_value > 0:
            vat_rate = round((vat_value / net_value) * 100)
        
        description = "Zakup towaru/usługi"
        if invoice_data.seller_name:
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
