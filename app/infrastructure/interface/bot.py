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
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

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
        
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_text
        ))
        self.app.add_handler(MessageHandler(filters.VOICE, handle_voice))
        self.app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        
        logger.debug("Telegram handlers registered")
    
    async def _cmd_start(self, update: Update, context):
        """Handle /start command."""
        user_name = update.effective_user.first_name or "Пользователь"
        await update.message.reply_text(
            f"👋 Здравствуйте, {user_name}!\n\n"
            "Я бот для P2P торговли с поддержкой:\n"
            "• 📝 Текстовых сообщений\n"
            "• 🎤 Голосовых сообщений\n"
            "• 📷 Скриншотов платежей\n\n"
            "Команды:\n"
            "/status - статус активных ордеров\n"
            "/cancel - отменить сделку\n"
            "/help - помощь"
        )
    
    async def _cmd_status(self, update: Update, context):
        """Handle /status command."""
        user_id = str(update.effective_user.id)
        
        try:
            orders = await p2p_bridge.orchestrator.get_user_orders(user_id)
            
            if not orders:
                await update.message.reply_text("📋 У вас нет активных ордеров")
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
            "где ORD123 - номер вашего ордера"
        )
    
    async def _cmd_help(self, update: Update, context):
        """Handle /help command."""
        await update.message.reply_text(
            "📖 Помощь по боту\n\n"
            "Команды:\n"
            "/start - начать работу\n"
            "/status - статус ордеров\n"
            "/cancel - отменить сделку\n"
            "/help - эта справка\n\n"
            "Поддерживаемые форматы:\n"
            "• Текстовые сообщения\n"
            "• Голосовые сообщения (требуется OpenAI API)\n"
            "• Фото (скриншоты платежей)\n\n"
            "Для работы с ордером отправьте номер ордера.\n"
            "Для подтверждения платежа отправьте скриншот."
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
