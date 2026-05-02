FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir .

CMD ["sh", "-c", "uvicorn code_council.server:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
