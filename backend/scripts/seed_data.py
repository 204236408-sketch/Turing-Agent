import json
import re
<<<<<<< HEAD
import sys
from pathlib import Path
from typing import Any

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

SCRIPT_PATH = Path(__file__).resolve()
BACKEND_ROOT = SCRIPT_PATH.parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from auth import register_user
from database import SessionLocal, init_database
from models import ForumCategory, ForumPost, KnowledgePoint, Question, Subject, User, VideoResource

DATA_DIR = BACKEND_ROOT / "data"
SUBJECT_FILE = DATA_DIR / "seed_subjects.json"
KNOWLEDGE_FILE = DATA_DIR / "seed_knowledge_points.json"
QUESTION_FILE = DATA_DIR / "seed_questions.json"
VIDEO_FILE = DATA_DIR / "seed_video_resources.json"
FORUM_CAT_FILE = DATA_DIR / "seed_forum_categories.json"
FORUM_POST_FILE = DATA_DIR / "seed_forum_posts.json"

DEMO_USER_EMAIL = "demo@turing408.ai"
DEMO_USER_NAME = "demo"
DEMO_USER_PASSWORD = "123456"
DEMO_USER_NICKNAME = "林同学"

DEFAULT_SUBJECTS = [
=======
from pytest import fail
from sqlalchemy.exc import IntegrityError
from database import SessionLocal, init_database
from services.seed_service import seed_all
from models import Subject, KnowledgePoint

# 标准408四大科目配置
STD_SUBJECTS = [
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
    {"name": "数据结构", "description": "408数据结构完整考纲体系", "sort_order": 1},
    {"name": "计算机组成原理", "description": "408计算机组成原理考点", "sort_order": 2},
    {"name": "操作系统", "description": "408操作系统核心知识点", "sort_order": 3},
    {"name": "计算机网络", "description": "408计算机网络全章节", "sort_order": 4},
]

<<<<<<< HEAD
RE_COMMA_SPACE = re.compile(r",\s+")


class SeedImporter:
    def __init__(self) -> None:
        self.db = SessionLocal()
        self.stats = {
            "subjects": 0,
            "knowledge_points": 0,
            "questions": 0,
            "videos": 0,
            "forum_categories": 0,
            "forum_posts": 0,
            "errors": [],
        }
        self.subject_map: dict[str, int] = {}
        self.demo_user_id: int | None = None

    def log_error(self, message: str) -> None:
        self.stats["errors"].append(message)
        print(f"[ERROR] {message}")

    def load_json(self, path: Path) -> list[Any]:
        if not path.exists():
            self.log_error(f"文件不存在: {path}")
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                self.log_error(f"{path} 根节点必须为数组")
                return []
            return data
        except json.JSONDecodeError as exc:
            self.log_error(f"JSON语法错误 {path}: {exc}")
            return []
        except Exception as exc:
            self.log_error(f"读取文件失败 {path}: {exc}")
            return []

    def clean_keywords(self, keywords: str) -> str:
        return RE_COMMA_SPACE.sub(",", keywords).strip()

    def get_subject_map(self) -> dict[str, int]:
        return {subject.name: subject.id for subject in self.db.query(Subject).all()}

    def ensure_demo_user(self) -> int:
        user = self.db.query(User).filter(User.email == DEMO_USER_EMAIL).first()
        if user:
            return user.id
        user = register_user(self.db, DEMO_USER_EMAIL, DEMO_USER_NAME, DEMO_USER_PASSWORD, DEMO_USER_NICKNAME)
        return user.id

    def import_subjects(self) -> None:
        records = self.load_json(SUBJECT_FILE)
        if not records:
            records = DEFAULT_SUBJECTS
        for idx, item in enumerate(records, 1):
            name = str(item.get("name", "")).strip()
            if not name:
                self.log_error(f"第{idx}条科目缺少name")
                continue
            description = str(item.get("description", f"408 {name} 考纲知识体系")).strip()
            sort_order = int(item.get("sort_order", idx)) if str(item.get("sort_order", "")).isdigit() else idx
            subject = self.db.query(Subject).filter(Subject.name == name).first()
            if subject:
                subject.description = description
                subject.sort_order = sort_order
            else:
                self.db.add(Subject(name=name, description=description, sort_order=sort_order))
                self.stats["subjects"] += 1
        self.db.commit()
        self.subject_map = self.get_subject_map()
        print(f"✅ 已导入/更新科目：{len(self.subject_map)} 条")

    def import_knowledge_points(self) -> None:
        items = self.load_json(KNOWLEDGE_FILE)
        if not items:
            return
        for idx, item in enumerate(items, 1):
            try:
                subject = str(item.get("subject", "")).strip()
                name = str(item.get("name", "")).strip()
                section = str(item.get("section", "")).strip()
                level = item.get("level")
                content = str(item.get("content", "")).strip()
                keywords = str(item.get("keywords", "")).strip()
                if not all([subject, name, section, level, content, keywords]):
                    raise ValueError("必填字段不足")
                if subject not in self.subject_map:
                    raise ValueError(f"未知科目：{subject}")
                keywords = self.clean_keywords(keywords)
                if "," in keywords and any(not part.strip() for part in keywords.split(",")):
                    raise ValueError("keywords格式不合法")
                existing = self.db.query(KnowledgePoint).filter(
                    KnowledgePoint.subject == subject,
                    KnowledgePoint.name == name,
                    KnowledgePoint.section == section,
                ).first()
                if existing:
                    continue
                kp = KnowledgePoint(
                    subject_id=self.subject_map[subject],
                    subject=subject,
                    parent_id=None,
                    parent_name=str(item.get("parent_name", subject)).strip(),
                    name=name,
                    section=section,
                    level=int(level),
                    content=content,
                    common_mistakes=str(item.get("common_mistakes", "")).strip(),
                    keywords=keywords,
                    is_high_frequency=bool(item.get("is_high_frequency", False)),
                )
                self.db.add(kp)
                self.stats["knowledge_points"] += 1
            except (IntegrityError, ValueError) as exc:
                self.db.rollback()
                self.log_error(f"知识点第{idx}条导入失败: {exc}")
            except Exception as exc:
                self.db.rollback()
                self.log_error(f"知识点第{idx}条导入异常: {exc}")
        self.db.commit()
        print(f"✅ 知识点导入完成：{self.stats['knowledge_points']} 条")

    def import_questions(self) -> None:
        items = self.load_json(QUESTION_FILE)
        if not items:
            return
        for idx, item in enumerate(items, 1):
            try:
                subject = str(item.get("subject", "")).strip()
                kp_name = str(item.get("knowledge_point", "")).strip()
                text = str(item.get("question_text", "")).strip()
                answer = str(item.get("standard_answer", "")).strip()
                question_type = str(item.get("question_type", "")).strip()
                variant_type = str(item.get("variant_type", "")).strip()
                if not all([subject, kp_name, text, answer, question_type, variant_type]):
                    raise ValueError("题目缺少必填字段")
                if subject not in self.subject_map:
                    raise ValueError(f"未知科目：{subject}")
                existing = self.db.query(Question).filter(
                    Question.subject == subject,
                    Question.knowledge_point == kp_name,
                    Question.question_text == text,
                ).first()
                if existing:
                    continue
                options = item.get("options") or []
                hints = item.get("hints") or []
                question = Question(
                    subject=subject,
                    knowledge_point=kp_name,
                    difficulty=str(item.get("difficulty", "中等")).strip(),
                    question_type=question_type,
                    variant_type=variant_type,
                    question_text=text,
                    options_json=options,
                    sub_questions_json=item.get("sub_questions") or [],
                    standard_answer=answer,
                    explanation=str(item.get("explanation", "")).strip(),
                    hints_json=hints,
                    recommend_reason=str(item.get("recommend_reason", "")).strip(),
                    source=str(item.get("source", "seed")).strip(),
                )
                self.db.add(question)
                self.stats["questions"] += 1
            except (IntegrityError, ValueError) as exc:
                self.db.rollback()
                self.log_error(f"题目第{idx}条导入失败: {exc}")
            except Exception as exc:
                self.db.rollback()
                self.log_error(f"题目第{idx}条导入异常: {exc}")
        self.db.commit()
        print(f"✅ 题库导入完成：{self.stats['questions']} 条")

    def import_video_resources(self) -> None:
        items = self.load_json(VIDEO_FILE)
        if not items:
            return
        for idx, item in enumerate(items, 1):
            try:
                subject = str(item.get("subject", "")).strip()
                title = str(item.get("title", "")).strip()
                url = str(item.get("url", "")).strip()
                if not all([subject, title, url]):
                    raise ValueError("视频数据缺少必填字段")
                existing = self.db.query(VideoResource).filter(VideoResource.url == url).first()
                if existing:
                    continue
                video = VideoResource(
                    subject=subject,
                    knowledge_point=str(item.get("knowledge_point", "")).strip(),
                    title=title,
                    platform=str(item.get("platform", "")).strip(),
                    url=url,
                    cover_url=str(item.get("cover_url", "")).strip(),
                    duration=str(item.get("duration", "")).strip(),
                    reason=str(item.get("reason", "")).strip(),
                    quality_score=int(item.get("quality_score", 0)) if item.get("quality_score") is not None else 0,
                    author=str(item.get("author", "")).strip(),
                    crawl_source=str(item.get("crawl_source", "seed")).strip(),
                )
                self.db.add(video)
                self.stats["videos"] += 1
            except (IntegrityError, ValueError) as exc:
                self.db.rollback()
                self.log_error(f"视频第{idx}条导入失败: {exc}")
            except Exception as exc:
                self.db.rollback()
                self.log_error(f"视频第{idx}条导入异常: {exc}")
        self.db.commit()
        print(f"✅ 视频资源导入完成：{self.stats['videos']} 条")

    def import_forum_categories(self) -> None:
        items = self.load_json(FORUM_CAT_FILE)
        if not items:
            return
        for idx, item in enumerate(items, 1):
            name = str(item.get("name", "")).strip()
            if not name:
                self.log_error(f"论坛分类第{idx}条缺少name")
                continue
            existing = self.db.query(ForumCategory).filter(ForumCategory.name == name).first()
            if existing:
                continue
            self.db.add(ForumCategory(name=name, description=str(item.get("description", "")).strip()))
            self.stats["forum_categories"] += 1
        self.db.commit()
        print(f"✅ 论坛分类导入完成：{self.stats['forum_categories']} 条")

    def import_forum_posts(self) -> None:
        if self.demo_user_id is None:
            self.demo_user_id = self.ensure_demo_user()
        items = self.load_json(FORUM_POST_FILE)
        if not items:
            return
        for idx, item in enumerate(items, 1):
            try:
                title = str(item.get("title", "")).strip()
                content = str(item.get("content", "")).strip()
                if not title or not content:
                    raise ValueError("论坛帖子缺少 title 或 content")
                category = str(item.get("category", item.get("subject", "")).strip()) or "全部"
                subject = str(item.get("subject", category)).strip()
                knowledge_point = str(item.get("knowledge_point", "")).strip()
                existing = self.db.query(ForumPost).filter(
                    ForumPost.user_id == self.demo_user_id,
                    ForumPost.title == title,
                ).first()
                if existing:
                    continue
                post = ForumPost(
                    user_id=self.demo_user_id,
                    category=category,
                    subject=subject,
                    knowledge_point=knowledge_point,
                    title=title,
                    content=content,
                    like_count=int(item.get("like_count", 0)) if item.get("like_count") is not None else 0,
                    collect_count=int(item.get("collect_count", 0)) if item.get("collect_count") is not None else 0,
                    comment_count=int(item.get("comment_count", 0)) if item.get("comment_count") is not None else 0,
                    is_top=bool(item.get("is_top", False)),
                    status=str(item.get("status", "normal")).strip(),
                    create_ip=str(item.get("create_ip", "")).strip(),
                )
                self.db.add(post)
                self.stats["forum_posts"] += 1
            except (IntegrityError, ValueError) as exc:
                self.db.rollback()
                self.log_error(f"论坛帖子第{idx}条导入失败: {exc}")
            except Exception as exc:
                self.db.rollback()
                self.log_error(f"论坛帖子第{idx}条导入异常: {exc}")
        self.db.commit()
        print(f"✅ 论坛帖子导入完成：{self.stats['forum_posts']} 条")

    def print_report(self) -> None:
        print("\n==================== 种子数据导入报告 ====================")
        print(f"科目: {self.stats['subjects']}")
        print(f"知识点: {self.stats['knowledge_points']}")
        print(f"题库: {self.stats['questions']}")
        print(f"视频资源: {self.stats['videos']}")
        print(f"论坛分类: {self.stats['forum_categories']}")
        print(f"论坛帖子: {self.stats['forum_posts']}")
        print(f"累计错误: {len(self.stats['errors'])}")
        if self.stats['errors']:
            print("\n错误明细：")
            for err in self.stats['errors']:
                print(f"- {err}")
        print("=======================================================\n")

    def run(self) -> None:
        init_database()
        self.demo_user_id = self.ensure_demo_user()
        self.import_subjects()
        self.import_knowledge_points()
        self.import_questions()
        self.import_video_resources()
        self.import_forum_categories()
        self.import_forum_posts()
        self.print_report()
        self.db.close()


if __name__ == "__main__":
    importer = SeedImporter()
    importer.run()
=======
def init_standard_subject(db):
    """初始化四大科目，存在跳过，返回名称-id映射"""
    for sub_info in STD_SUBJECTS:
        exist = db.query(Subject).filter(Subject.name == sub_info["name"]).first()
        if not exist:
            db.add(Subject(**sub_info))
    db.commit()
    print("✅ 标准4科科目初始化完成")
    return {sub.name: sub.id for sub in db.query(Subject).all()}

def clean_and_validate_text(raw_json_str):
    # 只清理keywords逗号空格，移除栈满/队满术语替换（不修改知识点原文）
    text = re.sub(r",\s+", ",", flags=re.M)
    return text

def check_keyword_format(kw_str):
    """校验关键词无空项、无多余空格"""
    if not kw_str or kw_str.strip() == "":
        return False
    parts = kw_str.split(",")
    for part in parts:
        if part.strip() == "":
            return False
    return True

def import_full_knowledge(db, sub_name_map, json_path="seed_knowledge_points.json"):
    """批量导入知识点JSON，仅清洗关键词格式，不修改正文术语"""
    # 文件读取与JSON解析异常捕获
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            raw = f.read()
        clean_str = clean_and_validate_text(raw)
        kp_list = json.loads(clean_str)
    except json.JSONDecodeError as e:
        print(f"❌ JSON语法错误：{str(e)}")
        db.rollback()
        return
    except FileNotFoundError:
        print(f"❌ 找不到文件 {json_path}")
        db.rollback()

    total_count = len(kp_list)
    success_count = 0
    fail_list = []
    # 分科目统计容器
    stat = {
        "数据结构": {"total": 0, "high_freq": 0},
        "计算机组成原理": {"total": 0, "high_freq": 0},
        "操作系统": {"total": 0, "high_freq": 0},
        "计算机网络": {"total": 0, "high_freq": 0},
    }

    for idx, item in enumerate(kp_list):
        try:
            # 必填字段非空校验
            required_fields = ["subject", "name", "section", "level", "content", "keywords", "is_high_frequency"]
            for field in required_fields:
                if field not in item or str(item[field]).strip() == "":
                    raise Exception(f"必填字段 {field} 为空")
            sub_name = item["subject"]
            if sub_name not in sub_name_map:
                raise Exception(f"不存在科目：{sub_name}")
            sub_id = sub_name_map[sub_name]
            # 关键词格式校验
            if not check_keyword_format(item["keywords"]):
                raise Exception("keywords存在空逗号/多余空格")
            # 组装模型
            kp = KnowledgePoint(
                subject_id=sub_id,
                subject=sub_name,
                parent_id=None,
                parent_name=item["parent_name"],
                name=item["name"],
                section=item["section"],
                level=item["level"],
                content=item["content"],
                common_mistakes=item["common_mistakes"],
                keywords=item["keywords"],
                is_high_frequency=item["is_high_frequency"],
                is_deleted=0
            )
            db.add(kp)
            success_count += 1
            stat[sub_name]["total"] += 1
            if item["is_high_frequency"]:
                stat[sub_name]["high_freq"] += 1
        except IntegrityError:
            db.rollback()
            fail_list.append({"index": idx, "item": item, "err": "唯一键uk冲突，知识点已存在"})
        except Exception as e:
            fail_list.append({"index": idx, "item": item, "err": str(e)})
    db.commit()
    # 打印统计汇总
    print("\n==================== 导入统计汇总 ====================")
    print(f"JSON总条目：{total_count} | 成功入库：{success_count} | 失败：{len(fail)}")
    for sub, data in stat.items():
        print(f"{sub}：总{data['total']}条，高频{data['high_freq']}条")
    print(f"全库高频知识点合计：{sum(v['high_freq'] for v in stat.values())}")
    if fail_list:
        print("\n前5条失败记录：")
        for f in fail_list[:5]:
            print(f"行{f['index']} 知识点{f['item']['name']} 错误：{f['err']}")
    print("=======================================================\n")

if __name__ == "__main__":
    # 1. 创建全部数据表
    init_database()
    # 开启会话
    with SessionLocal() as db:
        # 2. 调用service生成测试用户、题目、论坛、视频（service不再生成知识点）
        seed_all(db)
        # 3. 初始化标准4个科目
        subject_map = init_standard_subject(db)
        # 4. 执行JSON完整知识点导入（仅清洗关键词，不修改正文文字）
        import_full_knowledge(db, subject_map, "seed_knowledge_points.json")
    print("🎉 全部初始化流程执行完成")
>>>>>>> 2dbf2d9 (郭晶-6.26上午-修改版)
