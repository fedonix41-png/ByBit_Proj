"""
Main Telegram bot setup with multi-modal support.

Combines handlers with P2P system via bridge layer.
"""
import os
import asyncio
import signal
import multiprocessing
from typing import Optional

from loguru import logger
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

from app.infrastructure.interface.telegram_handlers import (
    handle_text, handle_voice, handle_photo, admin_only
)
from app.infrastructure.bridge.p2p_bridge import p2p_bridge
from app.config import ADMIN_TELEGRAM_IDS


class P2PTelegramBot:
    """Production-ready Telegram bot with multi-modal support."""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN not set in environment")
        
        self.app = Application.builder().token(self.token).build()
        self._setup_handlers()
        
        logger.info("P2PTelegramBot initialized")
    
    def _setup_handlers(self):
        """Setup all command and message handlers."""
        self.app.add_handler(CommandHandler("start", self._cmd_start))
        self.app.add_handler(CommandHandler("status", self._cmd_status))
        self.app.add_handler(CommandHandler("cancel", self._cmd_cancel))
        self.app.add_handler(CommandHandler("help", self._cmd_help))
        self.app.add_handler(CommandHandler("menu", self._cmd_menu))
        self.app.add_handler(CommandHandler("admin", self._cmd_admin))
        self.app.add_handler(CommandHandler("stats", self._cmd_stats))
        self.app.add_handler(CommandHandler("demo", self._cmd_demo))
        self.app.add_handler(CommandHandler("ask", self._cmd_ask))
        
        self.app.add_handler(CallbackQueryHandler(self._handle_callback))
        
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self._handle_text_with_ai_mode
        ))
        self.app.add_handler(MessageHandler(filters.VOICE, handle_voice))
        self.app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        
        logger.debug("Telegram handlers registered")
    
    def _get_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        """Get main menu keyboard (for clients)."""
        keyboard = [
            [
                InlineKeyboardButton("💬 Задать вопрос AI", callback_data="ai_ask"),
                InlineKeyboardButton("📊 Статус торговли", callback_data="menu_status")
            ],
            [
                InlineKeyboardButton("ℹ️ О боте", callback_data="menu_about")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    def _get_admin_menu_keyboard(self) -> InlineKeyboardMarkup:
        """Get admin menu keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("🧠 Анализ P2P", callback_data="menu_p2p_analysis"),
                InlineKeyboardButton("🛡️ Проверка мошенничества", callback_data="menu_fraud_check")
            ],
            [
                InlineKeyboardButton("⚙️ Настройки", callback_data="menu_settings"),
                InlineKeyboardButton("📊 Общая статистика", callback_data="admin_stats")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def _get_p2p_analysis_keyboard(self) -> InlineKeyboardMarkup:
        """Get P2P analysis submenu keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("📈 По типу ордера", callback_data="p2p_analysis_by_type"),
                InlineKeyboardButton("💱 По валюте", callback_data="p2p_analysis_by_currency")
            ],
            [
                InlineKeyboardButton("📊 Все предложения", callback_data="p2p_analysis_all"),
                InlineKeyboardButton("↩️ Назад", callback_data="menu_admin")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def _get_fraud_check_keyboard(self) -> InlineKeyboardMarkup:
        """Get fraud check submenu keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("📷 Анализ скриншота", callback_data="fraud_screenshot"),
                InlineKeyboardButton("🔍 Проверка ордера", callback_data="fraud_order")
            ],
            [
                InlineKeyboardButton("📋 История проверок", callback_data="fraud_history"),
                InlineKeyboardButton("↩️ Назад", callback_data="menu_admin")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def _get_settings_keyboard(self) -> InlineKeyboardMarkup:
        """Get settings submenu keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("🤖 AI-провайдер", callback_data="settings_ai_provider"),
                InlineKeyboardButton("🌐 Язык", callback_data="settings_language")
            ],
            [
                InlineKeyboardButton("📊 Баланс Bybit", callback_data="settings_bybit_balance"),
                InlineKeyboardButton("↩️ Назад", callback_data="menu_admin")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def _get_ai_chat_keyboard(self) -> InlineKeyboardMarkup:
        """Get AI chat mode keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("🔄 Новый вопрос", callback_data="ai_new_question"),
                InlineKeyboardButton("↩️ В меню", callback_data="menu_main")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def _get_demo_keyboard(self) -> InlineKeyboardMarkup:
        """Get demo features keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("📝 Текст", callback_data="demo_text"),
                InlineKeyboardButton("🎤 Голос", callback_data="demo_voice")
            ],
            [
                InlineKeyboardButton("📷 Фото", callback_data="demo_photo"),
                InlineKeyboardButton("🖼️ Анализ чека", callback_data="demo_receipt")
            ],
            [
                InlineKeyboardButton("📊 Статус", callback_data="demo_status"),
                InlineKeyboardButton("↩️ Назад", callback_data="menu_main")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def _get_back_keyboard(self, callback_data: str = "menu_main") -> InlineKeyboardMarkup:
        """Get keyboard with back button only."""
        return InlineKeyboardMarkup([[
            InlineKeyboardButton("↩️ Назад", callback_data=callback_data)
        ]])
    
    async def _cmd_start(self, update: Update, context):
        """Handle /start command."""
        user_name = update.effective_user.first_name or "Пользователь"
        context.user_data["ai_mode"] = False
        context.user_data["current_menu"] = "main"
        
        await update.message.reply_text(
            f"👋 Здравствуйте, {user_name}!\n\n"
            "Я P2P-бот для поддержки. Чем могу помочь?\n\n"
            "Выберите действие в меню:",
            reply_markup=self._get_main_menu_keyboard()
        )
    
    async def _cmd_menu(self, update: Update, context):
        """Handle /menu command - show interactive menu."""
        context.user_data["ai_mode"] = False
        context.user_data["current_menu"] = "main"
        
        await update.message.reply_text(
            "📋 **Главное меню**\n\n"
            "Выберите действие:",
            reply_markup=self._get_main_menu_keyboard()
        )

    @admin_only
    async def _cmd_admin(self, update: Update, context):
        """Handle /admin command - show admin menu."""
        context.user_data["ai_mode"] = False
        context.user_data["current_menu"] = "admin"
        
        await update.message.reply_text(
            "🛠 **Панель управления оператора**\n\n"
            "Выберите действие:",
            reply_markup=self._get_admin_menu_keyboard()
        )

    @admin_only
    async def _cmd_stats(self, update: Update, context):
        """Handle /stats command - show P2P statistics."""
        # TODO: Get real statistics from orchestrator
        stats_text = (
            "📊 **Статистика P2P (демо)**\n\n"
            "• Активных ордеров: 3\n"
            "• Успешных сделок за сегодня: 12\n"
            "• Оборот: 1,500 USDT\n"
            "• Профит: +45 USDT\n"
        )
        await update.message.reply_text(stats_text)
    
    async def _cmd_ask(self, update: Update, context):
        """Handle /ask command - direct access to AI chat."""
        context.user_data["ai_mode"] = True
        context.user_data["current_menu"] = "ai_chat"
        
        await update.message.reply_text(
            "💬 **Режим AI-диалога**\n\n"
            "Задайте любой вопрос о P2P торговле, криптовалютах, "
            "анализе рынка или проверке контрагентов.\n\n"
            "Я отвечу с учётом контекста диалога.",
            reply_markup=self._get_ai_chat_keyboard()
        )
    
    async def _cmd_demo(self, update: Update, context):
        """Handle /demo command - show demo features."""
        context.user_data["ai_mode"] = False
        context.user_data["current_menu"] = "demo"
        
        await update.message.reply_text(
            "🎬 **Демонстрация функций**\n\n"
            "Выберите функцию для тестирования:",
            reply_markup=self._get_demo_keyboard()
        )
    
    async def _handle_text_with_ai_mode(self, update: Update, context):
        """Handle text messages with AI mode awareness."""
        if context.user_data.get("ai_mode", False):
            context.user_data["last_interaction"] = "ai_chat"
        
        await handle_text(update, context)
    
    async def _handle_callback(self, update: Update, context):
        """Handle callback queries from inline keyboards."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "menu_main":
            context.user_data["ai_mode"] = False
            context.user_data["current_menu"] = "main"
            await query.edit_message_text(
                "📋 **Главное меню**\n\nВыберите действие:",
                reply_markup=self._get_main_menu_keyboard()
            )
            
        elif data == "menu_admin":
            if update.effective_user.id not in ADMIN_TELEGRAM_IDS:
                await query.answer("⛔ Нет доступа", show_alert=True)
                return
            context.user_data["ai_mode"] = False
            context.user_data["current_menu"] = "admin"
            await query.edit_message_text(
                "🛠 **Панель управления оператора**\n\nВыберите действие:",
                reply_markup=self._get_admin_menu_keyboard()
            )
        
        elif data == "ai_ask":
            context.user_data["ai_mode"] = True
            context.user_data["current_menu"] = "ai_chat"
            await query.edit_message_text(
                "💬 **Режим AI-диалога**\n\n"
                "Задайте любой вопрос о P2P торговле, криптовалютах, "
                "анализе рынка или проверке контрагентов.\n\n"
                "Я отвечу с учётом контекста диалога.",
                reply_markup=self._get_ai_chat_keyboard()
            )
        
        elif data == "ai_new_question":
            context.user_data["ai_mode"] = True
            context.user_data["current_menu"] = "ai_chat"
            await query.edit_message_text(
                "💬 **Новый вопрос**\n\n"
                "Задайте ваш вопрос:",
                reply_markup=self._get_ai_chat_keyboard()
            )
        
        elif data == "menu_p2p_analysis":
            if update.effective_user.id not in ADMIN_TELEGRAM_IDS:
                await query.answer("⛔ Нет доступа", show_alert=True)
                return
            context.user_data["current_menu"] = "p2p_analysis"
            await query.edit_message_text(
                "🧠 **Анализ P2P**\n\n"
                "Выберите тип анализа:",
                reply_markup=self._get_p2p_analysis_keyboard()
            )
        
        elif data == "p2p_analysis_by_type":
            await self._handle_p2p_analysis(query, context, "by_type")
        
        elif data == "p2p_analysis_by_currency":
            await self._handle_p2p_analysis(query, context, "by_currency")
        
        elif data == "p2p_analysis_all":
            await self._handle_p2p_analysis(query, context, "all")
        
        elif data == "menu_fraud_check":
            if update.effective_user.id not in ADMIN_TELEGRAM_IDS:
                await query.answer("⛔ Нет доступа", show_alert=True)
                return
            context.user_data["current_menu"] = "fraud_check"
            await query.edit_message_text(
                "🛡️ **Проверка мошенничества**\n\n"
                "Выберите тип проверки:",
                reply_markup=self._get_fraud_check_keyboard()
            )
        
        elif data == "fraud_screenshot":
            context.user_data["current_menu"] = "fraud_screenshot"
            await query.edit_message_text(
                "📷 **Анализ скриншота**\n\n"
                "Отправьте скриншот для проверки:\n"
                "• Скриншот переписки с контрагентом\n"
                "• Фото платежного документа\n"
                "• Скриншот профиля пользователя\n\n"
                "AI проанализирует изображение на наличие "
                "признаков мошенничества.",
                reply_markup=self._get_back_keyboard("menu_fraud_check")
            )
        
        elif data == "fraud_order":
            context.user_data["current_menu"] = "fraud_order"
            await query.edit_message_text(
                "🔍 **Проверка ордера**\n\n"
                "Отправьте номер ордера для проверки:\n\n"
                "Будет проверено:\n"
                "• Репутация контрагента\n"
                "• История сделок\n"
                "• Риски по параметрам ордера",
                reply_markup=self._get_back_keyboard("menu_fraud_check")
            )
        
        elif data == "fraud_history":
            await self._show_fraud_history(query, context)
        
        elif data == "menu_settings":
            if update.effective_user.id not in ADMIN_TELEGRAM_IDS:
                await query.answer("⛔ Нет доступа", show_alert=True)
                return
            context.user_data["current_menu"] = "settings"
            await query.edit_message_text(
                "⚙️ **Настройки**\n\n"
                "Выберите параметр для изменения:",
                reply_markup=self._get_settings_keyboard()
            )
        
        elif data == "settings_ai_provider":
            await self._handle_ai_provider_settings(query, context)
        
        elif data == "settings_language":
            await self._handle_language_settings(query, context)
        
        elif data == "settings_bybit_balance":
            if update.effective_user.id not in ADMIN_TELEGRAM_IDS:
                await query.answer("⛔ Нет доступа", show_alert=True)
                return
            await self._handle_bybit_balance(query, context)
        
        elif data == "admin_stats":
            if update.effective_user.id not in ADMIN_TELEGRAM_IDS:
                await query.answer("⛔ Нет доступа", show_alert=True)
                return
            await self._show_admin_stats_callback(query)
            
        elif data == "menu_status":
            await self._show_status_callback(query)
        
        elif data == "menu_help":
            context.user_data["current_menu"] = "help"
            await query.edit_message_text(
                "📖 **Помощь по боту**\n\n"
                "Команды:\n"
                "/start - начать работу\n"
                "/ask - AI-диалог\n"
                "/status - статус ордеров\n"
                "/cancel - отменить сделку\n"
                "/menu - главное меню\n"
                "/demo - демо функций\n"
                "/help - эта справка\n\n"
                "Поддерживаемые форматы:\n"
                "• Текстовые сообщения\n"
                "• Голосовые сообщения (требуется OpenAI API)\n"
                "• Фото (скриншоты платежей)\n\n"
                "Для работы с ордером отправьте номер ордера.\n"
                "Для подтверждения платежа отправьте скриншот.",
                reply_markup=self._get_back_keyboard()
            )
        
        elif data == "menu_about":
            context.user_data["current_menu"] = "about"
            await query.edit_message_text(
                "ℹ️ **О боте**\n\n"
                "P2P Automation Bot v2.0\n"
                "Powered by LangGraph & AI Agents\n\n"
                "Возможности:\n"
                "• AI-классификация намерений\n"
                "• Умный роутинг сообщений\n"
                "• Анализ скриншотов платежей\n"
                "• Транскрипция голосовых (Whisper)\n"
                "• Контекст диалога\n"
                "• Автоматические ответы\n"
                "• Проверка на мошенничество\n\n"
                "Ключи хранятся локально в контейнере.",
                reply_markup=self._get_back_keyboard()
            )
        
        elif data == "demo_text":
            await query.edit_message_text(
                "📝 **Демо: Текстовые сообщения**\n\n"
                "Отправьте любое текстовое сообщение, и я:\n"
                "1. Классифицирую намерение\n"
                "2. Определю маршрут обработки\n"
                "3. Сгенерирую ответ (с подтверждением)\n\n"
                "Примеры команд:\n"
                "• \"Привет\" - приветствие\n"
                "• \"Готов оплатить\" - ready_to_pay\n"
                "• \"Отправил платёж\" - payment_sent\n"
                "• \"Хочу отменить\" - cancel\n\n"
                "Просто напишите сообщение!",
                reply_markup=self._get_demo_keyboard()
            )
        
        elif data == "demo_voice":
            await query.edit_message_text(
                "🎤 **Демо: Голосовые сообщения**\n\n"
                "Запишите голосовое сообщение:\n"
                "1. Бот скачает аудио\n"
                "2. Whisper транскрибирует в текст\n"
                "3. Текст обработается как обычное сообщение\n\n"
                "Требуется OPENAI_API_KEY в конфигурации.\n\n"
                "Запишите голосовое прямо сейчас!",
                reply_markup=self._get_demo_keyboard()
            )
        
        elif data == "demo_photo":
            await query.edit_message_text(
                "📷 **Демо: Скриншоты платежей**\n\n"
                "Отправьте скриншот чека или квитанции:\n"
                "1. Бот проанализирует изображение (GPT-4 Vision)\n"
                "2. Извлечёт данные: сумма, валюта, дата\n"
                "3. Проверит соответствие ордеру\n\n"
                "Требуется OPENAI_API_KEY.\n\n"
                "Отправьте фото прямо сейчас!",
                reply_markup=self._get_demo_keyboard()
            )
        
        elif data == "demo_receipt":
            await query.edit_message_text(
                "🖼️ **Демо: Анализ чека**\n\n"
                "Специальный режим для платёжных документов:\n"
                "• Распознавание реквизитов\n"
                "• Проверка суммы и валюты\n"
                "• Оценка подлинности\n\n"
                "Отправьте фото чека с подписью \"чек\"",
                reply_markup=self._get_demo_keyboard()
            )
        
        elif data == "demo_status":
            await self._show_status_callback(query)
        
        elif data.startswith("settings_ai_provider_"):
            provider = data.replace("settings_ai_provider_", "")
            context.user_data["ai_provider"] = provider
            await self._handle_ai_provider_settings(query, context, saved=True)
        
        elif data.startswith("settings_lang_"):
            lang = data.replace("settings_lang_", "")
            context.user_data["language"] = lang
            await self._handle_language_settings(query, context, saved=True)
    
    async def _handle_p2p_analysis(self, query, context, analysis_type: str):
        """Handle P2P analysis requests."""
        context.user_data["current_menu"] = f"p2p_analysis_{analysis_type}"
        
        try:
            if analysis_type == "by_type":
                text = (
                    "📈 **Анализ по типу ордера**\n\n"
                    "Выберите тип ордера для анализа:\n\n"
                    "• BUY - предложения на покупку\n"
                    "• SELL - предложения на продажу\n\n"
                    "Отправьте сообщение с типом ордера."
                )
            elif analysis_type == "by_currency":
                text = (
                    "💱 **Анализ по валюте**\n\n"
                    "Доступные валюты:\n"
                    "• RUB - Российский рубль\n"
                    "• USD - Доллар США\n"
                    "• EUR - Евро\n"
                    "• USDT - Tether\n\n"
                    "Отправьте код валюты для анализа."
                )
            else:
                text = (
                    "📊 **Все P2P предложения**\n\n"
                    "Получение актуальных предложений с Bybit P2P...\n\n"
                    "Данные загружаются в реальном времени."
                )
            
            await query.edit_message_text(
                text,
                reply_markup=self._get_back_keyboard("menu_p2p_analysis")
            )
        except Exception as e:
            logger.error(f"P2P analysis error: {e}")
            await query.edit_message_text(
                "❌ Ошибка при анализе P2P предложений",
                reply_markup=self._get_back_keyboard("menu_p2p_analysis")
            )
    
    async def _show_fraud_history(self, query, context):
        """Show fraud check history."""
        context.user_data["current_menu"] = "fraud_history"
        
        history = context.user_data.get("fraud_check_history", [])
        
        if not history:
            text = (
                "📋 **История проверок**\n\n"
                "История пуста.\n\n"
                "После проверок ордеров или скриншотов, "
                "результаты будут отображаться здесь."
            )
        else:
            text = "📋 **История проверок**\n\n"
            for i, item in enumerate(history[-5:], 1):
                text += f"{i}. {item.get('type', 'Проверка')}\n"
                text += f"   Результат: {item.get('result', 'N/A')}\n\n"
        
        await query.edit_message_text(
            text,
            reply_markup=self._get_back_keyboard("menu_fraud_check")
        )
    
    async def _handle_ai_provider_settings(self, query, context, saved: bool = False):
        """Handle AI provider settings."""
        current = context.user_data.get("ai_provider", "openai")
        
        keyboard = [
            [
                InlineKeyboardButton(
                    f"{'✓ ' if current == 'openai' else ''}OpenAI",
                    callback_data="settings_ai_provider_openai"
                ),
                InlineKeyboardButton(
                    f"{'✓ ' if current == 'anthropic' else ''}Anthropic",
                    callback_data="settings_ai_provider_anthropic"
                )
            ],
            [
                InlineKeyboardButton(
                    f"{'✓ ' if current == 'google' else ''}Google",
                    callback_data="settings_ai_provider_google"
                ),
                InlineKeyboardButton(
                    f"{'✓ ' if current == 'local' else ''}Local",
                    callback_data="settings_ai_provider_local"
                )
            ],
            [InlineKeyboardButton("↩️ Назад", callback_data="menu_settings")]
        ]
        
        text = "🤖 **AI-провайдер**\n\n"
        if saved:
            text += f"✅ Провайдер изменён на: {current}\n\n"
        text += f"Текущий провайдер: **{current}**\n\nВыберите провайдер:"
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def _handle_language_settings(self, query, context, saved: bool = False):
        """Handle language settings."""
        current = context.user_data.get("language", "ru")
        
        keyboard = [
            [
                InlineKeyboardButton(
                    f"{'✓ ' if current == 'ru' else ''}🇷🇺 Русский",
                    callback_data="settings_lang_ru"
                ),
                InlineKeyboardButton(
                    f"{'✓ ' if current == 'en' else ''}🇬🇧 English",
                    callback_data="settings_lang_en"
                )
            ],
            [InlineKeyboardButton("↩️ Назад", callback_data="menu_settings")]
        ]
        
        text = "🌐 **Язык интерфейса**\n\n"
        if saved:
            text += f"✅ Язык изменён\n\n"
        text += f"Текущий язык: **{'Русский' if current == 'ru' else 'English'}**\n\nВыберите язык:"
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def _handle_bybit_balance(self, query, context):
        """Handle Bybit balance display."""
        context.user_data["current_menu"] = "bybit_balance"
        
        try:
            balance_info = await self._get_bybit_balance()
            
            text = "📊 **Баланс Bybit**\n\n"
            if balance_info:
                for coin, amount in balance_info.items():
                    text += f"• {coin}: {amount}\n"
            else:
                text += "Информация о балансе недоступна.\n\n"
                text += "Для отображения баланса настройте API ключи Bybit."
            
            await query.edit_message_text(
                text,
                reply_markup=self._get_back_keyboard("menu_settings")
            )
        except Exception as e:
            logger.error(f"Bybit balance error: {e}")
            await query.edit_message_text(
                "❌ Ошибка получения баланса Bybit\n\n"
                "Проверьте настройки API ключей.",
                reply_markup=self._get_back_keyboard("menu_settings")
            )
    
    async def _get_bybit_balance(self) -> dict:
        """Get Bybit account balance."""
        try:
            if hasattr(p2p_bridge, 'bybit_client') and p2p_bridge.bybit_client:
                balance = await p2p_bridge.bybit_client.get_wallet_balance()
                return balance
        except Exception as e:
            logger.error(f"Error fetching Bybit balance: {e}")
        return {}
        
    async def _show_admin_stats_callback(self, query):
        """Show stats in callback context."""
        stats_text = (
            "📊 **Статистика P2P (демо)**\n\n"
            "• Активных ордеров: 3\n"
            "• Успешных сделок за сегодня: 12\n"
            "• Оборот: 1,500 USDT\n"
            "• Профит: +45 USDT\n"
        )
        await query.edit_message_text(
            stats_text,
            reply_markup=self._get_back_keyboard("menu_admin")
        )
    
    async def _show_status_callback(self, query):
        """Show status in callback context."""
        user_id = str(query.from_user.id)
        
        try:
            orders = await p2p_bridge.orchestrator.get_user_orders(user_id)
            
            if not orders:
                await query.edit_message_text(
                    "📋 У вас нет активных ордеров\n\n"
                    "Для начала работы отправьте номер ордера.",
                    reply_markup=self._get_back_keyboard()
                )
                return
            
            status_text = "📋 **Ваши активные ордера:**\n\n"
            for o in orders:
                status_text += f"🔹 `{o['order_id']}`\n"
                status_text += f"   Статус: {o['status']}\n"
                status_text += f"   Сумма: {o['amount']} {o['crypto']}\n"
                status_text += f"   Цена: {o['price']} {o['currency']}\n\n"
            
            await query.edit_message_text(
                status_text,
                reply_markup=self._get_back_keyboard()
            )
        
        except Exception as e:
            logger.error(f"Status callback error: {e}")
            await query.edit_message_text(
                "❌ Ошибка получения статуса",
                reply_markup=self._get_back_keyboard()
            )
    
    async def _cmd_status(self, update: Update, context):
        """Handle /status command."""
        user_id = str(update.effective_user.id)
        
        try:
            orders = await p2p_bridge.orchestrator.get_user_orders(user_id)
            
            if not orders:
                await update.message.reply_text(
                    "📋 У вас нет активных ордеров",
                    reply_markup=self._get_back_keyboard()
                )
                return
            
            status_text = "📋 Ваши активные ордера:\n\n"
            for o in orders:
                status_text += f"🔹 {o['order_id']}\n"
                status_text += f"   Статус: {o['status']}\n"
                status_text += f"   Сумма: {o['amount']} {o['crypto']}\n"
                status_text += f"   Цена: {o['price']} {o['currency']}\n\n"
            
            await update.message.reply_text(status_text)
        
        except Exception as e:
            logger.error(f"Status command error: {e}")
            await update.message.reply_text("❌ Ошибка получения статуса")
    
    async def _cmd_cancel(self, update: Update, context):
        """Handle /cancel command."""
        await update.message.reply_text(
            "Для отмены сделки отправьте сообщение в формате:\n"
            "Отменить ORD123\n\n"
            "где ORD123 - номер вашего ордера",
            reply_markup=self._get_back_keyboard()
        )
    
    async def _cmd_help(self, update: Update, context):
        """Handle /help command."""
        await update.message.reply_text(
            "📖 Помощь по боту\n\n"
            "Команды:\n"
            "/start - начать работу\n"
            "/ask - AI-диалог\n"
            "/status - статус ордеров\n"
            "/cancel - отменить сделку\n"
            "/menu - главное меню\n"
            "/demo - демо функций\n"
            "/help - эта справка\n\n"
            "Поддерживаемые форматы:\n"
            "• Текстовые сообщения\n"
            "• Голосовые сообщения (требуется OpenAI API)\n"
            "• Фото (скриншоты платежей)\n\n"
            "Для работы с ордером отправьте номер ордера.\n"
            "Для подтверждения платежа отправьте скриншот.",
            reply_markup=self._get_main_menu_keyboard()
        )
    
    async def send_message(self, user_id: str, text: str, reply_markup: Optional[InlineKeyboardMarkup] = None):
        """Send message to user by ID."""
        try:
            await self.app.bot.send_message(
                chat_id=int(user_id), 
                text=text,
                reply_markup=reply_markup
            )
            logger.debug(f"Message sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send message to {user_id}: {e}")
            raise
            
    async def send_admin_alert(self, text: str, reply_markup: Optional[InlineKeyboardMarkup] = None):
        """Send an alert to all configured administrators."""
        if not ADMIN_TELEGRAM_IDS:
            logger.warning("No ADMIN_TELEGRAM_IDS configured, cannot send admin alert.")
            return
            
        for admin_id in ADMIN_TELEGRAM_IDS:
            try:
                await self.send_message(str(admin_id), text, reply_markup=reply_markup)
            except Exception as e:
                logger.error(f"Failed to send alert to admin {admin_id}: {e}")
    
    def run(self):
        """Run bot in polling mode with separate process."""
        logger.info("Starting Telegram bot...")
        
        p2p_bridge.set_telegram_bot(self)
        
        def run_polling():
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    self.app.run_polling(allowed_updates=Update.ALL_TYPES)
                )
            except KeyboardInterrupt:
                logger.info("Bot polling stopped")
            finally:
                loop.close()
        
        process = multiprocessing.Process(target=run_polling, daemon=True)
        process.start()
        
        try:
            process.join()
        except KeyboardInterrupt:
            logger.info("Shutting down Telegram bot...")
            process.terminate()
            process.join(timeout=5)
            if process.is_alive():
                process.kill()
