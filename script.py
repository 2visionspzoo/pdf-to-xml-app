import argparse
import configparser
import re
from xml.etree import ElementTree as ET
import PyPDF2
from datetime import datetime
import uuid

def extract_invoices_from_pdf(pdf_path):
    """Ekstraktuje dane faktury z PDF"""
    invoices = []
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            full_text = ""
            
            # Wyciągnij cały tekst z PDF
            for page_num in range(len(reader.pages)):
                full_text += reader.pages[page_num].extract_text() + "\n"
            
            # Parsowanie różnych formatów numeru faktury
            patterns_numer = [
                r'(?:Nr\.|Numer|nr)?\s*(?:faktury)?\s*:?\s*([A-Z0-9\-/\.]+)',
                r'FAKTURA\s+([A-Z0-9\-/\.]+)',
                r'Invoice\s+(?:no\.?)?\s*([A-Z0-9\-/\.]+)'
            ]
            
            # Parsowanie dat w różnych formatach
            patterns_data = [
                r'Data\s*wystawienia\s*:?\s*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4})',
                r'(?:z\s*dnia|dnia)\s*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4})',
                r'Date\s*:?\s*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4})'
            ]
            
            # Parsowanie NIP
            patterns_nip = [
                r'NIP\s*:?\s*(\d{3}[\-\s]?\d{3}[\-\s]?\d{2}[\-\s]?\d{2})',
                r'Tax\s*ID\s*:?\s*(\d{10})'
            ]
            
            # Parsowanie kwot
            patterns_kwoty = [
                r'(?:Razem|Do\s*zapłaty|Total)\s*:?\s*(\d+[,.]?\d*)',
                r'Brutto\s*:?\s*(\d+[,.]?\d*)',
                r'SUMA\s*:?\s*(\d+[,.]?\d*)'
            ]
            
            # Parsowanie stawki VAT
            patterns_vat = [
                r'VAT\s*(\d{1,2})%',
                r'(\d{1,2})%\s*VAT',
                r'Stawka\s*VAT\s*:?\s*(\d{1,2})'
            ]
            
            # Znajdź dopasowania
            numer = None
            for pattern in patterns_numer:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    numer = match.group(1)
                    break
            
            data = None
            for pattern in patterns_data:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    data = match.group(1)
                    break
            
            nip = None
            for pattern in patterns_nip:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    nip = re.sub(r'[\-\s]', '', match.group(1))
                    break
            
            kwota_brutto = None
            for pattern in patterns_kwoty:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    kwota_brutto = match.group(1).replace(',', '.')
                    break
            
            vat_rate = "23"  # domyślna stawka
            for pattern in patterns_vat:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    vat_rate = match.group(1)
                    break
            
            # Parsowanie danych sprzedawcy i nabywcy
            nazwa_sprzedawcy = extract_company_name(full_text, "sprzedawca")
            nazwa_nabywcy = extract_company_name(full_text, "nabywca")
            
            if numer and data:
                # Konwersja daty do formatu YYYY-MM-DD
                data_formatted = convert_date_format(data)
                
                # Oblicz kwoty netto i VAT
                if kwota_brutto:
                    brutto = float(kwota_brutto)
                    vat_decimal = int(vat_rate) / 100
                    netto = round(brutto / (1 + vat_decimal), 2)
                    kwota_vat = round(brutto - netto, 2)
                else:
                    brutto = netto = kwota_vat = 0.0
                
                invoices.append({
                    'numer': numer,
                    'data_wystawienia': data_formatted,
                    'data_sprzedazy': data_formatted,  # Często ta sama
                    'nip_sprzedawcy': nip or "0000000000",
                    'nazwa_sprzedawcy': nazwa_sprzedawcy or "NIEZNANY SPRZEDAWCA",
                    'nazwa_nabywcy': nazwa_nabywcy or "NIEZNANY NABYWCA", 
                    'brutto': brutto,
                    'netto': netto,
                    'vat': kwota_vat,
                    'stawka_vat': vat_rate,
                    'opis': f"Import faktury {numer}",
                    'konto': "402-10"  # Domyślne konto księgowe
                })
            
    except Exception as e:
        print(f"Błąd podczas parsowania PDF: {e}")
        
    return invoices

def extract_company_name(text, typ):
    """Wyciąga nazwę firmy z tekstu"""
    patterns = {
        "sprzedawca": [
            r'Sprzedawca\s*:?\s*([^\n]+)',
            r'Dostawca\s*:?\s*([^\n]+)'
        ],
        "nabywca": [
            r'Nabywca\s*:?\s*([^\n]+)',
            r'Odbiorca\s*:?\s*([^\n]+)'
        ]
    }
    
    for pattern in patterns.get(typ, []):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None

def convert_date_format(date_str):
    """Konwertuje datę do formatu YYYY-MM-DD"""
    try:
        # Obsługa różnych formatów dat
        for fmt in ('%d.%m.%Y', '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d'):
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
        return date_str  # Jeśli nie można skonwertować
    except:
        return date_str

