"""OCR 识别接口：上传、识别、反推用户答案、分析。

状态机：
- POST /api/ocr/upload      — 上传图片 → 后端多引擎 OCR + LLM 后处理 → 返回识别文本+行级置信度
- POST /api/ocr/guess       — 基于 OCR 文本反推用户可能的作答（用于前端"你的答案"预填）
- POST /api/ocr/analyze     — 提交错题分析（OCR 文本 + 用户答案 + 低置信度行 → Agent 推断标准答案 + 错因）
"""
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from agents.mistake_agent import analyze_ocr_text, infer_user_answer_from_ocr
from database import get_db
from dependencies import get_current_user
from schemas import OcrAnalyzeRequest, OcrGuessUserAnswerRequest
from services.ocr_service import save_and_recognize_upload
from models import User
from utils.response import success


router = APIRouter(prefix="/api/ocr", tags=["ocr"])


@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        result = await save_and_recognize_upload(file)
        return success(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR 识别失败：{str(e)}")


@router.post("/guess")
def guess_user_answer(
    payload: OcrGuessUserAnswerRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """基于 OCR 文本反推用户可能的作答（前端"你的答案"输入框预填用）。"""
    try:
        data = infer_user_answer_from_ocr(
            db,
            user.id,
            payload.text,
            payload.subject,
            payload.knowledge_point,
        )
        return success(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"反推用户答案失败：{str(e)}")


@router.post("/analyze")
def analyze(
    payload: OcrAnalyzeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        data = analyze_ocr_text(
            db,
            user.id,
            payload.text,
            payload.subject,
            payload.knowledge_point,
            payload.user_answer,
            payload.low_confidence_lines or [],
        )
        db.commit()
        return success(data)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"OCR 分析失败：{str(e)}")
