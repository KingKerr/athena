FROM python:3.11-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN python -m venv /app/.venv
COPY requirements.txt ./
RUN /app/.venv/bin/python -m pip install --upgrade pip setuptools wheel
RUN /app/.venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY . .

CMD ["uvicorn", "--app-dir", "app/api/src", "main:app", "--host", "0.0.0.0", "--port", "8000"]