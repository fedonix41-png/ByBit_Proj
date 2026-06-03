# Внешние интеграции (API)

**Расположение:** `app/integrations/`

Этот раздел описывает интеграцию с внешними сервисами: Bybit (получение ордеров, чат) и платформой Zavod (создание заявок, получение чеков).

## 1. Bybit Client (`bybit_client.py`)

Официальный SDK: `bybit-p2p` (устанавливается через `uv pip install bybit-p2p`).
В режиме разработки работает с `BYBIT_TESTNET=True`. Если SDK недоступен или API падает, система использует **Mock-режим** и генерирует тестовые ордера/балансы.

**Основные методы:**
- `get_orders(page, size)`, `get_pending_orders()`
- `get_ad_details(ad_id)`
- `get_chat_messages(order_id)`
- `send_chat_message(order_id, text)`, `upload_chat_file(order_id, path)`
- `release_assets(order_id)` (для продавца)
- `mark_as_paid(order_id, ...)` (для покупателя)

**Модели (Pydantic):**
- `Order` (order_id, side, currency, crypto, price, amount, status)
- `ChatMessage` (sender, text, timestamp, read)
- `Balance` (currency, available, locked, total)

## 2. Zavod Client (`zavod_client.py`)

Поскольку платформа Zavod является Vue.js приложением без открытого API, клиент проектируется под парсинг HTTP-запросов сайта (XHR) или использование headless-браузера (Playwright).

**Основные методы (в разработке):**
- `authenticate()` — Авторизация и получение сессионных кук / токенов.
- `create_order(order_data)` — Создание заявки на оплату (используя реквизиты, извлеченные AI из чата Bybit). Возвращает `zavod_order_id`.
- `check_order_status(zavod_order_id)` — Проверка статуса (выполнено ли, есть ли чек).
- `download_receipt(receipt_url)` — Скачивание чека оплаты для последующего парсинга через `PaymentParser`.
