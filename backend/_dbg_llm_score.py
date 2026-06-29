from services.video_service import _split_kp_tokens, _wangdao_llm_keyword_score
import sys
sys.path.insert(0, '.')

class V:
    def __init__(self, kp, title='', keywords=''):
        self.knowledge_point = kp
        self.title = title
        self.keywords = keywords

subject = '操作系统'
kp_section = '虚拟内存管理'
kp_kws = ['虚拟内存', '页表', '缺页中断', '页面置换', 'TLB']

sec_tokens = _split_kp_tokens(kp_section, exclude={subject})
print('sec_tokens:', sec_tokens)
long_tokens = [t for t in sec_tokens if len(t) >= 3]
print('long_tokens:', long_tokens)
print()

# 测试
v = V('请求分页管理方式', '王道计算机考研 操作系统 - 5.3.2_请求分页管理方式',
      '["请求分页", "页表机制", "缺页中断", "页面置换", "虚拟内存"]')
v_target = (v.knowledge_point + ' ' + v.title).lower()
print('v_target:', v_target)
print('long_tokens in v_target:', [t for t in long_tokens if t.lower() in v_target])
print('section_specific_present:', any(t.lower() in v_target for t in long_tokens))
print()

llm_s = _wangdao_llm_keyword_score(v, kp_kws, kp_section, subject)
print('llm_s =', llm_s)

# 虚拟内存基本概念
v2 = V('虚拟内存的基本概念', '王道计算机考研 操作系统 - 5.3.1_虚拟内存的基本概念',
       '["虚拟内存", "分页", "缺页", "地址映射", "页面置换"]')
llm_s2 = _wangdao_llm_keyword_score(v2, kp_kws, kp_section, subject)
print('llm_s2 =', llm_s2)
