# -*- coding: utf-8 -*-
"""
Generator XML dla wielu faktur w jednym pliku - format Comarch ERP Optima
"""
from lxml import etree
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class XMLGeneratorMulti:
    def __init__(self):
        self.xsd_schema = None
        try:
            with open('comarch_schema.xsd', 'rb') as f:
                schema_root = etree.parse(f)
                self.xsd_schema = etree.XMLSchema(schema_root)
        except Exception as e:
            logger.warning(f"Nie udało się załadować schematu XSD: {e}")

    def validate_xml(self, xml_str: str) -> bool:
        """Waliduje XML względem schematu XSD"""
        if not self.xsd_schema:
            logger.warning("Schemat XSD nie jest dostępny, pomijam walidację")
            return True
        try:
            xml_doc = etree.fromstring(xml_str.encode('utf-8'))
            self.xsd_schema.assertValid(xml_doc)
            return True
        except etree.DocumentInvalid as e:
            logger.error(f"Błąd walidacji XML: {e}")
            return False

    def generate_multi_invoice_xml(self, invoice_list) -> str:
        """Generuje XML z wieloma fakturami zgodny z formatem Comarch ERP Optima"""
        root = etree.Element("Dokumenty")
        
        for idx, comarch_data in enumerate(invoice_list, 1):
            dokument = etree.SubElement(root, "Dokument")
            dokument.set("Typ", comarch_data.document_type)
            
            naglowek = etree.SubElement(dokument, "Naglowek")
            etree.SubElement(naglowek, "Numer").text = comarch_data.invoice_number
            etree.SubElement(naglowek, "DataWystawienia").text = comarch_data.issue_date
            etree.SubElement(naglowek, "DataSprzedazy").text = comarch_data.sale_date or comarch_data.issue_date
            etree.SubElement(naglowek, "DataKsiegowania").text = datetime.now().strftime('%Y-%m-%d')
            
            kontrahent = etree.SubElement(naglowek, "Kontrahent")
            seller_nip = comarch_data.seller_nip if comarch_data.seller_nip else ""
            etree.SubElement(kontrahent, "NIP").text = seller_nip
            seller_name = comarch_data.seller_name if comarch_data.seller_name else "NIEZNANY DOSTAWCA"
            etree.SubElement(kontrahent, "Nazwa").text = seller_name
            
            if comarch_data.seller_address:
                adres_parts = []
                if comarch_data.seller_address.get('street'):
                    street = comarch_data.seller_address.get('street')
                    building = comarch_data.seller_address.get('building', '')
                    adres_parts.append(f"{street} {building}".strip())
                if comarch_data.seller_address.get('city'):
                    city = comarch_data.seller_address.get('city')
                    postal = comarch_data.seller_address.get('postal_code')
                    if postal:
                        adres_parts.append(f"{postal} {city}")
                    else:
                        adres_parts.append(city)
                adres_text = ", ".join(adres_parts) if adres_parts else "brak danych adresowych"
            else:
                adres_text = "brak danych adresowych"
            
            etree.SubElement(kontrahent, "Adres").text = adres_text
            etree.SubElement(kontrahent, "KodKraju").text = "PL"
            etree.SubElement(naglowek, "FormaPlatnosci").text = comarch_data.payment_method
            etree.SubElement(naglowek, "TerminPlatnosci").text = comarch_data.payment_date
            etree.SubElement(naglowek, "Waluta").text = comarch_data.currency
            
            pozycje = etree.SubElement(dokument, "Pozycje")
            for item in comarch_data.items:
                pozycja = etree.SubElement(pozycje, "Pozycja")
                etree.SubElement(pozycja, "Opis").text = item['description']
                etree.SubElement(pozycja, "Ilosc").text = str(item['quantity'])
                etree.SubElement(pozycja, "Jednostka").text = item.get('unit', 'szt.')
                etree.SubElement(pozycja, "CenaNetto").text = f"{item['unit_price']:.2f}"
                etree.SubElement(pozycja, "WartoscNetto").text = f"{item['net_value']:.2f}"
                etree.SubElement(pozycja, "StawkaVAT").text = str(item['vat_rate'])
                etree.SubElement(pozycja, "KwotaVAT").text = f"{item['vat_amount']:.2f}"
                etree.SubElement(pozycja, "WartoscBrutto").text = f"{item['gross_value']:.2f}"
                kategoria = "402-13" if 'usługa' in item['description'].lower() else "401-05"
                etree.SubElement(pozycja, "KategoriaKsiegowa").text = kategoria
                etree.SubElement(pozycja, "KontoKsiegowe").text = kategoria
            
            rejestr_vat = etree.SubElement(dokument, "RejestrVAT")
            etree.SubElement(rejestr_vat, "Typ").text = "Rejestr zakupu"
            for rate_str, amounts in comarch_data.vat_summary.items():
                rate = rate_str.replace('%', '')
                etree.SubElement(rejestr_vat, "StawkaVAT").text = rate
                etree.SubElement(rejestr_vat, "Netto").text = f"{amounts['net']:.2f}"
                etree.SubElement(rejestr_vat, "VAT").text = f"{amounts['vat']:.2f}"
                etree.SubElement(rejestr_vat, "Brutto").text = f"{amounts['gross']:.2f}"
            
            if comarch_data.jpk_flags:
                etree.SubElement(rejestr_vat, "JPK").text = ",".join(comarch_data.jpk_flags)
            etree.SubElement(rejestr_vat, "Odliczalny").text = "Tak"
            
            platnosc = etree.SubElement(dokument, "Platnosc")
            etree.SubElement(platnosc, "Kwota").text = f"{comarch_data.gross_total:.2f}"
            etree.SubElement(platnosc, "Waluta").text = comarch_data.currency
            etree.SubElement(platnosc, "DataPlatnosci").text = comarch_data.payment_date
            etree.SubElement(platnosc, "Status").text = "rozchód"
            
            if comarch_data.is_correction:
                etree.SubElement(dokument, "Korekta").text = f"Korekta faktury {comarch_data.invoice_number}"
            
            etree.SubElement(dokument, "Wersja").text = "2.00"
        
        xml_str = etree.tostring(
            root,
            pretty_print=True,
            xml_declaration=True,
            encoding='UTF-8'
        ).decode('utf-8')
        
        if not self.validate_xml(xml_str):
            logger.error("Wygenerowany XML nie przeszedł walidacji")
            raise ValueError("Niepoprawny XML")
        
        return xml_str