# Стратегия тестирования

## Обзор

Проект использует комплексный подход к тестированию с фокусом на AI-агентов, оркестратор и внешние интеграции. Текущий статус: отсутствуют автоматизированные тесты, только ручное тестирование.

## Текущая ситуация

### Что есть
- ✅ Ручное тестирование через Web UI
- ✅ Mock данные для безопасного тестирования
- ✅ Docker Compose для изолированного запуска
- ✅ FastAPI с автоматической документацией

### Чего нет
- ❌ Unit тесты
- ❌ Integration тесты
- ❌ E2E тесты
- ❌ CI/CD pipeline
- ❌ Test coverage measurement

## Архитектура тестирования

### Уровни тестирования

#### 1. Unit Tests (Модульные тесты)
**Цель**: Тестирование отдельных компонентов в изоляции
**Инструменты**: pytest, pytest-asyncio
**Coverage target**: 80%+

##### AI Agents testing
```python
# tests/unit/test_ai_agents.py
@pytest.mark.asyncio
async def test_intent_classifier():
    agent = IntentClassifier()
    result = await agent.classify("Хочу купить BTC")

    assert result["intent"] == "ready_to_pay"
    assert result["confidence"] > 0.8
    assert "entities" in result

@pytest.mark.asyncio
async def test_response_generator():
    agent = ResponseGenerator()
    context = {"intent": "ready_to_pay", "amount": 10000}

    result = await agent.generate(context)
    assert "response" in result
    assert len(result["response"]) > 10
```

##### Orchestrator testing
```python
# tests/unit/test_orchestrator.py
def test_state_initialization():
    state = P2PAutomationState(current_order_id="test_123")
    assert state.status == "idle"
    assert state.approval_required is False

@pytest.mark.asyncio
async def test_node_execution():
    state = P2PAutomationState()
    result = await fetch_order_details(state, {})

    assert result.order_details is not None
    assert "price" in result.order_details
```

##### Database testing
```python
# tests/unit/test_database.py
def test_order_model():
    order = Order(
        order_id="test_123",
        side="BUY",
        crypto="BTC",
        currency="RUB",
        amount=0.001,
        price=50000
    )
    assert order.order_id == "test_123"
    assert order.amount == 0.001

@pytest.mark.asyncio
async def test_session_management():
    async with get_test_session() as session:
        order = Order(order_id="test", ...)
        session.add(order)
        await session.commit()

        retrieved = await session.get(Order, order.id)
        assert retrieved.order_id == "test"
```

#### 2. Integration Tests (Интеграционные тесты)
**Цель**: Тестирование взаимодействия компонентов
**Инструменты**: pytest, testcontainers, httpx

##### API Integration
```python
# tests/integration/test_api.py
@pytest.mark.asyncio
async def test_full_api_flow():
    # Setup
    client = AsyncClient(app=app, base_url="http://test")

    # Create order
    response = await client.post("/api/start_monitor",
                               json={"order_id": "test_123"})
    assert response.status_code == 200

    run_id = response.json()["run_id"]

    # Check status
    response = await client.get(f"/api/run/{run_id}")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "running"
```

##### External API mocking
```python
# tests/integration/test_bybit_integration.py
@pytest.mark.asyncio
async def test_bybit_client():
    with patch('bybit_client.BybitAPI') as mock_api:
        mock_api.return_value.get_ads_list.return_value = [
            {"id": "ORD001", "price": 50000}
        ]

        client = BybitClient(use_mock=False)
        ads = await client.get_ads_list()

        assert len(ads) == 1
        assert ads[0]["id"] == "ORD001"
```

##### Database integration
```python
# tests/integration/test_database_integration.py
@pytest.mark.asyncio
async def test_order_persistence():
    async with get_test_session() as session:
        # Create order with messages
        order = Order(order_id="test", ...)
        message = Message(order_id=order.id, text="Hello")

        session.add(order)
        session.add(message)
        await session.commit()

        # Test relationships
        loaded_order = await session.get(Order, order.id)
        assert len(loaded_order.messages) == 1
        assert loaded_order.messages[0].text == "Hello"
```

#### 3. E2E Tests (End-to-End тесты)
**Цель**: Тестирование полного пользовательского сценария
**Инструменты**: pytest, playwright/selenium, testcontainers

