# -*- coding: utf-8 -*-
"""
Generator XML dla wielu faktur w jednym pliku
"""
from lxml import etree
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class XMLGeneratorMulti:
    def generate_multi_invoice_xml(self, invoice_list) -> str:
        """Generuje XML z wieloma fakturami zgodny z formatem JPK"""
        
        # Tworzenie głównego elementu
        root = etree.Element("JPK", nsmap={
            None: "http://jpk.mf.gov.pl/wzor/2022/02/17/02171/"
        })
        
        # Nagłówek
        naglowek = etree.SubElement(root, "Naglowek")
        etree.SubElement(naglowek, "KodFormularza").text = "JPK_FA"
        etree.SubElement(naglowek, "WariantFormularza").text = "3"
        etree.SubElement(naglowek, "DataWytworzeniaJPK").text = datetime.now().strftime('%Y-%m-%d')
        
        # Podmiot (zakładamy, że zawsze ten sam - 2VISION)
        if invoice_list:
            first_invoice = invoice_list[0]
            podmiot = etree.SubElement(root, "Podmiot")
            etree.SubElement(podmiot, "NIP").text = first_invoice.buyer_nip
            etree.SubElement(podmiot, "PelnaNazwa").text = first_invoice.buyer_name
        
        # Kontener na wszystkie faktury
        faktury_container = etree.SubElement(root, "Faktury")
        
        # Dodaj każdą fakturę
        for idx, comarch_data in enumerate(invoice_list, 1):
            # Faktura zakupu
            faktura = etree.SubElement(faktury_container, "FakturaZakup")
            etree.SubElement(faktura, "LpFaktury").text = str(idx)
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
        
        # Podsumowanie
        podsumowanie = etree.SubElement(root, "Podsumowanie")
        
        # Oblicz sumy ze wszystkich faktur
        total_net = sum(inv.net_total for inv in invoice_list)
        total_vat = sum(inv.vat_total for inv in invoice_list)
        total_gross = sum(inv.gross_total for inv in invoice_list)
        
        etree.SubElement(podsumowanie, "LiczbaFaktur").text = str(len(invoice_list))
        etree.SubElement(podsumowanie, "SumaNetto").text = f"{total_net:.2f}"
        etree.SubElement(podsumowanie, "SumaVAT").text = f"{total_vat:.2f}"
        etree.SubElement(podsumowanie, "SumaBrutto").text = f"{total_gross:.2f}"
        
        # Konwersja do stringa z pretty print
        xml_str = etree.tostring(
            root, 
            pretty_print=True, 
            xml_declaration=True,
            encoding='UTF-8'
        ).decode('utf-8')
        
        return xml_str