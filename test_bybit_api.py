#!/usr/bin/env python3
"""
Простой тест Bybit P2P API для проверки работоспособности
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

def test_bybit_api():
    """Тестирование основных функций Bybit P2P API"""
    print("🧪 Тестирование Bybit P2P API")
    print("=" * 50)

    try:
        # Импортируем клиент
        from bybit_p2p import P2P

        # Получаем ключи из окружения
        api_key = os.getenv('BYBIT_API_KEY')
        api_secret = os.getenv('BYBIT_API_SECRET')
        testnet = os.getenv('BYBIT_TESTNET', 'True').lower() == 'true'

        if not api_key or not api_secret:
            print("❌ Ошибка: BYBIT_API_KEY или BYBIT_API_SECRET не установлены")
            return False

        print(f"📡 Инициализация клиента (testnet={testnet})...")

        # Создаем клиент
        client = P2P(
            api_key=api_key,
            api_secret=api_secret,
            testnet=testnet
        )

        print("✅ Клиент инициализирован успешно")

        # Тест 0: Проверка базовых прав (информация об аккаунте)
        print("\n🔑 Тест 0: Проверка базовых прав API...")
        try:
            response = client.get_account_information()
            if response.get('retCode') == 0:
                print("✅ API ключ валиден и имеет базовые права")
                account_info = response.get('data', {})
                print(f"   👤 UID: {account_info.get('uid', 'N/A')}")
                print(f"   📧 Email: {account_info.get('email', 'скрыт')[:10]}...")
            else:
                print(f"⚠️  Базовые права отсутствуют: {response.get('retMsg', 'неизвестная ошибка')}")
                return False

        except Exception as e:
            print(f"❌ Ошибка при проверке API ключа: {e}")
            return False

        # Тест 1: Проверка баланса (обычно доступно)
        print("\n💰 Тест 1: Получение баланса аккаунта...")
        try:
            response = client.get_current_balance()
            print("✅ Запрос выполнен успешно")
            balances = response.get('data', [])
            print(f"📊 Найдено балансов: {len(balances)}")

            # Показываем все балансы
            for balance in balances:
                token = balance.get('tokenId', 'N/A')
                available = float(balance.get('available', 0))
                total = float(balance.get('total', 0))
                print(f"   {token}: {available} (доступно) / {total} (всего)")

        except Exception as e:
            print(f"⚠️  Баланс недоступен: {e}")
            print("   💡 Возможно нет прав на просмотр баланса")

        # Тест 2: Получение объявлений (P2P права)
        print("\n📋 Тест 2: Получение списка объявлений...")
        try:
            response = client.get_ads_list()
            print("✅ Запрос выполнен успешно")
            print(f"📊 Найдено объявлений: {len(response.get('data', []))}")

            # Показываем детали первого объявления
            if response.get('data'):
                ad = response['data'][0]
                print(f"   🆔 ID: {ad.get('id', 'N/A')}")
                print(f"   💰 Цена: {ad.get('price', 'N/A')} {ad.get('currency', '')}")
                print(f"   📈 Сумма: {ad.get('amount', 'N/A')} {ad.get('tokenId', '')}")
                print(f"   📊 Статус: {ad.get('status', 'N/A')}")
            else:
                print("   📝 У вас нет активных объявлений")

        except Exception as e:
            print(f"⚠️  P2P объявления недоступны: {e}")
            print("   💡 Проверьте, что включены 'P2P Trading' права в API Management")

        # Тест 3: Попытка отправки сообщения (если есть объявления)
        print("\n💬 Тест 3: Проверка отправки сообщений...")
        try:
            # Сначала получим список объявлений
            ads_response = client.get_ads_list()
            if ads_response.get('retCode') == 0 and ads_response.get('data'):
                # Возьмем ID первого объявления
                ad_id = ads_response['data'][0].get('id')
                if ad_id:
                    # Попробуем отправить тестовое сообщение
                    msg_response = client.send_message(ad_id, "Тестовое сообщение от API")
                    if msg_response.get('retCode') == 0:
                        print("✅ Отправка сообщений работает")
                    else:
                        print(f"⚠️  Отправка сообщений заблокирована: {msg_response.get('retMsg')}")
                else:
                    print("⚠️  Нет подходящих объявлений для теста сообщений")
            else:
                print("⚠️  Пропускаем тест сообщений (нет объявлений)")

        except Exception as e:
            print(f"⚠️  Тест отправки сообщений недоступен: {e}")

        print("\n📊 Резюме тестирования:")
        print("✅ Базовое API подключение работает")
        print("✅ API ключ валиден для testnet")

        # Определяем уровень доступа
        try:
            ads_test = client.get_ads_list()
            if ads_test.get('retCode') == 0:
                print("✅ P2P права доступа есть - интеграция готова!")
                return True
            else:
                print("⚠️  P2P права отсутствуют - настройте в API Management")
                return False
        except:
            print("⚠️  P2P права отсутствуют - настройте в API Management")
            return False

    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("💡 Установите bybit-p2p: pip install bybit-p2p")
        return False

    except Exception as e:
        print(f"❌ Непредвиденная ошибка: {e}")
        return False

if __name__ == "__main__":
    success = test_bybit_api()
    sys.exit(0 if success else 1)