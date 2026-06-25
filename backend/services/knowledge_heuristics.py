SUBJECT_KEYWORDS: list[tuple[list[str], str]] = [
    (["操作", "进程", "线程", "页面", "lru", "fifo", "缺页", "死锁", "信号量", "调度"], "操作系统"),
    (["tcp", "udp", "ip", "路由", "交换", "http", "握手", "dns", "arp"], "计算机网络"),
    (["二叉树", "排序", "查找", "栈", "队列", "链表", "图", "哈希"], "数据结构"),
    (["cpu", "指令", "cache", "流水", "中断", "dma", "存储", "浮点"], "计算机组成原理"),
]

KP_KEYWORDS: list[tuple[list[str], str]] = [
    (["页面", "lru", "fifo", "opt", "clock", "缺页", "置换"], "页面置换算法"),
    (["进程", "线程", "同步", "互斥", "信号量", "死锁", "调度"], "进程管理"),
    (["tcp", "udp", "time_wait", "握手", "挥手", "拥塞"], "传输层"),
    (["二叉树", "遍历", "前序", "中序", "后序", "层序"], "树与二叉树"),
    (["路由", "ip", "子网", "cidr", "nat"], "网络层"),
    (["cache", "缓存", "主存", "dma", "中断", "寻址"], "存储系统"),
]


def infer_subject(query: str) -> str:
    q_lower = query.lower()
    for keywords, subject in SUBJECT_KEYWORDS:
        if any(k in q_lower for k in keywords):
            return subject
    return ""


def infer_knowledge_point(query: str) -> str:
    q_lower = query.lower()
    for keywords, kp in KP_KEYWORDS:
        if any(k in q_lower for k in keywords):
            return kp
    return ""


def infer_all(query: str) -> dict:
    return {
        "subject": infer_subject(query),
        "knowledge_point": infer_knowledge_point(query),
    }
