# E-Commerce Telegram Bot

Aiogram 3 Telegram interface for the E-Commerce Django API.

> This project is part of a two-service application.
>
> **Related repository:** https://github.com/mayldute/ecommerce-api

## Features

- User onboarding
- Nested catalog browsing
- Product cards with images
- Cart management
- Checkout with FSM
- Delivery selection
- Admin access through a Telegram group
- Admin product creation
- Admin order status management
- One reusable `aiohttp.ClientSession`
- Typed settings and API services
- Tests and CI

## Setup

```bash
uv sync --extra dev
cp .env.example .env
```

Use the same `BOT_API_KEY` as in the Django backend.

Start Django first, then run:

```bash
uv run python -m app.main
```

## Tests and Quality

```bash
uv run pytest
uv run ruff format .
uv run ruff check . --fix
```

## Architecture

```text
Telegram handlers
      ↓
Typed API services
      ↓
Reusable HTTP client
      ↓
Django REST API
```
