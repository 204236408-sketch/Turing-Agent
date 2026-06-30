from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from config import BASE_DIR


DATA_DIR = Path(BASE_DIR) / "data"


def _load_json(name: str, fallback: Any) -> Any:
    path = DATA_DIR / name
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8-sig"))


POINT_RULES: dict[str, dict[str, dict[str, Any]]] = _load_json(
    "seed_point_rules.json",
    {"earn": {}, "spend": {}},
)

PLAN_DISPLAY_NAMES = {
    "月度会员": "月度会员",
    "学期会员": "季度会员",
    "季度会员": "季度会员",
    "年度会员": "年度会员",
    "普通用户": "普通用户",
}


def _display_plan_name(name: str | None) -> str:
    raw = name or "普通用户"
    return PLAN_DISPLAY_NAMES.get(raw, raw)


def ensure_point_tables(db: Session) -> None:
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS user_point_account (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            balance INTEGER DEFAULT 0,
            total_earned INTEGER DEFAULT 0,
            total_spent INTEGER DEFAULT 0,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """))
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS point_transaction (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            transaction_type VARCHAR(20) NOT NULL,
            action_type VARCHAR(80) NOT NULL,
            points INTEGER NOT NULL,
            balance_after INTEGER NOT NULL,
            target_type VARCHAR(50),
            target_id INTEGER,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """))
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS membership_plan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(50) NOT NULL UNIQUE,
            daily_points INTEGER DEFAULT 0,
            discount_rate FLOAT DEFAULT 1.0,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """))
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS user_membership (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            plan_id INTEGER NOT NULL,
            start_at DATETIME,
            end_at DATETIME,
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """))
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS daily_checkin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            checkin_date DATE NOT NULL,
            points_awarded INTEGER DEFAULT 0,
            streak_days INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, checkin_date)
        )
    """))
    db.commit()


def seed_membership_plans(db: Session) -> None:
    ensure_point_tables(db)
    plans = _load_json("seed_membership_plans.json", [])
    for plan in plans:
        exists = db.execute(
            text("SELECT id FROM membership_plan WHERE name = :name"),
            {"name": plan["name"]},
        ).mappings().first()
        if exists:
            continue
        db.execute(
            text("""
                INSERT INTO membership_plan (name, daily_points, discount_rate, description)
                VALUES (:name, :daily_points, :discount_rate, :description)
            """),
            plan,
        )
    db.commit()


def get_or_create_account(db: Session, user_id: int) -> dict[str, Any]:
    ensure_point_tables(db)
    account = db.execute(
        text("SELECT * FROM user_point_account WHERE user_id = :user_id"),
        {"user_id": user_id},
    ).mappings().first()
    if not account:
        db.execute(
            text("INSERT INTO user_point_account (user_id, balance, total_earned, total_spent) VALUES (:user_id, 0, 0, 0)"),
            {"user_id": user_id},
        )
        db.commit()
        account = db.execute(
            text("SELECT * FROM user_point_account WHERE user_id = :user_id"),
            {"user_id": user_id},
        ).mappings().first()
    return dict(account)


def get_active_membership(db: Session, user_id: int) -> dict[str, Any] | None:
    seed_membership_plans(db)
    now = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    row = db.execute(
        text("""
            SELECT um.id AS membership_id, um.start_at, um.end_at, um.is_active,
                   mp.id AS plan_id, mp.name, mp.daily_points, mp.discount_rate, mp.description
            FROM user_membership um
            JOIN membership_plan mp ON mp.id = um.plan_id
            WHERE um.user_id = :user_id
              AND um.is_active = 1
              AND (um.end_at IS NULL OR um.end_at >= :now)
            ORDER BY um.id DESC
            LIMIT 1
        """),
        {"user_id": user_id, "now": now},
    ).mappings().first()
    if not row:
        return None
    membership = dict(row)
    membership["display_name"] = _display_plan_name(membership.get("name"))
    return membership


def earn_points(
    db: Session,
    user_id: int,
    action_type: str,
    points: int | None = None,
    target_type: str | None = None,
    target_id: int | None = None,
    transaction_type: str = "earn",
    description: str | None = None,
) -> dict[str, Any]:
    rule = POINT_RULES.get("earn", {}).get(action_type, {})
    final_points = int(points if points is not None else rule.get("points", 0))
    if final_points <= 0:
        return {"earned": 0, "balance": get_or_create_account(db, user_id)["balance"], "message": "积分规则未配置"}

    account = get_or_create_account(db, user_id)
    if target_type and target_id is not None:
        exists = db.execute(
            text("""
                SELECT id FROM point_transaction
                WHERE user_id = :user_id AND action_type = :action_type
                  AND target_type = :target_type AND target_id = :target_id
                LIMIT 1
            """),
            {"user_id": user_id, "action_type": action_type, "target_type": target_type, "target_id": target_id},
        ).first()
        if exists:
            return {"earned": 0, "balance": account["balance"], "message": "该行为已获得过积分"}

    balance = round(float(account["balance"]) + final_points, 1)
    db.execute(
        text("""
            UPDATE user_point_account
            SET balance = :balance,
                total_earned = total_earned + :points,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = :user_id
        """),
        {"balance": balance, "points": final_points, "user_id": user_id},
    )
    db.execute(
        text("""
            INSERT INTO point_transaction
                (user_id, transaction_type, action_type, points, balance_after, target_type, target_id, description)
            VALUES
                (:user_id, :transaction_type, :action_type, :points, :balance_after, :target_type, :target_id, :description)
        """),
        {
            "user_id": user_id,
            "transaction_type": transaction_type,
            "action_type": action_type,
            "points": final_points,
            "balance_after": balance,
            "target_type": target_type,
            "target_id": target_id,
            "description": description or rule.get("label", action_type),
        },
    )
    db.commit()
    return {"earned": final_points, "balance": balance}


def spend_points(
    db: Session,
    user_id: int,
    action_type: str,
    base_cost: float | None = None,
    target_type: str | None = None,
    target_id: int | None = None,
) -> dict[str, Any]:
    rule = POINT_RULES.get("spend", {}).get(action_type, {})
    cost = float(base_cost if base_cost is not None else rule.get("points", 0))
    account = get_or_create_account(db, user_id)
    membership = get_active_membership(db, user_id)
    discount = float(membership["discount_rate"]) if membership else 1.0
    final_cost = round(cost * discount, 1) if cost > 0 else 0
    membership_name = _display_plan_name(membership["name"]) if membership else "普通用户"
    feature_name = rule.get("label", action_type)
    balance_before = float(account["balance"])

    if balance_before < final_cost:
        return {
            "success": False,
            "action_type": action_type,
            "feature_name": feature_name,
            "need_points": final_cost,
            "balance": balance_before,
            "base_cost": cost,
            "discount_rate": discount,
            "final_cost": final_cost,
            "membership_name": membership_name,
            "message": f"积分不足，当前功能折扣后需要 {final_cost:g} 积分",
        }

    balance = round(balance_before - final_cost, 1)
    db.execute(
        text("""
            UPDATE user_point_account
            SET balance = :balance,
                total_spent = total_spent + :points,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = :user_id
        """),
        {"balance": balance, "points": final_cost, "user_id": user_id},
    )
    db.execute(
        text("""
            INSERT INTO point_transaction
                (user_id, transaction_type, action_type, points, balance_after, target_type, target_id, description)
            VALUES
                (:user_id, 'spend', :action_type, :points, :balance_after, :target_type, :target_id, :description)
        """),
        {
            "user_id": user_id,
            "action_type": action_type,
            "points": -final_cost,
            "balance_after": balance,
            "target_type": target_type,
            "target_id": target_id,
            "description": f"{feature_name}，{membership_name}折扣后消耗 {final_cost:g} 积分",
        },
    )
    db.commit()
    return {
        "success": True,
        "action_type": action_type,
        "feature_name": feature_name,
        "spent": final_cost,
        "balance": balance,
        "base_cost": cost,
        "discount_rate": discount,
        "final_cost": final_cost,
        "membership_name": membership_name,
    }


def daily_checkin(db: Session, user_id: int) -> dict[str, Any]:
    ensure_point_tables(db)
    today = date.today()
    today_str = today.isoformat()
    exists = db.execute(
        text("SELECT points_awarded, streak_days FROM daily_checkin WHERE user_id = :user_id AND checkin_date = :day"),
        {"user_id": user_id, "day": today_str},
    ).mappings().first()
    account = get_or_create_account(db, user_id)
    if exists:
        return {
            "success": False,
            "earned": 0,
            "balance": account["balance"],
            "streak_days": exists["streak_days"],
            "message": "今日已完成打卡",
        }

    yesterday = (today - timedelta(days=1)).isoformat()
    prev = db.execute(
        text("SELECT streak_days FROM daily_checkin WHERE user_id = :user_id AND checkin_date = :day"),
        {"user_id": user_id, "day": yesterday},
    ).mappings().first()
    streak = int(prev["streak_days"]) + 1 if prev else 1
    points = 10
    bonus = []
    if streak == 3:
        points += 20
        bonus.append("连续打卡 3 天奖励 +20")
    if streak == 7:
        points += 50
        bonus.append("连续打卡 7 天奖励 +50")

    db.execute(
        text("""
            INSERT INTO daily_checkin (user_id, checkin_date, points_awarded, streak_days)
            VALUES (:user_id, :day, :points, :streak)
        """),
        {"user_id": user_id, "day": today_str, "points": points, "streak": streak},
    )
    db.commit()
    result = earn_points(
        db,
        user_id,
        "daily_checkin",
        points,
        target_type="daily_checkin",
        target_id=int(today.strftime("%Y%m%d")),
        description="每日登录打卡" + (f"（{'，'.join(bonus)}）" if bonus else ""),
    )
    return {"success": True, "earned": result["earned"], "balance": result["balance"], "streak_days": streak, "bonus": bonus}


def grant_daily_membership_points(db: Session, user_id: int) -> dict[str, Any]:
    membership = get_active_membership(db, user_id)
    if not membership or int(membership["daily_points"] or 0) <= 0:
        return {"granted": 0}
    day_id = int(date.today().strftime("%Y%m%d"))
    return earn_points(
        db,
        user_id,
        "membership_daily_grant",
        int(membership["daily_points"]),
        target_type="membership_daily",
        target_id=day_id,
        transaction_type="grant",
        description=f"{_display_plan_name(membership['name'])}每日赠送积分",
    )


def _safe_scalar(db: Session, sql: str, params: dict[str, Any]) -> int:
    try:
        value = db.execute(text(sql), params).scalar()
        return int(value or 0)
    except Exception:
        db.rollback()
        return 0


def _achievement_stats(db: Session, user_id: int, streak_days: int, total_earned: int) -> dict[str, Any]:
    mistake_fixed_count = _safe_scalar(
        db,
        "SELECT COUNT(*) FROM mistake WHERE user_id = :user_id AND is_deleted = 0 AND is_reviewed = 1",
        {"user_id": user_id},
    )
    mastered_count = _safe_scalar(
        db,
        "SELECT COALESCE(SUM(mastered_count), 0) FROM knowledge_mastery WHERE user_id = :user_id",
        {"user_id": user_id},
    )
    qa_count = _safe_scalar(
        db,
        "SELECT COALESCE(SUM(qa_count), 0) FROM knowledge_mastery WHERE user_id = :user_id",
        {"user_id": user_id},
    )
    note_count = _safe_scalar(
        db,
        "SELECT COUNT(*) FROM note WHERE user_id = :user_id",
        {"user_id": user_id},
    )
    today = date.today().isoformat()
    module_medals = [
        {"name": "连续学习者", "type": "streak", "current": streak_days, "target": 7, "rule": "连续打卡 7 天获得"},
        {"name": "错题终结者", "type": "mistake", "current": mistake_fixed_count, "target": 20, "rule": "错题本订正 20 题获得"},
        {"name": "知识探索者", "type": "mastery", "current": mastered_count, "target": 30, "rule": "知识图谱掌握 30 个知识点获得"},
        {"name": "AI提问官", "type": "qa", "current": qa_count, "target": 50, "rule": "智能问答提问 50 次获得"},
        {"name": "笔记达人", "type": "note", "current": note_count, "target": 20, "rule": "知识点导航添加 20 条学习笔记获得"},
    ]
    point_medals = [
        {"name": "青铜", "type": "point_bronze", "current": total_earned, "target": 100, "rule": "累计获得 100 积分"},
        {"name": "白银", "type": "point_silver", "current": total_earned, "target": 500, "rule": "累计获得 500 积分"},
        {"name": "黄金", "type": "point_gold", "current": total_earned, "target": 1500, "rule": "累计获得 1500 积分"},
        {"name": "钻石", "type": "point_diamond", "current": total_earned, "target": 5000, "rule": "累计获得 5000 积分"},
        {"name": "图灵之光", "type": "point_turing", "current": total_earned, "target": 10000, "rule": "累计获得 10000 积分"},
    ]
    for item in module_medals + point_medals:
        item["unlocked"] = int(item["current"]) >= int(item["target"])
        item["achieved_at"] = today if item["unlocked"] else None
    return {
        "mistake_fixed_count": mistake_fixed_count,
        "mastered_count": mastered_count,
        "qa_count": qa_count,
        "note_count": note_count,
        "medals": {
            "module": module_medals,
            "points": point_medals,
        },
    }


def account_overview(db: Session, user_id: int) -> dict[str, Any]:
    grant_daily_membership_points(db, user_id)
    account = get_or_create_account(db, user_id)
    membership = get_active_membership(db, user_id)
    checked = db.execute(
        text("SELECT streak_days FROM daily_checkin WHERE user_id = :user_id AND checkin_date = :day"),
        {"user_id": user_id, "day": date.today().isoformat()},
    ).mappings().first()
    streak_days = int(checked["streak_days"]) if checked else 0
    total_earned = int(account["total_earned"])
    stats = _achievement_stats(db, user_id, streak_days, total_earned)
    return {
        "account": {
            "balance": round(float(account["balance"]), 1),
            "total_earned": total_earned,
            "total_spent": round(float(account["total_spent"]), 1),
        },
        "today_checkin": bool(checked),
        "streak_days": streak_days,
        "mistake_fixed_count": stats["mistake_fixed_count"],
        "mastered_count": stats["mastered_count"],
        "qa_count": stats["qa_count"],
        "note_count": stats["note_count"],
        "medals": stats["medals"],
        "membership": membership or {
            "name": "普通用户",
            "display_name": "普通用户",
            "daily_points": 0,
            "discount_rate": 1.0,
            "description": "基础功能",
        },
        "rules": POINT_RULES,
    }


def list_transactions(db: Session, user_id: int, transaction_type: str | None = None, limit: int = 30) -> list[dict[str, Any]]:
    ensure_point_tables(db)
    params: dict[str, Any] = {"user_id": user_id, "limit": max(1, min(limit, 100))}
    condition = "WHERE user_id = :user_id"
    if transaction_type and transaction_type != "all":
        condition += " AND transaction_type = :transaction_type"
        params["transaction_type"] = transaction_type
    rows = db.execute(
        text(f"""
            SELECT id, transaction_type, action_type, points, balance_after, target_type, target_id, description, created_at
            FROM point_transaction
            {condition}
            ORDER BY id DESC
            LIMIT :limit
        """),
        params,
    ).mappings().all()
    return [dict(row) for row in rows]
