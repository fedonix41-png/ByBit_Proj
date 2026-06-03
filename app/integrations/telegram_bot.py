"""Telegram Bot integration for P2P automation."""
from loguru import logger
import os
import asyncio
import multiprocessing
import signal
import sys
from typing import Optional
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

class P2PTelegramBot:
    """Telegram Bot for customer communication."""
    
    def __init__(self, token: str = None):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN not set")
        
        self.app = Application.builder().token(self.token).build()
        self.orchestrator = None  # Will be set later
        self._setup_handlers()
    
    def set_orchestrator(self, orchestrator):
        """Set orchestrator for message processing."""
        self.orchestrator = orchestrator
    
    def _setup_handlers(self):
        """Setup command and message handlers."""
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("status", self.cmd_status))
        self.app.add_handler(CommandHandler("cancel", self.cmd_cancel))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.handle_message
        ))
        
        self.app.add_handler(MessageHandler(
            filters.PHOTO, 
            self.handle_photo
        ))
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        await update.message.reply_text(
            "👋 Здравствуйте! Я бот для P2P торговли.\n\n"
            "Команды:\n"
            "/status - статус активных ордеров\n"
            "/cancel - отменить сделку\n"
            "/help - помощь\n\n"
            "Отправьте номер ордера для начала работы."
        )
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        user_id = str(update.effective_user.id)
        
        if not self.orchestrator:
            await update.message.reply_text("⚠️ Система временно недоступна")
            return
        
        try:
            orders = await self.orchestrator.get_user_orders(user_id)
            
            if not orders:
                await update.message.reply_text("У вас нет активных ордеров")
                return
            
            status_text = "📋 Ваши активные ордера:\n\n"
            for order in orders:
                status_text += f"🔹 {order['order_id']}\n"
                status_text += f"   Статус: {order['status']}\n"
                status_text += f"   Сумма: {order['amount']} {order['crypto']}\n"
                status_text += f"   Цена: {order['price']} {order['currency']}\n\n"
            
            await update.message.reply_text(status_text)
        
        except Exception as e:
            logger.error(f"Status command error: {e}")
            await update.message.reply_text("❌ Ошибка получения статуса")
    
    async def cmd_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cancel command."""
        await update.message.reply_text(
            "Для отмены сделки отправьте номер ордера в формате:\n"
            "Отменить ORD123"
        )
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        await update.message.reply_text(
            "📖 Помощь по боту\n\n"
            "Команды:\n"
            "/start - начать работу\n"
            "/status - статус ордеров\n"
            "/cancel - отменить сделку\n"
            "/help - эта справка\n\n"
            "Для работы с ордером просто отправьте сообщение.\n"
            "Для подтверждения платежа отправьте скриншот."
        )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages."""
        user_id = str(update.effective_user.id)
        text = update.message.text
        message_id = str(update.message.message_id)
        
        logger.info(f"Message from {user_id}: {text}")
        
        if not self.orchestrator:
            await update.message.reply_text("⚠️ Система временно недоступна")
            return
        
        try:
            await self.orchestrator.process_telegram_message(
                user_id=user_id,
                text=text,
                message_id=message_id,
                username=update.effective_user.username
            )
        
        except Exception as e:
            logger.error(f"Message handling error: {e}")
            await update.message.reply_text("❌ Ошибка обработки сообщения")
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo messages (payment proofs)."""
        user_id = str(update.effective_user.id)
        photo = update.message.photo[-1]
        
        logger.info(f"Photo from {user_id}: {photo.file_id}")
        
        if not self.orchestrator:
            await update.message.reply_text("⚠️ Система временно недоступна")
            return
        
        try:
            file = await photo.get_file()
            photo_path = f"data/photos/{user_id}_{photo.file_id}.jpg"
            os.makedirs("data/photos", exist_ok=True)
            await file.download_to_drive(photo_path)
            
            await update.message.reply_text("✅ Скриншот получен. Проверяю платёж...")
            
            await self.orchestrator.process_payment_proof(
                user_id=user_id,
                photo_path=photo_path
            )
        
        except Exception as e:
            logger.error(f"Photo handling error: {e}")
            await update.message.reply_text("❌ Ошибка обработки скриншота")
    
    async def send_message(self, user_id: str, text: str):
        """Send message to user."""
        try:
            await self.app.bot.send_message(chat_id=int(user_id), text=text)
            logger.info(f"Message sent to {user_id}")
        except Exception as e:
            logger.error(f"Failed to send message to {user_id}: {e}")
            raise
    
    def run(self):
        """Run bot in polling mode in a separate process."""
        logger.info("Starting Telegram bot...")

        def run_polling():
            """Run polling in a separate process."""
            # Ignore SIGINT in child process
            signal.signal(signal.SIGINT, signal.SIG_IGN)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.app.run_polling(allowed_updates=Update.ALL_TYPES))
            except KeyboardInterrupt:
                logger.info("Bot stopped")
            finally:
                loop.close()

        # Start polling in a separate process
        polling_process = multiprocessing.Process(target=run_polling, daemon=True)
        polling_process.start()

        # Keep the main process alive
        try:
            polling_process.join()
        except KeyboardInterrupt:
            logger.info("Shutting down bot...")
            polling_process.terminate()
            polling_process.join(timeout=5)
