# E-COMMERCE-BOT — Getting Started Guide

The project consists of two modules:

- **bot** — the bot, command handling, and user interaction.
- **django** — Django backend (API, database, admin).

---

## Prerequisites

- Python 3.8+
- Virtual environment (venv/virtualenv)
- A `requirements.txt` file in each module
- For Django — a configured database (PostgreSQL/MySQL/SQLite — depending on your setup)
- `.env` files (see `.env.example`, if available)

---

## 1. Install and run bot

```bash
git clone https://github.com/E-COMMERCE-BOT/bot.git
cd bot

# Virtual environment
python3 -m venv venv
source venv/bin/activate      # Linux/macOS
# venv\\Scripts\\activate     # Windows

# Dependencies
pip install -r requirements.txt

# Environment
cp .env.example .env          # if .env.example exists
# fill .env (BOT_TOKEN, DJANGO_API_URL, etc.)

# Run the bot
python run.py
```

---

## 2. Install and run django

```bash
git clone https://github.com/E-COMMERCE-BOT/django.git
cd django

# Virtual environment
python3 -m venv venv
source venv/bin/activate      # Linux/macOS
# venv\\Scripts\\activate     # Windows

# Dependencies
pip install -r requirements.txt
# or manually: pip install django djangorestframework and others

# Migrations
python manage.py migrate

# (optional) superuser
# python manage.py createsuperuser

# Dev server
python manage.py runserver 0.0.0.0:8000
```

---

## Integration

1. Start **Django** (the API should be available, for example at `http://localhost:8000/`).
2. In the bot's `.env`, set the correct `DJANGO_API_URL`.
3. Start the **bot** with:

```bash
python run.py
```

---

## Environment Variables

### For bot

```
DJANGO_API_URL=http://localhost:8000
BOT_TOKEN=your_token
SECRET_KEY=secret
DEBUG=True
```

### For django

```
SECRET_KEY=...
DEBUG=True
DATABASE_URL=...
ALLOWED_HOSTS=...
```

> Note: The `DATABASE_URL` format depends on the chosen database. For PostgreSQL, for example:
> `DATABASE_URL=postgres://user:password@localhost:5432/dbname`

---

## Useful commands

### For Django

```bash
python manage.py makemigrations   # create migrations based on model changes
python manage.py migrate          # apply migrations to the database
python manage.py createsuperuser  # create a superuser for the admin
python manage.py runserver        # start the dev server (defaults to :8000)
```

### For bot

```bash
python run.py                     # start the bot
```

---
