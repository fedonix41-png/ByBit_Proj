#!/usr/bin/env python3
"""
Полная диагностика Bybit API прав доступа
"""
import os
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv(project_root / '.env')

def comprehensive_api_test():
    """Комплексная проверка всех API функций"""
    print("🔬 Комплексная диагностика Bybit API прав")
    print("=" * 60)

    try:
        from bybit_p2p import P2P

        api_key = os.getenv('BYBIT_API_KEY')
        api_secret = os.getenv('BYBIT_API_SECRET')
        testnet = os.getenv('BYBIT_TESTNET', 'True').lower() == 'true'

        if not api_key or not api_secret:
            print("❌ API ключи не найдены")
            return

        print(f"🔑 API Key: {api_key[:10]}...")
        print(f"🌐 Testnet: {testnet}")

        client = P2P(api_key=api_key, api_secret=api_secret, testnet=testnet)

        # Список всех доступных методов для тестирования
        tests = [
            ("get_account_information", "Информация об аккаунте", "Базовые права"),
            ("get_current_balance", "Баланс аккаунта", "Базовые права"),
            ("get_ads_list", "Список объявлений", "P2P Trading права"),
            ("get_orders", "Список ордеров", "P2P Trading права"),
            ("get_pending_orders", "Ожидающие ордера", "P2P Trading права"),
            ("get_user_payment_types", "Способы оплаты", "P2P Trading права"),
        ]

        results = {}

        for method_name, description, required_perm in tests:
            print(f"\n🔍 Тестирование: {description}")
            try:
                method = getattr(client, method_name)
                response = method()

                if response.get('retCode') == 0:
                    print(f"✅ {description}: ДОСТУПНО")
                    results[method_name] = "success"
                else:
                    error_msg = response.get('retMsg', 'неизвестная ошибка')
                    print(f"❌ {description}: {error_msg}")
                    results[method_name] = f"error: {error_msg}"

            except Exception as e:
                print(f"❌ {description}: {str(e)}")
                results[method_name] = f"exception: {str(e)}"

        print("\n" + "=" * 60)
        print("📊 РЕЗУЛЬТАТЫ ДИАГНОСТИКИ:")
        print("=" * 60)

        # Анализ результатов
        basic_rights = results.get('get_account_information', 'failed')
        balance_rights = results.get('get_current_balance', 'failed')
        p2p_rights = results.get('get_ads_list', 'failed')

        if 'success' in basic_rights:
            print("✅ Базовые права API: ЕСТЬ")
        else:
            print("❌ Базовые права API: ОТСУТСТВУЮТ")

        if 'success' in balance_rights:
            print("✅ Права на баланс: ЕСТЬ")
        else:
            print("⚠️  Права на баланс: ОТСУТСТВУЮТ")

        if 'success' in p2p_rights:
            print("✅ P2P Trading права: ЕСТЬ")
            print("🎉 ИНТЕГРАЦИЯ ГОТОВА К ИСПОЛЬЗОВАНИЮ!")
        else:
            print("❌ P2P Trading права: ОТСУТСТВУЮТ")
            print("\n💡 РЕШЕНИЕ:")
            print("1. Зайдите на https://testnet.bybit.com/")
            print("2. Account & Security → API Management")
            print("3. Найдите ваш API ключ и нажмите Edit")
            print("4. Включите 'P2P Trading' права (Read & Write)")
            print("5. Сохраните и подождите 5-10 минут")

        print("\n🔗 ПОЛЕЗНЫЕ ССЫЛКИ:")
        print("• Testnet: https://testnet.bybit.com/")
        print("• API Docs: https://bybit-exchange.github.io/docs/v5/")
        print("• P2P SDK: https://github.com/bybit-exchange/bybit-p2p")

        # Проверка на mainnet/testnet путаницу
        print("\n🔄 ПРОВЕРКА MAINNET/TESTNET:")
        try:
            # Пробуем mainnet
            mainnet_client = P2P(api_key=api_key, api_secret=api_secret, testnet=False)
            mainnet_response = mainnet_client.get_account_information()

            if mainnet_response.get('retCode') == 0:
                print("⚠️  ВНИМАНИЕ: API ключ работает на MAINNET!")
                print("   Это значит, что ключ создан для ПРОДАКШЕНА")
                print("   Создайте новый ключ на testnet.bybit.com")
            else:
                print("✅ API ключ корректно настроен для TESTNET")

        except Exception as e:
            print(f"✅ Подтверждено: ключ предназначен только для testnet ({e})")

    except ImportError:
        print("❌ bybit-p2p не установлен")
        print("Установите: pip install bybit-p2p")

if __name__ == "__main__":
    comprehensive_api_test()