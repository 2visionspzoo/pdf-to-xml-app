@echo off
REM ============================================
REM Test bezpośredni na fakturze
REM ============================================

cd /d C:\pdf-to-xml-app

echo.
echo ############################################################
echo #           TEST NA RZECZYWISTEJ FAKTURZE                  #
echo ############################################################
echo.

python test_direct.py

echo.
pause
