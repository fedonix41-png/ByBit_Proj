# Telegram-бот и Обработка сообщений

**Расположение:** `app/infrastructure/interface/`, `app/infrastructure/handlers/`, `app/infrastructure/bridge/`

Этот модуль отвечает за взаимодействие с оператором или пользователем через Telegram, а также за предварительную фильтрацию (спам, rate limit) и передачу данных в ядро AI (оркестратор).

## 1. Навигация (`bot.py`)

Бот работает через `python-telegram-bot`. Пользователь **не вводит текстовые команды** — навигация через кнопки.

### 1.1 Уровни навигации

**Уровень 1 — Persistent Reply Keyboard (постоянная нижняя панель)**

Устанавливается при `/start`, не скрывается. Работает как таб-бар мобильного приложения:

| Кнопка | `BTN_*` константа | Обычный юзер | Admin |
|--------|-------------------|:---:|:---:|
| `🏠 Главная` | `BTN_HOME` | ✅ | ✅ |
| `💬 Спросить AI` | `BTN_AI` | ✅ | ✅ |
| `📋 Статус` | `BTN_STATUS` | ✅ | ✅ |
| `❓ Помощь` | `BTN_HELP` | ✅ | — |
| `🛠 Панель` | `BTN_PANEL` | — | ✅ |

Обработчик кнопок: `_handle_text_with_ai_mode()` → приоритет 1 — проверка `BTN_*` → вызов `_nav_*()`.

**Уровень 2 — Bot Menu Button (☰ у поля ввода)**

Настраивается в `_post_init()` через `set_my_commands()` с разными scope:
- `BotCommandScopeDefault()` → обычные пользователи видят только `/start`
- `BotCommandScopeChat(chat_id=admin_id)` → каждый admin видит `/start /status /stats /demo /help`

**Уровень 3 — Inline Keyboard (контентная область)**

Навигация внутри чата через InlineKeyboardButton. Заголовки экранов содержат breadcrumbs:
`🛠 › 👥 Пользователи`, `🛠 › ⚙️ Настройки` и т.д.

### 1.2 Единственная точка входа

`/start` — единственная команда, которую нужно знать пользователю:
1. Регистрирует в `TelegramUser`
2. Устанавливает persistent keyboard (`is_persistent=True`)
3. Показывает приветственную карточку с inline-меню

Остальные команды (`/menu`, `/admin` и др.) — legacy, работают но не рекламируются.

### 1.3 Обработка медиа
- **Текст:** FSM-диспетчер → `MessageProcessor` → `P2P Bridge`
- **Голос (Whisper):** транскрибируется → маркер `[VOICE]`
- **Фото (Vision):** GPT-4 Vision → маркер `[PAYMENT_PROOF]` или `[IMAGE_ANALYSIS]`



## 2. Admin-панель (`bot.py` + `admin_service.py`)

**Доступ:** только Telegram IDs из `ADMIN_TELEGRAM_IDS` в `.env`.

### 2.1 Разделы меню `/admin`

| Раздел | Callback | Описание |
|--------|----------|----------|
| 📊 Статистика | `admin_stats` | Реальные данные из БД: ордера, пользователи, AI, нарушения, баланс Bybit |
| 🤖 Статус бота | `admin_bot_status` | Uptime, версия, здоровье компонентов (DB, Redis) через `/health` |
| 👥 Пользователи | `admin_users` | Список, блокировка, разблокировка, назначение группы |
| 📢 Рассылка | `admin_broadcast` | Рассылка всем или по группе с подтверждением |
| 🧠 Анализ P2P | `menu_p2p_analysis` | Анализ P2P предложений |
| 🛡️ Проверка фрода | `menu_fraud_check` | Анализ скриншотов и ордеров на мошенничество |
| ⚙️ Настройки | `menu_settings` | AI-провайдер, язык, баланс Bybit |

### 2.2 FSM-диалоги (состояния в `user_data["pending_action"]`)

| Константа | Описание |
|-----------|----------|
| `FSM_BLOCK_AWAIT_ID` | Ожидание ввода Telegram ID для блокировки |
| `FSM_UNBLOCK_AWAIT_ID` | Ожидание ввода Telegram ID для разблокировки |
| `FSM_BROADCAST_AWAIT_TEXT` | Ожидание текста рассылки |
| `FSM_BROADCAST_CONFIRM` | Ожидание подтверждения рассылки |
| `FSM_SET_GROUP_AWAIT_ID` | Ожидание ID пользователя для смены группы |
| `FSM_SET_GROUP_AWAIT_GRP` | Ожидание названия группы |

Диспетчер FSM: `_handle_admin_text_input()` вызывается из `_handle_text_with_ai_mode()` при наличии `pending_action` и admin-прав.

### 2.3 Рассылка

- **Всем:** отправка всем `TelegramUser` с `is_active=True`, `is_blocked=False`
- **По группе:** фильтрация по `TelegramUser.group`
- Ограничение: 0.05 сек между сообщениями (Telegram rate limit)
- Реализация: `_execute_broadcast(text, group)` → возвращает `(sent, failed)`

## 3. Реестр пользователей (`TelegramUser`)

Модель в `app/database/models.py`, таблица `telegram_users`.
- Регистрация/обновление: `upsert_telegram_user()` при каждом `/start`
- Поля: `telegram_id`, `username`, `first_name`, `group`, `is_blocked`, `last_active_at`
- Группы (`group`): `all` (по умолчанию), `vip`, `blocked`, произвольные теги
- Используется для: рассылок, статистики, управления доступом

Бизнес-логика: `app/infrastructure/interface/admin_service.py`

## 4. Безопасность и Спам-фильтры (`message_processor.py`, `spam_detector.py`)

Все сообщения до передачи в AI-ядро проходят через `MessageProcessor`.

**Функции MessageProcessor:**
- **Rate limiting:** Redis-based sliding window (15 сообщений/мин).
- **Blacklist:** Проверка `BlacklistEntry` (users, words, patterns).
- **Spam Detection:** ML + regex анализ.
- **Business Rules:** Учёт `ViolationHistory`, бан при превышении порога.
- **A/B Testing & Webhooks:** Уведомления о подозрительной активности.

## 5. P2P Bridge (`p2p_bridge.py`)

Адаптер между Telegram-интерфейсом и LangGraph-оркестратором.
- **Сохранение контекста:** In-memory история сообщений (`MAX_CONVERSATION_HISTORY = 20`).
- **Маршрутизация:** Вызывает `orchestrator.process_telegram_message(...)`.
- **Ретраи:** `@retry` из `tenacity` при сбоях API.
- **Семантические маркеры:** см. `app/domain/prompts/semantic_markers.py`.

## 6. Admin Service (`admin_service.py`)

**Расположение:** `app/infrastructure/interface/admin_service.py`

Функции:

| Функция | Описание |
|---------|----------|
| `upsert_telegram_user(...)` | Регистрация/обновление пользователя |
| `get_all_telegram_user_ids(group)` | ID пользователей для рассылки |
| `get_user_groups()` | Список доступных групп |
| `set_user_group(id, group)` | Назначение группы |
| `block_user(id, reason, ...)` | Блокировка: запись в `BlacklistEntry` + флаг в `TelegramUser` |
| `unblock_user(id)` | Разблокировка |
| `is_user_blocked(id)` | Проверка статуса |
| `get_admin_stats()` | Сводная статистика из БД |
| `get_top_violators(limit)` | Топ нарушителей за 30 дней |
| `get_recent_violations(limit)` | Последние нарушения |
| `get_bot_health()` | HTTP-запрос к `/health` FastAPI |
