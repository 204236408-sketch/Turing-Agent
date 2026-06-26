from __future__ import annotations

from sqlalchemy.orm import Session

from models import VideoResource


KP_ALIASES: dict[str, set[str]] = {
    "栈、队列和数组": {"栈和队列", "栈", "队列", "数组"},
    "树与二叉树": {"树与二叉树", "二叉树", "树", "树、森林"},
    "进程与线程": {"进程与线程", "进程", "线程", "同步与互斥", "进程同步", "死锁"},
    "内存管理": {"内存管理", "分页", "分页管理", "虚拟内存", "页面置换", "LRU", "FIFO", "页面置换算法"},
    "计算机系统概述": {"计算机系统概述", "概述", "OS概述"},
    "输入输出系统": {"输入输出系统", "I/O", "IO", "输入输出", "IO系统", "总线与 I/O", "总线与IO"},
    "总线": {"总线", "总线与 I/O", "总线与IO"},
    "中央处理器": {"中央处理器", "CPU", "数据通路", "控制器"},
    "数据的表示和运算": {"数据的表示和运算", "数据表示", "运算", "数据表示与运算", "浮点数", "数据通路"},
    "文件管理": {"文件管理", "文件系统", "文件", "目录"},
    "输入输出管理": {"输入输出管理", "I/O管理", "IO管理", "输入输出", "I/O", "IO系统"},
    "传输层": {"传输层", "TCP", "UDP"},
    "计算机网络体系结构": {"计算机网络体系结构", "体系结构", "网络体系结构"},
    "串": {"串", "字符串"},
    "查找": {"查找", "散列"},
    "排序": {"排序"},
    "图": {"图"},
    "线性表": {"线性表", "链表", "顺序表"},
    "存储系统": {"存储系统", "Cache", "主存", "存储器", "高速缓冲", "虚拟存储器"},
    "指令系统": {"指令系统", "指令", "寻址", "CISC", "RISC", "流水线"},
    "物理层": {"物理层", "通信基础", "传输介质"},
    "数据链路层": {"数据链路层", "介质访问", "局域网", "差错控制"},
    "网络层": {"网络层", "IP", "IPv4", "IPv6", "路由"},
    "应用层": {"应用层", "DNS", "万维网", "HTTP", "电子邮件"},
    "绪论": {"绪论", "算法", "算法评价"},
}


def expand_aliases(kp: str) -> set[str]:
    kp_lower = kp.lower()
    expanded = {kp_lower}
    if kp in KP_ALIASES:
        expanded.update(a.lower() for a in KP_ALIASES[kp])
    for ch, aliases in KP_ALIASES.items():
        for a in aliases:
            if a.lower() == kp_lower:
                expanded.add(ch.lower())
                expanded.update(x.lower() for x in KP_ALIASES.get(ch, set()))
    return expanded


def recommend_videos(
    db: Session,
    subject: str = "",
    knowledge_point: str = "",
    limit: int = 8,
) -> list[dict]:
    query = db.query(VideoResource).filter(VideoResource.is_deleted == False)
    if subject:
        query = query.filter(VideoResource.subject == subject)
    all_videos = query.order_by(VideoResource.quality_score.desc()).all()
    if not all_videos:
        all_videos = (
            db.query(VideoResource)
            .filter(VideoResource.is_deleted == False)
            .order_by(VideoResource.quality_score.desc())
            .limit(20)
            .all()
        )
    kp = knowledge_point or ""
    expanded = expand_aliases(kp) if kp else set()

    def match_score(v: VideoResource) -> int:
        vkp = (v.knowledge_point or "").lower()
        title = (v.title or "").lower()
        if kp and vkp == kp.lower():
            return 100
        if expanded and vkp in expanded:
            return 80
        for a in expanded:
            if a and len(a) >= 2 and a in vkp:
                return 70
        for a in expanded:
            if a and len(a) >= 2 and a in title:
                return 50
        if kp and vkp and len(vkp) >= 2 and vkp in kp.lower():
            return 30
        return 10

    scored = [(match_score(v), v) for v in all_videos]
    scored.sort(key=lambda x: (-x[0], -(x[1].quality_score or 0)))
    seen: set[str] = set()
    items: list[dict] = []
    for score, v in scored:
        if v.url in seen:
            continue
        seen.add(v.url)
        items.append({
            "id": v.id,
            "title": v.title,
            "platform": v.platform or "Bilibili",
            "url": v.url,
            "cover_url": v.cover_url or "",
            "duration": v.duration or "",
            "author": v.author or "",
            "reason": v.reason or "",
            "subject": v.subject,
            "knowledge_point": v.knowledge_point or "",
            "match_level": (
                "exact" if score >= 100
                else ("alias" if score >= 70
                      else ("keyword" if score >= 50 else "subject"))
            ),
        })
        if len(items) >= limit:
            break
    return items
