# ZARA KIDS Backend

Django + DRF backend for the ZARA KIDS POS/WMS app.

## Local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

API: `http://127.0.0.1:8000/api/`
Admin: `http://127.0.0.1:8000/admin/`

## Railway

Use this directory as the Railway Root Directory.

Required variables:

```text
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<long random secret>
DJANGO_ALLOWED_HOSTS=.railway.app,.up.railway.app
CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app
CSRF_TRUSTED_ORIGINS=https://your-frontend.vercel.app,https://*.vercel.app
DATABASE_URL=${{Postgres.DATABASE_URL}}
```
