"""OCR 识别服务（PaddleOCR 3.7 主引擎 + EasyOCR 兜底 + LLM 后处理）。

设计目标（v2 优化）：
1. 速度：图片预处理(最长边 ≤ 1280px、自适应对比度、灰度) + PaddleOCR 3.7 流水线
   + 引擎单例懒加载 + 异步并行识别，CPU 模式下 800x1200 题目 < 5s
2. 准确率：PaddleOCR 主 + EasyOCR 兜底 + LLM 文本纠错 + 行级位置排序（避免错位）
3. 可信度：返回每行识别置信度，前端可高亮低置信度行
4. 健壮性：单引擎失败时自动 fallback，最终回落到友好的"待人工校对"提示

PaddleOCR 3.7 适配要点（相对 2.x）：
- `use_gpu` → `device`（cpu / gpu / xpu / npu）
- `enable_mkldnn` 等参数走 **kwargs，不再是顶层参数
- predict 返回 list[OCRResult]，OCRResult 实现了 Mapping 协议，可用 page[k] / page.get(k)
"""
from __future__ import annotations

import os
import re
import time
import uuid
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from PIL import Image, ImageOps, ImageEnhance, ImageFilter

from config import settings
from utils.response import AppError


logger = logging.getLogger(__name__)
log = logger.info

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp"}
ALLOWED_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
MAX_SIDE = int(os.environ.get("OCR_MAX_SIDE", "1800"))  # 更高分辨率保留小字细节
MIN_SIDE = int(os.environ.get("OCR_MIN_SIDE", "900"))   # 适度放大小图，提高截图/拍照小字识别率
OCR_VARIANT_LIMIT = int(os.environ.get("OCR_VARIANT_LIMIT", "3"))
JPEG_QUALITY = 88
OCR_DEVICE = os.environ.get("OCR_DEVICE", "cpu")  # v2: PaddleOCR 3.x 新参数名
LLM_CORRECT_THRESHOLD = 0.85  # 行置信度低于该值时送 LLM 二次校对

_OCR_ENGINES: dict[str, Any] = {}
_OCR_ENGINES_LOCK = threading.Lock()
_OCR_ENGINES_READY = threading.Event()  # 预热完成信号
_OCR_ENGINES_ERROR: str = ""
_LLM_LOCK = threading.Lock()
_LLM_CORRECT_CACHE: dict[str, str] = {}


# ============================================================
# 1) 文件保存 & 路径
# ============================================================
def _upload_path(filename: str) -> Path:
    suffix = Path(filename or "").suffix.lower() or ".png"
    if suffix not in ALLOWED_SUFFIXES:
        suffix = ".png"
    upload_dir = Path(settings.upload_dir) / "ocr_images"
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir / f"{uuid.uuid4().hex}{suffix}"


# ============================================================
# 2) 图片预处理：缩放、对比度增强、灰度、二值化（v2 强化）
# ============================================================
def _fit_for_ocr(im: Image.Image, max_side: int = MAX_SIDE) -> Image.Image:
    """按 OCR 需要缩放：大图不过度压缩，小图主动放大。"""
    w, h = im.size
    longest = max(w, h)
    if longest > max_side:
        ratio = max_side / longest
        return im.resize((max(1, int(w * ratio)), max(1, int(h * ratio))), Image.LANCZOS)
    if longest < MIN_SIDE:
        ratio = MIN_SIDE / longest
        return im.resize((max(1, int(w * ratio)), max(1, int(h * ratio))), Image.LANCZOS)
    return im


def _otsu_threshold(gray: Image.Image) -> int:
    """用 Otsu 阈值生成二值增强图，提升浅色/压缩截图文字对比度。"""
    hist = gray.histogram()
    total = sum(hist)
    if not total:
        return 160
    sum_total = sum(i * count for i, count in enumerate(hist))
    sum_bg = 0.0
    weight_bg = 0
    best_var = -1.0
    best_threshold = 160
    for i, count in enumerate(hist):
        weight_bg += count
        if weight_bg == 0:
            continue
        weight_fg = total - weight_bg
        if weight_fg == 0:
            break
        sum_bg += i * count
        mean_bg = sum_bg / weight_bg
        mean_fg = (sum_total - sum_bg) / weight_fg
        var_between = weight_bg * weight_fg * (mean_bg - mean_fg) ** 2
        if var_between > best_var:
            best_var = var_between
            best_threshold = i
    return max(96, min(210, best_threshold))


