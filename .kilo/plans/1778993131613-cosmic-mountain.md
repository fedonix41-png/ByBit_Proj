# План: Полноценный веб-интерфейс для тестирования bybit_p2p

**Цель:** Расширить веб-интерфейс для полного покрытия всех функций библиотеки bybit_p2p.

**Стек:** Jinja2 + Vanilla JS (встроенный в HTML), Single Page Application с табами.

**Запуск:** `uv run python main.py` или `./start.sh server` (порт 8000)

---

## Этап 1: Расширение REST API (backend)

### 1.1 Новые эндпоинты для объявлений
| Эндпоинт | Метод | Функция bybit_p2p |
|----------|-------|-------------------|
| `POST /api/ads` | POST | post_new_ad() |
| `PUT /api/ads/{ad_id}` | PUT | update_ad() |
| `DELETE /api/ads/{ad_id}` | DELETE | remove_ad() |
| `GET /api/ads/online` | GET | get_online_ads() |
| `GET /api/ads/{ad_id}` | GET | get_ad_details() |

### 1.2 Новые эндпоинты для ордеров
| Эндпоинт | Метод | Функция bybit_p2p |
|----------|-------|-------------------|
| `GET /api/orders` | GET | get_orders() |
| `GET /api/orders/pending` | GET | get_pending_orders() |

### 1.3 Новые эндпоинты для действий по ордерам
| Эндпоинт | Метод | Функция bybit_p2p |
|----------|-------|-------------------|
| `POST /api/order/{order_id}/mark_paid` | POST | mark_as_paid() |
| `POST /api/order/{order_id}/release` | POST | release_assets() |
| `POST /api/order/{order_id}/upload` | POST | upload_chat_file() |
| `POST /api/chat/{order_id}/send` | POST | send_chat_message() |

### 1.4 Новые эндпоинты для информации о пользователе
| Эндпоинт | Метод | Функция bybit_p2p |
|----------|-------|-------------------|
| `GET /api/account` | GET | get_account_information() |
| `GET /api/counterparty/{order_id}` | GET | get_counterparty_info() |

### 1.5 Обновление bybit_client.py
Добавить методы:
- `update_ad(ad_id, **params)` — обновление объявления
- `get_ad_details(ad_id)` — детали объявления
- `get_account_information()` — информация об аккаунте
- `get_counterparty_info(order_id)` — информация о контрагенте
- `upload_chat_file(order_id, file)` — загрузка файла в чат

---

## Этап 2: UI — Табы и навигация

### 2.1 Структура страницы (табы)
```
┌─────────────────────────────────────────────────────────────────┐
│  [Объявления] [Ордера] [Чат] [Аккаунт] [Мониторинг]             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Контент активного таба                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Таб «Объявления» (Ads)
**Отображение:**
- Таблица моих объявлений: ID, side, crypto/currency, price, amount, status
- Действия: редактировать, удалить
- Кнопка «Создать объявление»

**Форма создания объявления (модальное окно):**
- Side: BUY/SELL (select)
- Crypto: USDT, BTC (select)
- Currency: RUB, USD (select)
- Price: float (input)
- Min amount: float (input)
- Max amount: float (input)
- Payment methods: multiselect из get_user_payment_types()

**Поиск публичных объявлений:**
- Фильтры: token, currency, side
- Таблица результатов

### 2.3 Таб «Ордера» (Orders)
**Отображение:**
- Таблица ордеров: ID, side, crypto/currency, amount, price, status, counterparty
- Фильтр по статусу: All / Pending / Completed / Cancelled
- Пагинация (page, size)

**Действия по ордеру:**
- Кнопка «Детали» → модальное окно с полной информацией
- Если BUY и pending: «Отметить оплаченным» → mark_as_paid()
- Если SELL и pending: «Отпустить активы» → release_assets()

### 2.4 Таб «Чат» (Chat)
**Отображение:**
- Select выбора ордера (из pending orders)
- История сообщений (существующий UI)
- Форма отправки сообщения

**Новые функции:**
- `POST /api/chat/{order_id}/send` — отправка сообщения
- Загрузка файла: `<input type="file">` + `POST /api/order/{order_id}/upload`

### 2.5 Таб «Аккаунт» (Account)
**Информация об аккаунте:**
- User ID, Nickname, Status, Level, Registered at
- Получение: `GET /api/account`

**Баланс:**
- Существующий UI (таблица с валютами)
- Обновление по кнопке

**Способы оплаты:**
- Существующий UI
- Обновление по кнопке

**Информация о контрагенте:**
- Input для order_id
- Кнопка «Получить информацию»
- Результат: nickname, rating, trades_count, cancellation_rate

### 2.6 Таб «Мониторинг» (Monitor)
**Существующий функционал:**
- Выбор ордера
- Запуск мониторинга
- Approval UI
- Лог активности

**Улучшения:**
- Счётчик активных runs
- Визуализация state (JSON tree)
- Цветовая индикация статуса

---

## Этап 3: Модели данных (models.py)

```python
class CreateAdRequest(BaseModel):
    side: Literal["BUY", "SELL"]
    currency: str
    crypto: str
    price: float
    min_amount: float
    max_amount: float
    payment_methods: List[str]

class UpdateAdRequest(BaseModel):
    price: Optional[float] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None

class SendMessageRequest(BaseModel):
    text: str

class AccountInfo(BaseModel):
    user_id: str
    nickname: str
    status: str
    level: int
    registered_at: Optional[datetime]

class CounterpartyInfo(BaseModel):
    nickname: str
    rating: float
    trades_count: int
    cancellation_rate: float

