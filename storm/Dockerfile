FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libexpat1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Smoke test: garante que o stack geo (rasterio/rioxarray) importa com todas
# as libs de sistema presentes — se faltar algo, o build falha aqui e nao
# gera crash-loop em producao.
RUN python -c "import rasterio, rioxarray; print('geo stack OK')"

COPY main.py wind_engine.py /app/
COPY data /app/data

EXPOSE 8005

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]