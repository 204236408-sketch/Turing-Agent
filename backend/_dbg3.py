import services.video_service as vs
import re
text = "图的遍历"
exclude = {"数据结构"} | vs.GENERIC_STOP_TOKENS
print(f"exclude has 的: {'的' in exclude}")
print(f"exclude has 遍历: {'遍历' in exclude}")

stem = vs._strip_generic_suffix(text) or text
print(f"stem: {stem!r}")
sources = [text, stem] if stem != text else [text]
print(f"sources: {sources}")

out = []
seen = set()
for src in sources:
    print(f"Processing src: {src!r}")
    if src == text and len(src) >= 1 and src not in exclude and src not in seen:
        out.append(src)
        seen.add(src)
        print(f"  Added full: {src}")
    raw_parts = re.findall(r"[\u4e00-\u9fff]+|[A-Za-z0-9]+", src)
    print(f"  raw_parts: {raw_parts}")
    for p in raw_parts:
        if re.match(r"^[A-Za-z0-9]+$", p):
            continue
        phrases = re.split(r"[、，, \t]+|和|与|及|或", p)
        print(f"  phrases: {phrases}")
        for ph in phrases:
            ph = ph.strip()
            if len(ph) < 2 or ph in exclude or ph in seen:
                print(f"    SKIP ph={ph!r}")
                continue
            out.append(ph)
            seen.add(ph)
            print(f"    Added ph={ph!r}")
            if "的" in ph and len(ph) >= 4:
                subs = re.split(r"的", ph)
                print(f"    splitting 的: {subs}")
                for sub in subs:
                    sub = sub.strip()
                    if len(sub) >= 2 and sub not in exclude and sub not in seen:
                        out.append(sub)
                        seen.add(sub)
                        print(f"      Added sub={sub!r}")
                    else:
                        print(f"      SKIP sub={sub!r}")
print(f"final: {out}")
