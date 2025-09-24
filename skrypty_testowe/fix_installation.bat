@echo off
chcp 65001 > nul
echo =========================================
echo Naprawa instalacji PDF-to-XML Converter
echo =========================================
echo.

echo [1] Aktualizacja pip...
python -m pip install --upgrade pip

echo.
echo [2] Instalacja pakietów jeden po drugim...
echo.

echo Instalacja pdfplumber...
python -m pip install pdfplumber==0.11.4

echo Instalacja pytesseract...
python -m pip install pytesseract==0.3.13

echo Instalacja pdf2image...
python -m pip install pdf2image==1.17.0

echo Instalacja lxml...
python -m pip install lxml==5.3.0

echo Instalacja Pillow...
python -m pip install Pillow==11.0.0

echo Instalacja PyPDF2...
python -m pip install PyPDF2==3.0.1

echo Instalacja python-dateutil...
python -m pip install python-dateutil==2.9.0

echo Instalacja openpyxl...
python -m pip install openpyxl==3.1.5

echo Instalacja pandas...
python -m pip install pandas==2.2.3

echo.
echo =========================================
echo Instalacja zakończona!
echo =========================================
pause