import json
from sqlalchemy.orm import Session
from auth import register_user
from models import (
    AnswerRecord,
    ForumCategory,
    ForumPost,
    KnowledgePoint,
    Mistake,
    Question,
    Subject,
    User,
    VideoResource,
)


SUBJECTS = {
    "数据结构": ["线性表", "栈和队列", "树与二叉树", "图", "查找", "排序"],
    "计算机组成原理": ["数据表示与运算", "存储系统", "指令系统", "中央处理器", "总线与 I/O"],
    "操作系统": ["进程与线程", "同步与互斥", "死锁", "内存管理", "页面置换算法", "文件系统"],
    "计算机网络": ["体系结构", "数据链路层", "网络层", "传输层", "应用层"],
}


def seed_all(db: Session) -> None:
    seed_demo_user(db)
    seed_knowledge(db)
    seed_questions(db)
    seed_forum(db)
    seed_videos(db)
    seed_mistakes(db)
    synchronize_existing_mastery(db)
    db.commit()


def seed_demo_user(db: Session) -> User:
    user = db.query(User).filter(User.email == "demo@turing408.ai").first()
    if not user:
        user = register_user(db, "demo@turing408.ai", "demo", "123456", "林同学")
    return user


def seed_knowledge(db: Session) -> None:
    if db.query(KnowledgePoint).count() > 0:
        print("库中已存在完整知识点，跳过演示知识点生成")
        return
    if db.query(Subject).count():
        return
    demo = db.query(User).filter(User.email == "demo@turing408.ai").first()
    for order, (subject, points) in enumerate(SUBJECTS.items(), 1):
        db.add(Subject(name=subject, description=f"408 {subject} 考纲知识体系", sort_order=order))
        for idx, point in enumerate(points, 1):
            db.add(
                KnowledgePoint(
                    subject=subject,
                    name=point,
                    parent_name=subject,
                    section=point,
                    level=2,
                    is_high_frequency=idx % 2 == 0 or point in {"页面置换算法", "传输层", "排序"},
                    content=f"{point} 是 {subject} 的核心复习单元，需要掌握定义、流程、计算题和常见陷阱。",
                    common_mistakes="概念混淆、步骤遗漏、计算边界漏算",
                    keywords=f"{subject},{point},408",
                )
            )


def synchronize_existing_mastery(db: Session) -> None:
    from services.mastery_service import synchronize_user_mastery

    points = [(row.subject, row.name) for row in db.query(KnowledgePoint).all()]
    for user in db.query(User).all():
        synchronize_user_mastery(db, user.id, points)


def seed_questions(db: Session) -> None:
    if db.query(Question).count():
        return
    questions = [
        (
            "操作系统",
            "页面置换算法",
            "某系统为进程分配 3 个页框，页面访问序列为 1, 2, 3, 1, 4, 2, 5。采用 LRU 算法时，缺页次数为多少？",
            ["A. 4 次", "B. 5 次", "C. 6 次", "D. 7 次"],
            "C",
            "按 LRU 规则逐次更新最近访问顺序，初始装入也算缺页，共 6 次。",
        ),
        (
            "计算机网络",
            "传输层",
            "TCP 连接释放时，主动关闭方进入 TIME_WAIT 的主要目的是什么？",
            ["A. 等待应用层确认", "B. 保证旧报文消失并可重传最后 ACK", "C. 释放端口", "D. 重新建立连接"],
            "B",
            "TIME_WAIT 等待 2MSL，用于可靠关闭和避免旧报文影响后续连接。",
        ),
        (
            "数据结构",
            "树与二叉树",
            "若只给出一棵普通二叉树的前序和后序序列，通常能否唯一确定该二叉树？",
            ["A. 一定可以", "B. 一定不可以", "C. 通常不可以", "D. 只要结点不同就可以"],
            "C",
            "前序和后序都不能提供左右子树的明确分界，普通二叉树通常不能唯一还原。",
        ),
    ]
    for subject, point, text, options, answer, explanation in questions:
        db.add(
            Question(
                subject=subject,
                knowledge_point=point,
                difficulty="中等",
                question_type="选择题",
                question_text=text,
                options_json=json.dumps(options, ensure_ascii=False),
                standard_answer=answer,
                explanation=explanation,
                hints_json=json.dumps(["先写出关键状态变化。", "注意边界条件和初始状态。"], ensure_ascii=False),
                recommend_reason=f"用于巩固 {point} 的高频考法。",
                source="seed",
            )
        )


