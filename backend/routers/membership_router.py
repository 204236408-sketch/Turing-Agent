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
    subscribe_plan,
)
from utils.response import success


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
    return success(subscribe_plan(db, user.id, payload.plan_id))


@router.post("/payment/create")
def create_payment(payload: PaymentCreateRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(create_payment_order(db, user.id, payload.plan_id, payload.agreed))


@router.post("/payment/complete")
def complete_payment(payload: PaymentCompleteRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(complete_payment_order(db, user.id, payload.order_no))


@router.get("/my")
def my(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return success(my_membership(db, user.id))
