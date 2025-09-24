@echo off
echo ====================================
echo Instalacja pakietów Python
echo ====================================
echo.

python -m pip install --upgrade pip
python -m pip install -r ..\requirements.txt

echo.
echo ====================================
echo Sprawdzanie instalacji
echo ====================================
python -c "import pdfplumber; print('✓ pdfplumber OK')"
python -c "import pytesseract; print('✓ pytesseract OK')"
python -c "import lxml; print('✓ lxml OK')"
python -c "import PIL; print('✓ Pillow OK')"
python -c "import PyPDF2; print('✓ PyPDF2 OK')"
python -c "import dateutil; print('✓ dateutil OK')"

echo.
pause