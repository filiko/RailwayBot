FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV DJANGO_SETTINGS_MODULE=config.settings

RUN python manage.py migrate --noinput || true
RUN python manage.py collectstatic --noinput || true

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8000/health || exit 1

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
