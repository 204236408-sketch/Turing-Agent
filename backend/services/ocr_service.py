import uuid
import os
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from config import settings
from utils.response import AppError


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp"}
ALLOWED_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
_OCR_ENGINE: Any = None


def _upload_path(filename: str) -> Path:
    suffix = Path(filename or "").suffix.lower() or ".png"
    if suffix not in ALLOWED_SUFFIXES:
        suffix = ".png"
    upload_dir = Path(settings.upload_dir) / "ocr_images"
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir / f"{uuid.uuid4().hex}{suffix}"


def _extract_paddle_text(result: Any) -> str:
    lines: list[str] = []
    pages = result if isinstance(result, list) else [result]
    for page in pages:
        if not page:
            continue
        if isinstance(page, dict):
            lines.extend(str(text) for text in page.get("rec_texts", []) if text)
            continue
        for item in page:
            if not item or len(item) < 2:
                continue
            text_info = item[1]
            if isinstance(text_info, (list, tuple)) and text_info:
                lines.append(str(text_info[0]))
    return "\n".join(line.strip() for line in lines if line and line.strip())


def _get_ocr_engine() -> Any:
    global _OCR_ENGINE
    if _OCR_ENGINE is None:
        os.environ.setdefault("FLAGS_use_mkldnn", "0")
        os.environ.setdefault("FLAGS_enable_pir_api", "0")
        from paddleocr import PaddleOCR  # type: ignore

        _OCR_ENGINE = PaddleOCR(
            lang="ch",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            enable_mkldnn=False,
        )
    return _OCR_ENGINE


def recognize_image(path: Path) -> dict[str, Any]:
    try:
        ocr = _get_ocr_engine()
        text = _extract_paddle_text(ocr.predict(str(path)))
        return {
            "recognized_text": text,
            "engine": "paddleocr",
            "ocr_available": True,
            "warning": "" if text else "PaddleOCR 未识别到可用文字，请手动校对或换一张更清晰的图片。",
        }
    except Exception as exc:
        return {
            "recognized_text": "后端 OCR 保底结果：图片已上传，请在此校对或补充题目文字后提交错题分析。",
            "engine": "backend-fallback-paddleocr",
            "ocr_available": False,
            "warning": f"PaddleOCR 暂不可用，已进入人工校对流程：{exc.__class__.__name__}: {exc}",
        }


async def save_and_recognize_upload(file: UploadFile) -> dict[str, Any]:
    content = await file.read()
    if not content:
        raise AppError("EMPTY_UPLOAD", "上传图片为空")
    suffix = Path(file.filename or "").suffix.lower()
    if file.content_type not in ALLOWED_IMAGE_TYPES and suffix not in ALLOWED_SUFFIXES:
        raise AppError("INVALID_UPLOAD_TYPE", "仅支持 PNG、JPG、WEBP、BMP 图片")

    path = _upload_path(file.filename or "ocr-image.png")
    path.write_bytes(content)

    try:
        from PIL import Image

        with Image.open(path) as image:
            image.verify()
    except Exception as exc:
        return {
            "filename": file.filename,
            "size": len(content),
            "stored_path": str(path),
            "upload_id": path.stem,
            "recognized_text": "图片文件已上传，但内容无法作为有效图片解码，请重新选择清晰的 PNG/JPG 图片。",
            "engine": "image-verify-failed",
            "ocr_available": False,
            "warning": f"图片解码失败：{exc.__class__.__name__}: {exc}",
        }

    recognized = recognize_image(path)
    return {
        "filename": file.filename,
        "size": len(content),
        "stored_path": str(path),
        "upload_id": path.stem,
        **recognized,
    }