##### Web UI testing
```python
# tests/e2e/test_web_ui.py
def test_order_monitoring_flow(page):
    # Navigate to UI
    page.goto("http://localhost:8000")

    # Select order
    page.click("#order-ORD001")

    # Start monitoring
    page.click("#start-monitoring")

    # Wait for state update
    page.wait_for_selector(".monitoring-active")

    # Approve response
    page.click("#approve-response")

    # Verify completion
    page.wait_for_selector(".completed")
```

##### Telegram Bot testing
```python
# tests/e2e/test_telegram_bot.py
@pytest.mark.asyncio
async def test_telegram_conversation():
    # Setup test bot
    bot = TelegramBot(test_config)

    # Simulate user message
    await simulate_telegram_message("/start", chat_id=123)

    # Check response
    messages = await bot.get_chat_messages(123)
    assert "Привет" in messages[-1]["text"]

    # Simulate payment message
    await simulate_telegram_message("Оплатил", chat_id=123)

    # Check intent classification triggered
    # Verify orchestrator state
```

##### Full P2P flow
```python
# tests/e2e/test_full_flow.py
@pytest.mark.asyncio
async def test_complete_p2p_transaction():
    # 1. Create test order in Bybit
    order_id = await create_test_order()

    # 2. Start monitoring via API
    run_id = await start_monitoring(order_id)

    # 3. Simulate customer message
    await send_telegram_message(order_id, "Готов оплатить")

    # 4. Wait for AI processing
    await wait_for_intent_classification(run_id)

    # 5. Approve response via UI
    await approve_response(run_id)

    # 6. Simulate payment proof
    await send_payment_screenshot(order_id)

    # 7. Wait for fraud analysis
    await wait_for_risk_analysis(run_id)

    # 8. Approve payment
    await approve_payment(run_id)

    # 9. Verify completion
    status = await get_run_status(run_id)
    assert status == "completed"

    # 10. Check notifications
    notifications = await get_telegram_notifications(order_id)
    assert "завершена" in notifications[-1]
```

## Test Infrastructure

### Test Database
```python
# tests/conftest.py
@pytest.fixture
async def test_db():
    # Create test database
    engine = create_async_engine("sqlite:///./test.db")

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()
    os.remove("./test.db")
```

### Mock Services
```python
# tests/mocks/
class MockBybitAPI:
    async def get_ads_list(self):
        return [Order(id="ORD001", price=50000, ...)]

class MockTelegramBot:
    async def send_message(self, chat_id, text):
        # Log message, don't send
        return True

class MockProcessingAPI:
    async def submit_transaction(self, data):
        return {"transaction_id": "txn_123", "status": "completed"}
```

### Test Configuration
```python
# tests/conftest.py
@pytest.fixture
def test_config():
    return {
        "ai_provider": "mock",
        "bybit_use_mock": True,
        "processing_use_mock": True,
        "telegram_use_mock": True,
        "database_url": "sqlite:///./test.db"
    }
```

## CI/CD Pipeline

### GitHub Actions
```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: test

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -e .
        pip install pytest pytest-asyncio pytest-cov

    - name: Run tests
      run: pytest --cov=./ --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
- repo: https://github.com/pre-commit/pre-commit-hooks
  rev: v4.4.0
  hooks:
  - id: trailing-whitespace
  - id: end-of-file-fixer
  - id: check-yaml
  - id: check-added-large-files

- repo: https://github.com/psf/black
  rev: 23.3.0
  hooks:
  - id: black

- repo: https://github.com/pycqa/isort
  rev: 5.12.0
  hooks:
  - id: isort
```

## Test Data Management

### Fixtures
```python
# tests/fixtures/
@pytest.fixture
def sample_order():
    return Order(
        order_id="ORD001",
        side="BUY",
        crypto="BTC",
        currency="RUB",
        amount=0.001,
        price=50000,
        status="active"
    )

@pytest.fixture
def sample_message():
    return Message(
        text="Хочу купить BTC",
        intent="ready_to_pay",
        confidence=0.95
    )
```

### Test Scenarios
```python
# tests/scenarios/
SUCCESSFUL_P2P_FLOW = {
    "order": {...},
    "messages": [
        {"text": "Здравствуйте", "intent": "greeting"},
        {"text": "Готов оплатить", "intent": "ready_to_pay"},
        {"photo": "payment.jpg", "payment_data": {...}}
    ],
    "expected_outcome": "completed"
}

HIGH_RISK_TRANSACTION = {
    "order": {...},
    "payment_data": {"amount": 1000, "card": "suspicious"},
    "expected_risk_score": 0.85,
    "requires_approval": True
}
```

