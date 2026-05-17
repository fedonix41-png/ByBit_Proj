# Безопасность

**Расположение:** `app/core/`

---

## Аутентификация

**Файл:** `auth.py`

JWT-based аутентификация с refresh токенами.

### Конфигурация

| Переменная | Default | Описание |
|------------|---------|----------|
| `JWT_SECRET_KEY` | - | Секретный ключ (ОБЯЗАТЕЛЬНО сменить в прод!) |
| `JWT_ALGORITHM` | HS256 | Алгоритм подписи |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | 15 | Время жизни access токена |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Время жизни refresh токена |
| `MAX_FAILED_LOGIN_ATTEMPTS` | 5 | Попыток до блокировки |
| `ACCOUNT_LOCKOUT_MINUTES` | 15 | Время блокировки |

### Токены

| Токен | Время жизни | Назначение |
|-------|-------------|------------|
| Access | 15 минут | API запросы |
| Refresh | 7 дней | Обновление access токена |

### Password Requirements

- Минимум 8 символов
- Минимум 1 заглавная буква
- Минимум 1 цифра

---

## Rate Limiting

**Файл:** `rate_limit.py`

Sliding window rate limiter с Redis backend.

### Endpoint Limits

| Endpoint | Max | Window |
|----------|-----|--------|
| /auth/login | 5 | 60 сек |
| /auth/register | 3 | 3600 сек |
| /auth/refresh | 10 | 60 сек |
| default | 100 | 60 сек |

### Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1715012345
Retry-After: 30  # при 429
```

---

## Security Headers

**Файл:** `security_headers.py`

### Добавляемые headers

| Header | Значение | Назначение |
|--------|----------|------------|
| X-Frame-Options | DENY | Clickjacking защита |
| X-Content-Type-Options | nosniff | MIME sniffing защита |
| X-XSS-Protection | 1; mode=block | XSS фильтр |
| Content-Security-Policy | default-src 'self' | XSS защита |
| Strict-Transport-Security | max-age=31536000 | HTTPS только |
| Referrer-Policy | strict-origin-when-cross-origin | Referrer контроль |

---

## CORS

**Файл:** `security_headers.py`

Whitelist-based CORS (не "*").

### Конфигурация

```bash
ALLOWED_ORIGINS=http://localhost:3000,http://example.com
```

---

## Audit Logging

**Модель:** `SecurityAuditLog`

### Event Types

| Event | Описание |
|-------|----------|
| login_success | Успешный вход |
| login_failed | Неудачный вход |
| login_blocked | Блокировка |
| logout | Выход |
| token_refresh | Обновление токена |
| api_access | API запрос |
| account_locked | Блокировка аккаунта |

---

## Backup

**Скрипт:** `scripts/backup_db.sh`

### Возможности

- `./scripts/backup_db.sh` — создать backup (Docker)
- `./scripts/backup_db.sh --local` — backup из локального PostgreSQL
- `./scripts/backup_db.sh --restore <file>` — восстановить
- `./scripts/backup_db.sh --list` — список backups
- `./scripts/backup_db.sh --rotate` — очистка старых

### Cron (ежедневно в 2:00)

```bash
# Редактировать crontab
crontab -e

# Добавить строку:
0 2 * * * cd /path/to/project && ./scripts/cron_backup.sh >> logs/backup.log 2>&1
```

### Retention

По умолчанию: 30 дней.

### Docker Volume

Backup автоматически монтируются в `./backups:/app/backups`

---

## WebSocket Authentication

**Файл:** `deps.py`

WebSocket соединения не поддерживают стандартный HTTP Bearer authentication. Для аутентификации WebSocket используется передача токена через query-параметр.

### Использование

```javascript
// Подключение с токеном
const ws = new WebSocket(`ws://localhost:8000/ws?token=${accessToken}`);
```

### Функции

| Функция | Назначение |
|---------|------------|
| `get_optional_user_ws` | Опциональная аутентификация для WebSocket |
| `_extract_token_from_websocket` | Извлечение токена из WebSocket |

### Источники токена

1. Query-параметр `token` (рекомендуется)
2. `Sec-WebSocket-Protocol` header с префиксом `Bearer.`

---

## Валидация конфигурации

При запуске `validate_config()` проверяет:

| Проверка | Условие | Предупреждение |
|----------|---------|----------------|
| JWT Secret | `== "change-me-in-production"` | ❌ CRITICAL в production |
| CORS Origins | `== "*"` | ❌ CRITICAL в production |
| JWT Secret | default значение | ⚠️ WARNING в development |
| CORS Origins | `== "*"` | ⚠️ WARNING в development |
