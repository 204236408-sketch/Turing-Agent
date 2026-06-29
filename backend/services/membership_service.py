from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from services.points_service import (
    account_overview,
    ensure_point_tables,
    get_active_membership,
    seed_membership_plans,
)
from utils.response import AppError


PLAN_DAYS = {
    "月度会员": 30,
    "学期会员": 90,
    "年度会员": 365,
}

PLAN_PRICE = {
    "月度会员": "12.9",
    "学期会员": "29.9",
    "年度会员": "99.9",
}

PLAN_DISPLAY_NAME = {
    "月度会员": "月度会员",
    "学期会员": "季度会员",
    "年度会员": "年度会员",
}

PLAN_PRICE_LABEL = {
    "月度会员": "12.9/月",
    "学期会员": "29.9/季",
    "年度会员": "99.9/年",
}


def _format_plan(row: dict[str, Any]) -> dict[str, Any]:
    plan = dict(row)
    plan["display_name"] = PLAN_DISPLAY_NAME.get(plan["name"], plan["name"])
    plan["price"] = PLAN_PRICE.get(plan["name"], "0")
    plan["price_label"] = PLAN_PRICE_LABEL.get(plan["name"], "")
    plan["duration_days"] = PLAN_DAYS.get(plan["name"], 0)
    return plan


def ensure_payment_table(db: Session) -> None:
    ensure_point_tables(db)
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS membership_payment_order (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_no VARCHAR(64) NOT NULL UNIQUE,
            user_id INTEGER NOT NULL,
            plan_id INTEGER NOT NULL,
            amount VARCHAR(20) NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            qr_payload TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            paid_at DATETIME
        )
    """))
    db.commit()


def list_plans(db: Session) -> list[dict[str, Any]]:
    seed_membership_plans(db)
    rows = db.execute(
        text("""
            SELECT id, name, daily_points, discount_rate, description
            FROM membership_plan
            ORDER BY daily_points ASC, id ASC
        """)
    ).mappings().all()
    return [_format_plan(dict(row)) for row in rows]


def create_payment_order(db: Session, user_id: int, plan_id: int, agreed: bool) -> dict[str, Any]:
    if not agreed:
        raise AppError("AGREEMENT_REQUIRED", "请先同意会员服务协议", status_code=400)
    ensure_payment_table(db)
    plan = db.execute(
        text("SELECT id, name, daily_points, discount_rate, description FROM membership_plan WHERE id = :id"),
        {"id": plan_id},
    ).mappings().first()
    if not plan or plan["name"] == "普通用户":
        raise AppError("PLAN_NOT_FOUND", "会员套餐不存在", status_code=404)
    plan_data = _format_plan(dict(plan))
    order_no = f"VIP{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{uuid4().hex[:8].upper()}"
    qr_payload = f"TRAE-MEMBER-PAY://order={order_no}&amount={plan_data['price']}&plan={plan_data['display_name']}"
    db.execute(
        text("""
            INSERT INTO membership_payment_order (order_no, user_id, plan_id, amount, status, qr_payload)
            VALUES (:order_no, :user_id, :plan_id, :amount, 'pending', :qr_payload)
        """),
        {
            "order_no": order_no,
            "user_id": user_id,
            "plan_id": plan_id,
            "amount": plan_data["price"],
            "qr_payload": qr_payload,
        },
    )
    db.commit()
    return {
        "order_no": order_no,
        "status": "pending",
        "amount": plan_data["price"],
        "price_label": plan_data["price_label"],
        "plan": plan_data,
        "qr_payload": qr_payload,
        "message": "订单已创建，请扫码支付",
    }


def complete_payment_order(db: Session, user_id: int, order_no: str) -> dict[str, Any]:
    ensure_payment_table(db)
    order = db.execute(
        text("""
            SELECT order_no, user_id, plan_id, amount, status
            FROM membership_payment_order
            WHERE order_no = :order_no AND user_id = :user_id
        """),
        {"order_no": order_no, "user_id": user_id},
    ).mappings().first()
    if not order:
        raise AppError("ORDER_NOT_FOUND", "支付订单不存在", status_code=404)
    if order["status"] == "paid":
        return {"paid": True, "order_no": order_no, "status": "paid", "overview": account_overview(db, user_id)}
    result = subscribe_plan(db, user_id, int(order["plan_id"]))
    db.execute(
        text("""
            UPDATE membership_payment_order
            SET status = 'paid', paid_at = CURRENT_TIMESTAMP
            WHERE order_no = :order_no AND user_id = :user_id
        """),
        {"order_no": order_no, "user_id": user_id},
    )
    db.commit()
    return {
        "paid": True,
        "order_no": order_no,
        "status": "paid",
        "membership": result.get("membership"),
        "overview": account_overview(db, user_id),
    }


def subscribe_plan(db: Session, user_id: int, plan_id: int) -> dict[str, Any]:
    seed_membership_plans(db)
    plan = db.execute(
        text("SELECT id, name, daily_points, discount_rate, description FROM membership_plan WHERE id = :id"),
        {"id": plan_id},
    ).mappings().first()
    if not plan:
        raise AppError("PLAN_NOT_FOUND", "会员套餐不存在", status_code=404)
    if plan["name"] == "普通用户":
        db.execute(
            text("UPDATE user_membership SET is_active = 0 WHERE user_id = :user_id AND is_active = 1"),
            {"user_id": user_id},
        )
        db.commit()
        return {"subscribed": True, "plan": dict(plan), "membership": None, "overview": account_overview(db, user_id)}

    start = datetime.utcnow()
    end = start + timedelta(days=PLAN_DAYS.get(plan["name"], 30))
    db.execute(
        text("UPDATE user_membership SET is_active = 0 WHERE user_id = :user_id AND is_active = 1"),
        {"user_id": user_id},
    )
    db.execute(
        text("""
            INSERT INTO user_membership (user_id, plan_id, start_at, end_at, is_active)
            VALUES (:user_id, :plan_id, :start_at, :end_at, 1)
        """),
        {
            "user_id": user_id,
            "plan_id": plan_id,
            "start_at": start.isoformat(sep=" ", timespec="seconds"),
            "end_at": end.isoformat(sep=" ", timespec="seconds"),
        },
    )
    db.commit()
    return {
        "subscribed": True,
        "plan": _format_plan(dict(plan)),
        "membership": get_active_membership(db, user_id),
        "overview": account_overview(db, user_id),
    }


def my_membership(db: Session, user_id: int) -> dict[str, Any]:
    ensure_point_tables(db)
    return {"membership": get_active_membership(db, user_id)}
