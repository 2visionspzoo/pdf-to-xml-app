# Bazowy obraz: Lekki Python 3.12 dla efektywności
FROM python:3.12-slim

# Ustaw katalog roboczy
WORKDIR /app

# Skopiuj pliki do kontenera
COPY requirements.txt .
COPY script.py .

# Zainstaluj zależności
RUN pip install --no-cache-dir -r requirements.txt

# ENTRYPOINT: Uruchamia skrypt z config.txt jako argumentem
ENTRYPOINT ["python", "script.py", "--config", "config.txt"]