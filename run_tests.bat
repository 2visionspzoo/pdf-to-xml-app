@echo off
REM ===========================================
REM Uruchom testy systemu PDF to XML
REM ===========================================

echo.
echo ############################################################
echo #          TESTY SYSTEMU PDF TO XML CONVERTER             #
echo ############################################################
echo.

REM Przejdź do głównego katalogu projektu
cd /d C:\pdf-to-xml-app

echo [1/4] TEST POPRAWEK PARSERA
echo ============================================
python skrypty_testowe\test_parser_fixes_part1.py
if %errorlevel% neq 0 (
    echo [!] Test parsera zakończony z błędami
) else (
    echo [OK] Test parsera zakończony pomyślnie
)

echo.
echo [2/4] SZYBKI TEST NA PRZYKŁADOWEJ FAKTURZE
echo ============================================
python skrypty_testowe\test_quick.py
if %errorlevel% neq 0 (
    echo [!] Szybki test zakończony z błędami
) else (
    echo [OK] Szybki test zakończony pomyślnie
)

echo.
echo [3/4] TEST DEMONSTRACYJNY
echo ============================================
python skrypty_testowe\test_demo.py
if %errorlevel% neq 0 (
    echo [!] Test demonstracyjny zakończony z błędami
) else (
    echo [OK] Test demonstracyjny zakończony pomyślnie
)

echo.
echo [4/4] TEST NA WSZYSTKICH FAKTURACH (opcjonalny)
echo ============================================
choice /C YN /M "Czy uruchomić test na wszystkich fakturach?"
if errorlevel 2 goto skip_all_test
if errorlevel 1 (
    python skrypty_testowe\test_real_invoices.py
)
:skip_all_test

echo.
echo ############################################################
echo #                  TESTY ZAKOŃCZONE                       #
echo ############################################################
echo.
echo Wyniki testów znajdziesz w:
echo - skrypty_testowe\test_quick_output.json
echo - skrypty_testowe\test_demo_output.json
echo - skrypty_testowe\test_real_invoices_report.json (jeśli uruchomiono)
echo.
pause