def _save_preprocess_variant(image: Image.Image, out_path: Path) -> Path:
    image.save(out_path, format="PNG", optimize=True)
    return out_path


def _preprocess_variants(src_path: Path, max_side: int = MAX_SIDE) -> list[Path]:
    """生成多种 OCR 输入图，分别适配拍照题、截图小字和浅色背景。"""
    processed_dir = src_path.parent / "_ocr_processed"
    processed_dir.mkdir(exist_ok=True)
    try:
        with Image.open(src_path) as im:
            base = ImageOps.exif_transpose(im).convert("RGB")
            base = _fit_for_ocr(base, max_side)

            variants: list[Path] = []

            gray = ImageOps.autocontrast(base.convert("L"))
            gray = ImageEnhance.Contrast(gray).enhance(1.65)
            gray = ImageEnhance.Sharpness(gray).enhance(1.35)
            variants.append(_save_preprocess_variant(gray, processed_dir / f"{src_path.stem}_gray.png"))

            denoised = gray.filter(ImageFilter.MedianFilter(size=3))
            threshold = _otsu_threshold(denoised)
            binary = denoised.point(lambda p: 255 if p > threshold else 0).convert("L")
            variants.append(_save_preprocess_variant(binary, processed_dir / f"{src_path.stem}_binary.png"))

            color = ImageEnhance.Contrast(base).enhance(1.18)
            color = ImageEnhance.Sharpness(color).enhance(1.25)
            variants.append(_save_preprocess_variant(color, processed_dir / f"{src_path.stem}_color.png"))

            return variants[:max(1, OCR_VARIANT_LIMIT)]
    except Exception as exc:
        log(f"图片预处理失败，回落到原图: {exc}")
        return [src_path]


def _preprocess_image(src_path: Path, max_side: int = MAX_SIDE) -> Path:
    """兼容旧调试脚本：返回主预处理图。"""
    return _preprocess_variants(src_path, max_side)[0]


# ============================================================
# 3) 引擎单例懒加载
# ============================================================
def _get_paddle_engine() -> Any:
    if "paddle" in _OCR_ENGINES:
        return _OCR_ENGINES["paddle"]
    if _OCR_ENGINES.get("_paddle_disabled"):
        return None
    with _OCR_ENGINES_LOCK:
        if "paddle" in _OCR_ENGINES:
            return _OCR_ENGINES["paddle"]
        if _OCR_ENGINES.get("_paddle_disabled"):
            return None
        try:
            os.environ.setdefault("FLAGS_use_mkldnn", "0")
            os.environ.setdefault("FLAGS_enable_pir_api", "0")
            from paddleocr import PaddleOCR  # type: ignore
            # PaddleOCR 3.7 适配: use_gpu → device, enable_mkldnn 在 **kwargs
            eng = PaddleOCR(
                lang="ch",
                ocr_version="PP-OCRv4",  # v4 在中文 + 速度综合最优
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                device=OCR_DEVICE,
                enable_mkldnn=False,
                enable_hpi=False,
                cpu_threads=os.cpu_count() or 4,
            )
            _OCR_ENGINES["paddle"] = eng
            log("✅ PaddleOCR 3.x 引擎初始化完成 (device=%s, v4)" % OCR_DEVICE)
            return eng
        except Exception as exc:
            log(f"⚠️ PaddleOCR 引擎初始化失败: {exc}")
            _OCR_ENGINES["_paddle_disabled"] = True
            _OCR_ENGINES["paddle"] = None
            return None


