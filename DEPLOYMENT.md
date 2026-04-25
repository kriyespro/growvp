Deployment Guide
================

Quick Start with Docker
-----------------------
1. Copy env template:
   - cp .env.example .env
2. Build and run:
   - docker compose up --build
3. Open app:
   - http://127.0.0.1:8000

Production Checklist
--------------------
- Set strong DJANGO_SECRET_KEY
- Set DJANGO_DEBUG=False
- Set DJANGO_ALLOWED_HOSTS to your domain(s)
- Use managed PostgreSQL and set DATABASE_URL
- Enable HTTPS termination at load balancer/reverse proxy
- Run migrations before traffic:
  - python manage.py migrate
- Collect static:
  - python manage.py collectstatic --noinput

Manual Non-Docker Deploy
------------------------
1. Install dependencies:
   - pip install -r requirements.txt
2. Export environment variables (.env)
3. Run migrations:
   - python manage.py migrate
4. Collect static:
   - python manage.py collectstatic --noinput
5. Start app server:
   - gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3

Notes
-----
- App is now database-url driven. If DATABASE_URL is not set, SQLite is used.
- For cloud deployment, point DATABASE_URL to PostgreSQL.
