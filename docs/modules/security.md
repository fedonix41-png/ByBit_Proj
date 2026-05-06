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

### Использование

```bash
# Создать backup
./scripts/backup_db.sh

# Восстановить
./scripts/backup_db.sh --restore backups/p2p_backup_YYYYMMDD_HHMMSS.sql.gz

# Список backups
./scripts/backup_db.sh --list
```

### Cron (ежедневно в 2:00)

```bash
0 2 * * * /path/to/scripts/cron_backup.sh
```

### Retention

По умолчанию: 30 дней.