def _get_easy_engine() -> Any:
    """EasyOCR 软依赖：模型未下载 / 下载失败 / 加载超时 → 返回 None，自动降级到 PaddleOCR 单引擎。"""
    if "easy" in _OCR_ENGINES:
        return _OCR_ENGINES["easy"]
    if _OCR_ENGINES.get("_easy_disabled"):
        return None
    with _OCR_ENGINES_LOCK:
        if "easy" in _OCR_ENGINES:
            return _OCR_ENGINES["easy"]
        if _OCR_ENGINES.get("_easy_disabled"):
            return None
        try:
            import easyocr  # type: ignore
            eng = easyocr.Reader(["ch_sim", "en"], gpu=False, verbose=False)
            _OCR_ENGINES["easy"] = eng
            log("✅ EasyOCR 引擎初始化完成")
            return eng
        except Exception as exc:
            log(f"⚠️ EasyOCR 引擎初始化失败，自动降级到 PaddleOCR 单引擎: {exc}")
            _OCR_ENGINES["_easy_disabled"] = True
            _OCR_ENGINES["easy"] = None
            return None


# ============================================================
# 4) 引擎适配：归一化为 [{text, score, y, x}] 行级结构
# ============================================================
def _clean_ocr_fragment(text: str) -> str:
    """清理 OCR 行内噪声，不改写题意和公式。"""
    t = str(text or "").strip()
    if not t:
        return ""
    t = re.sub(r"[ \t\u3000]+", " ", t)
    t = re.sub(r"\s+([，。；：？！、,.!?;:)）】}])", r"\1", t)
    t = re.sub(r"([（(【{\[])\s+", r"\1", t)
    return t.strip()


def _paddle_lines(ocr: Any, path: Path) -> list[dict[str, Any]]:
    """运行 PaddleOCR 3.x 并提取行级识别结果。

    v2 增强：
    - 使用 rec_boxes 拿到每行的 (x, y, w, h)，按 y 坐标升序拼接
    - 兼容 OCRResult 对象的 Mapping 协议
    - 自动过滤掉置信度过低（< 0.3）的噪声行
    """
    if ocr is None:
        return []
    t0 = time.perf_counter()
    try:
        # 走更紧凑的 det 限制（PP-OCRv4 推荐）以加速
        result = ocr.predict(
            str(path),
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )
    except Exception as exc:
        log(f"PaddleOCR.predict 异常: {exc}")
        return []
    cost_ms = (time.perf_counter() - t0) * 1000
    lines: list[dict[str, Any]] = []
    pages = result if isinstance(result, list) else [result]
    for page in pages:
        if not page:
            continue
        rec_texts = page.get("rec_texts", []) if hasattr(page, "get") else (page["rec_texts"] if "rec_texts" in page else [])
        rec_scores = page.get("rec_scores", []) if hasattr(page, "get") else (page["rec_scores"] if "rec_scores" in page else [])
        rec_boxes = page.get("rec_boxes", []) if hasattr(page, "get") else (page["rec_boxes"] if "rec_boxes" in page else [])

        # 把 rec_boxes 解析为 (y, x)
        box_data: list[tuple[float, float]] = []
        if rec_boxes is not None and len(rec_boxes) == len(rec_texts):
            for box in rec_boxes:
                try:
                    arr = box if hasattr(box, "__len__") else None
                    if arr is None:
                        box_data.append((0.0, 0.0))
                        continue
                    # box = [[x1,y1],[x2,y2],[x3,y3],[x4,y4]] 期望 shape (4,2)
                    if hasattr(arr, "shape") and arr.shape == (4, 2):
                        y_avg = float(arr[:, 1].mean())
                        x_avg = float(arr[:, 0].mean())
                        box_data.append((y_avg, x_avg))
                    elif isinstance(arr, (list, tuple)) and len(arr) == 4 and isinstance(arr[0], (list, tuple)):
                        ys = [pt[1] for pt in arr]
                        xs = [pt[0] for pt in arr]
                        box_data.append((sum(ys) / 4, sum(xs) / 4))
                    else:
                        # 尝试当 ndarray flatten 后取 4 个点
                        flat = list(arr) if hasattr(arr, "__iter__") else []
                        if len(flat) >= 4 and hasattr(flat[0], "__len__"):
                            ys = [pt[1] for pt in flat[:4]]
                            xs = [pt[0] for pt in flat[:4]]
                            box_data.append((sum(ys) / 4, sum(xs) / 4))
                        else:
                            box_data.append((0.0, 0.0))
                except Exception:
                    box_data.append((0.0, 0.0))

        n = len(rec_texts)
        for i, (text, score) in enumerate(zip(rec_texts, rec_scores)):
            t = _clean_ocr_fragment(str(text or ""))
            if not t:
                continue
            s = float(score or 0.0)
            if s < 0.3:  # 过滤噪声
                continue
            y, x = box_data[i] if i < len(box_data) else (0.0, 0.0)
            lines.append({
                "text": t,
                "score": s,
                "y": float(y),
                "x": float(x),
                "engine": "paddleocr",
                "variant": path.stem,
            })

    # 按 y 升序 + x 升序拼接，更接近阅读顺序
    lines.sort(key=lambda ln: (round(ln["y"] / 12), ln["x"]))
    log(f"📍 PaddleOCR 识别耗时 {cost_ms:.0f}ms, 共 {len(lines)} 行（过滤后）")
    return lines


