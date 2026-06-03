# Telegram-бот и Обработка сообщений

**Расположение:** `app/infrastructure/interface/`, `app/infrastructure/handlers/`, `app/infrastructure/bridge/`

Этот модуль отвечает за взаимодействие с оператором или пользователем через Telegram, а также за предварительную фильтрацию (спам, rate limit) и передачу данных в ядро AI (оркестратор).

## 1. Интерфейс и Команды (`bot.py` и `telegram_handlers.py`)

Бот работает через `python-telegram-bot` (запускается через polling в отдельном процессе).

**Основные команды:**
- `/start`, `/menu` — Главное меню (InlineKeyboard)
- `/ask` — Режим AI-диалога
- `/status` — Статус ордеров

**InlineKeyboard Меню:**
Включает разделы "Задать вопрос AI", "Статус торговли", "Анализ P2P", "Проверка мошенничества", "Настройки". 
Настройки позволяют выбрать AI-провайдера (OpenRouter, OpenAI и др.), язык и посмотреть баланс Bybit.

**Обработка медиа:**
- **Текст:** Передается напрямую.
- **Голос (Whisper):** Скачивается, транскрибируется (через OpenAI Whisper) и передается как текст с маркером `[VOICE]`.
- **Фото (Vision):** Анализируется через `gpt-4o` (OpenAI/OpenRouter) и передается с маркером `[PAYMENT_PROOF]` или `[IMAGE_ANALYSIS]`.

## 2. Безопасность и Спам-фильтры (`message_processor.py` и `spam_detector.py`)

Все сообщения до передачи в AI-ядро проходят через `MessageProcessor`.

**Функции MessageProcessor:**
- **Rate limiting:** Redis-based sliding window (например, 15 сообщений в минуту).
- **Blacklist:** Проверка на запрещенные слова и заблокированных пользователей.
- **Spam Detection:** ML-анализ через OpenRouter для выявления фишинга, скама или оффтопа.
- **Business Rules:** Проверка на нарушения и выдача банов (запись в `ViolationHistory`).
- **A/B Testing & Webhooks:** Уведомления о подозрительных активностях администратору.

## 3. P2P Bridge (`p2p_bridge.py`)

Адаптер между Telegram-интерфейсом и LangGraph-оркестратором.
- **Сохранение контекста:** Хранит in-memory историю сообщений (`MAX_CONVERSATION_HISTORY = 20`).
- **Маршрутизация:** Вызывает `orchestrator.process_telegram_message(...)`.
- **Ретраи:** Автоматические повторы (`@retry` из `tenacity`) при временных сбоях API оркестратора или LLM.
- **Семантические маркеры:** Оборачивает входы в стандартные теги (см. `app/domain/prompts/semantic_markers.py`).
