FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock* /app/

RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi --no-root

COPY . /app/

RUN poetry install --no-interaction --no-ansi --no-root

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "core.wsgi:application"]
