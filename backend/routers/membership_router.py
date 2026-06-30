from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models import User
from services.membership_service import (
    complete_payment_order,
    create_payment_order,
    list_plans,
    my_membership,
    payment_order_status,
)
from utils.response import AppError, success


router = APIRouter(prefix="/api/membership", tags=["membership"])


class SubscribeRequest(BaseModel):
    plan_id: int


class PaymentCreateRequest(BaseModel):
    plan_id: int
    agreed: bool = False


class PaymentCompleteRequest(BaseModel):
    order_no: str


@router.get("/plans")
def plans(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success({"items": list_plans(db)})


@router.post("/subscribe")
def subscribe(payload: SubscribeRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    raise AppError("PAYMENT_REQUIRED", "请先完成支付确认，支付成功后系统会自动开通会员", status_code=400)


@router.post("/payment/create")
def create_payment(payload: PaymentCreateRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(create_payment_order(db, user.id, payload.plan_id, payload.agreed))


@router.post("/payment/complete")
def complete_payment(payload: PaymentCompleteRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(complete_payment_order(db, user.id, payload.order_no))


@router.get("/payment/status/{order_no}")
def payment_status(order_no: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(payment_order_status(db, user.id, order_no))


@router.get("/my")
def my(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(my_membership(db, user.id))
