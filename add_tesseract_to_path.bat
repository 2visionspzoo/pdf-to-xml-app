@echo off
REM ============================================
REM Dodaj Tesseract do PATH (tymczasowo)
REM ============================================

echo.
echo Dodawanie Tesseract do PATH dla tej sesji...
set PATH=%PATH%;C:\Program Files\Tesseract-OCR

echo Tesseract dodany do PATH
echo.
echo Sprawdzanie...
tesseract --version

echo.
echo Teraz możesz uruchomić testy w tym oknie.
echo.
cmd /k
