import json
import re
from pytest import fail
from sqlalchemy.exc import IntegrityError
from database import SessionLocal, init_database
from services.seed_service import seed_all
from models import Subject, KnowledgePoint

# 标准408四大科目配置
STD_SUBJECTS = [
    {"name": "数据结构", "description": "408数据结构完整考纲体系", "sort_order": 1},
    {"name": "计算机组成原理", "description": "408计算机组成原理考点", "sort_order": 2},
    {"name": "操作系统", "description": "408操作系统核心知识点", "sort_order": 3},
    {"name": "计算机网络", "description": "408计算机网络全章节", "sort_order": 4},
]

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
