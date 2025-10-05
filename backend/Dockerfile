FROM python:3.11.9-slim

ENV PYTHONDONTWRITEBYTECODE=1         PYTHONUNBUFFERED=1         PIP_NO_CACHE_DIR=1         PIP_DISABLE_PIP_VERSION_CHECK=1         PIP_DEFAULT_TIMEOUT=100

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends         build-essential curl &&         rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

ENV ML_MODE=http         ML_SERVICE_URL=http://ml:8001         DATABASE_URL=postgresql+psycopg2://postgres:postgres@db:5432/exoseeker

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
