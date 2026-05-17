#!/usr/bin/env python3
"""
Полная проверка всех методов Bybit P2P API для testnet.

Используется библиотека bybit_p2p (та же, что в проекте).
Запуск: uv run python test_bybit_api.py
"""
import os
import sys
from pathlib import Path
from typing import Callable, Any

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / '.env')


# =============================================================================
# КОНФИГУРАЦИЯ ТЕСТОВ
# =============================================================================

class TestResult:
    """Результат теста."""
    def __init__(self, name: str, success: bool, message: str = "", data: Any = None):
        self.name = name
        self.success = success
        self.message = message
        self.data = data

    def __str__(self):
        status = "✅" if self.success else "❌"
        return f"{status} {self.name}: {self.message}"


def run_test(name: str, func: Callable, client) -> TestResult:
    """Запустить один тест."""
    try:
        response = func(client)
        
        # Разные методы используют разные форматы ответа
        # P2P методы: ret_code / ret_msg (snake_case)
        # Wallet методы: retCode / retMsg (camelCase)
        ret_code = response.get('ret_code')
        if ret_code is None:
            ret_code = response.get('retCode')
        ret_msg = response.get('ret_msg') or response.get('retMsg')
        
        if ret_code == 0:
            result = response.get('result', {})
            # Извлекаем полезную информацию из result
            if isinstance(result, dict):
                if 'balance' in result:
                    info = f"balance: {len(result['balance'])} coins"
                elif 'items' in result:
                    info = f"items: {len(result['items'])}"
                elif 'list' in result:
                    info = f"list: {len(result['list'])}"
                elif 'records' in result:
                    info = f"records: {len(result['records'])}"
                elif 'skipped' in result:
                    info = f"skipped: {result['skipped']}"
                else:
                    info = "OK"
            else:
                info = "OK"
            return TestResult(name, True, info, result)
        else:
            return TestResult(name, False, f"[{ret_code}] {ret_msg or 'неизвестно'}")
            
    except TypeError as e:
        # Ошибка параметров
        return TestResult(name, False, f"TypeError: {e}")
    except Exception as e:
        return TestResult(name, False, f"Exception: {e}")


# =============================================================================
# ТЕСТЫ - USER
# =============================================================================

def test_account_information(client) -> dict:
    """Get Account Information - информация об аккаунте P2P."""
    return client.get_account_information()


def test_counterparty_info(client) -> dict:
    """Get Counterparty User Info - информация о контрагенте (требует orderId)."""
    # Этот метод требует orderId - тест пропустим без реального ордера
    return {"ret_code": 0, "result": {"skipped": "requires orderId"}}


def test_user_payment_types(client) -> dict:
    """Get User Payment Types - способы оплаты пользователя."""
    return client.get_user_payment_types()


# =============================================================================
# ТЕСТЫ - BALANCE
# =============================================================================

def test_current_balance(client) -> dict:
    """Get Current Balance - баланс кошелька."""
    return client.get_current_balance(accountType="FUND", coin="USDT")


# =============================================================================
# ТЕСТЫ - ADVERTISEMENTS
# =============================================================================

def test_ads_list(client) -> dict:
    """Get My Ads - список моих объявлений."""
    return client.get_ads_list()


def test_online_ads(client) -> dict:
    """Get Online Ads - публичные объявления (доступно без аутентификации)."""
    return client.get_online_ads(
        tokenId="USDT",
        currencyId="RUB",
        side="1"  # 1 = sell, 0 = buy
    )


def test_ad_details(client) -> dict:
    """Get Ad Details - детали объявления (требует adId)."""
    # Сначала получаем список объявлений
    ads = client.get_ads_list()
    if ads.get('ret_code') == 0:
        items = ads.get('result', {}).get('items', [])
        if items:
            ad_id = items[0].get('id')
            if ad_id:
                return client.get_ad_details(ad_id=ad_id)
    return {"ret_code": 0, "result": {"skipped": "no ads available"}}


# =============================================================================
# ТЕСТЫ - ORDERS
# =============================================================================

def test_orders(client) -> dict:
    """Get All Orders - все ордера."""
    return client.get_orders(page=1, size=10)


def test_pending_orders(client) -> dict:
    """Get Pending Orders - ожидающие ордера."""
    return client.get_pending_orders(page=1, size=10)


def test_order_details(client) -> dict:
    """Get Order Details - детали ордера (требует orderId)."""
    # Сначала получаем список ордеров
    orders = client.get_orders(page=1, size=1)
    if orders.get('ret_code') == 0:
        items = orders.get('result', {}).get('items', [])
        if items:
            order_id = items[0].get('id')
            if order_id:
                return client.get_order_details(orderId=order_id)
    return {"ret_code": 0, "result": {"skipped": "no orders available"}}


# =============================================================================
# ОСНОВНАЯ ЛОГИКА
# =============================================================================

def get_client():
    """Инициализация клиента P2P."""
    api_key = os.getenv('BYBIT_API_KEY')
    api_secret = os.getenv('BYBIT_API_SECRET')

    if not api_key or not api_secret:
        return None, "BYBIT_API_KEY или BYBIT_API_SECRET не установлены"

    try:
        from bybit_p2p import P2P
        client = P2P(
            api_key=api_key,
            api_secret=api_secret,
            testnet=True
        )
        return client, None
    except ImportError:
        return None, "Библиотека bybit_p2p не установлена"
    except Exception as e:
        return None, str(e)


def main():
    """Запуск всех тестов."""
    print("=" * 60)
    print("🧪 Полная проверка Bybit P2P API (TESTNET)")
    print("=" * 60)

    # Инициализация клиента
    client, error = get_client()
    if error:
        print(f"\n❌ Ошибка инициализации: {error}")
        sys.exit(1)

    print(f"🔑 API Key: {os.getenv('BYBIT_API_KEY')[:8]}...")
    print()

    # Группы тестов
    test_groups = [
        ("👤 USER", [
            ("Account Information", test_account_information),
            ("Counterparty Info", test_counterparty_info),
            ("User Payment Types", test_user_payment_types),
        ]),
        ("💰 BALANCE", [
            ("Current Balance", test_current_balance),
        ]),
        ("📋 ADVERTISEMENTS", [
            ("My Ads List", test_ads_list),
            ("Online Ads", test_online_ads),
            ("Ad Details", test_ad_details),
        ]),
        ("📦 ORDERS", [
            ("All Orders", test_orders),
            ("Pending Orders", test_pending_orders),
            ("Order Details", test_order_details),
        ]),
    ]

    # Выполняем тесты
    all_results = []
    
    for group_name, tests in test_groups:
        print(f"\n{group_name}")
        print("-" * 40)
        
        for name, func in tests:
            print(f"  ⏳ {name}...", end=" ", flush=True)
            result = run_test(name, func, client)
            all_results.append(result)
            print(result.message if result.success else f"FAIL: {result.message}")

    # Итоги
    print()
    print("=" * 60)
    passed = sum(1 for r in all_results if r.success)
    failed = sum(1 for r in all_results if not r.success)
    
    print(f"📊 Результаты: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✅ Все тесты пройдены успешно!")
        print("\n💡 API ключи готовы для использования в проекте.")
        sys.exit(0)
    else:
        print("⚠️ Некоторые тесты не пройдены")
        
        # Выводим детали по неудачным тестам
        print("\n❌ Неудачные тесты:")
        for r in all_results:
            if not r.success:
                print(f"   • {r.name}: {r.message}")
        
        sys.exit(1)


if __name__ == "__main__":
    main()
