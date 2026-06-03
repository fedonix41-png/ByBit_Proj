"""
Admin service: business logic for admin panel operations.

Provides data access and actions for:
- Real statistics (DB + Bybit)
- User management (blacklist, groups)
- Broadcast (all users / by group)
- Bot health status
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import os

from loguru import logger

from app.database.session import get_db_context
from app.database.models import (
    BlacklistEntry, ViolationHistory, Order,
    AIInteraction, TelegramUser,
)


# ---------------------------------------------------------------------------
# User Registry
# ---------------------------------------------------------------------------

def upsert_telegram_user(
    telegram_id: int,
    username: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str],
    language_code: Optional[str] = None,
) -> None:
    """Register or update a Telegram user in the registry."""
    tid = str(telegram_id)
    try:
        with get_db_context() as db:
            user = db.query(TelegramUser).filter(
                TelegramUser.telegram_id == tid
            ).first()
            if user:
                user.username = username
                user.first_name = first_name
                user.last_name = last_name
                user.last_active_at = datetime.utcnow()
                user.is_active = True
            else:
                user = TelegramUser(
                    telegram_id=tid,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    language_code=language_code,
                    group="all",
                )
                db.add(user)
    except Exception as e:
        logger.error(f"upsert_telegram_user error: {e}")


def get_all_telegram_user_ids(group: Optional[str] = None) -> List[int]:
    """Return list of telegram_id ints for broadcast.

    Args:
        group: None or 'all' → everyone; otherwise filter by group tag.
    """
    try:
        with get_db_context() as db:
            q = db.query(TelegramUser.telegram_id).filter(
                TelegramUser.is_active == True,
                TelegramUser.is_blocked == False,
            )
            if group and group != "all":
                q = q.filter(TelegramUser.group == group)
            rows = q.all()
            return [int(r[0]) for r in rows]
    except Exception as e:
        logger.error(f"get_all_telegram_user_ids error: {e}")
        return []


def get_user_groups() -> List[str]:
    """Return distinct group tags from telegram_users."""
    try:
        with get_db_context() as db:
            rows = db.query(TelegramUser.group).distinct().all()
            return sorted({r[0] for r in rows if r[0]})
    except Exception as e:
        logger.error(f"get_user_groups error: {e}")
        return ["all"]


def set_user_group(telegram_id: int, group: str) -> bool:
    """Set group tag for a user."""
    tid = str(telegram_id)
    try:
        with get_db_context() as db:
            user = db.query(TelegramUser).filter(
                TelegramUser.telegram_id == tid
            ).first()
            if not user:
                return False
            user.group = group
            return True
    except Exception as e:
        logger.error(f"set_user_group error: {e}")
        return False


def get_registered_users_count() -> int:
    """Total registered users."""
    try:
        with get_db_context() as db:
            return db.query(TelegramUser).filter(
                TelegramUser.is_active == True
            ).count()
    except Exception as e:
        logger.error(f"get_registered_users_count error: {e}")
        return 0


# ---------------------------------------------------------------------------
# Blacklist management
# ---------------------------------------------------------------------------

def block_user(
    telegram_id: int,
    reason: str,
    created_by: str,
    expires_hours: Optional[int] = None,
) -> Tuple[bool, str]:
    """Add user to blacklist (type='user').

    Returns (success, message).
    """
    tid = str(telegram_id)
    try:
        with get_db_context() as db:
            existing = db.query(BlacklistEntry).filter(
                BlacklistEntry.entry_type == "user",
                BlacklistEntry.value == tid,
                BlacklistEntry.is_active == True,
            ).first()
            if existing:
                return False, f"Пользователь {tid} уже заблокирован"

            expires_at = None
            if expires_hours:
                expires_at = datetime.utcnow() + timedelta(hours=expires_hours)

            entry = BlacklistEntry(
                entry_type="user",
                value=tid,
                reason=reason,
                severity="high",
                is_active=True,
                created_by=created_by,
                expires_at=expires_at,
            )
            db.add(entry)

            # Mark in telegram_users too
            user = db.query(TelegramUser).filter(
                TelegramUser.telegram_id == tid
            ).first()
            if user:
                user.is_blocked = True
                user.group = "blocked"

        return True, f"✅ Пользователь {tid} заблокирован"
    except Exception as e:
        logger.error(f"block_user error: {e}")
        return False, f"❌ Ошибка блокировки: {e}"


def unblock_user(telegram_id: int) -> Tuple[bool, str]:
    """Deactivate all active blacklist entries for a user."""
    tid = str(telegram_id)
    try:
        with get_db_context() as db:
            entries = db.query(BlacklistEntry).filter(
                BlacklistEntry.entry_type == "user",
                BlacklistEntry.value == tid,
                BlacklistEntry.is_active == True,
            ).all()
            if not entries:
                return False, f"Пользователь {tid} не найден в блокировке"
            for e in entries:
                e.is_active = False

            # Unmark in telegram_users
            user = db.query(TelegramUser).filter(
                TelegramUser.telegram_id == tid
            ).first()
            if user:
                user.is_blocked = False
                if user.group == "blocked":
                    user.group = "all"

        return True, f"✅ Пользователь {tid} разблокирован"
    except Exception as e:
        logger.error(f"unblock_user error: {e}")
        return False, f"❌ Ошибка разблокировки: {e}"


def is_user_blocked(telegram_id: int) -> bool:
    """Check whether a user is currently blacklisted."""
    tid = str(telegram_id)
    try:
        with get_db_context() as db:
            entry = db.query(BlacklistEntry).filter(
                BlacklistEntry.entry_type == "user",
                BlacklistEntry.value == tid,
                BlacklistEntry.is_active == True,
                (BlacklistEntry.expires_at == None) | (BlacklistEntry.expires_at > datetime.utcnow()),
            ).first()
            return entry is not None
    except Exception as e:
        logger.error(f"is_user_blocked error: {e}")
        return False


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def get_admin_stats() -> Dict[str, Any]:
    """Aggregate real statistics from the database."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)

    stats: Dict[str, Any] = {}

    try:
        with get_db_context() as db:
            # Orders
            total_orders = db.query(Order).count()
            orders_today = db.query(Order).filter(Order.created_at >= today_start).count()
            completed_orders = db.query(Order).filter(
                Order.status.in_(["completed", "released", "paid"])
            ).count()
            active_orders = db.query(Order).filter(
                Order.status.in_(["pending", "waiting", "processing"])
            ).count()

            # Violations
            violations_today = db.query(ViolationHistory).filter(
                ViolationHistory.detected_at >= today_start
            ).count()
            violations_week = db.query(ViolationHistory).filter(
                ViolationHistory.detected_at >= week_ago
            ).count()
            blocked_users = db.query(BlacklistEntry).filter(
                BlacklistEntry.entry_type == "user",
                BlacklistEntry.is_active == True,
                (BlacklistEntry.expires_at == None) | (BlacklistEntry.expires_at > now),
            ).count()

            # AI usage
            ai_calls_today = db.query(AIInteraction).filter(
                AIInteraction.created_at >= today_start
            ).count()
            ai_tokens_today = db.query(AIInteraction.tokens_used).filter(
                AIInteraction.created_at >= today_start,
                AIInteraction.tokens_used != None,
            ).all()
            total_tokens = sum(r[0] for r in ai_tokens_today if r[0])

            # Users
            total_users = db.query(TelegramUser).filter(
                TelegramUser.is_active == True
            ).count()
            new_users_today = db.query(TelegramUser).filter(
                TelegramUser.first_seen_at >= today_start
            ).count()

        stats = {
            "orders": {
                "total": total_orders,
                "today": orders_today,
                "completed": completed_orders,
                "active": active_orders,
            },
            "violations": {
                "today": violations_today,
                "week": violations_week,
                "blocked_users": blocked_users,
            },
            "ai": {
                "calls_today": ai_calls_today,
                "tokens_today": total_tokens,
            },
            "users": {
                "total": total_users,
                "new_today": new_users_today,
            },
            "generated_at": now.isoformat(),
        }
    except Exception as e:
        logger.error(f"get_admin_stats error: {e}")
        stats["error"] = str(e)

    return stats


