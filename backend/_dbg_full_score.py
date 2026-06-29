from services.video_service import _split_kp_tokens, _wangdao_llm_keyword_score, _wangdao_match_score, _wangdao_section_alignment
import sys
sys.path.insert(0, '.')

class V:
    def __init__(self, kp, title='', keywords=''):
        self.knowledge_point = kp
        self.title = title
        self.keywords = keywords

subject = '操作系统'
kp_section = '虚拟内存管理'
kp_name = '内存管理'
kp_kws = ['虚拟内存', '页表', '缺页中断', '页面置换', 'TLB']

videos = [
    V('两级页表', '王道计算机考研 操作系统 - 5.3.3_两级页表',
      '["两级页表", "页表结构", "页表分级", "地址映射", "虚拟内存"]'),
    V('请求分页管理方式', '王道计算机考研 操作系统 - 5.3.2_请求分页管理方式',
      '["请求分页", "页表机制", "缺页中断", "页面置换", "虚拟内存"]'),
    V('虚拟内存的基本概念', '王道计算机考研 操作系统 - 5.3.1_虚拟内存的基本概念',
      '["虚拟内存", "分页", "缺页", "地址映射", "页面置换"]'),
    V('页面置换算法', '王道计算机考研 操作系统 - 5.3.4_页面置换算法',
      '["页面置换", "置换算法", "FIFO", "LRU", "缺页率"]'),
]

for v in videos:
    s = _wangdao_match_score(v, kp_name, kp_section, subject)
    llm_s = _wangdao_llm_keyword_score(v, kp_kws, kp_section, subject)
    align = _wangdao_section_alignment(v, kp_name, kp_section, subject)
    if llm_s >= 60 and llm_s > s:
        s_final = max(s, llm_s)
    elif llm_s >= 40:
        s_final = min(100, max(s, llm_s) + 5)
    else:
        s_final = s
    print(f'{v.knowledge_point}: match={s} llm={llm_s} align={align} final={s_final}')