def seed_forum(db: Session) -> None:
    if db.query(ForumCategory).count():
        return
    demo = db.query(User).filter(User.email == "demo@turing408.ai").first()
    for idx, name in enumerate(["全部", "数据结构", "组成原理", "操作系统", "计算机网络", "经验分享"], 1):
        db.add(ForumCategory(name=name, description=f"{name} 讨论区", sort_order=idx))
    if demo:
        posts = [
            ForumPost(
                user_id=demo.id,
                category="操作系统",
                subject="操作系统",
                knowledge_point="页面置换算法",
                title="LRU 页面置换到底什么时候更新访问顺序？",
                content="命中后到底要不要移动最近使用位置？做题总漏。",
                like_count=28,
                comment_count=12,
            ),
            ForumPost(
                user_id=demo.id,
                category="计算机网络",
                subject="计算机网络",
                knowledge_point="传输层",
                title="TCP 四次挥手中 TIME_WAIT 为什么必须保留？",
                content="除了保证最后一个 ACK 能够重传之外，TIME_WAIT 对旧报文段消失还有什么作用？",
                like_count=21,
                comment_count=9,
            ),
            ForumPost(
                user_id=demo.id,
                category="数据结构",
                subject="数据结构",
                knowledge_point="树与二叉树",
                title="二叉树遍历序列还原，有没有统一判断思路？",
                content="前序加中序、后序加中序都能还原，只有前序加后序为什么通常不行？",
                like_count=36,
                comment_count=18,
            ),
            ForumPost(
                user_id=demo.id,
                category="组成原理",
                subject="计算机组成原理",
                knowledge_point="存储系统",
                title="Cache 地址划分总算错位数，求检查方法",
                content="标记、组号和块内地址位数有没有一套固定的验算步骤？",
                like_count=15,
                comment_count=7,
            ),
            ForumPost(
                user_id=demo.id,
                category="经验分享",
                subject="经验分享",
                knowledge_point="",
                title="408 四科复习顺序怎么安排比较合理？",
                content="我打算先数据结构再组成原理，然后操作系统和计算机网络，大家觉得这个顺序怎么样？",
                like_count=46,
                comment_count=23,
            ),
            ForumPost(
                user_id=demo.id,
                category="操作系统",
                subject="操作系统",
                knowledge_point="进程管理",
                title="进程和线程的区别到底怎么记忆最牢固？",
                content="每次面试或者做题都混淆，特别是资源分配和调度的区别，求一个记忆口诀。",
                like_count=19,
                comment_count=8,
            ),
        ]
        db.add_all(posts)


def seed_videos(db: Session) -> None:
    if db.query(VideoResource).count():
        return
    db.add_all(
        [
            VideoResource(
                subject="操作系统",
                knowledge_point="页面置换算法",
                section="页面置换算法",
                title="408 操作系统：页面置换算法 LRU/FIFO/OPT",
                url="https://www.bilibili.com/",
                reason="适合在错题后快速回看完整模拟过程。",
            ),
            VideoResource(
                subject="计算机网络",
                knowledge_point="传输层",
                section="传输层",
                title="TCP 三次握手与四次挥手高频考点",
                url="https://www.bilibili.com/",
                reason="覆盖 TIME_WAIT、ACK 重传和旧报文消失。",
            ),
        ]
    )


def seed_mistakes(db: Session) -> None:
    from datetime import datetime, timedelta
    if db.query(Mistake).count():
        return
    user = db.query(User).filter(User.email == "demo@turing408.ai").first()
    if not user:
        return
    questions = db.query(Question).all()
    if not questions:
        return
    mistakes_data = [
        (questions[0].id, "操作系统", "页面置换算法", "规则混淆", "LRU 页面命中后忘记更新最近访问顺序", "先画出页框再逐次标记最近使用时间"),
        (questions[1].id, "计算机网络", "传输层", "概念理解错误", "TIME_WAIT 作用与端口释放混淆", "记住 TIME_WAIT 是 2MSL 等待旧报文消失"),
        (questions[2].id, "数据结构", "树与二叉树", "综合应用能力不足", "前序和后序缺少中序分区信息无法唯一还原", "画图示例理解前序+后序的歧义性"),
    ]
    for qid, subj, point, etype, reason, suggestion in mistakes_data:
        m = Mistake(
            user_id=user.id,
            answer_record_id=None,
            question_id=qid,
            subject=subj,
            knowledge_point=point,
            error_type=etype,
            error_reason=reason,
            suggestion=suggestion,
            input_type="系统出题",
        )
        db.add(m)
        db.flush()
    db.query(Mistake).filter(Mistake.subject == "页面置换算法", Mistake.user_id == user.id).update(
        {"mastery_status": "不熟", "create_time": datetime.utcnow() - timedelta(days=2)})
    db.query(Mistake).filter(Mistake.subject == "传输层", Mistake.user_id == user.id).update(
        {"mastery_status": "不会", "create_time": datetime.utcnow() - timedelta(days=1)})
    db.query(Mistake).filter(Mistake.subject == "树与二叉树", Mistake.user_id == user.id).update(
        {"mastery_status": "不熟", "create_time": datetime.utcnow() - timedelta(hours=6)})