def get_top_violators(limit: int = 5) -> List[Dict[str, Any]]:
    """Top users by violation count in last 30 days."""
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    try:
        from sqlalchemy import func
        with get_db_context() as db:
            rows = (
                db.query(
                    ViolationHistory.user_id,
                    ViolationHistory.username,
                    func.count(ViolationHistory.id).label("count"),
                )
                .filter(ViolationHistory.detected_at >= thirty_days_ago)
                .group_by(ViolationHistory.user_id, ViolationHistory.username)
                .order_by(func.count(ViolationHistory.id).desc())
                .limit(limit)
                .all()
            )
            return [
                {"user_id": r.user_id, "username": r.username or "—", "count": r.count}
                for r in rows
            ]
    except Exception as e:
        logger.error(f"get_top_violators error: {e}")
        return []


def get_recent_violations(limit: int = 10) -> List[Dict[str, Any]]:
    """Most recent violations."""
    try:
        with get_db_context() as db:
            rows = (
                db.query(ViolationHistory)
                .order_by(ViolationHistory.detected_at.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "user_id": r.user_id,
                    "username": r.username or "—",
                    "type": r.violation_type,
                    "severity": r.severity,
                    "at": r.detected_at.strftime("%d.%m %H:%M"),
                }
                for r in rows
            ]
    except Exception as e:
        logger.error(f"get_recent_violations error: {e}")
        return []


# ---------------------------------------------------------------------------
# Bot health (calls local FastAPI /health)
# ---------------------------------------------------------------------------

async def get_bot_health() -> Dict[str, Any]:
    """Fetch health info from the local FastAPI server."""
    import httpx
    host = os.getenv("HOST", "127.0.0.1")
    port = os.getenv("PORT", "8000")
    url = f"http://{host}:{port}/health"
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(url)
            return resp.json()
    except Exception as e:
        logger.warning(f"get_bot_health error: {e}")
        return {"status": "unavailable", "error": str(e)}
