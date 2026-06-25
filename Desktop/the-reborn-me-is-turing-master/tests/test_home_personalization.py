from uuid import uuid4

from test_smoke import client

from database import SessionLocal
from models import (
    AnswerRecord,
    KnowledgeMastery,
    Mistake,
    Question,
    QuestionGenerationSession,
    User,
    UserMemory,
    UserProfile,
)


def test_home_initial_state_and_weak_point_recommendation():
    suffix = uuid4().hex[:10]
    email = f"home-{suffix}@example.com"
    registered = client.post(
        "/api/auth/register",
        json={"email": email, "username": f"home_{suffix}", "password": "12345678", "nickname": "首页测试用户"},
    ).json()["data"]
    user_id = registered["user"]["id"]
    headers = {"Authorization": f"Bearer {registered['access_token']}"}

    try:
        initial = client.get("/api/home/overview", headers=headers).json()["data"]
        assert initial["today_plan"]["empty_state"] is True
        assert initial["stats"]["weekly_answers"] == 0
        assert initial["stats"]["accuracy"] == 0
        assert initial["stats"]["weak_points"] == 0
        assert initial["stats"]["memory_entries"] == 0
        assert initial["knowledge_graph"]["summary"] == {
            "未学": 20,
            "掌握": 0,
            "不熟": 0,
            "不会": 0,
            "薄弱点": 0,
        }
        assert initial["recommendations"][0]["mode"] == "四科随机综合"

        generated = client.post(
            "/api/questions/generate-smart",
            headers=headers,
            json={"recommend_mode": "薄弱点强化", "count": 1},
        ).json()["data"]
        question = generated["questions"][0]
        recommendation = generated["recommendation"]
        assert recommendation["mode"] == "四科随机综合"
        assert recommendation["knowledge_point"] in question["question_text"]

        wrong_answer = "A" if question["standard_answer"] != "A" else "B"
        for _ in range(3):
            checked = client.post(
                "/api/answers/check",
                headers=headers,
                json={"question_id": question["id"], "user_answer": wrong_answer},
            ).json()["data"]
        assert checked["mastery"]["status"] == "薄弱点"

        updated = client.get("/api/home/overview", headers=headers).json()["data"]
        assert updated["stats"]["weekly_answers"] == 3
        assert updated["stats"]["weak_points"] >= 1
        assert updated["today_plan"]["mode"] == "薄弱点强化"
        assert updated["today_plan"]["knowledge_point"] == recommendation["knowledge_point"]
    finally:
        with SessionLocal() as db:
            session_ids = [
                row[0]
                for row in db.query(QuestionGenerationSession.id)
                .filter(QuestionGenerationSession.user_id == user_id)
                .all()
            ]
            db.query(UserMemory).filter(UserMemory.user_id == user_id).delete(synchronize_session=False)
            db.query(Mistake).filter(Mistake.user_id == user_id).delete(synchronize_session=False)
            db.query(AnswerRecord).filter(AnswerRecord.user_id == user_id).delete(synchronize_session=False)
            db.query(KnowledgeMastery).filter(KnowledgeMastery.user_id == user_id).delete(synchronize_session=False)
            if session_ids:
                db.query(Question).filter(Question.session_id.in_(session_ids)).delete(synchronize_session=False)
                db.query(QuestionGenerationSession).filter(
                    QuestionGenerationSession.id.in_(session_ids)
                ).delete(synchronize_session=False)
            db.query(UserProfile).filter(UserProfile.user_id == user_id).delete(synchronize_session=False)
            db.query(User).filter(User.id == user_id).delete(synchronize_session=False)
            db.commit()