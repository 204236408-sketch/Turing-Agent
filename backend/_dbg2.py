import re
text = "图的遍历"
raw_parts = re.findall(r"[\u4e00-\u9fff]+|[A-Za-z0-9]+", text)
print(f"raw_parts: {raw_parts!r}")
phrases = re.split(r"[、，, \t]+|和|与|及|或", raw_parts[0])
print(f"phrases: {phrases!r}")
for ph in phrases:
    has_de = "的" in ph
    print(f"  ph={ph!r}, 的 in ph={has_de}, len(ph)={len(ph)}")
    if has_de and len(ph) >= 4:
        subs = re.split(r"的", ph)
        print(f"    subs: {subs!r}")