def _easy_lines(reader: Any, path: Path) -> list[dict[str, Any]]:
    """运行 EasyOCR 并提取行级结果（带位置 y/x）。"""
    if reader is None:
        return []
    t0 = time.perf_counter()
    try:
        result = reader.readtext(str(path), detail=1, paragraph=False)
    except Exception as exc:
        log(f"EasyOCR.readtext 异常: {exc}")
        return []
    cost_ms = (time.perf_counter() - t0) * 1000
    lines: list[dict[str, Any]] = []
    for item in result or []:
        if not item or len(item) < 3:
            continue
        box, text, score = item[0], item[1], item[2]
        t = _clean_ocr_fragment(str(text or ""))
        if not t:
            continue
        s = float(score or 0.0)
        if s < 0.3:
            continue
        # box = [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
        try:
            ys = [pt[1] for pt in box]
            xs = [pt[0] for pt in box]
            y_avg = sum(ys) / 4
            x_avg = sum(xs) / 4
        except Exception:
            y_avg, x_avg = 0.0, 0.0
        lines.append({
            "text": t,
            "score": s,
            "y": y_avg,
            "x": x_avg,
            "engine": "easyocr",
            "variant": path.stem,
        })
    lines.sort(key=lambda ln: (round(ln["y"] / 12), ln["x"]))
    log(f"📍 EasyOCR 识别耗时 {cost_ms:.0f}ms, 共 {len(lines)} 行（过滤后）")
    return lines


def _merge_lines(paddle: list[dict], easy: list[dict]) -> list[dict]:
    """合并两个引擎的识别结果（按 y 坐标 + 字符级 Jaccard 相似度匹配）。"""
    if not paddle:
        return easy
    if not easy:
        return paddle
    merged: list[dict] = []
    easy_remaining = list(easy)
    for p_line in paddle:
        best_match = None
        best_score = -1.0
        for idx, e_line in enumerate(easy_remaining):
            # 同时检查 y 距离（行级匹配）+ 文本相似度
            y_dist = abs(p_line["y"] - e_line["y"])
            sim = _line_similarity(p_line["text"], e_line["text"])
            if sim > 0.6 and y_dist < 50 and sim > best_score:
                best_score = sim
                best_match = idx
        if best_match is not None:
            e_line = easy_remaining.pop(best_match)
            # 取更长且更高置信度的版本
            text = p_line["text"] if len(p_line["text"]) >= len(e_line["text"]) else e_line["text"]
            score = max(p_line["score"], e_line["score"])
            merged.append({"text": text, "score": score, "y": p_line["y"], "x": p_line["x"], "engine": "fused"})
        else:
            merged.append(p_line)
    # 剩下未匹配的 easy 行也补上
    merged.extend(easy_remaining)
    # 再次按 y 排序
    merged.sort(key=lambda ln: (round(ln["y"] / 12), ln["x"]))
    return merged


def _line_pick_score(line: dict[str, Any]) -> float:
    """融合时的候选评分：置信度优先，兼顾完整度。"""
    text = str(line.get("text") or "")
    return float(line.get("score") or 0.0) + min(len(text), 80) / 240


