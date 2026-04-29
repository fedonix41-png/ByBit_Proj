#!/usr/bin/env python3
"""
Диагностика Bybit API ключей - проверка mainnet vs testnet
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

def test_api_key_detailed():
    """Подробная диагностика API ключей"""
    print("🔍 Диагностика Bybit API ключей")
    print("=" * 50)

    api_key = os.getenv('BYBIT_API_KEY')
    api_secret = os.getenv('BYBIT_API_SECRET')

    if not api_key or not api_secret:
        print("❌ API ключи не найдены в .env")
        return

    print(f"🔑 API Key: {api_key[:10]}...")
    print(f"🔒 API Secret: {api_secret[:10]}...")

    # Тест 1: Попытка подключения к mainnet
    print("\n🌐 Тест 1: Проверка mainnet API...")
    try:
        from bybit_p2p import P2P
        client_mainnet = P2P(
            api_key=api_key,
            api_secret=api_secret,
            testnet=False  # Mainnet
        )

        # Пробуем простой запрос
        response = client_mainnet.get_account_information()
        if response.get('retCode') == 0:
            print("✅ API ключ работает на MAINNET")
            print("   Это означает, что ключ создан для ПРОДАКШЕНА!")
            print("   ⚠️  НЕ ИСПОЛЬЗУЙТЕ ЭТОТ КЛЮЧ ДЛЯ РАЗРАБОТКИ!")
        else:
            print(f"❌ Mainnet API: {response.get('retMsg', 'ошибка')}")

    except Exception as e:
        print(f"❌ Ошибка mainnet: {e}")

    # Тест 2: Попытка подключения к testnet
    print("\n🧪 Тест 2: Проверка testnet API...")
    try:
        client_testnet = P2P(
            api_key=api_key,
            api_secret=api_secret,
            testnet=True  # Testnet
        )

        # Пробуем простой запрос
        response = client_testnet.get_account_information()
        if response.get('retCode') == 0:
            print("✅ API ключ работает на TESTNET")
            account_info = response.get('data', {})
            print(f"   👤 UID: {account_info.get('uid', 'N/A')}")

            # Проверяем P2P права
            print("\n🔐 Тест 3: Проверка P2P прав доступа...")
            try:
                ads_response = client_testnet.get_ads_list()
                if ads_response.get('retCode') == 0:
                    print("✅ P2P права доступа есть!")
                    print(f"   📋 Объявлений: {len(ads_response.get('data', []))}")
                else:
                    print(f"❌ Нет P2P прав: {ads_response.get('retMsg', 'ошибка')}")
                    print("   💡 Решение: Включите 'P2P Trading' права в API Management")
            except Exception as e:
                print(f"❌ Ошибка P2P: {e}")

        else:
            print(f"❌ Testnet API: {response.get('retMsg', 'ошибка')}")
            print("   💡 Возможно ключ создан для mainnet, нужен testnet ключ")

    except Exception as e:
        print(f"❌ Ошибка testnet: {e}")

    print("\n📋 Рекомендации:")
    print("1. Убедитесь, что API ключ создан на testnet.bybit.com")
    print("2. Проверьте, что включены права 'P2P Trading'")
    print("3. API ключи mainnet и testnet - РАЗНЫЕ!")
    print("4. Подождите 5-10 минут после изменения прав")
    print("5. Проверьте IP привязку если установлена")

    print("\n🔗 Ссылки:")
    print("• Testnet: https://testnet.bybit.com/")
    print("• API Management: Account & Security → API Management")

if __name__ == "__main__":
    test_api_key_detailed()