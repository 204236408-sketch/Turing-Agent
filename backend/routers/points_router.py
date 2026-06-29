from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models import User
from services.points_service import (
    POINT_RULES,
    account_overview,
    daily_checkin,
    earn_points,
    list_transactions,
    spend_points,
)
from utils.response import success


router = APIRouter(prefix="/api/points", tags=["points"])


class PointEarnRequest(BaseModel):
    action_type: str
    points: int | None = None
    target_type: str | None = None
    target_id: int | None = None


class PointSpendRequest(BaseModel):
    action_type: str
    base_cost: float | None = None
    target_type: str | None = None
    target_id: int | None = None


@router.get("/account")
def account(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(account_overview(db, user.id))


@router.get("/rules")
def rules():
    return success(POINT_RULES)


@router.post("/checkin")
def checkin(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(daily_checkin(db, user.id))


@router.post("/earn")
def earn(payload: PointEarnRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(
        earn_points(
            db,
            user.id,
            payload.action_type,
            payload.points,
            payload.target_type,
            payload.target_id,
        )
    )


@router.post("/spend")
def spend(payload: PointSpendRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(
        spend_points(
            db,
            user.id,
            payload.action_type,
            payload.base_cost,
            payload.target_type,
            payload.target_id,
        )
    )


@router.get("/transactions")
def transactions(
    transaction_type: str | None = Query(default="all"),
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return success({"items": list_transactions(db, user.id, transaction_type, limit)})