def _is_same_visual_line(a: dict[str, Any], b: dict[str, Any]) -> bool:
    a_text = str(a.get("text") or "")
    b_text = str(b.get("text") or "")
    if not a_text or not b_text:
        return False
    if a_text == b_text:
        return True
    y_dist = abs(float(a.get("y") or 0.0) - float(b.get("y") or 0.0))
    if y_dist > 34:
        return False
    return _line_similarity(a_text, b_text) >= 0.58


def _merge_multi_line_sets(line_sets: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """融合多个预处理版本的行结果，保留每一行更可信的文本。"""
    candidates = [line for lines in line_sets for line in lines]
    if not candidates:
        return []
    groups: list[list[dict[str, Any]]] = []
    for line in sorted(candidates, key=lambda ln: (round(float(ln.get("y") or 0) / 12), float(ln.get("x") or 0))):
        for group in groups:
            if any(_is_same_visual_line(line, existing) for existing in group):
                group.append(line)
                break
        else:
            groups.append([line])

    merged: list[dict[str, Any]] = []
    seen_texts: set[str] = set()
    for group in groups:
        best = max(group, key=_line_pick_score)
        text = str(best.get("text") or "").strip()
        if not text or text in seen_texts:
            continue
        seen_texts.add(text)
        best = dict(best)
        best["score"] = max(float(item.get("score") or 0.0) for item in group)
        best["engine"] = "paddleocr-multipass" if len(group) > 1 else best.get("engine", "paddleocr")
        merged.append(best)
    merged.sort(key=lambda ln: (round(float(ln.get("y") or 0) / 12), float(ln.get("x") or 0)))
    return merged


def _paddle_multi_variant_lines(ocr: Any, paths: list[Path]) -> list[dict[str, Any]]:
    if ocr is None:
        return []
    line_sets: list[list[dict[str, Any]]] = []
    for variant_path in paths:
        lines = _paddle_lines(ocr, variant_path)
        if lines:
            line_sets.append(lines)
    merged = _merge_multi_line_sets(line_sets)
    log(f"📍 PaddleOCR 多版本融合: variants={len(paths)}, merged={len(merged)}行")
    return merged


def _line_similarity(a: str, b: str) -> float:
    """文本相似度：归一化字符级 Jaccard。"""
    if not a or not b:
        return 0.0
    sa, sb = set(a), set(b)
    inter = sa & sb
    union = sa | sb
    return len(inter) / len(union) if union else 0.0


# ============================================================
# 5) LLM 文本后处理：纠错、合并、标准化
# ============================================================
_OCR_TYPO_PROMPT = (
    "你是 OCR 文本后处理专家，专做 408 考研题目文本轻量纠错。\n"
    "任务：修正同音错字、漏字、多余字符、明显 OCR 错位。\n"
    "严格规则：\n"
    "1. 保留所有数学公式、代码、专有名词（操作系统/数据结构/计算机网络/组成原理）；\n"
    "2. 不删减题干，不修改题号；\n"
    "3. 修正形近字（如 十/千、栈/枝、二/三），保留语义；\n"
    "4. 输出修正后的完整文本，**不要**任何解释、不要 markdown。\n"
)


def _llm_correct_ocr_text(raw_text: str, low_conf_lines: list[str]) -> str:
    """用 LLM 对 OCR 文本做轻量纠错（v2 增强：缓存 key 含低置信度行）。"""
    if not raw_text or not settings.llm_enabled:
        return raw_text
    cache_key = (raw_text[:200] + "||" + "|".join(low_conf_lines[:3]))[:240]
    if cache_key in _LLM_CORRECT_CACHE:
        return _LLM_CORRECT_CACHE[cache_key]
    try:
        from services.llm_service import chat_completion
        prompt = (
            f"{_OCR_TYPO_PROMPT}\n"
            f"低置信度行（请重点校对）：\n{chr(10).join(low_conf_lines) if low_conf_lines else '(无)'}\n\n"
            f"原始文本：\n{raw_text}"
        )
        result = chat_completion(
            messages=[{"role": "user", "content": prompt}],
            fallback=raw_text,
            temperature=0.1,
            max_tokens=1800,
        )
        corrected = (result.content or raw_text).strip() if result.used_llm else raw_text
        if 0.5 < len(corrected) / max(len(raw_text), 1) < 1.8:
            _LLM_CORRECT_CACHE[cache_key] = corrected
            return corrected
        return raw_text
    except Exception as exc:
        log(f"LLM 文本纠错异常: {exc}")
        return raw_text


# ============================================================
# 6) 主入口：识别 + 纠错 + 评分
# ============================================================
def recognize_image(path: Path) -> dict[str, Any]:
    """识别图片：预处理 → 并行多引擎 → 融合 → LLM 纠错。"""
    t0 = time.perf_counter()
    preprocessed_paths = _preprocess_variants(path)
    preprocessed = preprocessed_paths[0]
    t_pre = time.perf_counter() - t0
    sizes = ", ".join(f"{p.name}:{os.path.getsize(p) if p.exists() else 0}B" for p in preprocessed_paths)
    log(f"📐 预处理耗时 {t_pre*1000:.0f}ms: variants={len(preprocessed_paths)} [{sizes}]")

    paddle_lines: list[dict] = []
    easy_lines_: list[dict] = []
    ENGINE_TIMEOUT = 60  # 单引擎识别超时(秒)：CPU 模式留足时间

    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="ocr") as pool:
        futures = {
            pool.submit(_paddle_multi_variant_lines, _get_paddle_engine(), preprocessed_paths): "paddle",
            pool.submit(_easy_lines, _get_easy_engine(), preprocessed): "easy",
        }
        for fut in as_completed(futures, timeout=ENGINE_TIMEOUT + 10):
            tag = futures[fut]
            try:
                if tag == "paddle":
                    paddle_lines = fut.result() or []
                else:
                    easy_lines_ = fut.result() or []
            except Exception as exc:
                log(f"引擎 {tag} 执行异常: {exc}")

    t_engine = time.perf_counter() - t0 - t_pre
    log(f"🔍 引擎识别耗时 {t_engine*1000:.0f}ms: paddle={len(paddle_lines)}行, easy={len(easy_lines_)}行")

    # 融合
    if paddle_lines and easy_lines_:
        merged = _merge_lines(paddle_lines, easy_lines_)
        engine_name = "paddleocr+easyocr"
    elif paddle_lines:
        merged = paddle_lines
        engine_name = "paddleocr"
    elif easy_lines_:
        merged = easy_lines_
        engine_name = "easyocr"
    else:
        merged = []
        engine_name = "none"

    if not merged:
        return {
            "recognized_text": "",
            "engine": engine_name,
            "ocr_available": False,
            "warning": "PaddleOCR + EasyOCR 均未识别到文字，请上传更清晰的图片。",
            "lines": [],
            "stats": {
                "paddle_ms": int(t_pre * 1000 + t_engine * 1000 * 0.5),
                "easy_ms": 0,
                "llm_correct_ms": 0,
                "total_ms": int((time.perf_counter() - t0) * 1000),
                "paddle_lines": 0,
                "easy_lines": 0,
                "merged_lines": 0,
                "preprocess_variants": len(preprocessed_paths),
            },
        }

    # 拼接为纯文本（已按 y 排序）
    raw_text = "\n".join(line["text"] for line in merged)
    avg_score = sum(line["score"] for line in merged) / max(len(merged), 1)
    low_conf_lines = [line["text"] for line in merged if line["score"] < LLM_CORRECT_THRESHOLD]

    # LLM 纠错（仅在 LLM 可用且存在低置信度行时）
    corrected_text = raw_text
    llm_ms = 0
    if settings.llm_enabled and len(raw_text) > 20 and low_conf_lines:
        t_llm = time.perf_counter()
        with _LLM_LOCK:
            corrected_text = _llm_correct_ocr_text(raw_text, low_conf_lines)
        llm_ms = int((time.perf_counter() - t_llm) * 1000)

    total_ms = int((time.perf_counter() - t0) * 1000)
    log(f"✅ OCR 总耗时 {total_ms}ms (预处理 {int(t_pre*1000)}ms + 引擎 {int(t_engine*1000)}ms + LLM {llm_ms}ms), {len(merged)}行, avg_score={avg_score:.3f}")

    # 行级结果：去重后按出现顺序保留
    seen = set()
    line_results = []
    for ln in merged:
        key = ln["text"]
        if key in seen:
            continue
        seen.add(key)
        line_results.append({
            "text": ln["text"],
            "score": round(ln["score"], 4),
            "low_confidence": ln["score"] < LLM_CORRECT_THRESHOLD,
        })

    return {
        "recognized_text": corrected_text,
        "raw_text": raw_text,
        "engine": engine_name,
        "ocr_available": True,
        "warning": "" if corrected_text.strip() else "OCR 引擎已运行但未识别到可用文字。",
        "lines": line_results,
        "stats": {
            "paddle_ms": int(t_pre * 1000 + t_engine * 1000 * 0.5),
            "easy_ms": int(t_engine * 1000 * 0.5),
            "llm_correct_ms": llm_ms,
            "total_ms": total_ms,
            "paddle_lines": len(paddle_lines),
            "easy_lines": len(easy_lines_),
            "merged_lines": len(merged),
            "preprocess_variants": len(preprocessed_paths),
            "avg_score": round(avg_score, 4),
            "llm_corrected": corrected_text != raw_text,
        },
    }