## Performance Testing

### Load Testing
```python
# tests/performance/
@pytest.mark.asyncio
async def test_concurrent_orders():
    # Test 10 simultaneous orders
    tasks = []
    for i in range(10):
        task = asyncio.create_task(process_order(f"ORD{i}"))
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    assert all(results)
```

### AI Agent Performance
```python
@pytest.mark.asyncio
async def test_ai_response_time():
    agent = IntentClassifier()

    start_time = time.time()
    result = await agent.classify("Complex message with many details")
    duration = time.time() - start_time

    assert duration < 2.0  # Max 2 seconds
    assert result["confidence"] > 0.7
```

## Security Testing

### API Security
```python
# tests/security/
def test_api_authentication():
    # Test without auth
    response = client.get("/api/orders")
    assert response.status_code == 401

    # Test with invalid token
    response = client.get("/api/orders", headers={"Authorization": "invalid"})
    assert response.status_code == 401
```

### Input Validation
```python
def test_sql_injection():
    # Test malicious input
    malicious_input = "'; DROP TABLE orders; --"
    response = client.post("/api/start_monitor", json={"order_id": malicious_input})
    assert response.status_code == 400
```

## Reporting and Metrics

### Coverage Reports
```bash
# Generate coverage report
pytest --cov=./ --cov-report=html
open htmlcov/index.html
```

### Test Results
```bash
# JUnit XML for CI
pytest --junitxml=test-results.xml

# Allure reports
pytest --alluredir=allure-results
allure serve allure-results
```

### Performance Metrics
```python
# Custom metrics
test_execution_time = time.time() - start_time
prometheus_metrics.test_duration.labels(test_name).observe(test_execution_time)
```

## Implementation Roadmap

### Phase 1: Foundation (2 weeks)
- [ ] Setup pytest infrastructure
- [ ] Write unit tests for AI agents (80% coverage)
- [ ] Write unit tests for orchestrator nodes
- [ ] Setup test database fixtures

### Phase 2: Integration (2 weeks)
- [ ] Integration tests for API endpoints
- [ ] Mock external services
- [ ] Database integration tests
- [ ] WebSocket testing

### Phase 3: E2E (2 weeks)
- [ ] E2E tests for Web UI
- [ ] Telegram bot integration tests
- [ ] Full P2P flow testing
- [ ] Performance testing

### Phase 4: CI/CD (1 week)
- [ ] GitHub Actions pipeline
- [ ] Pre-commit hooks
- [ ] Coverage reporting
- [ ] Security testing

### Phase 5: Maintenance (Ongoing)
- [ ] Test data updates
- [ ] New feature testing
- [ ] Performance monitoring
- [ ] Regression testing

## Best Practices

### Test Organization
- **tests/unit/**: Модульные тесты
- **tests/integration/**: Интеграционные тесты
- **tests/e2e/**: End-to-end тесты
- **tests/fixtures/**: Тестовые данные
- **tests/mocks/**: Mock объекты

### Naming Conventions
```python
# Unit tests
def test_function_name():
def test_function_name_with_condition():

# Integration tests
def test_api_endpoint():
def test_component_integration():

# E2E tests
def test_user_journey():
def test_complete_workflow():
```

### Test Isolation
- Каждый тест независим
- Использовать fixtures для setup/cleanup
- Не делить состояние между тестами
- Параллельное выполнение

### Mock Strategy
- Mock внешние API (Bybit, Processing, AI providers)
- Использовать реальную БД для integration tests
- Mock тяжелые операции (OCR, file uploads)

## Troubleshooting

### Common Issues
```
Проблема: Tests fail randomly
Решение: Проверить на race conditions, добавить asyncio.sleep()

Проблема: Database locked
Решение: Использовать отдельную БД для тестов, cleanup fixtures

Проблема: Slow tests
Решение: Mock heavy operations, use async properly
```

### Debug Tools
```python
# Debug failing test
pytest -xvs --pdb test_file.py::test_function

# Run specific test
pytest tests/unit/test_ai_agents.py::test_intent_classifier -v

# Profile slow test
pytest --durations=10
```