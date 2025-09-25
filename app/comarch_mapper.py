# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
import re
import requests

logger = logging.getLogger(__name__)

@dataclass  
class ComarchInvoiceData:
    """Struktura danych zgodna z Comarch ERP Optima"""
    document_type: str = "FZ"
    invoice_number: str = ""
    issue_date: str = ""
    sale_date: str = ""
    is_correction: bool = False
    currency: str = "PLN"
    jpk_flags: List[str] = None
    seller_code: str = ""
    seller_name: str = ""
    seller_nip: str = ""
    seller_regon: str = ""
    seller_address: Dict = None
    buyer_code: str = ""
    buyer_name: str = ""
    buyer_nip: str = ""
    buyer_address: Dict = None
    payment_method: str = "przelew"
    payment_date: str = ""
    items: List[Dict] = None
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

    def validate_nip(self, nip: str) -> bool:
        """Walidacja NIP przez API GUS lub prostą weryfikację"""
        if not nip or len(nip) != 10 or not nip.isdigit():
            return False
        try:
            response = requests.get(f"https://wl-api.mf.gov.pl/api/check/nip/{nip}")
            return response.status_code == 200 and response.json().get('result', {}).get('status') == 'Czynny'
        except:
            # Fallback: prosty algorytm weryfikacji NIP
            weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
            checksum = sum(int(nip[i]) * weights[i] for i in range(9)) % 11
            return checksum == int(nip[9])

    def map_invoice_data(self, invoice_data) -> ComarchInvoiceData:
        """Mapuje dane z PDF do struktury Comarch"""
        comarch_data = ComarchInvoiceData()
        if isinstance(invoice_data, dict):
            invoice_number = invoice_data.get('invoice_number')
            invoice_date = invoice_data.get('invoice_date')
            sale_date = invoice_data.get('sale_date')
            is_correction = invoice_data.get('is_correction', False)
            currency = invoice_data.get('currency', 'PLN')
            jpk_flags = invoice_data.get('jpk_flags', [])
            seller_info = invoice_data.get('seller', {})
            seller_name = seller_info.get('name')
            seller_nip = seller_info.get('nip')
            payment_method = invoice_data.get('payment_method')
            payment_date = invoice_data.get('payment_date')
            items = invoice_data.get('items', [])
            summary = invoice_data.get('summary', {})
            net_total = float(summary.get('net_total', 0))
            vat_total = float(summary.get('vat_total', 0))
            gross_total = float(summary.get('gross_total', 0))
        else:
            invoice_number = getattr(invoice_data, 'invoice_number', None)
            invoice_date = getattr(invoice_data, 'invoice_date', None)
            sale_date = getattr(invoice_data, 'sale_date', None)
            is_correction = getattr(invoice_data, 'is_correction', False)
            currency = getattr(invoice_data, 'currency', 'PLN')
            jpk_flags = getattr(invoice_data, 'jpk_flags', [])
            seller_name = getattr(invoice_data, 'seller_name', None)
            seller_nip = getattr(invoice_data, 'seller_nip', None)
            payment_method = getattr(invoice_data, 'payment_method', None)
            payment_date = getattr(invoice_data, 'payment_date', None)
            items = getattr(invoice_data, 'items', [])
            net_total = float(getattr(invoice_data, 'net_total', 0))
            vat_total = float(getattr(invoice_data, 'vat_total', 0))
            gross_total = float(getattr(invoice_data, 'gross_total', 0))

        comarch_data.document_type = "KF" if is_correction else "FZ"
        comarch_data.invoice_number = self._clean_invoice_number(invoice_number)
        comarch_data.issue_date = self._format_date(invoice_date)
        comarch_data.sale_date = self._format_date(sale_date) if sale_date else comarch_data.issue_date
        comarch_data.is_correction = is_correction
        comarch_data.currency = currency
        comarch_data.jpk_flags = jpk_flags or []
        comarch_data.seller_name = self._clean_company_name(seller_name)
        comarch_data.seller_nip = self._format_nip(seller_nip)
        comarch_data.seller_code = self._generate_seller_code(seller_name, seller_nip)
        if not self.validate_nip(comarch_data.seller_nip):
            logger.warning(f"Niepoprawny NIP sprzedawcy: {comarch_data.seller_nip}")
        comarch_data.buyer_name = self.default_buyer['name']
        comarch_data.buyer_nip = self.default_buyer['nip']
        comarch_data.buyer_code = self.default_buyer['code']
        comarch_data.buyer_address = self.default_buyer['address']
        comarch_data.payment_method = self._map_payment_method(payment_method)
        comarch_data.payment_date = self._format_date(payment_date) if payment_date else self._calculate_payment_date(comarch_data.issue_date)
        comarch_data.items = self._map_items(items) if items else self._create_single_item_from_dict(invoice_data) if isinstance(invoice_data, dict) else self._create_single_item(invoice_data)
        comarch_data.net_total = net_total
        comarch_data.vat_total = vat_total
        comarch_data.gross_total = gross_total
        comarch_data.vat_summary = self._calculate_vat_summary(comarch_data.items)
        
        # Walidacja sum
        calc_net = sum(item['net_value'] for item in comarch_data.items)
        calc_vat = sum(item['vat_amount'] for item in comarch_data.items)
        calc_gross = sum(item['gross_value'] for item in comarch_data.items)
        if abs(calc_net - net_total) > 0.01 or abs(calc_vat - vat_total) > 0.01 or abs(calc_gross - gross_total) > 0.01:
            logger.warning(f"Niezgodność sum: pozycje (net={calc_net:.2f}, vat={calc_vat:.2f}, gross={calc_gross:.2f}) vs podsumowanie (net={net_total:.2f}, vat={vat_total:.2f}, gross={gross_total:.2f})")
            comarch_data.net_total = calc_net
            comarch_data.vat_total = calc_vat
            comarch_data.gross_total = calc_gross
        
        return comarch_data

    def _clean_invoice_number(self, number: Optional[str]) -> str:
        return str(number).strip() if number else "BRAK_NUMERU"

    def _format_date(self, date_str: Optional[str]) -> str:
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d')
        try:
            for fmt in ['%d.%m.%Y', '%d-%m-%Y', '%Y.%m.%d', '%Y-%m-%d']:
                try:
                    return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
                except ValueError:
                    continue
        except:
            pass
        return datetime.now().strftime('%Y-%m-%d')

    def _clean_company_name(self, name: Optional[str]) -> str:
        return str(name).strip() if name and str(name).lower() not in [':', 'none', ''] else "NIEZNANY DOSTAWCA"

    def _format_nip(self, nip: Optional[str]) -> str:
        if not nip:
            return ""
        cleaned = re.sub(r'[^\d]', '', str(nip))
        return cleaned if len(cleaned) == 10 else ""

    def _generate_seller_code(self, name: Optional[str], nip: Optional[str]) -> str:
        if nip and len(nip) == 10:
            return f"KONTR_{nip[-4:]}"
        return "KONTR_UNKNOWN"

    def _map_payment_method(self, method: Optional[str]) -> str:
        if not method:
            return "przelew"
        method = str(method).lower()
        if 'przelew' in method or 'transfer' in method:
            return "przelew"
        elif 'gotówka' in method or 'cash' in method:
            return "gotówka"
        return "przelew"

    def _calculate_payment_date(self, issue_date: str) -> str:
        try:
            issue = datetime.strptime(issue_date, '%Y-%m-%d')
            payment = issue + timedelta(days=14)
            return payment.strftime('%Y-%m-%d')
        except:
            return (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')

    def _map_items(self, items: List[Dict]) -> List[Dict]:
        mapped_items = []
        for i, item in enumerate(items, 1):
            description = item.get('description', 'Usługa/towar')
            quantity = float(item.get('quantity', 1))
            unit = item.get('unit', 'szt.')
            unit_price = float(item.get('unit_price', 0))
            net_value = float(item.get('net_amount', unit_price * quantity))
            vat_rate = float(item.get('vat_rate', 23))
            
            mapped_item = {
                'lp': i,
                'description': description,
                'quantity': quantity,
                'unit': unit,
                'unit_price': unit_price,
                'net_value': net_value,
                'vat_rate': vat_rate,
                'vat_amount': 0,
                'gross_value': 0
            }
            
            vat_amount = float(item.get('vat_amount', 0))
            gross_amount = float(item.get('gross_amount', 0))
            
            if gross_amount == 10000.0 and net_value == 0.0:
                logger.warning(f"Detected default gross value 10000.00 for item {i}, recalculating")
                gross_amount = 0.0
            
            if vat_amount == 0 and gross_amount > net_value:
                vat_amount = gross_amount - net_value
            
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
        net_value = float(invoice_data.net_total or 0)
        vat_value = float(invoice_data.vat_total or 0)
        gross_value = float(invoice_data.gross_total or 0)
        
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
        summary = invoice_data.get('summary', {})
        net_value = float(summary.get('net_total', 0))
        vat_value = float(summary.get('vat_total', 0))
        gross_value = float(summary.get('gross_total', 0))
        
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
        vat_summary = {}
        for item in items:
            vat_rate = str(item['vat_rate']) + '%'
            if vat_rate not in vat_summary:
                vat_summary[vat_rate] = {
                    'net': 0.0,
                    'vat': 0.0,
                    'gross': 0.0
                }
            vat_summary[vat_rate]['net'] += float(item['net_value'])
            vat_summary[vat_rate]['vat'] += float(item['vat_amount'])
            vat_summary[vat_rate]['gross'] += float(item['gross_value'])
        
        for rate in vat_summary:
            vat_summary[rate]['net'] = round(vat_summary[rate]['net'], 2)
            vat_summary[rate]['vat'] = round(vat_summary[rate]['vat'], 2)
            vat_summary[rate]['gross'] = round(vat_summary[rate]['gross'], 2)
        
        return vat_summary