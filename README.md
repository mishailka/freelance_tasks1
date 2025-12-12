# АКМ. Менеджер проектов — Telegram модуль (Бот1 + Бот3 + Миниапп)

Проект реализует:
- **Бот1 (userbot на Pyrogram)** — создание/настройка групп, кик участников, fallback-рассылка если Бот3 заблокирован.
- **Бот3 (обычный Telegram Bot)** — уведомления подрядчикам и кнопки запуска мини‑приложения.
- **Миниприложение (Telegram WebApp)** — личный кабинет подрядчика: заказ, этапы, имущество, профиль.

ТЗ: бот1 создаёт и настраивает групповой чат (название/иконка/описание, добавление Бот2/Бот3 с анонимным статусом, Куратор с label, подрядчики, очистка сообщений, открытие истории) и возвращает GroupID+ссылку. Бот3 шлёт уведомления, а при блокировке — вызывает Бот1 для первого контакта и удаляет сообщение после появления подрядчика в группе. Миниапп реализует функции личного кабинета и API для CRM/фронтенда.

## Быстрый старт (Docker Compose)

### 1) Подготовьте .env файлы
Скопируйте примеры:
```bash
cp services/bot1_userbot/.env.example services/bot1_userbot/.env
cp services/bot3_notify_bot/.env.example services/bot3_notify_bot/.env
cp services/miniapp/.env.example services/miniapp/.env
```

Заполните значения:
- **Bot3**: `BOT3_TOKEN`, `BOT3_USERNAME` (без @)
- **Bot1 (userbot)**: `TG_API_ID`, `TG_API_HASH`, `PYROGRAM_SESSION_STRING`
- Общие: `CRM_API_KEY` (одинаковый во всех сервисах), `MINIAPP_PUBLIC_URL` (публичный URL миниаппа, например через ngrok/Cloudflare Tunnel)

> ⚠️ Бот1 — это **аккаунт пользователя** Telegram. Для него нужен session string.

### 2) Сгенерируйте Pyrogram session string
Локально (вне Docker), в виртуальном окружении:
```bash
python -m venv .venv && . .venv/bin/activate
pip install pyrogram tgcrypto
python services/scripts/generate_pyrogram_session.py
```
Скрипт попросит `api_id/api_hash`, номер телефона и код, и выдаст строку `PYROGRAM_SESSION_STRING`.

### 3) Запуск
```bash
docker compose up --build
```

Сервисы:
- Miniapp: http://localhost:8000
- Bot1 API: http://localhost:8001
- Bot3 API: http://localhost:8002

## CRM API (пример вызовов)

Все CRM-методы защищены заголовком:
`X-CRM-API-Key: <CRM_API_KEY>`

### 1) Создать чат (Бот1)
```bash
curl -X POST http://localhost:8001/api/crm/create_group \
  -H "Content-Type: application/json" \
  -H "X-CRM-API-Key: $CRM_API_KEY" \
  -d '{
    "order_id":"ORD-1001",
    "title":"Заказ 1001",
    "description":"Описание заказа",
    "icon_base64": null,
    "curator_id": 123456789,
    "curator_label":"Куратор",
    "contractor_ids":[111111111,222222222],
    "bot2_username":"planfix_logger_bot",
    "bot3_username":"your_notify_bot"
  }'
```

### 2) Запинить «Детали заказа» (Бот3)
```bash
curl -X POST http://localhost:8002/api/crm/pin_order_details \
  -H "Content-Type: application/json" \
  -H "X-CRM-API-Key: $CRM_API_KEY" \
  -d '{
    "chat_id": -1001234567890,
    "order_id":"ORD-1001",
    "title":"Заказ 1001"
  }'
```

### 3) Уведомить о новом заказе (Бот3 + fallback через Бот1)
```bash
curl -X POST http://localhost:8002/api/crm/notify_new_order \
  -H "Content-Type: application/json" \
  -H "X-CRM-API-Key: $CRM_API_KEY" \
  -d '{
    "contractor_id": 111111111,
    "order_title":"Заказ 1001",
    "group_link":"https://t.me/+XXXXXXX",
    "group_id": -1001234567890
  }'
```

### 4) Уведомить об оплате (Бот3)
```bash
curl -X POST http://localhost:8002/api/crm/notify_payment \
  -H "Content-Type: application/json" \
  -H "X-CRM-API-Key: $CRM_API_KEY" \
  -d '{
    "contractor_id": 111111111,
    "amount_rub": 15000,
    "order_id":"ORD-1001"
  }'
```

### 5) Отстранить подрядчика (кик из чата — Бот1)
```bash
curl -X POST http://localhost:8001/api/crm/remove_contractor \
  -H "Content-Type: application/json" \
  -H "X-CRM-API-Key: $CRM_API_KEY" \
  -d '{
    "chat_id": -1001234567890,
    "contractor_id": 111111111
  }'
```

## CRM ↔ Miniapp API

### Upsert заказа (CRM → miniapp)
`POST http://localhost:8000/api/crm/orders`

### Delete заказа (CRM → miniapp)
`DELETE http://localhost:8000/api/crm/orders/{order_id}`

### Обновить профиль подрядчика (CRM → miniapp)
`PUT http://localhost:8000/api/crm/contractors/{username}`

Схемы см. в Swagger:
- http://localhost:8000/docs
- http://localhost:8001/docs
- http://localhost:8002/docs

## Миниапп (WebApp)
Фронтенд — статический (HTML/JS) и работает в Telegram WebApp.
Для авторизации миниаппа используется `initData` из `Telegram.WebApp.initData`.

Для локальной отладки без подписи:
- В `services/miniapp/.env` поставьте `TELEGRAM_AUTH_DISABLED=true`.

## Лицензия
MIT
