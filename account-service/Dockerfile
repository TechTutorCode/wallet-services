FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 appuser

COPY requirements.txt .
RUN pip install --no-cache-dir --no-warn-script-location -r requirements.txt

COPY --chown=appuser:appuser . .
USER appuser

EXPOSE 8050

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8050"]
