"""逐步检查 _wangdao_match_score 得分构成"""
from database import SessionLocal
from models import VideoResource
import services.video_service as vs

# 直接调用，看每一步的中间分
v_kp = "TCP可靠传输、流量控制（咸鱼版）"
v_title = "王道计算机考研 计算机网络 - 5.3.4 TCP可靠传输、流量控制（咸鱼版）"
kp_name = "数据链路层"
kp_section = "流量控制与可靠传输机制"
subject = "计算机网络"

v = VideoResource(
    id=1, knowledge_point=v_kp, title=v_title,
    subject=subject, is_active=True, is_deleted=False
)

# 模拟打分
v_kp_clean = v_kp.strip()
v_title_clean = v_title.strip()
score = 0

kp_name_specific = vs._strip_subject_prefix(kp_name, subject)
v_kp_specific = vs._strip_subject_prefix(v_kp_clean, subject)
print(f"kp_name_specific: {kp_name_specific!r}")
print(f"v_kp_specific: {v_kp_specific!r}")

is_parent_only = bool(kp_section and kp_section not in {subject, ""} and kp_section != kp_name)
parent_cap = 50 if is_parent_only else 100
print(f"is_parent_only: {is_parent_only}, parent_cap: {parent_cap}")

print("\n--- kp_name block ---")
if kp_name and kp_name not in {subject, ""}:
    if v_kp_clean == kp_name:
        score = max(score, min(100, parent_cap))
        print(f"  v_kp == kp_name: score={score}")
    kp_stem = vs._strip_generic_suffix(kp_name)
    v_stem = vs._strip_generic_suffix(v_kp_clean)
    print(f"  kp_stem: {kp_stem!r}, v_stem: {v_stem!r}")
    if kp_stem and v_stem:
        if kp_stem == v_stem:
            score = max(score, min(95, parent_cap))
            print(f"  kp_stem == v_stem: score={score}")
        elif len(kp_stem) >= 2 and kp_stem in v_stem:
            score = max(score, min(85, parent_cap))
            print(f"  kp_stem in v_stem: score={score}")

print("\n--- kp_section block ---")
if kp_section and kp_section not in {subject, ""}:
    if v_kp_clean == kp_section:
        score = max(score, 60)
    sec_stem = vs._strip_generic_suffix(kp_section)
    v_stem2 = vs._strip_generic_suffix(v_kp_clean)
    print(f"  sec_stem: {sec_stem!r}, v_stem2: {v_stem2!r}")
    if sec_stem and v_stem2:
        if sec_stem == v_stem2:
            score = max(score, 55)
            print(f"  sec_stem == v_stem2: score={score}")
        elif len(sec_stem) >= 2 and sec_stem in v_stem2:
            sec_specific = vs._strip_subject_prefix(sec_stem, subject)
            v_specific = vs._strip_subject_prefix(v_stem2, subject)
            if vs._is_meaningful_topic(sec_specific) and vs._is_meaningful_topic(v_specific):
                if sec_specific in v_specific or v_specific in sec_specific:
                    score = max(score, 50)
                    print(f"  sec_stem in v_stem2: score={score}")

print("\n--- section token block ---")
if kp_section and kp_section not in {subject, ""} and v_kp_clean:
    sec_tokens = vs._split_kp_tokens(kp_section, exclude={subject})
    print(f"  sec_tokens: {sec_tokens!r}")
    if sec_tokens and vs._is_meaningful_topic(v_kp_specific):
        v_target = v_kp_specific + v_kp_clean
        sec_hits = [t for t in sec_tokens if t in v_target]
        print(f"  v_target: {v_target!r}")
        print(f"  sec_hits: {sec_hits!r}")
        if sec_hits:
            max_len = max(len(t) for t in sec_hits)
            n_hits = len(sec_hits)
            n_total = len(sec_tokens)
            print(f"  n_hits={n_hits}, n_total={n_total}, max_len={max_len}")
            if n_hits == n_total and n_total >= 2:
                score = max(score, 70)
                print(f"  full match: score={score}")
            elif max_len >= 3:
                score = max(score, 65)
                print(f"  3+ char match: score={score}")
            else:
                leading_hit = any(v_kp_clean.startswith(t) for t in sec_hits)
                if leading_hit:
                    score = max(score, 55)
                    print(f"  2-char leading: score={score}")
        if v_title_clean:
            title_hits = [t for t in sec_tokens if t in v_title_clean]
            print(f"  title_hits: {title_hits!r}")
            if title_hits:
                max_len = max(len(t) for t in title_hits)
                if max_len >= 3:
                    score = max(score, 50)
                    print(f"  title 3+ char match: score={score}")

print(f"\nFINAL: {score}")
