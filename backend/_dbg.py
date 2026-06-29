from services.video_service import _strip_generic_suffix, _split_kp_tokens
text = "图的遍历"
exclude = {"数据结构"}
print(f"text: {text!r}")
print(f"stem: {_strip_generic_suffix(text)!r}")
print(f"tokens: {_split_kp_tokens(text, exclude=exclude)!r}")