def generate_optima_xml(invoices, output_path):
    """Generuje XML zgodny z Comarch ERP Optima"""
    
    # Korzeń dokumentu
    root = ET.Element("ImportData")
    root.set("xmlns", "http://www.comarch.pl/XMLData")
    
    for inv in invoices:
        # Generuj GUID dla kontrahenta
        kontrahent_guid = str(uuid.uuid4()).upper()
        
        # Węzeł kontrahenta (wymagany)
        kontrahent = ET.SubElement(root, "Kontrahent")
        kontrahent.set("GUID", kontrahent_guid)
        
        ET.SubElement(kontrahent, "NIP").text = inv['nip_sprzedawcy']
        ET.SubElement(kontrahent, "Nazwa").text = inv['nazwa_sprzedawcy']
        ET.SubElement(kontrahent, "Status").text = "dostawca"
        ET.SubElement(kontrahent, "Waluta").text = "PLN"
        ET.SubElement(kontrahent, "FormaPlatnosci").text = "przelew"
        ET.SubElement(kontrahent, "Termin").text = "7"
        
        # Adres (wymagany dla kontrahenta)
        adres = ET.SubElement(kontrahent, "Adres")
        ET.SubElement(adres, "Ulica").text = "Nieznana"
        ET.SubElement(adres, "Miasto").text = "Nieznane"
        ET.SubElement(adres, "KodPocztowy").text = "00-000"
        ET.SubElement(adres, "Kraj").text = "PL"
        
        # Węzeł rejestru VAT
        rejestr_vat = ET.SubElement(root, "RejestrVat")
        rejestr_vat.set("Typ", "Rejestr zakupu ZAKUP")
        
        ET.SubElement(rejestr_vat, "Numer").text = inv['numer']
        ET.SubElement(rejestr_vat, "DataWystawienia").text = inv['data_wystawienia']
        ET.SubElement(rejestr_vat, "DataSprzedazy").text = inv['data_sprzedazy']
        
        # Data płatności (7 dni od wystawienia)
        try:
            data_platnosci = datetime.strptime(inv['data_wystawienia'], '%Y-%m-%d')
            data_platnosci = data_platnosci.replace(day=data_platnosci.day + 7)
            ET.SubElement(rejestr_vat, "DataPlatnosci").text = data_platnosci.strftime('%Y-%m-%d')
        except:
            ET.SubElement(rejestr_vat, "DataPlatnosci").text = inv['data_wystawienia']
        
        ET.SubElement(rejestr_vat, "KontrahentGUID").text = kontrahent_guid
        ET.SubElement(rejestr_vat, "Konto").text = inv['konto']
        
        # Kwoty
        kwoty = ET.SubElement(rejestr_vat, "Kwoty")
        ET.SubElement(kwoty, "Netto").text = str(inv['netto'])
        ET.SubElement(kwoty, "VAT").text = str(inv['vat'])
        ET.SubElement(kwoty, "Brutto").text = str(inv['brutto'])
        
        ET.SubElement(rejestr_vat, "StawkaVAT").text = f"{inv['stawka_vat']} opodatkowana"
        ET.SubElement(rejestr_vat, "Opis").text = inv['opis']
        ET.SubElement(rejestr_vat, "FormaPlatnosci").text = "przelew"
        
        # Węzeł dokumentu (opcjonalny dla pełniejszej struktury)
        dokument = ET.SubElement(root, "Dokument")
        dokument.set("Typ", "FZ")
        
        naglowek = ET.SubElement(dokument, "Naglowek")
        ET.SubElement(naglowek, "Numer").text = inv['numer']
        ET.SubElement(naglowek, "Data").text = inv['data_wystawienia']
        ET.SubElement(naglowek, "SprzedawcaNIP").text = inv['nip_sprzedawcy']
        
        pozycje = ET.SubElement(dokument, "Pozycje")
        pozycja = ET.SubElement(pozycje, "Pozycja")
        ET.SubElement(pozycja, "Nazwa").text = inv['opis']
        ET.SubElement(pozycja, "Ilosc").text = "1"
        ET.SubElement(pozycja, "CenaNetto").text = str(inv['netto'])
        ET.SubElement(pozycja, "VAT").text = inv['stawka_vat']
        ET.SubElement(pozycja, "Brutto").text = str(inv['brutto'])
        
        podsumowanie = ET.SubElement(dokument, "Podsumowanie")
        ET.SubElement(podsumowanie, "Netto").text = str(inv['netto'])
        ET.SubElement(podsumowanie, "VAT").text = str(inv['vat'])
        ET.SubElement(podsumowanie, "Brutto").text = str(inv['brutto'])
    
    # Formatowanie XML z wcięciami
    indent_xml(root)
    
    # Zapis do pliku
    tree = ET.ElementTree(root)
    tree.write(output_path, encoding='utf-8', xml_declaration=True)
    print(f"Wygenerowano XML z {len(invoices)} fakturami")

def indent_xml(elem, level=0):
    """Dodaje wcięcia do XML dla lepszej czytelności"""
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent_xml(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def main():
    parser = argparse.ArgumentParser(description='Konwerter PDF na XML dla Comarch ERP Optima')
    parser.add_argument('--config', required=True, help='Ścieżka do pliku config.txt')
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.config)

    input_pdf = config['PATHS']['input_pdf']
    output_xml = config['PATHS']['output_xml']

    print(f"Przetwarzanie pliku: {input_pdf}")
    invoices = extract_invoices_from_pdf(input_pdf)
    
    if invoices:
        generate_optima_xml(invoices, output_xml)
        print(f"XML wygenerowany w: {output_xml}")
        print(f"Znaleziono {len(invoices)} faktur:")
        for inv in invoices:
            print(f"  - {inv['numer']} z dnia {inv['data_wystawienia']}, kwota: {inv['brutto']} PLN")
    else:
        print("Nie znaleziono żadnych faktur w pliku PDF")

if __name__ == "__main__":
    main()
