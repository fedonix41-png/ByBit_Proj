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
    handle_text, handle_voice, handle_photo
)
from app.infrastructure.bridge.p2p_bridge import p2p_bridge


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
        self.app.add_handler(CommandHandler("demo", self._cmd_demo))
        
        self.app.add_handler(CallbackQueryHandler(self._handle_callback))
        
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_text
        ))
        self.app.add_handler(MessageHandler(filters.VOICE, handle_voice))
        self.app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        
        logger.debug("Telegram handlers registered")
    
    def _get_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        """Get main menu keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("📋 Статус ордеров", callback_data="menu_status"),
                InlineKeyboardButton("❓ Помощь", callback_data="menu_help")
            ],
            [
                InlineKeyboardButton("🎤 Голосовое сообщение", callback_data="demo_voice"),
                InlineKeyboardButton("📷 Скриншот платежа", callback_data="demo_photo")
            ],
            [
                InlineKeyboardButton("💬 Текстовый диалог", callback_data="demo_text"),
                InlineKeyboardButton("ℹ️ О боте", callback_data="menu_about")
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
                InlineKeyboardButton("🔙 В меню", callback_data="menu_main")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    async def _cmd_start(self, update: Update, context):
        """Handle /start command."""
        user_name = update.effective_user.first_name or "Пользователь"
        await update.message.reply_text(
            f"👋 Здравствуйте, {user_name}!\n\n"
            "Я бот для P2P торговли с поддержкой:\n"
            "• 📝 Текстовых сообщений\n"
            "• 🎤 Голосовых сообщений\n"
            "• 📷 Скриншотов платежей\n\n"
            "Нажмите /menu для интерактивного меню\n"
            "Нажмите /demo для демонстрации функций",
            reply_markup=self._get_main_menu_keyboard()
        )
    
    async def _cmd_menu(self, update: Update, context):
        """Handle /menu command - show interactive menu."""
        await update.message.reply_text(
            "📋 **Главное меню**\n\n"
            "Выберите действие:",
            reply_markup=self._get_main_menu_keyboard()
        )
    
    async def _cmd_demo(self, update: Update, context):
        """Handle /demo command - show demo features."""
        await update.message.reply_text(
            "🎬 **Демонстрация функций**\n\n"
            "Выберите функцию для тестирования:",
            reply_markup=self._get_demo_keyboard()
        )
    
    async def _handle_callback(self, update: Update, context):
        """Handle callback queries from inline keyboards."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "menu_main":
            await query.edit_message_text(
                "📋 **Главное меню**\n\nВыберите действие:",
                reply_markup=self._get_main_menu_keyboard()
            )
        
        elif data == "menu_status":
            await self._show_status_callback(query)
        
        elif data == "menu_help":
            await query.edit_message_text(
                "📖 **Помощь по боту**\n\n"
                "Команды:\n"
                "/start - начать работу\n"
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
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 В меню", callback_data="menu_main")
                ]])
            )
        
        elif data == "menu_about":
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
                "• Автоматические ответы\n\n"
                "Ключи хранятся локально в контейнере.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 В меню", callback_data="menu_main")
                ]])
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
    
    async def _show_status_callback(self, query):
        """Show status in callback context."""
        user_id = str(query.from_user.id)
        
        try:
            orders = await p2p_bridge.orchestrator.get_user_orders(user_id)
            
            if not orders:
                await query.edit_message_text(
                    "📋 У вас нет активных ордеров\n\n"
                    "Для начала работы отправьте номер ордера.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 В меню", callback_data="menu_main")
                    ]])
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
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 В меню", callback_data="menu_main")
                ]])
            )
        
        except Exception as e:
            logger.error(f"Status callback error: {e}")
            await query.edit_message_text(
                "❌ Ошибка получения статуса",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 В меню", callback_data="menu_main")
                ]])
            )
    
    async def _cmd_status(self, update: Update, context):
        """Handle /status command."""
        user_id = str(update.effective_user.id)
        
        try:
            orders = await p2p_bridge.orchestrator.get_user_orders(user_id)
            
            if not orders:
                await update.message.reply_text(
                    "📋 У вас нет активных ордеров",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("📋 Меню", callback_data="menu_main")
                    ]])
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
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📋 Меню", callback_data="menu_main")
            ]])
        )
    
    async def _cmd_help(self, update: Update, context):
        """Handle /help command."""
        await update.message.reply_text(
            "📖 Помощь по боту\n\n"
            "Команды:\n"
            "/start - начать работу\n"
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
    
    async def send_message(self, user_id: str, text: str):
        """Send message to user by ID."""
        try:
            await self.app.bot.send_message(chat_id=int(user_id), text=text)
            logger.debug(f"Message sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send message to {user_id}: {e}")
            raise
    
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
