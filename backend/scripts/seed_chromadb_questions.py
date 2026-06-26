"""
将 seed_questions.json 灌入 ChromaDB seed_questions_vector 集合。

用法：
    cd backend && python scripts/seed_chromadb_questions.py

前置条件：ChromaDB 持久化路径由 settings.chroma_path 指定。
"""
import json
import logging
import sys
from pathlib import Path

# 确保 backend 目录在 sys.path 中
backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from config import settings
from services.chroma_service import upsert_document, delete_collection

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("seed_chromadb_questions")

COLLECTION = "seed_questions_vector"
DATA_PATH = Path(backend_dir) / "data" / "seed_questions.json"


def main() -> None:
    if not DATA_PATH.exists():
        logger.error("种子题数据文件不存在: %s", DATA_PATH)
        sys.exit(1)

    with open(DATA_PATH, encoding="utf-8") as f:
        questions = json.load(f)

    if not isinstance(questions, list) or len(questions) == 0:
        logger.error("种子题数据为空或格式错误")
        sys.exit(1)

    logger.info("读取到 %d 道种子题，准备导入 ChromaDB 集合「%s」", len(questions), COLLECTION)

    # 清空旧数据（集合级全量替换）
    logger.info("清空旧集合 %s ...", COLLECTION)
    delete_collection(COLLECTION)

    ok = fail = 0
    for i, q in enumerate(questions):
        doc_id = f"seed_q_{i}"
        subject = q.get("subject", "")
        kp = q.get("knowledge_point", "")
        question_text = q.get("question_text", "")
        options = q.get("options", [])
        standard_answer = q.get("standard_answer", "")
        explanation = q.get("explanation", "")
        difficulty = q.get("difficulty", "")
        q_type = q.get("question_type", "")

        # 构造要写入 ChromaDB 的文本（题目 + 标准答案 + 解析）
        text_parts = [question_text]
        if options:
            text_parts.append("选项：" + " ".join(options))
        if standard_answer:
            text_parts.append(f"答案：{standard_answer}")
        if explanation:
            text_parts.append(f"解析：{explanation}")
        text = "\n".join(text_parts)

        metadata = {
            "subject": subject,
            "knowledge_point": kp,
            "difficulty": difficulty,
            "question_type": q_type,
            "standard_answer": standard_answer,
            "source": "seed",
            "index": i,
        }

        result = upsert_document(COLLECTION, doc_id, text, metadata)
        if result.get("stored"):
            ok += 1
        else:
            logger.warning("导入失败 [%s]: %s", doc_id, result.get("error"))
            fail += 1

    logger.info("导入完成：成功 %d 条，失败 %d 条", ok, fail)


if __name__ == "__main__":
    main()
