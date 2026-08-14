FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /code

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
    && pip install -r /tmp/requirements.txt

COPY . .

EXPOSE 8000

CMD python manage.py migrate --noinput \
    && python manage.py collectstatic --noinput \
    && gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --timeout 120 --graceful-timeout 120
