from database import SessionLocal, init_database
from models import KnowledgePoint
from services.chroma_service import upsert_document


if __name__ == "__main__":
    init_database()
    with SessionLocal() as db:
        for item in db.query(KnowledgePoint).all():
            upsert_document(
                "knowledge_base_408",
                str(item.id),
                f"{item.subject} {item.name} {item.content}",
                {"subject": item.subject, "knowledge_point": item.name},
            )
    print("开发版已模拟导入 ChromaDB；生产版可替换 chroma_service 实现")
