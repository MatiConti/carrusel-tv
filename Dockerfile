FROM python:3.11-slim

WORKDIR /app

# Primero las dependencias para cachear capas de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Luego el codigo fuente
COPY carrusel_tv.py .

# El bot se levanta en un solo proceso
CMD ["python", "-u", "carrusel_tv.py"]