class OnlineAdsRequest(BaseModel):
    token: str = "USDT"
    currency: str = "RUB"
    side: Literal["BUY", "SELL"] = "SELL"
```

---

## Этап 4: JavaScript (внутри index.html)

### 4.1 Модульная структура (в рамках одного <script>)
```javascript
// Состояние приложения
let currentTab = 'ads';
let accessToken = null;

// Модули
const AdsAPI = {
    list: () => authFetch('/api/ads'),
    create: (data) => authFetch('/api/ads', {method: 'POST', body: JSON.stringify(data)}),
    update: (id, data) => authFetch(`/api/ads/${id}`, {method: 'PUT', body: JSON.stringify(data)}),
    delete: (id) => authFetch(`/api/ads/${id}`, {method: 'DELETE'}),
    online: (params) => authFetch(`/api/ads/online?${new URLSearchParams(params)}`),
};

const OrdersAPI = {
    list: (page, size) => authFetch(`/api/orders?page=${page}&size=${size}`),
    pending: (page, size) => authFetch(`/api/orders/pending?page=${page}&size=${size}`),
    details: (id) => authFetch(`/api/order/${id}`),
    markPaid: (id, paymentType, paymentId) => authFetch(`/api/order/${id}/mark_paid`, {method: 'POST', body: JSON.stringify({payment_type: paymentType, payment_id: paymentId})}),
    release: (id) => authFetch(`/api/order/${id}/release`, {method: 'POST'}),
};

const ChatAPI = {
    messages: (orderId) => authFetch(`/api/chat/${orderId}`),
    send: (orderId, text) => authFetch(`/api/chat/${orderId}/send`, {method: 'POST', body: JSON.stringify({text})}),
    upload: (orderId, formData) => authFetch(`/api/order/${orderId}/upload`, {method: 'POST', body: formData}),
};

const AccountAPI = {
    info: () => authFetch('/api/account'),
    counterparty: (orderId) => authFetch(`/api/counterparty/${orderId}`),
};
```

### 4.2 Переключение табов
```javascript
function showTab(tabName) {
    currentTab = tabName;
    // Скрыть все секции, показать нужную
    document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
    document.getElementById(`tab-${tabName}`).style.display = 'block';
    // Обновить активный таб
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    // Загрузить данные
    switch(tabName) {
        case 'ads': loadAds(); break;
        case 'orders': loadOrders(); break;
        case 'chat': loadPendingOrdersForChat(); break;
        case 'account': loadAccountInfo(); break;
        case 'monitor': loadActiveRuns(); break;
    }
}
```

---

## Этап 5: CSS (style.css)

### 5.1 Новые компоненты
```css
/* Табы */
.tabs { display: flex; gap: 0; border-bottom: 1px solid var(--border); }
.tab-btn { padding: 12px 24px; background: transparent; border: none; color: var(--text-secondary); cursor: pointer; }
.tab-btn.active { color: var(--accent); border-bottom: 2px solid var(--accent); }
.tab-content { display: none; }

/* Модальные окна */
.modal { position: fixed; inset: 0; background: rgba(0,0,0,0.8); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal.hidden { display: none; }
.modal-content { background: var(--bg-card); padding: 24px; border-radius: 12px; max-width: 500px; width: 100%; }

/* Формы */
.form-group { margin-bottom: 16px; }
.form-label { display: block; margin-bottom: 8px; color: var(--text-secondary); }
.form-input, .form-select { width: 100%; padding: 10px; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 6px; color: var(--text-primary); }

/* Toast уведомления */
.toast { position: fixed; bottom: 20px; right: 20px; padding: 12px 24px; border-radius: 8px; z-index: 2000; }
.toast.success { background: var(--success); color: white; }
.toast.error { background: var(--danger); color: white; }
```

---

## Файлы для изменения

| Файл | Изменения |
|------|-----------|
| `server.py` | +15 новых эндпоинтов |
| `bybit_client.py` | +5 новых методов |
| `models.py` | +6 новых моделей |
| `templates/index.html` | Реструктуризация (табы), новые формы, JS |
| `static/style.css` | Стили для табов, модалок, форм |

---

## Порядок реализации

### Фаза 1: Backend (server.py + bybit_client.py + models.py)
1. Добавить новые Pydantic модели
2. Добавить методы в bybit_client.py
3. Добавить эндпоинты в server.py
4. Протестировать через curl/Postman

### Фаза 2: Frontend Structure
1. Переработать index.html на табовую структуру
2. Добавить CSS для табов и модалок
3. Базовый layout для каждого таба

### Фаза 3: Frontend Functionality
1. Таб «Объявления» — CRUD
2. Таб «Ордера» — списки + действия
3. Таб «Чат» — отправка + файлы
4. Таб «Аккаунт» — информация
5. Таб «Мониторинг» — существующий UI

### Фаза 4: Documentation
1. Обновить `docs/overview.md`
2. Обновить `docs/modules/bybit_client.md`
3. Обновить `docs/status.md`

---

## Как проверить

```bash
# Запуск сервера
uv run python main.py

# Проверка API
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/account
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/orders
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/ads/online?token=USDT&currency=RUB

# Веб-интерфейс
open http://localhost:8000
```

---

## Риски

1. **mark_as_paid** требует payment_type и payment_id — нужно выбрать из get_user_payment_types()
2. **upload_chat_file** — multipart/form-data, требует отдельной обработки
3. **get_counterparty_info** — может вернуть ограниченные данные (зависит от настроек приватности контрагента)
