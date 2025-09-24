# -*- coding: utf-8 -*-
from lxml import etree
import logging

logger = logging.getLogger(__name__)

class XMLGenerator:
    def generate_xml(self, comarch_data) -> str:
        """Generuje XML zgodny z formatem Comarch ERP Optima"""
        
        # Tworzenie głównego elementu
        root = etree.Element("JPK", nsmap={
            None: "http://jpk.mf.gov.pl/wzor/2022/02/17/02171/"
        })
        
        # Nagłówek
        naglowek = etree.SubElement(root, "Naglowek")
        etree.SubElement(naglowek, "KodFormularza").text = "JPK_FA"
        etree.SubElement(naglowek, "WariantFormularza").text = "3"
        etree.SubElement(naglowek, "DataWytworzeniaJPK").text = comarch_data.issue_date
        
        # Podmiot
        podmiot = etree.SubElement(root, "Podmiot")
        etree.SubElement(podmiot, "NIP").text = comarch_data.buyer_nip
        etree.SubElement(podmiot, "PelnaNazwa").text = comarch_data.buyer_name
        
        # Faktura zakupu
        faktura = etree.SubElement(root, "FakturaZakup")
        etree.SubElement(faktura, "TypDokumentu").text = "FZ"
        etree.SubElement(faktura, "NrFaktury").text = comarch_data.invoice_number
        etree.SubElement(faktura, "DataWystawienia").text = comarch_data.issue_date
        etree.SubElement(faktura, "DataWplywu").text = comarch_data.issue_date
        
        # Sprzedawca
        etree.SubElement(faktura, "NazwaDostawcy").text = comarch_data.seller_name
        etree.SubElement(faktura, "NrIdDostawcy").text = comarch_data.seller_nip
        
        # Kwoty
        etree.SubElement(faktura, "K_43").text = f"{comarch_data.net_total:.2f}"
        etree.SubElement(faktura, "K_44").text = f"{comarch_data.vat_total:.2f}"
        etree.SubElement(faktura, "K_45").text = f"{comarch_data.gross_total:.2f}"
        
        # Pozycje faktury
        for item in comarch_data.items:
            wiersz = etree.SubElement(faktura, "FakturaZakupWiersz")
            etree.SubElement(wiersz, "Lp").text = str(item['lp'])
            etree.SubElement(wiersz, "NazwaTowaru").text = item['description']
            etree.SubElement(wiersz, "Ilosc").text = f"{item['quantity']:.4f}"
            etree.SubElement(wiersz, "CenaJedn").text = f"{item['unit_price']:.2f}"
            etree.SubElement(wiersz, "WartoscNetto").text = f"{item['net_value']:.2f}"
            etree.SubElement(wiersz, "StawkaVAT").text = f"{item['vat_rate']}%"
            etree.SubElement(wiersz, "KwotaVAT").text = f"{item['vat_amount']:.2f}"
        
        # Konwersja do stringa z pretty print
        xml_str = etree.tostring(
            root, 
            pretty_print=True, 
            xml_declaration=True,
            encoding='UTF-8'
        ).decode('utf-8')
        
        return xml_str
