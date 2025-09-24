#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prosty interfejs GUI do konwertera faktur PDF-to-XML
"""

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import sys
import os
from pathlib import Path
import subprocess
import threading

# Dodaj katalog główny do ścieżki
sys.path.insert(0, str(Path(__file__).parent))

class PDFtoXMLConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Konwerter Faktur PDF → XML (Comarch Optima)")
        self.root.geometry("700x500")
        
        # Nagłówek
        header = tk.Label(root, text="KONWERTER FAKTUR PDF → XML", 
                         font=("Arial", 16, "bold"))
        header.pack(pady=10)
        
        # Frame dla przycisków
        button_frame = tk.Frame(root)
        button_frame.pack(pady=20)
        
        # Przycisk - konwertuj pojedynczy plik
        self.btn_single = tk.Button(button_frame, 
                                    text="📄 Konwertuj pojedynczy plik PDF",
                                    command=self.convert_single_file,
                                    width=30, height=2,
                                    font=("Arial", 10))
        self.btn_single.pack(pady=5)
        
        # Przycisk - konwertuj folder
        self.btn_folder = tk.Button(button_frame, 
                                    text="📁 Konwertuj wszystkie pliki z folderu 'input'",
                                    command=self.convert_folder,
                                    width=30, height=2,
                                    font=("Arial", 10))
        self.btn_folder.pack(pady=5)
        
        # Przycisk - otwórz folder input
        self.btn_open_input = tk.Button(button_frame, 
                                        text="📂 Otwórz folder 'input'",
                                        command=self.open_input_folder,
                                        width=30, height=2,
                                        font=("Arial", 10))
        self.btn_open_input.pack(pady=5)
        
        # Przycisk - otwórz folder output
        self.btn_open_output = tk.Button(button_frame, 
                                         text="📂 Otwórz folder 'output'",
                                         command=self.open_output_folder,
                                         width=30, height=2,
                                         font=("Arial", 10))
        self.btn_open_output.pack(pady=5)
        
        # Obszar logów
        log_label = tk.Label(root, text="Logi:", font=("Arial", 10, "bold"))
        log_label.pack(pady=(20, 5))
        
        self.log_text = scrolledtext.ScrolledText(root, height=10, width=80)
        self.log_text.pack(pady=5, padx=10)
        
        # Footer
        footer = tk.Label(root, text="© 2025 PDF-to-XML Converter for Comarch Optima", 
                         font=("Arial", 8))
        footer.pack(side=tk.BOTTOM, pady=5)
        
        self.log("System gotowy do pracy")
    
    def log(self, message):
        """Dodaje wpis do logów"""
        self.log_text.insert(tk.END, f"► {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def convert_single_file(self):
        """Konwertuje pojedynczy plik PDF"""
        # Wybierz plik
        file_path = filedialog.askopenfilename(
            title="Wybierz fakturę PDF",
            filetypes=[("Pliki PDF", "*.pdf"), ("Wszystkie pliki", "*.*")],
            initialdir=r"C:\pdf-to-xml-app\input"
        )
        
        if not file_path:
            return
        
        self.log(f"Wybrano plik: {os.path.basename(file_path)}")
        
        # Określ plik wyjściowy
        output_name = Path(file_path).stem + ".xml"
        output_path = Path(r"C:\pdf-to-xml-app\output") / output_name
        
        # Uruchom konwersję w osobnym wątku
        thread = threading.Thread(target=self._run_conversion, 
                                 args=(file_path, str(output_path)))
        thread.start()
    
    def convert_folder(self):
        """Konwertuje wszystkie pliki z folderu input"""
        input_dir = Path(r"C:\pdf-to-xml-app\input")
        pdf_files = list(input_dir.glob("*.pdf"))
        
        if not pdf_files:
            messagebox.showwarning("Brak plików", 
                                  "Brak plików PDF w folderze 'input'")
            return
        
        self.log(f"Znaleziono {len(pdf_files)} plików PDF do konwersji")
        
        # Uruchom konwersję w osobnym wątku
        thread = threading.Thread(target=self._run_batch_conversion)
        thread.start()
    
    def _run_conversion(self, input_path, output_path):
        """Uruchamia konwersję pojedynczego pliku"""
        try:
            self.log(f"Rozpoczynam konwersję...")
            
            cmd = [
                sys.executable,
                r"C:\pdf-to-xml-app\app\main.py",
                "--input", input_path,
                "--output", output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log(f"✅ Sukces! XML zapisany jako: {os.path.basename(output_path)}")
                messagebox.showinfo("Sukces", 
                                   f"Konwersja zakończona!\nPlik zapisany jako:\n{output_path}")
            else:
                self.log(f"❌ Błąd podczas konwersji")
                self.log(result.stderr or result.stdout)
                messagebox.showerror("Błąd", "Wystąpił błąd podczas konwersji")
                
        except Exception as e:
            self.log(f"❌ Błąd: {str(e)}")
            messagebox.showerror("Błąd", f"Błąd: {str(e)}")
    
    def _run_batch_conversion(self):
        """Uruchamia konwersję wszystkich plików"""
        try:
            self.log("Rozpoczynam konwersję wszystkich plików...")
            
            cmd = [sys.executable, r"C:\pdf-to-xml-app\app\main.py"]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log("✅ Wszystkie pliki zostały przekonwertowane!")
                output_dir = Path(r"C:\pdf-to-xml-app\output")
                xml_files = list(output_dir.glob("*.xml"))
                self.log(f"Wygenerowano {len(xml_files)} plików XML")
                messagebox.showinfo("Sukces", 
                                   f"Konwersja zakończona!\n"
                                   f"Wygenerowano {len(xml_files)} plików XML")
            else:
                self.log("❌ Błąd podczas konwersji")
                self.log(result.stderr or result.stdout)
                messagebox.showerror("Błąd", "Wystąpił błąd podczas konwersji")
                
        except Exception as e:
            self.log(f"❌ Błąd: {str(e)}")
            messagebox.showerror("Błąd", f"Błąd: {str(e)}")
    
    def open_input_folder(self):
        """Otwiera folder input w eksploratorze"""
        input_dir = r"C:\pdf-to-xml-app\input"
        os.startfile(input_dir)
        self.log("Otwarto folder 'input'")
    
    def open_output_folder(self):
        """Otwiera folder output w eksploratorze"""
        output_dir = r"C:\pdf-to-xml-app\output"
        os.startfile(output_dir)
        self.log("Otwarto folder 'output'")


if __name__ == "__main__":
    root = tk.Tk()
    app = PDFtoXMLConverterGUI(root)
    root.mainloop()
