# E-COMMERCE-BOT — Getting Started Guide

The project consists of two modules:

- [bot](https://github.com/E-COMMERCE-BOT/bot) — the bot, handling commands and user interactions.
- [django](https://github.com/E-COMMERCE-BOT/django) — the Django backend (API, DB, admin).

---

## Prerequisites

- Python 3.8+
- Virtual environment (venv/virtualenv)
- A `requirements.txt` in each module
- For Django — a configured database (PostgreSQL/MySQL/SQLite depending on configuration)
- `.env` files (see `.env.example` if present)

---

## 1. Installing and Running bot

```bash
git clone https://github.com/E-COMMERCE-BOT/bot.git
cd bot

# Virtual environment
python3 -m venv venv
source venv/bin/activate      # Linux/macOS
# venv\Scripts\activate       # Windows

# Dependencies
pip install -r requirements.txt

# Environment
cp .env.example .env          # if .env.example exists
# fill out .env (BOT_TOKEN, DJANGO_API_URL, etc.)

# Run the bot
python run.py
```

---

## 2. Installing and Running django

```bash
git clone https://github.com/E-COMMERCE-BOT/django.git
cd django

# Virtual environment
python3 -m venv venv
source venv/bin/activate      # Linux/macOS
# venv\Scripts\activate       # Windows

# Dependencies
pip install -r requirements.txt
# or manually: pip install django djangorestframework, etc.

# Migrations
python manage.py migrate

# (optional) superuser
# python manage.py createsuperuser

# Dev server
python manage.py runserver 0.0.0.0:8000
```

---

## Integration

1. Start Django (the API should be available, e.g., at `http://localhost:8000/`).
2. In the bot’s `.env` set the correct `APP_URL`.
3. Start the bot with:

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

Note: The `DATABASE_URL` format depends on the chosen DB. For PostgreSQL:
`DATABASE_URL=postgres://user:password@localhost:5432/dbname`

---

## Useful Commands

### For Django

```bash
python manage.py makemigrations   # create migrations from model changes
python manage.py migrate          # apply migrations to the database
python manage.py createsuperuser  # create an admin user for the admin panel
python manage.py runserver        # start the dev server (defaults to :8000)
```

### For bot

```bash
python run.py                     # start the bot
```

---

## Production Recommendations

- Use a WSGI/ASGI server (Gunicorn/Uvicorn/Daphne) behind a reverse proxy (Nginx).
- Keep secrets outside the repository (environment variables, secret managers).
- Configure `ALLOWED_HOSTS`, CORS, logging, and monitoring.
- Enable HTTPS/SSL and proper proxy headers on the server.


- **README.md** — project launch instructions
- **Project architecture description** — overall interaction diagram between modules (bot and django)
- **API usage examples** — sample requests to the backend (Django REST API)
- **Database schema** — description of tables and relationships in the project

---

## 🧭 Architecture

The project is split into two independent modules:

- **bot** — user interaction (handling commands, integrations).
- **django** — REST API + business logic + database.

Interaction diagram (simplified example):

```mermaid
sequenceDiagram
    participant User
    participant Bot
    participant API as Django API
    participant DB as Database

    User->>Bot: Command /add_to_cart
    Bot->>API: POST /api/cart/items { product_id, qty }
    API->>DB: INSERT cart_item
    DB-->>API: OK
    API-->>Bot: 201 Created
    Bot-->>User: Item added to cart
```

### Components and Responsibilities

| Component | Responsibility |
|---|---|
| **bot** | Commands, dialog flows, input validation, API calls |
| **django (REST API)** | Models, serializers, views, permissions, business rules |
| **DB** | Stores users, products, orders, and related entities |

> Note: check `urls.py`/`views.py` and `models.py` in the `django` repository for exact endpoints and models.

---

## 🔌 API: Usage Examples

Below are typical REST endpoints for an e-commerce backend. Replace paths with the actual ones (see `django/urls.py`).

### Product Catalog

```bash
# Get product list
curl http://localhost:8000/api/products/

# Get product details
curl http://localhost:8000/api/products/42/
```

Sample list response:
```json
[
  {
    "id": 42,
    "name": "T‑Shirt",
    "price": "19.99",
    "category": {"id": 3, "name": "Clothes"},
    "image": "http://localhost:8000/media/products/tshirt.jpg",
    "in_stock": 14
  }
]
```

### Cart

```bash
# Add to cart
curl -X POST http://localhost:8000/api/cart/items/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"product_id":42,"quantity":2}'

# Get current cart
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/cart/
```

---

## ⚙️ Environment Variables (Detailed)

### For bot
```
TOKEN=...
ADMIN_CHAT_ID=...
base_url=...
BOT_API_KEY=...
APP_URL=...
```

### For django
```
SECRET_KEY=...

DB_NAME=...
DB_USER=...
DB_PASS=...
DB_HOST=...
DB_PORT=...

BOT_API_KEY=...

TELEGRAM_BOT_TOKEN=...

SITE_URL=...

ALLOWED_HOSTS=...
```

---

## 🔧 Useful Commands

### For Django
```bash
python manage.py makemigrations   # create migrations from model changes
python manage.py migrate          # apply migrations to the database
python manage.py createsuperuser  # create an admin user for the admin panel
python manage.py runserver        # start the dev server (defaults to :8000)
```

### For bot
```bash
python run.py                     # start the bot
```

---

## 🚀 Production Recommendations

- WSGI/ASGI (Gunicorn/Uvicorn/Daphne) behind a reverse proxy (Nginx).
- Store environment variables/secrets outside the repository.
- Configure `ALLOWED_HOSTS`, CORS/CSRF, logging, monitoring.
- Enable HTTPS/SSL and proper proxy headers.


## 🗄️ Database Schema

Below is the current schema of the project’s models.

```mermaid
erDiagram
    USER ||--o{ ORDER : places
    ORDER ||--o{ ORDERITEM : contains
    PRODUCT ||--o{ ORDERITEM : included
    CATEGORY ||--o{ PRODUCT : contains
    ORDER }o--|| STATUS : has
    ORDER }o--|| DELIVERYTYPE : uses

    USER {
        bigint tg_id PK "unique ID from Telegram"
        string name
        string lastname
        string surname
        string phone
        string address
        datetime created_at
    }

    CATEGORY {
        int id PK
        string name
        int? parent_id FK
    }

    PRODUCT {
        int id PK
        string name
        text description
        string photo (ImageField)
        decimal price
        int stock
        datetime created_at
        int category_id FK
    }

    STATUS {
        int id PK
        string name
        string description
    }

    DELIVERYTYPE {
        int id PK
        string name
        string description
        decimal price
    }

    ORDER {
        int id PK
        string number "ORD-000001"
        int user_id FK
        int? status_id FK
        int? delivery_type_id FK
        datetime created_at
    }

    ORDERITEM {
        int id PK
        int order_id FK
        int product_id FK
        int quantity
    }
```

---

### Tables and Fields

#### User
- `tg_id` — unique Telegram user ID (indexed).
- `name`, `lastname`, `surname` — personal data.
- `phone`, `address` — contacts.
- `created_at` — registration date.

#### Category
- `name` — category name.
- `parent` — relation to parent category (supports nested structure).

#### Product
- `name`, `description`, `photo`.
- `price` — price (Decimal).
- `stock` — stock quantity.
- `category` — relation to category.
- `created_at` — creation date.
- Method `is_available()` returns `True` if the product is in stock.

#### Status
- `name`, `description` — order status (e.g., created, paid, shipped).

#### DeliveryType
- `name`, `description`, `price` — delivery option and its cost.

#### Order
- `number` — unique order number like `ORD-000001`.
- `user` — relation to user.
- `status` — current order status.
- `delivery_type` — chosen delivery type.
- `created_at` — creation date.
- Method `get_total()` — computes the order’s total (items + delivery).

#### OrderItem
- `order` — link to the order.
- `product` — link to the product.
- `quantity` — quantity.
- Method `get_total()` — line cost (price × quantity).
