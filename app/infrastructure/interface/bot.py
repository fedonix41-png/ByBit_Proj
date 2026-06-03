"""
Main Telegram bot setup with multi-modal support and full admin panel.

Combines handlers with P2P system via bridge layer.
Admin panel provides:
  - Real statistics (DB + Bybit)
  - User management (view, block, unblock, group assignment)
  - Broadcast (all users / by group)
  - Bot health status
  - FSM-style dialogs for admin input flows
"""
import os
import asyncio
import signal
import multiprocessing
from datetime import datetime
from typing import Optional, List

from loguru import logger
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    BotCommand,
    BotCommandScopeDefault,
    BotCommandScopeChat,
    MenuButtonCommands,
)
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

from app.infrastructure.interface.telegram_handlers import (
    handle_text, handle_voice, handle_photo, admin_only
)
from app.infrastructure.bridge.p2p_bridge import p2p_bridge
from app.config import ADMIN_TELEGRAM_IDS

# ---------------------------------------------------------------------------
# Persistent Reply Keyboard button labels
# (these are the button texts users tap — no commands needed)
# ---------------------------------------------------------------------------
BTN_HOME    = "🏠 Главная"
BTN_AI      = "💬 Спросить AI"
BTN_STATUS  = "📋 Статус"
BTN_HELP    = "❓ Помощь"
BTN_PANEL   = "🛠 Панель"      # admin only
BTN_BACK    = "↩️ Назад"

# Bot start time for uptime calculation
_BOT_START_TIME: datetime = datetime.utcnow()


# ---------------------------------------------------------------------------
# FSM pending-action constants
# ---------------------------------------------------------------------------
FSM_BLOCK_AWAIT_ID       = "admin_block_await_id"
FSM_UNBLOCK_AWAIT_ID     = "admin_unblock_await_id"
FSM_BROADCAST_AWAIT_TEXT = "admin_broadcast_await_text"
FSM_BROADCAST_AWAIT_GRP  = "admin_broadcast_await_group"
FSM_BROADCAST_CONFIRM    = "admin_broadcast_confirm"
FSM_SET_GROUP_AWAIT_ID   = "admin_set_group_await_id"
FSM_SET_GROUP_AWAIT_GRP  = "admin_set_group_await_group"


