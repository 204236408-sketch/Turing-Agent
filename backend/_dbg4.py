import services.video_service as vs
text = "图的遍历"
exclude = {"数据结构"} | vs.GENERIC_STOP_TOKENS
ph = "图的遍历"
print(f"len(ph) < 2: {len(ph) < 2}")
print(f"ph in exclude: {ph in exclude}")
print(f"ph in seen: {ph in set()}")
# 单独检查
print(f"'图的遍历' == '的'? {'图的遍历' == '的'}")
print(f"'图的遍历' == '数据结构'? {'图的遍历' == '数据结构'}")