# ============================================================
# 7) 上传 + 识别统一入口
# ============================================================
async def save_and_recognize_upload(file: UploadFile) -> dict[str, Any]:
    content = await file.read()
    if not content:
        raise AppError("EMPTY_UPLOAD", "上传图片为空")
    suffix = Path(file.filename or "").suffix.lower()
    if file.content_type not in ALLOWED_IMAGE_TYPES and suffix not in ALLOWED_SUFFIXES:
        raise AppError("INVALID_UPLOAD_TYPE", "仅支持 PNG、JPG、WEBP、BMP 图片")

    path = _upload_path(file.filename or "ocr-image.png")
    path.write_bytes(content)

    # 图片解码校验
    try:
        with Image.open(path) as image:
            image.verify()
    except Exception as exc:
        return {
            "filename": file.filename,
            "size": len(content),
            "stored_path": str(path),
            "upload_id": path.stem,
            "recognized_text": "图片文件已上传，但内容无法作为有效图片解码，请重新选择清晰的 PNG/JPG 图片。",
            "raw_text": "",
            "engine": "image-verify-failed",
            "ocr_available": False,
            "warning": f"图片解码失败：{exc.__class__.__name__}: {exc}",
            "lines": [],
        }

    recognized = recognize_image(path)
    return {
        "filename": file.filename,
        "size": len(content),
        "stored_path": str(path),
        "upload_id": path.stem,
        **recognized,
    }


# ============================================================
# 8) 预热：应用启动时后台预加载两个引擎
# ============================================================
def warmup_ocr_engines() -> None:
    """后台线程预加载 OCR 引擎，避免首次上传时冷启动。

    软依赖：任一引擎失败都不会阻塞另一个引擎；提供 _OCR_ENGINES_READY 信号。
    """
    def _worker():
        try:
            t = time.perf_counter()
            _get_paddle_engine()
            log(f"🔥 PaddleOCR 预热耗时 {(time.perf_counter() - t) * 1000:.0f}ms")
        except Exception as exc:
            log(f"⚠️ PaddleOCR 预热失败（首次上传时会重试）: {exc}")
        try:
            t = time.perf_counter()
            _get_easy_engine()
            log(f"🔥 EasyOCR 预热耗时 {(time.perf_counter() - t) * 1000:.0f}ms")
        except Exception as exc:
            log(f"⚠️ EasyOCR 预热失败（将自动降级到 PaddleOCR 单引擎）: {exc}")
        _OCR_ENGINES_READY.set()
        log("🔥 OCR 引擎预热阶段结束")
    threading.Thread(target=_worker, name="ocr-warmup", daemon=True).start()