class P2PTelegramBot:
    """Production-ready Telegram bot with multi-modal support and full admin panel."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN not set in environment")

        self.app = (
            Application.builder()
            .token(self.token)
            .post_init(self._post_init)
            .build()
        )
        self._setup_handlers()

        logger.info("P2PTelegramBot initialized")

    # ------------------------------------------------------------------
    # Handler registration
    # ------------------------------------------------------------------

    def _setup_handlers(self):
        """Setup all command and message handlers."""
        # /start is the ONLY command users need to know.
        # Everything else is accessible via persistent Reply Keyboard buttons.
        self.app.add_handler(CommandHandler("start",  self._cmd_start))
        # Legacy text commands still work but are not advertised to users:
        self.app.add_handler(CommandHandler("status", self._cmd_status))
        self.app.add_handler(CommandHandler("cancel", self._cmd_cancel))
        self.app.add_handler(CommandHandler("help",   self._cmd_help))
        self.app.add_handler(CommandHandler("menu",   self._cmd_menu))
        self.app.add_handler(CommandHandler("admin",  self._cmd_admin))
        self.app.add_handler(CommandHandler("stats",  self._cmd_stats))
        self.app.add_handler(CommandHandler("demo",   self._cmd_demo))
        self.app.add_handler(CommandHandler("ask",    self._cmd_ask))

        self.app.add_handler(CallbackQueryHandler(self._handle_callback))

        # Text handler catches BOTH nav button taps and regular messages.
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self._handle_text_with_ai_mode
        ))
        self.app.add_handler(MessageHandler(filters.VOICE, handle_voice))
        self.app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # ------------------------------------------------------------------
    # post_init: configure bot-level commands by scope
    # ------------------------------------------------------------------

    async def _post_init(self, application: Application) -> None:
        """Called after Application is initialised — set commands per scope.

        Regular users only see /start in the ☰ menu button.
        Admins additionally see the full command list.
        """
        user_commands = [
            BotCommand("start", "▶️ Запустить / Главное меню"),
        ]
        admin_commands = [
            BotCommand("start",  "▶️ Запустить / Главное меню"),
            BotCommand("status", "📋 Статус ордеров"),
            BotCommand("stats",  "📊 Статистика (admin)"),
            BotCommand("demo",   "🎬 Демонстрация функций"),
            BotCommand("help",   "❓ Помощь"),
        ]

        try:
            # Set minimal commands for all users
            await application.bot.set_my_commands(
                user_commands,
                scope=BotCommandScopeDefault(),
            )
            # Set extended commands for each admin
            for admin_id in ADMIN_TELEGRAM_IDS:
                try:
                    await application.bot.set_my_commands(
                        admin_commands,
                        scope=BotCommandScopeChat(chat_id=admin_id),
                    )
                except Exception as e:
                    logger.warning(f"Could not set commands for admin {admin_id}: {e}")
            logger.info("Bot commands set by scope")
        except Exception as e:
            logger.warning(f"_post_init set_my_commands failed: {e}")

    # ------------------------------------------------------------------
    # Persistent Reply Keyboard (always-visible bottom bar)
    # ------------------------------------------------------------------

    def _get_persistent_keyboard(self, is_admin: bool = False) -> ReplyKeyboardMarkup:
        """Bottom persistent keyboard — acts as app tab bar.

        Users tap these buttons instead of typing commands.
        Admin gets an extra 🛠 Панель tab.
        """
        if is_admin:
            rows = [
                [KeyboardButton(BTN_HOME), KeyboardButton(BTN_AI)],
                [KeyboardButton(BTN_STATUS), KeyboardButton(BTN_PANEL)],
            ]
        else:
            rows = [
                [KeyboardButton(BTN_HOME), KeyboardButton(BTN_AI)],
                [KeyboardButton(BTN_STATUS), KeyboardButton(BTN_HELP)],
            ]
        return ReplyKeyboardMarkup(
            rows,
            resize_keyboard=True,
            is_persistent=True,       # never auto-hides
            input_field_placeholder="Напишите вопрос или выберите раздел…",
        )

    # ------------------------------------------------------------------
    # Inline keyboards (content area navigation)
    # ------------------------------------------------------------------

    def _get_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        """Main menu content area — shown INSIDE the chat."""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("💬 Спросить AI",       callback_data="ai_ask"),
                InlineKeyboardButton("📋 Статус ордеров",    callback_data="menu_status"),
            ],
            [
                InlineKeyboardButton("🎬 Демо функций",      callback_data="menu_demo"),
                InlineKeyboardButton("ℹ️ О боте",            callback_data="menu_about"),
            ],
        ])

    def _get_admin_menu_keyboard(self) -> InlineKeyboardMarkup:
        """Admin control panel main keyboard."""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📊 Статистика",        callback_data="admin_stats"),
                InlineKeyboardButton("🤖 Статус бота",       callback_data="admin_bot_status"),
            ],
            [
                InlineKeyboardButton("👥 Пользователи",      callback_data="admin_users"),
                InlineKeyboardButton("📢 Рассылка",          callback_data="admin_broadcast"),
            ],
            [
                InlineKeyboardButton("🧠 Анализ P2P",        callback_data="menu_p2p_analysis"),
                InlineKeyboardButton("🛡️ Проверка фрода",   callback_data="menu_fraud_check"),
            ],
            [
                InlineKeyboardButton("⚙️ Настройки",         callback_data="menu_settings"),
            ],
        ])

    def _get_users_menu_keyboard(self) -> InlineKeyboardMarkup:
        """Admin users submenu."""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📋 Все пользователи",  callback_data="users_list"),
                InlineKeyboardButton("⚠️ Нарушители",        callback_data="users_violators"),
            ],
            [
                InlineKeyboardButton("🚫 Заблокировать",     callback_data="users_block"),
                InlineKeyboardButton("✅ Разблокировать",    callback_data="users_unblock"),
            ],
            [
                InlineKeyboardButton("🏷️ Назначить группу", callback_data="users_set_group"),
                InlineKeyboardButton("↩️ Назад",             callback_data="menu_admin"),
            ],
        ])

    def _get_broadcast_menu_keyboard(self, groups: list) -> InlineKeyboardMarkup:
        """Broadcast target selection keyboard, built from available groups."""
        rows = []
        # First row: send to all
        rows.append([
            InlineKeyboardButton("📢 Всем пользователям",   callback_data="broadcast_group:all"),
        ])
        # Rows for each custom group (max 6)
        for grp in groups[:6]:
            if grp != "all":
                rows.append([
                    InlineKeyboardButton(f"🔖 Группа: {grp}", callback_data=f"broadcast_group:{grp}"),
                ])
        rows.append([
            InlineKeyboardButton("↩️ Назад",                 callback_data="menu_admin"),
        ])
        return InlineKeyboardMarkup(rows)

    def _get_p2p_analysis_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📈 По типу ордера",    callback_data="p2p_analysis_by_type"),
                InlineKeyboardButton("💱 По валюте",         callback_data="p2p_analysis_by_currency"),
            ],
            [
                InlineKeyboardButton("📊 Все предложения",   callback_data="p2p_analysis_all"),
                InlineKeyboardButton("↩️ Назад",             callback_data="menu_admin"),
            ],
        ])

    def _get_fraud_check_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📷 Анализ скриншота",  callback_data="fraud_screenshot"),
                InlineKeyboardButton("🔍 Проверка ордера",   callback_data="fraud_order"),
            ],
            [
                InlineKeyboardButton("📋 История проверок",  callback_data="fraud_history"),
                InlineKeyboardButton("↩️ Назад",             callback_data="menu_admin"),
            ],
        ])

    def _get_settings_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🤖 AI-провайдер",      callback_data="settings_ai_provider"),
                InlineKeyboardButton("🌐 Язык",              callback_data="settings_language"),
            ],
            [
                InlineKeyboardButton("📊 Баланс Bybit",      callback_data="settings_bybit_balance"),
                InlineKeyboardButton("↩️ Назад",             callback_data="menu_admin"),
            ],
        ])

    def _get_ai_chat_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 Новый вопрос",      callback_data="ai_new_question"),
                InlineKeyboardButton("↩️ В меню",            callback_data="menu_main"),
            ],
        ])

    def _get_demo_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📝 Текст",             callback_data="demo_text"),
                InlineKeyboardButton("🎤 Голос",             callback_data="demo_voice"),
            ],
            [
                InlineKeyboardButton("📷 Фото",              callback_data="demo_photo"),
                InlineKeyboardButton("🖼️ Анализ чека",      callback_data="demo_receipt"),
            ],
            [
                InlineKeyboardButton("📊 Статус",            callback_data="demo_status"),
                InlineKeyboardButton("↩️ Назад",             callback_data="menu_main"),
            ],
        ])

    def _get_nav_keyboard(
        self,
        back: str = "menu_main",
        refresh: Optional[str] = None,
    ) -> InlineKeyboardMarkup:
        """Navigation keyboard with optional Refresh button."""
        row = [InlineKeyboardButton("↩️ Назад", callback_data=back)]
        if refresh:
            row.insert(0, InlineKeyboardButton("🔄 Обновить", callback_data=refresh))
        return InlineKeyboardMarkup([row])

    def _get_confirm_broadcast_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Отправить",         callback_data="broadcast_confirm_yes"),
                InlineKeyboardButton("❌ Отмена",            callback_data="broadcast_confirm_no"),
            ],
        ])

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    async def _cmd_start(self, update: Update, context):
        """Handle /start — register user, install persistent keyboard, show home."""
        user = update.effective_user
        is_admin = user.id in ADMIN_TELEGRAM_IDS
        context.user_data["ai_mode"] = False
        context.user_data["current_menu"] = "main"
        context.user_data["is_admin"] = is_admin
        context.user_data.pop("pending_action", None)

        # Register in TelegramUser registry
        try:
            from app.infrastructure.interface.admin_service import upsert_telegram_user
            upsert_telegram_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                language_code=user.language_code,
            )
        except Exception as e:
            logger.warning(f"upsert_telegram_user on /start failed: {e}")

        name = user.first_name or "Пользователь"
        admin_hint = "\n🛠 _Tap \"Панель\" для доступа к управлению_" if is_admin else ""

        # Step 1: Install persistent bottom keyboard (one-time setup)
        await update.message.reply_text(
            "⌨️",  # invisible trigger to set the keyboard
            reply_markup=self._get_persistent_keyboard(is_admin),
        )

        # Step 2: Send the actual welcome card with inline menu
        await update.message.reply_text(
            f"👋 Привет, *{name}*!\n\n"
            f"Я P2P-ассистент на базе AI.\n"
            f"Используй кнопки внизу или тап по карточкам.{admin_hint}",
            parse_mode="Markdown",
            reply_markup=self._get_main_menu_keyboard(),
        )

    async def _cmd_menu(self, update: Update, context):
        """Handle /menu — restore persistent keyboard and show home screen."""
        is_admin = update.effective_user.id in ADMIN_TELEGRAM_IDS
        context.user_data["ai_mode"] = False
        context.user_data["current_menu"] = "main"
        context.user_data.pop("pending_action", None)
        # Reinstall persistent keyboard in case it was lost
        await update.message.reply_text(
            "🏠 *Главная*",
            parse_mode="Markdown",
            reply_markup=self._get_persistent_keyboard(is_admin),
        )
        await update.message.reply_text(
            "Выберите действие:",
            reply_markup=self._get_main_menu_keyboard(),
        )

    @admin_only
    async def _cmd_admin(self, update: Update, context):
        """Handle /admin — show admin panel (legacy, prefer 🛠 Панель button)."""
        context.user_data["ai_mode"] = False
        context.user_data["current_menu"] = "admin"
        context.user_data.pop("pending_action", None)
        await update.message.reply_text(
            "🛠 *Панель управления*",
            parse_mode="Markdown",
            reply_markup=self._get_admin_menu_keyboard(),
        )

    @admin_only
    async def _cmd_stats(self, update: Update, context):
        """Handle /stats — show real statistics."""
        text = await self._build_stats_text()
        await update.message.reply_text(
            text,
            reply_markup=self._get_nav_keyboard(back="menu_admin", refresh="admin_stats"),
        )

    async def _cmd_ask(self, update: Update, context):
        """Handle /ask — enter AI chat mode."""
        context.user_data["ai_mode"] = True
        context.user_data["current_menu"] = "ai_chat"
        await update.message.reply_text(
            "💬 **Режим AI-диалога**\n\n"
            "Задайте любой вопрос о P2P торговле, криптовалютах, "
            "анализе рынка или проверке контрагентов.\n\n"
            "Я отвечу с учётом контекста диалога.",
            reply_markup=self._get_ai_chat_keyboard(),
        )

    async def _cmd_demo(self, update: Update, context):
        """Handle /demo — show demo features."""
        context.user_data["ai_mode"] = False
        context.user_data["current_menu"] = "demo"
        await update.message.reply_text(
            "🎬 **Демонстрация функций**\n\nВыберите функцию:",
            reply_markup=self._get_demo_keyboard(),
        )

    # ------------------------------------------------------------------
    # Text message dispatcher
    # ------------------------------------------------------------------

    async def _handle_text_with_ai_mode(self, update: Update, context):
        """Route text: nav buttons → admin FSM → AI mode → P2P bridge.

        Priority:
          1. Persistent keyboard nav buttons (highest priority)
          2. Admin FSM input (when pending_action is set)
          3. AI chat mode
          4. P2P bridge (default)
        """
        text = update.message.text.strip()
        uid = update.effective_user.id
        is_admin = uid in ADMIN_TELEGRAM_IDS

        # ── Priority 1: Persistent keyboard navigation ──────────────────
        if text == BTN_HOME:
            await self._nav_home(update, context)
            return

        if text == BTN_AI:
            await self._nav_ai(update, context)
            return

        if text == BTN_STATUS:
            await self._nav_status(update, context)
            return

        if text == BTN_HELP:
            await self._nav_help(update, context)
            return

        if text == BTN_PANEL:
            if not is_admin:
                await update.message.reply_text("⛔ Нет доступа к панели управления.")
                return
            await self._nav_admin_panel(update, context)
            return

        # ── Priority 2: Admin FSM ───────────────────────────────────────
        pending = context.user_data.get("pending_action")
        if pending and is_admin:
            await self._handle_admin_text_input(update, context)
            return

        # ── Priority 3 & 4: AI mode / P2P bridge ───────────────────────
        if context.user_data.get("ai_mode", False):
            context.user_data["last_interaction"] = "ai_chat"

        await handle_text(update, context)

    # ------------------------------------------------------------------
    # Navigation action handlers (called from Reply Keyboard buttons)
    # ------------------------------------------------------------------

    async def _nav_home(self, update: Update, context):
        """🏠 Home button handler."""
        context.user_data["ai_mode"] = False
        context.user_data["current_menu"] = "main"
        context.user_data.pop("pending_action", None)
        await update.message.reply_text(
            "🏠 *Главная*",
            parse_mode="Markdown",
            reply_markup=self._get_main_menu_keyboard(),
        )

    async def _nav_ai(self, update: Update, context):
        """💬 AI button handler — enter AI chat mode."""
        context.user_data["ai_mode"] = True
        context.user_data["current_menu"] = "ai_chat"
        await update.message.reply_text(
            "💬 *Режим AI-диалога*\n\n"
            "Задайте любой вопрос о P2P торговле, криптовалютах, "
            "анализе рынка или проверке контрагентов.",
            parse_mode="Markdown",
            reply_markup=self._get_ai_chat_keyboard(),
        )

    async def _nav_status(self, update: Update, context):
        """📋 Status button handler."""
        user_id = str(update.effective_user.id)
        try:
            orders = await p2p_bridge.orchestrator.get_user_orders(user_id)
            if not orders:
                await update.message.reply_text(
                    "📋 *Статус*\n\nАктивных ордеров нет.",
                    parse_mode="Markdown",
                    reply_markup=self._get_nav_keyboard(),
                )
                return
            status_text = "📋 *Активные ордера:*\n\n"
            for o in orders:
                status_text += (
                    f"🔹 `{o['order_id']}`\n"
                    f"   {o['status']} · {o['amount']} {o['crypto']} · {o['price']} {o['currency']}\n"
                )
            await update.message.reply_text(
                status_text,
                parse_mode="Markdown",
                reply_markup=self._get_nav_keyboard(),
            )
        except Exception as e:
            logger.error(f"_nav_status error: {e}")
            await update.message.reply_text(
                "📋 *Статус*\n\n❌ Не удалось получить данные.",
                parse_mode="Markdown",
                reply_markup=self._get_nav_keyboard(),
            )

    async def _nav_help(self, update: Update, context):
        """❓ Help button handler."""
        context.user_data["ai_mode"] = False
        await update.message.reply_text(
            "❓ *Помощь*\n\n"
            "Используй кнопки внизу экрана для навигации:\n\n"
            "🏠 *Главная* — главный экран и быстрые действия\n"
            "💬 *Спросить AI* — задай вопрос о P2P\n"
            "📋 *Статус* — посмотреть активные ордера\n\n"
            "*Форматы сообщений:*\n"
            "• Текст — вопросы, номера ордеров\n"
            "• Голос — транскрибируется автоматически\n"
            "• Фото — анализ скриншотов и чеков",
            parse_mode="Markdown",
            reply_markup=self._get_nav_keyboard(),
        )

    async def _nav_admin_panel(self, update: Update, context):
        """🛠 Admin Panel button handler (admin only)."""
        context.user_data["ai_mode"] = False
        context.user_data["current_menu"] = "admin"
        context.user_data.pop("pending_action", None)
        await update.message.reply_text(
            "🛠 *Панель управления*",
            parse_mode="Markdown",
            reply_markup=self._get_admin_menu_keyboard(),
        )

    # ------------------------------------------------------------------
    # Admin FSM input handlers
    # ------------------------------------------------------------------

    async def _handle_admin_text_input(self, update: Update, context):
        """Dispatch admin text input based on pending_action FSM state."""
        pending = context.user_data.get("pending_action")
        text = update.message.text.strip()

        if pending == FSM_BLOCK_AWAIT_ID:
            await self._fsm_block_user(update, context, text)

        elif pending == FSM_UNBLOCK_AWAIT_ID:
            await self._fsm_unblock_user(update, context, text)

        elif pending == FSM_BROADCAST_AWAIT_TEXT:
            # Store text, ask for group selection
            context.user_data["broadcast_text"] = text
            context.user_data.pop("pending_action", None)
            from app.infrastructure.interface.admin_service import get_user_groups
            groups = get_user_groups()
            await update.message.reply_text(
                f"📢 Текст сохранён:\n\n_{text}_\n\nВыберите получателей:",
                parse_mode="Markdown",
                reply_markup=self._get_broadcast_menu_keyboard(groups),
            )

        elif pending == FSM_BROADCAST_CONFIRM:
            # Unexpected text during confirm — ignore
            await update.message.reply_text(
                "Нажмите одну из кнопок выше для подтверждения.",
                reply_markup=self._get_confirm_broadcast_keyboard(),
            )

        elif pending == FSM_SET_GROUP_AWAIT_ID:
            try:
                uid = int(text)
                context.user_data["set_group_target_id"] = uid
                context.user_data["pending_action"] = FSM_SET_GROUP_AWAIT_GRP
                await update.message.reply_text(
                    f"Введите название группы для пользователя `{uid}`:\n"
                    "(например: `vip`, `operator`, `banned_watch`)",
                    parse_mode="Markdown",
                )
            except ValueError:
                await update.message.reply_text("❌ Введите числовой Telegram ID.")

        elif pending == FSM_SET_GROUP_AWAIT_GRP:
            group_name = text.lower().strip()
            target_id = context.user_data.pop("set_group_target_id", None)
            context.user_data.pop("pending_action", None)
            if not target_id:
                await update.message.reply_text("❌ Сессия истекла. Повторите.")
                return
            from app.infrastructure.interface.admin_service import set_user_group
            ok = set_user_group(target_id, group_name)
            if ok:
                await update.message.reply_text(
                    f"✅ Пользователь `{target_id}` переведён в группу `{group_name}`.",
                    parse_mode="Markdown",
                    reply_markup=self._get_nav_keyboard(back="admin_users"),
                )
            else:
                await update.message.reply_text(
                    f"❌ Пользователь `{target_id}` не найден в реестре.",
                    parse_mode="Markdown",
                    reply_markup=self._get_nav_keyboard(back="admin_users"),
                )

        else:
            # Unknown pending action — clear it
            context.user_data.pop("pending_action", None)
            await handle_text(update, context)

    async def _fsm_block_user(self, update: Update, context, text: str):
        context.user_data.pop("pending_action", None)
        try:
            uid = int(text)
        except ValueError:
            await update.message.reply_text(
                "❌ Неверный формат. Введите числовой Telegram ID.",
                reply_markup=self._get_nav_keyboard(back="admin_users"),
            )
            return

        admin_name = update.effective_user.username or str(update.effective_user.id)
        from app.infrastructure.interface.admin_service import block_user
        ok, msg = block_user(
            telegram_id=uid,
            reason="Заблокирован администратором через бот",
            created_by=admin_name,
        )
        await update.message.reply_text(
            msg,
            reply_markup=self._get_nav_keyboard(back="admin_users"),
        )

    async def _fsm_unblock_user(self, update: Update, context, text: str):
        context.user_data.pop("pending_action", None)
        try:
            uid = int(text)
        except ValueError:
            await update.message.reply_text(
                "❌ Неверный формат. Введите числовой Telegram ID.",
                reply_markup=self._get_nav_keyboard(back="admin_users"),
            )
            return

        from app.infrastructure.interface.admin_service import unblock_user
        ok, msg = unblock_user(telegram_id=uid)
        await update.message.reply_text(
            msg,
            reply_markup=self._get_nav_keyboard(back="admin_users"),
        )

    # ------------------------------------------------------------------
    # Data builders (reusable for commands and callbacks)
    # ------------------------------------------------------------------

    async def _build_stats_text(self) -> str:
        """Build real statistics text from DB."""
        from app.infrastructure.interface.admin_service import get_admin_stats
        s = get_admin_stats()
        if "error" in s:
            return f"❌ Ошибка получения статистики:\n{s['error']}"

        o = s.get("orders", {})
        v = s.get("violations", {})
        ai = s.get("ai", {})
        u = s.get("users", {})
        ts = s.get("generated_at", "—")[:16].replace("T", " ")

        # Try to get Bybit balance
        balance_line = ""
        try:
            bal = await self._get_bybit_balance()
            if bal:
                parts = [f"{coin}: {amt}" for coin, amt in list(bal.items())[:3]]
                balance_line = "💰 **Баланс:** " + " | ".join(parts) + "\n"
        except Exception:
            pass

        return (
            f"📊 **Статистика P2P**\n"
            f"_Обновлено: {ts} UTC_\n\n"
            f"📦 **Ордера:**\n"
            f"  • Всего: {o.get('total', 0)}\n"
            f"  • За сегодня: {o.get('today', 0)}\n"
            f"  • Активных: {o.get('active', 0)}\n"
            f"  • Завершено: {o.get('completed', 0)}\n\n"
            f"👥 **Пользователи:**\n"
            f"  • Всего зарегистрировано: {u.get('total', 0)}\n"
            f"  • Новых сегодня: {u.get('new_today', 0)}\n\n"
            f"⚠️ **Нарушения:**\n"
            f"  • Сегодня: {v.get('today', 0)}\n"
            f"  • За неделю: {v.get('week', 0)}\n"
            f"  • Заблокировано: {v.get('blocked_users', 0)}\n\n"
            f"🤖 **AI:**\n"
            f"  • Вызовов сегодня: {ai.get('calls_today', 0)}\n"
            f"  • Токенов сегодня: {ai.get('tokens_today', 0):,}\n\n"
            f"{balance_line}"
        )

    async def _build_bot_status_text(self) -> str:
        """Build bot status text from /health endpoint."""
        from app.infrastructure.interface.admin_service import get_bot_health
        health = await get_bot_health()

        uptime_sec = int((datetime.utcnow() - _BOT_START_TIME).total_seconds())
        hours, rem = divmod(uptime_sec, 3600)
        minutes, seconds = divmod(rem, 60)
        uptime_str = f"{hours}ч {minutes}м {seconds}с"

        status_icon = "✅" if health.get("status") == "healthy" else "⚠️"
        components = health.get("components", {})

        db_status   = "✅" if components.get("database") == "ok" else f"❌ {components.get('database', '—')}"
        redis_status = "✅" if "ok" in str(components.get("redis", "")) else f"⚠️ {components.get('redis', '—')}"

        version = health.get("version", "—")
        srv_ts = health.get("timestamp", "—")[:16].replace("T", " ") if health.get("timestamp") else "—"

        return (
            f"🤖 **Статус бота**\n\n"
            f"{status_icon} **Сервер:** {health.get('status', 'unknown')}\n"
            f"⏱ **Uptime бота:** {uptime_str}\n"
            f"🔢 **Версия:** {version}\n"
            f"🕐 **Сервер время:** {srv_ts}\n\n"
            f"🔌 **Компоненты:**\n"
            f"  • БД: {db_status}\n"
            f"  • Redis: {redis_status}\n"
        )

    # ------------------------------------------------------------------
    # Callback handler (main dispatcher)
    # ------------------------------------------------------------------

    async def _handle_callback(self, update: Update, context):
        """Dispatch all inline keyboard callbacks."""
        query = update.callback_query
        await query.answer()
        data = query.data
        uid = update.effective_user.id
        is_admin = uid in ADMIN_TELEGRAM_IDS

        # ---- Main menu ----
        if data == "menu_main":
            context.user_data["ai_mode"] = False
            context.user_data["current_menu"] = "main"
            context.user_data.pop("pending_action", None)
            await query.edit_message_text(
                "🏠 *Главная*",
                parse_mode="Markdown",
                reply_markup=self._get_main_menu_keyboard(),
            )

        # ---- Admin panel root ----
        elif data == "menu_admin":
            if not is_admin:
                await query.answer("⛔ Нет доступа", show_alert=True)
                return
            context.user_data["current_menu"] = "admin"
            context.user_data.pop("pending_action", None)
            await query.edit_message_text(
                "🛠 *Панель управления*",
                parse_mode="Markdown",
                reply_markup=self._get_admin_menu_keyboard(),
            )

        # ---- Statistics ----
        elif data == "admin_stats":
            if not is_admin:
                await query.answer("⛔ Нет доступа", show_alert=True)
                return
            context.user_data["current_menu"] = "admin_stats"
            await query.answer("⏳ Загружаю данные…")
            text = await self._build_stats_text()
            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=self._get_nav_keyboard(back="menu_admin", refresh="admin_stats"),
            )

        # ---- Bot status ----
        elif data == "admin_bot_status":
            if not is_admin:
                await query.answer("⛔ Нет доступа", show_alert=True)
                return
            context.user_data["current_menu"] = "admin_bot_status"
            await query.answer("⏳ Проверяю…")
            text = await self._build_bot_status_text()
            await query.edit_message_text(
                text,
                parse_mode="Markdown",
                reply_markup=self._get_nav_keyboard(back="menu_admin", refresh="admin_bot_status"),
            )

        # ---- Users menu ----
        elif data == "admin_users":
            if not is_admin:
                await query.answer("⛔ Нет доступа", show_alert=True)
                return
            context.user_data["current_menu"] = "admin_users"
            context.user_data.pop("pending_action", None)
            await query.edit_message_text(
                "🛠 › 👥 *Пользователи*\n\nВыберите действие:",
                parse_mode="Markdown",
                reply_markup=self._get_users_menu_keyboard(),
            )

        elif data == "users_list":
            if not is_admin:
                await query.answer("⛔ Нет доступа", show_alert=True)
                return
            await self._show_users_list(query)

        elif data == "users_violators":
            if not is_admin:
                await query.answer("⛔ Нет доступа", show_alert=True)
                return
            await self._show_violators(query)

        elif data == "users_block":
            if not is_admin:
                await query.answer("⛔ Нет доступа", show_alert=True)
                return
            context.user_data["pending_action"] = FSM_BLOCK_AWAIT_ID
            await query.edit_message_text(
                "🚫 **Блокировка пользователя**\n\n"
                "Введите Telegram ID пользователя для блокировки\n"
                "(числовой ID, например: `123456789`):",
                parse_mode="Markdown",
                reply_markup=self._get_nav_keyboard(back="admin_users"),
            )

        elif data == "users_unblock":
            if not is_admin:
                await query.answer("⛔ Нет доступа", show_alert=True)
                return
            context.user_data["pending_action"] = FSM_UNBLOCK_AWAIT_ID
            await query.edit_message_text(
                "✅ **Разблокировка пользователя**\n\n"
                "Введите Telegram ID для разблокировки:",
                parse_mode="Markdown",
                reply_markup=self._get_nav_keyboard(back="admin_users"),
            )

        elif data == "users_set_group":
            if not is_admin:
                await query.answer("⛔ Нет доступа", show_alert=True)
                return
            context.user_data["pending_action"] = FSM_SET_GROUP_AWAIT_ID
            await query.edit_message_text(
                "🏷️ **Назначить группу**\n\n"
                "Введите Telegram ID пользователя:",
                parse_mode="Markdown",
                reply_markup=self._get_nav_keyboard(back="admin_users"),
            )

        # ---- Broadcast ----
        elif data == "admin_broadcast":
            if not is_admin:
                await query.answer("⛔ Нет доступа", show_alert=True)
                return
            context.user_data["current_menu"] = "admin_broadcast"
            context.user_data["pending_action"] = FSM_BROADCAST_AWAIT_TEXT
            await query.edit_message_text(
                "🛠 › 📢 *Рассылка*\n\n"
                "Напишите текст сообщения."
                "После ввода выберите группу получателей.",
                parse_mode="Markdown",
                reply_markup=self._get_nav_keyboard(back="menu_admin"),
            )

        elif data.startswith("broadcast_group:"):
            if not is_admin:
                await query.answer("⛔ Нет доступа", show_alert=True)
                return
            group = data.replace("broadcast_group:", "")
            broadcast_text = context.user_data.get("broadcast_text")
            if not broadcast_text:
                await query.edit_message_text(
                    "❌ Текст рассылки не найден. Начните сначала.",
                    reply_markup=self._get_nav_keyboard(back="admin_broadcast"),
                )
                return
            context.user_data["broadcast_group"] = group
            context.user_data["pending_action"] = FSM_BROADCAST_CONFIRM
            from app.infrastructure.interface.admin_service import get_all_telegram_user_ids
            count = len(get_all_telegram_user_ids(group=group if group != "all" else None))
            grp_label = "всем пользователям" if group == "all" else f"группе «{group}»"
            await query.edit_message_text(
                f"📢 **Подтвердите рассылку**\n\n"
                f"Группа: {grp_label} ({count} чел.)\n\n"
                f"Текст:\n_{broadcast_text}_\n\n"
                f"Отправить?",
                parse_mode="Markdown",
                reply_markup=self._get_confirm_broadcast_keyboard(),
            )

        elif data == "broadcast_confirm_yes":
            if not is_admin:
                await query.answer("⛔ Нет доступа", show_alert=True)
                return
            broadcast_text = context.user_data.pop("broadcast_text", None)
            broadcast_group = context.user_data.pop("broadcast_group", "all")
            context.user_data.pop("pending_action", None)
            if not broadcast_text:
                await query.edit_message_text("❌ Текст рассылки не найден.")
                return
            await query.edit_message_text("📤 Выполняю рассылку…")
            sent, failed = await self._execute_broadcast(broadcast_text, broadcast_group)
            await query.edit_message_text(
                f"✅ **Рассылка завершена**\n\n"
                f"• Отправлено: {sent}\n"
                f"• Ошибок: {failed}",
                parse_mode="Markdown",
                reply_markup=self._get_nav_keyboard(back="menu_admin"),
            )

        elif data == "broadcast_confirm_no":
            context.user_data.pop("broadcast_text", None)
            context.user_data.pop("broadcast_group", None)
            context.user_data.pop("pending_action", None)
            await query.edit_message_text(
                "❌ Рассылка отменена.",
                reply_markup=self._get_nav_keyboard(back="menu_admin"),
            )

        # ---- AI chat ----
        elif data == "ai_ask":
            context.user_data["ai_mode"] = True
            context.user_data["current_menu"] = "ai_chat"
            await query.edit_message_text(
                "💬 **Режим AI-диалога**\n\n"
                "Задайте любой вопрос о P2P торговле, криптовалютах, "
                "анализе рынка или проверке контрагентов.",
                reply_markup=self._get_ai_chat_keyboard(),
            )

        elif data == "ai_new_question":
            context.user_data["ai_mode"] = True
            await query.edit_message_text(
                "💬 **Новый вопрос**\n\nЗадайте ваш вопрос:",
                reply_markup=self._get_ai_chat_keyboard(),
            )

        # ---- P2P Analysis ----
        elif data == "menu_p2p_analysis":
            if not is_admin:
                await query.answer("⛔ Нет доступа", show_alert=True)
                return
            context.user_data["current_menu"] = "p2p_analysis"
            await query.edit_message_text(
                "🛠 › 🧠 *Анализ P2P*\n\nВыберите тип анализа:",
                parse_mode="Markdown",
                reply_markup=self._get_p2p_analysis_keyboard(),
            )

        elif data in ("p2p_analysis_by_type", "p2p_analysis_by_currency", "p2p_analysis_all"):
            analysis_type = data.replace("p2p_analysis_", "")
            await self._handle_p2p_analysis(query, context, analysis_type)

        # ---- Fraud check ----
        elif data == "menu_fraud_check":
            if not is_admin:
                await query.answer("⛔ Нет доступа", show_alert=True)
                return
            context.user_data["current_menu"] = "fraud_check"
            await query.edit_message_text(
                "🛠 › 🛡️ *Проверка фрода*\n\nВыберите тип проверки:",
                parse_mode="Markdown",
                reply_markup=self._get_fraud_check_keyboard(),
            )

        elif data == "fraud_screenshot":
            context.user_data["current_menu"] = "fraud_screenshot"
            await query.edit_message_text(
                "📷 **Анализ скриншота**\n\n"
                "Отправьте скриншот для проверки:\n"
                "• Скриншот переписки с контрагентом\n"
                "• Фото платёжного документа\n"
                "• Скриншот профиля пользователя\n\n"
                "AI проанализирует изображение на признаки мошенничества.",
                reply_markup=self._get_nav_keyboard(back="menu_fraud_check"),
            )

        elif data == "fraud_order":
            context.user_data["current_menu"] = "fraud_order"
            await query.edit_message_text(
                "🔍 **Проверка ордера**\n\n"
                "Отправьте номер ордера для проверки:\n"
                "• Репутация контрагента\n"
                "• История сделок\n"
                "• Риски по параметрам ордера",
                reply_markup=self._get_nav_keyboard(back="menu_fraud_check"),
            )

        elif data == "fraud_history":
            await self._show_fraud_history(query, context)

        # ---- Settings ----
        elif data == "menu_settings":
            if not is_admin:
                await query.answer("⛔ Нет доступа", show_alert=True)
                return
            context.user_data["current_menu"] = "settings"
            await query.edit_message_text(
                "🛠 › ⚙️ *Настройки*\n\nВыберите параметр:",
                parse_mode="Markdown",
                reply_markup=self._get_settings_keyboard(),
            )

        elif data == "settings_ai_provider":
            await self._handle_ai_provider_settings(query, context)

        elif data == "settings_language":
            await self._handle_language_settings(query, context)

        elif data == "settings_bybit_balance":
            if not is_admin:
                await query.answer("⛔ Нет доступа", show_alert=True)
                return
            await self._handle_bybit_balance(query, context)

        elif data.startswith("settings_ai_provider_"):
            provider = data.replace("settings_ai_provider_", "")
            context.user_data["ai_provider"] = provider
            await self._handle_ai_provider_settings(query, context, saved=True)

        elif data.startswith("settings_lang_"):
            lang = data.replace("settings_lang_", "")
            context.user_data["language"] = lang
            await self._handle_language_settings(query, context, saved=True)

        # ---- Status ----
        elif data == "menu_status":
            await self._show_status_callback(query)

        # ---- Help / About ----
        elif data == "menu_help":
            context.user_data["current_menu"] = "help"
            await query.edit_message_text(
                "❓ *Помощь*\n\n"
                "Используй кнопки внизу экрана для навигации:\n\n"
                "🏠 *Главная* — главный экран\n"
                "💬 *Спросить AI* — задай вопрос о P2P\n"
                "📋 *Статус* — активные ордера\n\n"
                "*Форматы сообщений:*\n"
                "• Текст — вопросы, номера ордеров\n"
                "• Голос — транскрибируется автоматически\n"
                "• Фото — анализ скриншотов и чеков",
                parse_mode="Markdown",
                reply_markup=self._get_nav_keyboard(),
            )

        elif data == "menu_about":
            context.user_data["current_menu"] = "about"
            await query.edit_message_text(
                "ℹ️ *О боте*\n\n"
                "P2P Automation Bot v2.1\n"
                "Powered by LangGraph & AI Agents\n\n"
                "*Возможности:*\n"
                "• AI-классификация намерений\n"
                "• Анализ скриншотов платежей\n"
                "• Транскрипция голосовых (Whisper)\n"
                "• Проверка на мошенничество\n"
                "• Admin-панель с реальными данными",
                parse_mode="Markdown",
                reply_markup=self._get_nav_keyboard(),
            )

        # ---- Demo ----
        elif data == "menu_demo":
            context.user_data["current_menu"] = "demo"
            await query.edit_message_text(
                "🎬 *Демонстрация функций*\n\nВыберите режим:",
                parse_mode="Markdown",
                reply_markup=self._get_demo_keyboard(),
            )

        # ---- Demo ----
        elif data == "demo_text":
            await query.edit_message_text(
                "📝 **Демо: Текстовые сообщения**\n\n"
                "Отправьте любое текстовое сообщение:\n"
                "• «Привет» — приветствие\n"
                "• «Готов оплатить» — ready_to_pay\n"
                "• «Отправил платёж» — payment_sent\n"
                "• «Хочу отменить» — cancel",
                reply_markup=self._get_demo_keyboard(),
            )

        elif data == "demo_voice":
            await query.edit_message_text(
                "🎤 **Демо: Голосовые сообщения**\n\n"
                "Запишите голосовое — Whisper транскрибирует в текст.\n"
                "Требуется OPENAI_API_KEY.",
                reply_markup=self._get_demo_keyboard(),
            )

        elif data == "demo_photo":
            await query.edit_message_text(
                "📷 **Демо: Скриншоты платежей**\n\n"
                "Отправьте скриншот чека — GPT-4 Vision извлечёт данные:\n"
                "сумма, валюта, дата, реквизиты.",
                reply_markup=self._get_demo_keyboard(),
            )

        elif data == "demo_receipt":
            await query.edit_message_text(
                "🖼️ **Демо: Анализ чека**\n\n"
                "Отправьте фото чека с подписью «чек».",
                reply_markup=self._get_demo_keyboard(),
            )

        elif data == "demo_status":
            await self._show_status_callback(query)

    # ------------------------------------------------------------------
    # Admin section renderers
    # ------------------------------------------------------------------

    async def _show_users_list(self, query):
        """Show last 10 registered users."""
        from app.infrastructure.interface.admin_service import get_registered_users_count
        from app.database.session import get_db_context
        from app.database.models import TelegramUser as TGUser

        total = get_registered_users_count()
        try:
            with get_db_context() as db:
                rows = (
                    db.query(TGUser)
                    .filter(TGUser.is_active == True)
                    .order_by(TGUser.last_active_at.desc())
                    .limit(10)
                    .all()
                )
        except Exception as e:
            logger.error(f"_show_users_list DB error: {e}")
            rows = []

        text = f"👥 **Пользователи** (всего: {total})\n\nПоследние 10 активных:\n\n"
        if rows:
            for u in rows:
                name = f"@{u.username}" if u.username else (u.first_name or "—")
                blocked_icon = " 🚫" if u.is_blocked else ""
                grp = f"[{u.group}]" if u.group != "all" else ""
                ts = u.last_active_at.strftime("%d.%m %H:%M") if u.last_active_at else "—"
                text += f"• `{u.telegram_id}` {name}{blocked_icon} {grp} — {ts}\n"
        else:
            text += "_Пользователей нет_"

        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=self._get_nav_keyboard(back="admin_users", refresh="users_list"),
        )

    async def _show_violators(self, query):
        """Show top violators from DB."""
        from app.infrastructure.interface.admin_service import get_top_violators, get_recent_violations
        top = get_top_violators(limit=5)
        recent = get_recent_violations(limit=5)

        text = "⚠️ **Нарушители (топ-5 за 30 дней)**\n\n"
        if top:
            for i, v in enumerate(top, 1):
                name = f"@{v['username']}" if v.get("username") and v["username"] != "—" else v["user_id"]
                text += f"{i}. `{v['user_id']}` {name} — {v['count']} нарушений\n"
        else:
            text += "_Нарушений не зафиксировано_\n"

        text += "\n📋 **Последние нарушения:**\n\n"
        if recent:
            for v in recent:
                name = f"@{v['username']}" if v.get("username") and v["username"] != "—" else v["user_id"]
                text += f"• [{v['at']}] `{v['user_id']}` {name} — {v['type']} ({v['severity']})\n"
        else:
            text += "_Нет данных_"

        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=self._get_nav_keyboard(back="admin_users", refresh="users_violators"),
        )

    async def _show_fraud_history(self, query, context):
        """Show fraud check history from user session."""
        context.user_data["current_menu"] = "fraud_history"
        history = context.user_data.get("fraud_check_history", [])

        if not history:
            text = (
                "📋 **История проверок**\n\n"
                "История пуста.\n\n"
                "После проверок ордеров или скриншотов результаты будут здесь."
            )
        else:
            text = "📋 **История проверок**\n\n"
            for i, item in enumerate(history[-5:], 1):
                text += f"{i}. {item.get('type', 'Проверка')}\n"
                text += f"   Результат: {item.get('result', 'N/A')}\n\n"

        await query.edit_message_text(
            text,
            reply_markup=self._get_nav_keyboard(back="menu_fraud_check"),
        )

    async def _handle_p2p_analysis(self, query, context, analysis_type: str):
        """Handle P2P analysis requests."""
        context.user_data["current_menu"] = f"p2p_analysis_{analysis_type}"
        try:
            if analysis_type == "by_type":
                text = (
                    "📈 **Анализ по типу ордера**\n\n"
                    "Выберите тип ордера для анализа:\n"
                    "• BUY — предложения на покупку\n"
                    "• SELL — предложения на продажу\n\n"
                    "Отправьте тип ордера."
                )
            elif analysis_type == "by_currency":
                text = (
                    "💱 **Анализ по валюте**\n\n"
                    "Доступные валюты: RUB, USD, EUR, USDT\n\n"
                    "Отправьте код валюты для анализа."
                )
            else:
                text = (
                    "📊 **Все P2P предложения**\n\n"
                    "Получение актуальных предложений с Bybit P2P…\n"
                    "Данные загружаются в реальном времени."
                )
            await query.edit_message_text(
                text,
                reply_markup=self._get_nav_keyboard(back="menu_p2p_analysis"),
            )
        except Exception as e:
            logger.error(f"P2P analysis error: {e}")
            await query.edit_message_text(
                "❌ Ошибка при анализе P2P предложений",
                reply_markup=self._get_nav_keyboard(back="menu_p2p_analysis"),
            )

    async def _handle_ai_provider_settings(self, query, context, saved: bool = False):
        """Handle AI provider settings."""
        current = context.user_data.get("ai_provider", "openai")
        keyboard = [
            [
                InlineKeyboardButton(f"{'✓ ' if current == 'openai' else ''}OpenAI",     callback_data="settings_ai_provider_openai"),
                InlineKeyboardButton(f"{'✓ ' if current == 'anthropic' else ''}Anthropic", callback_data="settings_ai_provider_anthropic"),
            ],
            [
                InlineKeyboardButton(f"{'✓ ' if current == 'google' else ''}Google",     callback_data="settings_ai_provider_google"),
                InlineKeyboardButton(f"{'✓ ' if current == 'local' else ''}Local",       callback_data="settings_ai_provider_local"),
            ],
            [InlineKeyboardButton("↩️ Назад", callback_data="menu_settings")],
        ]
        text = "🤖 **AI-провайдер**\n\n"
        if saved:
            text += f"✅ Провайдер изменён на: {current}\n\n"
        text += f"Текущий: **{current}**\n\nВыберите провайдер:"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    async def _handle_language_settings(self, query, context, saved: bool = False):
        """Handle language settings."""
        current = context.user_data.get("language", "ru")
        keyboard = [
            [
                InlineKeyboardButton(f"{'✓ ' if current == 'ru' else ''}🇷🇺 Русский", callback_data="settings_lang_ru"),
                InlineKeyboardButton(f"{'✓ ' if current == 'en' else ''}🇬🇧 English",  callback_data="settings_lang_en"),
            ],
            [InlineKeyboardButton("↩️ Назад", callback_data="menu_settings")],
        ]
        text = "🌐 **Язык интерфейса**\n\n"
        if saved:
            text += "✅ Язык изменён\n\n"
        text += f"Текущий: **{'Русский' if current == 'ru' else 'English'}**\n\nВыберите язык:"
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

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
                text += "Информация о балансе недоступна.\n\nНастройте API ключи Bybit."
            await query.edit_message_text(
                text,
                reply_markup=self._get_nav_keyboard(back="menu_settings", refresh="settings_bybit_balance"),
            )
        except Exception as e:
            logger.error(f"Bybit balance error: {e}")
            await query.edit_message_text(
                "❌ Ошибка получения баланса Bybit\n\nПроверьте настройки API ключей.",
                reply_markup=self._get_nav_keyboard(back="menu_settings"),
            )

    async def _get_bybit_balance(self) -> dict:
        """Get Bybit account balance."""
        try:
            if hasattr(p2p_bridge, "bybit_client") and p2p_bridge.bybit_client:
                return await p2p_bridge.bybit_client.get_wallet_balance()
        except Exception as e:
            logger.error(f"Error fetching Bybit balance: {e}")
        return {}

    async def _show_status_callback(self, query):
        """Show order status in callback context."""
        user_id = str(query.from_user.id)
        try:
            orders = await p2p_bridge.orchestrator.get_user_orders(user_id)
            if not orders:
                await query.edit_message_text(
                    "📋 У вас нет активных ордеров\n\nДля начала работы отправьте номер ордера.",
                    reply_markup=self._get_nav_keyboard(),
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
                reply_markup=self._get_nav_keyboard(),
            )
        except Exception as e:
            logger.error(f"Status callback error: {e}")
            await query.edit_message_text(
                "❌ Ошибка получения статуса",
                reply_markup=self._get_nav_keyboard(),
            )

    # ------------------------------------------------------------------
    # Broadcast execution
    # ------------------------------------------------------------------

    async def _execute_broadcast(self, text: str, group: str) -> tuple[int, int]:
        """Send broadcast message to all users in the specified group.

        Returns (sent_count, failed_count).
        """
        from app.infrastructure.interface.admin_service import get_all_telegram_user_ids
        user_ids = get_all_telegram_user_ids(group=group if group != "all" else None)
        sent, failed = 0, 0
        for user_id in user_ids:
            try:
                await self.app.bot.send_message(
                    chat_id=user_id,
                    text=f"📢 {text}",
                )
                sent += 1
                await asyncio.sleep(0.05)  # Telegram rate limit safety
            except Exception as e:
                logger.warning(f"Broadcast failed for {user_id}: {e}")
                failed += 1
        logger.info(f"Broadcast complete: sent={sent}, failed={failed}, group={group}")
        return sent, failed

    # ------------------------------------------------------------------
    # Remaining command handlers
    # ------------------------------------------------------------------

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
            "Для отмены сделки отправьте:\n"
            "Отменить ORD123\n\n"
            "где ORD123 — номер вашего ордера",
            reply_markup=self._get_nav_keyboard(),
        )

    async def _cmd_help(self, update: Update, context):
        """Handle /help command."""
        await update.message.reply_text(
            "📖 Помощь по боту\n\n"
            "/start — начать работу\n"
            "/ask — AI-диалог\n"
            "/status — статус ордеров\n"
            "/cancel — отменить сделку\n"
            "/menu — главное меню\n"
            "/demo — демо функций\n"
            "/admin — панель оператора\n"
            "/help — эта справка\n\n"
            "Поддерживаемые форматы:\n"
            "• Текстовые сообщения\n"
            "• Голосовые (OpenAI Whisper)\n"
            "• Фото (анализ чеков)",
            reply_markup=self._get_main_menu_keyboard(),
        )

    # ------------------------------------------------------------------
    # External API
    # ------------------------------------------------------------------

    async def send_message(self, user_id: str, text: str, reply_markup: Optional[InlineKeyboardMarkup] = None):
        """Send message to user by ID."""
        try:
            await self.app.bot.send_message(
                chat_id=int(user_id),
                text=text,
                reply_markup=reply_markup,
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

    # ------------------------------------------------------------------
    # Runner
    # ------------------------------------------------------------------

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
