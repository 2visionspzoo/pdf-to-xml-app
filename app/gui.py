# -*- coding: utf-8 -*-
"""
Interfejs graficzny Tkinter do edycji danych faktur przed generowaniem XML
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import os
from .pdf_processor import PDFProcessor
from .comarch_mapper import ComarchMapper
from .xml_generator import XMLGenerator
from .xml_generator_multi import XMLGeneratorMulti
import logging

logger = logging.getLogger(__name__)

class InvoiceGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Konwerter Faktur PDF do XML")
        self.root.geometry("800x600")
        
        self.processor = PDFProcessor(parser_type='universal')
        self.mapper = ComarchMapper()
        self.xml_generator = XMLGenerator()
        self.xml_generator_multi = XMLGeneratorMulti()
        
        self.current_data = None
        self.invoice_list = []
        
        self.create_widgets()
    
    def create_widgets(self):
        """Tworzy elementy interfejsu"""
        # Ramka na wybór plików
        file_frame = ttk.LabelFrame(self.root, text="Wybór Plików", padding=10)
        file_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(file_frame, text="Wybierz PDF", command=self.load_pdf).pack(side="left", padx=5)
        ttk.Button(file_frame, text="Wybierz folder PDF", command=self.load_directory).pack(side="left", padx=5)
        self.file_label = ttk.Label(file_frame, text="Brak wybranego pliku")
        self.file_label.pack(side="left", padx=5)
        
        # Ramka na dane faktury
        data_frame = ttk.LabelFrame(self.root, text="Dane Faktury", padding=10)
        data_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Pola edytowalne
        fields = [
            ("Numer faktury", "invoice_number"),
            ("Data wystawienia", "issue_date"),
            ("Data sprzedaży", "sale_date"),
            ("Sprzedawca", "seller_name"),
            ("NIP sprzedawcy", "seller_nip"),
            ("Metoda płatności", "payment_method"),
            ("Termin płatności", "payment_date"),
            ("Waluta", "currency"),
            ("Netto", "net_total"),
            ("VAT", "vat_total"),
            ("Brutto", "gross_total")
        ]
        
        self.entries = {}
        for i, (label, key) in enumerate(fields):
            ttk.Label(data_frame, text=label).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            entry = ttk.Entry(data_frame, width=50)
            entry.grid(row=i, column=1, sticky="ew", padx=5, pady=2)
            self.entries[key] = entry
        
        # Tabela pozycji
        items_frame = ttk.LabelFrame(data_frame, text="Pozycje", padding=5)
        items_frame.grid(row=len(fields), column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        
        self.items_tree = ttk.Treeview(items_frame, columns=("Lp", "Opis", "Ilość", "Jednostka", "Cena netto", "VAT", "Brutto"), show="headings")
        self.items_tree.heading("Lp", text="Lp")
        self.items_tree.heading("Opis", text="Opis")
        self.items_tree.heading("Ilość", text="Ilość")
        self.items_tree.heading("Jednostka", text="Jednostka")
        self.items_tree.heading("Cena netto", text="Cena netto")
        self.items_tree.heading("VAT", text="VAT%")
        self.items_tree.heading("Brutto", text="Brutto")
        self.items_tree.pack(fill="both", expand=True)
        
        # Przyciski
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill="x", padx=5, pady=5)
        ttk.Button(button_frame, text="Zapisz XML", command=self.save_xml).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Zapisz wiele XML", command=self.save_multi_xml).pack(side="left", padx=5)
    
    def load_pdf(self):
        """Ładuje pojedynczy plik PDF i wypełnia dane"""
        file_path = filedialog.askopenfilename(filetypes=[("Pliki PDF", "*.pdf")])
        if file_path:
            self.file_label.config(text=Path(file_path).name)
            try:
                invoice_data = self.processor.extract_from_pdf(file_path)
                self.current_data = self.mapper.map_invoice_data(invoice_data)
                self.current_data.source_file = Path(file_path).name
                self.populate_fields()
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie udało się przetworzyć pliku: {e}")
    
    def load_directory(self):
        """Ładuje wszystkie PDF z folderu"""
        directory = filedialog.askdirectory()
        if directory:
            self.file_label.config(text=f"Folder: {directory}")
            self.invoice_list = []
            for pdf_file in Path(directory).glob("*.pdf"):
                try:
                    invoice_data = self.processor.extract_from_pdf(str(pdf_file))
                    comarch_data = self.mapper.map_invoice_data(invoice_data)
                    comarch_data.source_file = pdf_file.name
                    self.invoice_list.append(comarch_data)
                except Exception as e:
                    logger.error(f"Błąd przetwarzania {pdf_file.name}: {e}")
            messagebox.showinfo("Sukces", f"Załadowano {len(self.invoice_list)} faktur")
    
    def populate_fields(self):
        """Wypełnia pola danymi faktury"""
        if not self.current_data:
            return
        for key, entry in self.entries.items():
            value = getattr(self.current_data, key, "")
            entry.delete(0, tk.END)
            entry.insert(0, str(value))
        
        for item in self.items_tree.get_children():
            self.items_tree.delete(item)
        
        for item in self.current_data.items:
            self.items_tree.insert("", "end", values=(
                item['lp'],
                item['description'],
                item['quantity'],
                item['unit'],
                f"{item['unit_price']:.2f}",
                item['vat_rate'],
                f"{item['gross_value']:.2f}"
            ))
    
    def save_xml(self):
        """Zapisuje pojedynczy XML"""
        if not self.current_data:
            messagebox.showwarning("Ostrzeżenie", "Brak danych faktury")
            return
        output_file = filedialog.asksaveasfilename(defaultextension=".xml", filetypes=[("Pliki XML", "*.xml")])
        if output_file:
            try:
                xml_content = self.xml_generator.generate_xml(self.current_data)
                with open(output_file, 'w', encoding='utf-8-sig') as f:
                    f.write(xml_content)
                messagebox.showinfo("Sukces", f"Zapisano XML do {output_file}")
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie udało się zapisać XML: {e}")
    
    def save_multi_xml(self):
        """Zapisuje wiele faktur do jednego XML"""
        if not self.invoice_list:
            messagebox.showwarning("Ostrzeżenie", "Brak załadowanych faktur")
            return
        output_file = filedialog.asksaveasfilename(defaultextension=".xml", filetypes=[("Pliki XML", "*.xml")])
        if output_file:
            try:
                xml_content = self.xml_generator_multi.generate_multi_invoice_xml(self.invoice_list)
                with open(output_file, 'w', encoding='utf-8-sig') as f:
                    f.write(xml_content)
                messagebox.showinfo("Sukces", f"Zapisano XML z {len(self.invoice_list)} fakturami do {output_file}")
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie udało się zapisać XML: {e}")

# Alias dla kompatybilności wstecznej
PDFInvoiceConverterGUI = InvoiceGUI

def main():
    root = tk.Tk()
    app = InvoiceGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()