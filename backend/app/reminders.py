"""低价提醒：写入、去重、列表与已读。"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError

from .db import SessionLocal
from .models import Reminder

# 只有这两种信号才值得打断用户
REMINDABLE_SIGNALS = {"buy_now", "consider"}

SIGNAL_ACTION = {
    "buy_now": "建议购买",
    "consider": "可以考虑",
}


def serialize_reminder(row: Reminder) -> dict:
    """把 ORM 行转成前端 / API 用的字典。"""
    return {
        "id": row.id,
        "origin": row.origin,
        "destination": row.destination,
        "flight_date": row.flight_date.isoformat(),
        "price": row.price,
        "target_price": row.target_price,
        "signal": row.signal,
        "message": row.message,
        "created_at": row.created_at.isoformat(timespec="seconds"),
        "is_read": row.is_read,
    }


def build_reminder_message(
    origin: str,
    destination: str,
    price: float,
    signal: str,
    target_price: float | None,
) -> str:
    """生成提醒中心展示文案，例如「BJS→SHA 跌到 ¥504（目标 ¥700）建议购买」。"""
    action = SIGNAL_ACTION.get(signal, "可以考虑")
    if target_price is not None:
        return (
            f"{origin}→{destination} 跌到 ¥{price:.0f}"
            f"（目标 ¥{target_price:.0f}）{action}"
        )
    return f"{origin}→{destination} 跌到 ¥{price:.0f}，{action}"


def maybe_create_reminder(
    origin: str,
    destination: str,
    flight_date: date,
    price: float | None,
    signal: str,
    target_price: float | None = None,
) -> dict | None:
    """信号为 buy_now / consider 时写一条提醒；同航线同日期已存在则跳过。"""
    origin = origin.upper()
    destination = destination.upper()
    if signal not in REMINDABLE_SIGNALS or price is None:
        return None

    db = SessionLocal()
    try:
        existing = db.scalar(
            select(Reminder).where(
                Reminder.origin == origin,
                Reminder.destination == destination,
                Reminder.flight_date == flight_date,
            )
        )
        if existing is not None:
            return None

        row = Reminder(
            origin=origin,
            destination=destination,
            flight_date=flight_date,
            price=float(price),
            target_price=float(target_price) if target_price is not None else None,
            signal=signal,
            message=build_reminder_message(
                origin, destination, float(price), signal, target_price
            ),
            created_at=datetime.now(),
            is_read=False,
        )
        db.add(row)
        try:
            db.commit()
        except IntegrityError:
            # 并发下唯一约束兜底，不当成错误
            db.rollback()
            return None
        db.refresh(row)
        return serialize_reminder(row)
    finally:
        db.close()


def list_reminders(limit: int = 20) -> list[dict]:
    """按创建时间倒序取最近若干条。"""
    db = SessionLocal()
    try:
        rows = db.scalars(
            select(Reminder).order_by(Reminder.created_at.desc()).limit(limit)
        ).all()
        return [serialize_reminder(row) for row in rows]
    finally:
        db.close()


def unread_count() -> int:
    """未读条数，供顶栏角标使用。"""
    db = SessionLocal()
    try:
        count = db.scalar(
            select(func.count())
            .select_from(Reminder)
            .where(Reminder.is_read.is_(False))
        )
        return int(count or 0)
    finally:
        db.close()


def mark_read(reminder_id: int) -> dict | None:
    """标记单条已读；不存在则返回 None。"""
    db = SessionLocal()
    try:
        row = db.get(Reminder, reminder_id)
        if row is None:
            return None
        if not row.is_read:
            row.is_read = True
            db.commit()
            db.refresh(row)
        return serialize_reminder(row)
    finally:
        db.close()


def mark_all_read() -> int:
    """全部标为已读，返回实际更新条数。"""
    db = SessionLocal()
    try:
        result = db.execute(
            update(Reminder).where(Reminder.is_read.is_(False)).values(is_read=True)
        )
        db.commit()
        return int(result.rowcount or 0)
    finally:
        db.close()
