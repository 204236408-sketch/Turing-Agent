from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session
from agents.mistake_agent import analyze_ocr_text
from database import get_db
from dependencies import get_current_user
from schemas import OcrAnalyzeRequest
from services.ocr_service import save_and_recognize_upload
from models import User
from utils.response import success


router = APIRouter(prefix="/api/ocr", tags=["ocr"])


@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    return success(await save_and_recognize_upload(file))


@router.post("/analyze")
def analyze(payload: OcrAnalyzeRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    data = analyze_ocr_text(
        db,
        user.id,
        payload.text,
        payload.subject,
        payload.knowledge_point,
        payload.user_answer,
    )
    db.commit()
    return success(data)
