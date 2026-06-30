FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements requirements
RUN pip install -r requirements/production.txt

COPY . .

RUN chmod +x /app/docker/start.sh

ENV DJANGO_SETTINGS_MODULE=config.settings.production

EXPOSE 8000

CMD ["/app/docker/start.sh"]
