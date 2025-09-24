@echo off
chcp 65001 > nul
title Test Diagnostyczny Parsowania

echo ════════════════════════════════════════════════════════════════
echo                  TEST DIAGNOSTYCZNY PARSOWANIA
echo ════════════════════════════════════════════════════════════════
echo.

cd C:\pdf-to-xml-app
python skrypty_testowe\test_parsing_diagnosis.py

echo.
echo ════════════════════════════════════════════════════════════════
echo Test zakończony. Sprawdź wyniki powyżej.
echo ════════════════════════════════════════════════════════════════
pause
