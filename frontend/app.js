const theme=document.body.dataset.theme;
const themeName={cockpit:"智能学习驾驶舱",workspace:"轻量学习工作台",study:"沉浸式研习空间"}[theme];
const pages=[
 ["home","⌂","学习首页"],["qa","✦","知识问答"],["question","✎","智能出题"],["mistake","!","错题本"],["forum","◎","学习论坛"],["report","▥","学习报告"]
];
const questionBank=[
 {meta:"2026 模拟 · 第 1 题 · 2 分",title:"某系统为进程分配 3 个页框，页面访问序列为 1, 2, 3, 1, 4, 2, 5。采用 LRU 算法时，缺页次数为多少？",options:["A. 4 次","B. 5 次","C. 6 次","D. 7 次"],reason:"你之前在 LRU 缺页次数统计中多次遗漏页面更新，本题用于专项巩固。",hint:"先画出 3 个页框，再按访问顺序逐项更新最近使用状态。",answer:"标准答案：C · 共发生 6 次缺页。"},
 {meta:"2026 模拟 · 第 2 题 · 2 分",title:"在请求分页系统中，若某进程访问的页面不在内存中，此时首先会发生什么？",options:["A. 进程直接终止","B. 产生缺页中断","C. 立即执行页面置换","D. 修改页表有效位"],reason:"该题用于检查你是否真正理解缺页处理流程，而不只是会计算缺页次数。",hint:"CPU 访问页表时发现有效位为 0，需要先转入操作系统处理。",answer:"标准答案：B · 首先产生缺页中断，再由操作系统判断调页与置换。"},
 {meta:"2026 模拟 · 第 3 题 · 2 分",title:"下列页面置换算法中，可能产生 Belady 异常的是哪一种？",options:["A. FIFO","B. LRU","C. OPT","D. Clock 改进算法"],reason:"你正在复习 FIFO、LRU 与 OPT 的差异，本题用于强化算法性质辨析。",hint:"思考增加页框数后，缺页次数反而可能增加的经典算法。",answer:"标准答案：A · FIFO 可能产生 Belady 异常。"}
];
let currentQuestionIndex=0;
let activeQuestions=[...questionBank];
let countdownTimer=null;
const app=document.getElementById("app");
function applyBrandName(html){return html.replaceAll("重生之我是图灵","重生之我是图灵")}
app.innerHTML=applyBrandName(loginHTML());
// 登录页面Mock数据：当前固定演示账号
function loginHTML(){
  return `<section class="login turing-login">
    <div class="login-art turing-story">
      <img class="turing-hero-image" src="assets/turing-408-hero.png" alt="图灵在密码研究室中备考计算机 408 的主题插画">
      <div class="turing-shade"></div>
      <div class="turing-brand">
        <div class="turing-monogram">T</div>
        <div class="logo">
          重生之我是图灵
          <small>TURING 408 AGENT</small>
        </div>
      </div>
      <article class="login-copy turing-copy">
        <span class="eyebrow">A TURING REBIRTH STORY</span>
        <h1>《重生之图灵备战408》</h1>
        <div class="story-scroll">
          <h2>简介</h2>
          <p>穿越成艾伦·图灵的我，拥有现代考研生的记忆。</p>
          <p>本该潜心研究可计算性理论、破解恩尼格玛密码，如今多了一桩心事——备考计算机408。</p>
          <p>我亲手创造了图灵机，计算机组成原理的源头出自我的构想；各类算法都是我随手推演出来的数据结构；我提前研究进程调度思想，铺垫了操作系统；依靠密码研究，吃透通信原理，拿捏计算机网络。</p>
          <p>别人熬夜背诵的408考点，全都是我自己当年提出的理论。</p>
          <p>考试那天，看着试卷上一道道题目，内心感慨：居然要答我自己发明的东西。</p>
          <div class="opening">
            <span>开篇</span>
            <p>睁开眼，我便是图灵。可脑海里挥之不去的，是堆积如山的408复习资料。</p>
            <p>全世界都等着我开创计算机时代，而我眼下首要任务，是把我毕生搭建的整套理论背熟，应付一场考研考试。</p>
          </div>
        </div>
      </article>
      <div class="login-flow turing-flow">
        <span>计算理论</span>
        <span>数据结构</span>
        <span>组成原理</span>
        <span>操作系统</span>
        <span>计算机网络</span>
      </div>
    </div>
    <div class="login-form">
      <div class="form-card">
        <span class="eyebrow">TURING 408 AGENT</span>
        <h2>欢迎回来，未来的计算机先驱</h2>
        <p>继续这场由图灵本人亲自参加的 408 备考计划</p>
        <div class="field">
          <label>邮箱或用户名</label>
          <input value="demo@turing408.ai">
        </div>
        <div class="field">
          <label>密码</label>
          <input type="password" value="123456">
        </div>
        <button class="primary full" onclick="enterApp()">进入图灵学习空间</button>
        <button class="ghost full" onclick="toast('注册流程：账号信息 → 验证 → 创建用户画像')">创建新账号</button>
        <div class="demo-note">演示账号已自动填充 · 数据仅保存在本地</div>
      </div>
    </div>
  </section>`
}
function enterApp(){
  app.innerHTML=applyBrandName(shellHTML())
  repairPagePlacement()
  bindAll()
  showPage("home")
}
function repairPagePlacement(){
  const main=document.querySelector(".shell .main")
  if(!main)return
  ;["forum","report"].forEach(id=>{
    const page=document.getElementById(id)
    if(page&&page.parentElement!==main)main.appendChild(page)
  })
}
function knowledgeGraphHTML(){
  const groups={
    数据结构:[["算法",50,12,"hot"],["排序",28,25,"core"],["查找",23,51,"core"],["图",24,75,"core"],["树与二叉树",52,78,"hot"],["线性表",76,27,"core"],["栈和队列",84,50,"hot"],["串",76,76,"core"]],组成原理:[["计算机系统概述",54,13,"core"],["数据的表示和运算",80,27,"core"],["存储系统",84,54,"hot"],["指令系统",62,75,"core"],["中央处理器",36,73,"core"],["总线",20,50,"core"],["I/O系统",29,27,"core"]],操作系统:[["进程管理",74,24,"core"],["处理机调度",88,41,"core"],["同步与互斥",80,70,"hot"],["内存管理",48,78,"core"],["文件管理",20,70,"core"],["输入/输出",13,43,"core"],["操作系统概述",40,20,"core"]],计算机网络:[["计算机网络体系结构",53,13,"core"],["物理层",82,26,"core"],["数据链路层",82,57,"hot"],["网络层",52,78,"core"],["传输层",21,64,"core"],["应用层",16,34,"core"]]
  };
  const children={
    数据结构:["顺序表","链表","队列","KMP","遍历","最短路径","二分查找","快速排序","堆排序","哈希表","并查集","B树"],组成原理:["补码","浮点数","存储芯片","Cache","虚拟存储器","寻址方式","流水线","中断","DMA","总线仲裁","磁盘"],操作系统:["进程状态","线程","调度算法","信号量","死锁","分页","页面置换","文件分配","磁盘调度","设备管理","I/O控制"],计算机网络:["OSI模型","TCP/IP","编码","差错控制","以太网","ARP","IP","路由算法","TCP","UDP","HTTP","DNS"]
  };
  const colors={
    数据结构:"#7da2e3",组成原理:"#d9b16f",操作系统:"#df9fbb",计算机网络:"#72c2a9"
  };
  return `<article class="card knowledge-graph-card"><div class="kg-toolbar"><div><h3>408 全局知识图谱</h3><p>按四科完整考纲展示知识点关系，可切换单科视图或总览。</p></div><div class="kg-tabs"><button class="active" data-graph-filter="all">总览</button>${Object.keys(groups).map(x=>`<button data-graph-filter="${x}">${x}</button>`).join("")}</div></div><div class="kg-actions"><button id="structureLayer" class="active">知识结构</button><button id="masteryLayer">叠加掌握状态</button><span id="layerNote">当前展示完整知识结构</span></div><div class="kg-canvas" id="knowledgeGraphCanvas">${Object.entries(groups).map(([subject,nodes],groupIndex)=>`<section class="kg-quadrant kg-q${groupIndex+1}" data-graph-group="${subject}" style="--kg-color:${colors[subject]}"><div class="kg-watermark">${subject}</div><svg class="kg-lines" viewBox="0 0 100 100" preserveAspectRatio="none">${nodes.map(n=>`<line x1="50" y1="50" x2="${n[1]}" y2="${n[2]}"></line>`).join("")}</svg><div class="kg-center">${subject}</div>${nodes.map((n,nodeIndex)=>`<button class="graph-point kg-node ${n[3]}" style="--x:${n[1]}%;--y:${n[2]}%" data-subject="${subject}" data-level="${n[3]==="hot"?"high":"key"}"><span>${n[0]}</span>${children[subject].slice(nodeIndex,nodeIndex+2).map((child,childIndex)=>`<i class="kg-child c${childIndex+1}">${child}</i>`).join("")}</button>`).join("")}</section>`).join("")}</div><div class="kg-legend"><span><i class="normal"></i>普通知识点</span><span><i class="important"></i>重点知识点</span><span><i class="weak"></i>个人薄弱点（叠加后显示）</span></div></article>`
}
function enhanceKnowledgeGraph(){
  const home=document.getElementById("home")
  const old=home?.querySelector(".two-col")
  if(!old)return
  old.className="home-knowledge-layout"
  old.innerHTML=knowledgeGraphHTML()
}
function shellHTML(){
  return `<div class="shell">
    <aside class="sidebar">
      <div class="brand-lockup">
        <div class="brand-mark">图</div>
        <div class="logo">
          重生之我是图灵
          <small>TURING 408 AGENT</small>
        </div>
      </div>
      <nav class="nav">
        ${pages.map(p=>`<button data-page="${p[0]}"><i>${p[1]}</i>${p[2]}</button>`).join("")}
      </nav>
      <div class="memory-chip">
        <b>🔥 连续学习 7 天</b>
        长期记忆已加载。今天再学习 18 分钟，即可完成本周目标。
      </div>
    </aside>
    <div class="main">
      <header class="topbar">
        <div>
          <h1 id="pageTitle">学习首页</h1>
          <p id="pageSub">基于长期记忆生成的个性化学习空间</p>
        </div>
        <div class="top-actions">
          <button class="account-trigger" id="openAccount" aria-label="打开个人账户设置">
            <span class="avatar" id="topAvatar">林</span>
            <span class="account-brief">
              <b id="topUserName">林同学</b>
              <small>个人账户</small>
            </span>
            <span class="account-arrow">⌄</span>
          </button>
        </div>
      </header>
      ${homeHTML()}
      ${qaHTML()}
      ${questionHTML()}
      ${mistakeHTML()}
      ${forumHTML()}
      ${reportHTML()}
    </div>
  </div>
  ${accountSettingsHTML()}
  <div id="toast" style="position:fixed;right:20px;bottom:24px;background:var(--ink);color:var(--panel);padding:11px 14px;border-radius:9px;font-size:9px;opacity:0;transition:.2s;z-index:200"></div>`
}
function accountSettingsHTML(){
  return `<div class="account-mask" id="accountMask"></div>
    <aside class="account-panel compact-account-panel" id="accountPanel" aria-hidden="true">
      <div class="account-panel-head">
        <div>
          <span class="eyebrow">PERSONAL CENTER</span>
          <h2>个人账户</h2>
          <p>修改账号昵称与登录密码</p>
        </div>
        <button class="account-close" id="closeAccount" aria-label="关闭账户设置">×</button>
      </div>
      <div class="account-setting-list">
        <section class="account-setting-item">
          <div class="setting-index">01</div>
          <div class="setting-body">
            <label for="accountName">账号昵称</label>
            <input id="accountName" value="林同学" autocomplete="nickname">
            <small>修改后按 Enter 或点击空白处自动保存</small>
          </div>
        </section>
        <section class="account-setting-item password-list-item">
          <div class="setting-index">02</div>
          <div class="setting-body">
            <label>修改密码</label>
            <div class="inline-password-fields">
              <input id="oldPassword" type="password" placeholder="当前密码" autocomplete="current-password">
              <input id="newPassword" type="password" placeholder="新密码（至少 8 位）" autocomplete="new-password">
              <input id="confirmPassword" type="password" placeholder="确认新密码" autocomplete="new-password">
            </div>
            <small>在确认密码框按 Enter 完成修改</small>
          </div>
        </section>
      </div>
    </aside>`
}
function forumHTML(){
  return `<section class="page" id="forum">
    <div class="forum-hero">
      <div>
        <span class="eyebrow">TURING 408 COMMUNITY</span>
        <h2>一起讨论，也一起上岸</h2>
        <p>分享解题思路、复习方法与踩坑记录，让每一次提问都成为可复用的学习经验。</p>
      </div>
      <button class="primary forum-create" id="openForumComposer">＋ 发布新讨论</button>
    </div>
    <div class="forum-toolbar card">
      <div class="forum-categories">${["全部","数据结构","计算机组成原理","操作系统","计算机网络","经验分享"].map((x,i)=>`<button class="${i===0?"active":""}" data-forum-category="${x}">${x}</button>`).join("")}</div>
      <label class="forum-search"><span>⌕</span><input id="forumSearch" placeholder="搜索讨论主题或关键词"></label>
    </div>
    <div class="forum-layout">
      <section class="forum-feed" id="forumFeed">${"<div class='card' style='text-align:center;padding:40px;color:var(--muted);font-size:10px'>正在加载讨论列表…</div>"}</section>
      <aside class="forum-side">
        <article class="card forum-rules">
          <div class="head"><h3>社区公约</h3><span class="tag">友好讨论</span></div>
          <p>围绕 408 学习交流，尊重不同解题路径；发布资料时请注明来源，不分享侵权内容。</p>
        </article>
        <article class="card forum-hot">
          <div class="head"><h3>今日热议</h3><span class="tag" id="hotTag">TOP 3</span></div>
          <ol id="hotList"><li style="text-align:center;color:var(--muted);font-size:9px;padding:15px 0;border:0">加载中…</li></ol>
        </article>
        <article class="card forum-checkin">
          <b>本周社区打卡</b><strong id="checkinCount">-</strong><span>位同学完成学习记录</span>
          <button class="soft" id="forumCheckin">今日打卡</button>
        </article>
      </aside>
    </div>
    <div class="forum-modal-mask" id="forumModalMask"></div>
    <div class="forum-modal" id="forumModal">
      <div class="head">
        <div><span class="eyebrow">NEW DISCUSSION</span><h3>发布新讨论</h3></div>
        <button class="account-close" id="closeForumComposer">×</button>
      </div>
      <div class="field"><label>选择板块</label><select id="forumSubject"><option>数据结构</option><option>组成原理</option><option>操作系统</option><option>计算机网络</option><option>经验分享</option></select></div>
      <div class="field"><label>讨论标题</label><input id="forumTitle" placeholder="用一句话说明你想讨论的问题"></div>
      <div class="field"><label>详细内容</label><textarea id="forumContent" placeholder="补充背景、你的思考或已经尝试过的方法"></textarea></div>
      <div class="forum-modal-actions"><button class="ghost" id="cancelForumPost">取消</button><button class="primary" id="publishForumPost">发布讨论</button></div>
    </div>
  </section>`
}
function forumPostCardHTML(p){
  const likeCount=Number(p.like_count||0);
  const commentCount=Number(p.comment_count||0);
  return `<article class="card forum-post" data-post-id="${p.id}" data-forum-subject="${escapeHtml(String(p.subject||""))}">
    <div class="forum-vote">
      <button data-forum-like aria-label="点赞">赞</button>
      <b data-forum-like-count>${likeCount}</b>
    </div>
    <div class="forum-post-body">
      <div class="forum-post-meta">
        <span class="forum-subject">${escapeHtml(String(p.subject||""))}</span>
        ${p.is_hot?'<span class="forum-hot-tag">热门</span>':""}
        <span>${escapeHtml(String(p.time||""))}</span>
      </div>
      <h3>${escapeHtml(p.title)}</h3>
      <p>${escapeHtml(p.content)}</p>
      <div class="forum-post-footer">
        <span><i>${p.avatar}</i>${p.author}</span>
        <div>
          <button class="forum-ai-button" data-forum-ai="${p.id}"><span>AI</span> 小助手解答</button>
          <button data-forum-comment="${p.id}">评论 ${p.comment_count}</button>
        </div>
      </div>
      <div class="forum-ai-answer" id="forumAi${p.id}">
        <div class="forum-ai-head">
          <span class="forum-ai-mark">AI</span>
          <div><b>图灵 AI 小助手</b><small>结合 408 考纲与帖子内容生成</small></div>
          <button data-close-ai>收起</button>
        </div>
        <div class="forum-ai-content" id="forumAiContent${p.id}">
          <p style="color:var(--muted)">点击「小助手解答」生成 AI 回答…</p>
        </div>
        <div class="forum-ai-followup">
          <input placeholder="继续追问这个问题…">
          <button data-ai-followup="${p.id}">发送</button>
        </div>
      </div>
      <div class="forum-comment-box" id="forumComment${p.id}">
        <input placeholder="写下你的回复…">
        <button class="primary" data-submit-comment="${p.id}">回复</button>
      </div>
      <div class="forum-comments-list" id="forumCommentsList${p.id}" style="display:none;margin-top:10px">
        <div class="forum-comments-items" id="forumCommentsItems${p.id}"></div>
      </div>
    </div>
  </article>`
}
function forumAiAnswer(p){
  return ""
}
function homeHTML(){
  const subjects=[["数据结构",[["线性表","key"],["栈和队列","high"],["树与二叉树","high"],["图","key"],["查找与排序","high"]]],["计算机组成原理",[["数据表示与运算","key"],["存储系统","high"],["指令系统","key"],["中央处理器","high"],["总线与 I/O","key"]]],["操作系统",[["进程与线程","key"],["同步与互斥","high"],["死锁","high"],["内存管理","high"],["文件系统","key"]]],["计算机网络",[["体系结构","key"],["数据链路层","high"],["网络层","high"],["传输层","high"],["应用层","key"]]]];
  return `<section class="page" id="home">
    <div class="home-focus-grid">
      <article class="card hero-main">
        <div class="hero-task">
          <span class="eyebrow">TODAY'S AGENT PLAN</span>
          <h2>今天优先攻克<br>页面置换算法</h2>
          <p>原因：你最近 3 次在 LRU 缺页次数统计中出错，历史错误模式为"规则混淆 + 计算遗漏"。</p>
          <button class="primary" onclick="showPage('question')">开始个性化训练 →</button>
        </div>
      </article>
      <article class="card countdown-card">
        <div class="exam-countdown">
          <span>2026 考研初试倒计时</span>
          <div class="countdown-days"><b id="countdownDays">180</b><small>天</small></div>
          <div class="countdown-clock">
            <div><b id="countdownHours">00</b><small>时</small></div><i>:</i>
            <div><b id="countdownMinutes">00</b><small>分</small></div><i>:</i>
            <div><b id="countdownSeconds">00</b><small>秒</small></div>
          </div>
          <p id="examDateLabel">目标日期：2026 年 12 月 19 日</p>
        </div>
      </article>
      <article class="card today-recommend-card">
        <div class="head"><h3>今日推荐</h3></div>
        <div class="recommend">
          <div class="rec"><b>操作系统 · 页面置换算法</b><small>3 次类似错误 · 建议中等难度</small></div>
          <div class="rec"><b>计算机网络 · TCP 握手</b><small>近期连续追问 SYN / ACK 顺序</small></div>
          <div class="rec"><b>数据结构 · 二叉树遍历</b><small>间隔复习已到期</small></div>
        </div>
      </article>
    </div>
    <div class="stats">
      <div class="card stat"><small>本周答题</small><strong>36</strong><span class="delta">27 道正确</span></div>
      <div class="card stat"><small>综合正确率</small><strong>75%</strong><span class="delta">↑ 6%</span></div>
      <div class="card stat"><small>长期薄弱点</small><strong>3</strong><span class="delta">已改善 2 个</span></div>
      <div class="card stat"><small>记忆条目</small><strong>28</strong><span class="delta">本周新增 7 条</span></div>
    </div>
    <div class="two-col">
      <article class="card progress-card">
        <div class="head"><h3>四科学习进度</h3></div>
        ${subjects.map(s=>`<div class="subject-progress"><b>${s[0]}</b>${s[1].map(p=>`<span class="dot ${p[1]}"></span>`).join("")}</div>`).join("")}
      </article>
      <article class="card quick-qa-card">
        <div class="head"><h3>快捷问答</h3></div>
        <div class="qa-quick-list">
          <div class="quick-qa" onclick="qaQuickAsk('请解释 LRU 页面置换算法的基本思想')"><b>Q</b><span>请解释 LRU 页面置换算法的基本思想</span></div>
          <div class="quick-qa" onclick="qaQuickAsk('TCP 三次握手为什么是三次而不是两次？')"><b>Q</b><span>TCP 三次握手为什么是三次而不是两次？</span></div>
          <div class="quick-qa" onclick="qaQuickAsk('二叉树的中序遍历非递归实现')"><b>Q</b><span>二叉树的中序遍历非递归实现</span></div>
        </div>
      </article>
    </div>
  </section>`
}
let currentConversationId = null;
function qaHTML(){
  return `<section class="page" id="qa">
    <div class="chat-layout">
      <aside class="card conversation-list">
        <div class="head">
          <h3>历史会话</h3>
          <button class="soft" id="newConversation">＋</button>
        </div>
        <div id="conversationItems">
          <div class="conversation-empty">暂无历史会话</div>
        </div>
        <div class="memory">
          <b>会话记忆</b>
          <p>最近 5–10 轮 + 当前摘要 + 长期记忆 + 语义检索</p>
        </div>
      </aside>
      <article class="card chat">
        <div class="head">
          <h3 id="currentChatTitle">知识问答</h3>
        </div>
        <div class="messages" id="messages">
          <div class="chat-empty-state">
            <p>点击「＋」开始新的知识问答会话</p>
            <p>输入 408 相关问题，AI Agent 将结合知识库和你的学习记忆回答</p>
          </div>
        </div>
        <div class="composer">
          <input id="qaInput" placeholder="输入你的 408 学习问题…">
          <button class="primary" id="sendQa">发送</button>
        </div>
      </article>
    </div>
  </section>`
}
function questionHTML(){
  const causes=["概念理解错误","审题错误","计算错误","知识遗忘","规则混淆","步骤遗漏","表达不完整","综合应用能力不足"];
  return `<section class="page" id="question">
    <div class="question-launcher">
      <div class="launch-card">
        <span>☷</span>
        <div><b>自由选择出题</b><small>从四科、章节、难度和题型中任意组合</small></div>
        <button class="primary" id="openManualDrawer">左侧选择</button>
      </div>
      <div class="launch-or">OR</div>
      <div class="launch-card">
        <span>✦</span>
        <div><b>智能推荐出题</b><small>根据薄弱点、错题和高频提问生成</small></div>
        <button class="primary" id="openSmartDrawer">右侧选择</button>
      </div>
    </div><div class="question-config"><span class="tag">当前出题条件</span><span class="config-chip" id="configMode">智能推荐</span><span class="config-chip" id="configSubject">操作系统</span><span class="config-chip" id="configPoint">页面置换算法</span><span class="config-chip" id="configDifficulty">中等</span><span class="config-chip" id="configType">选择题 · 3 道</span><button class="ghost" id="changeConfig">重新选择</button></div><div class="question-stage"><button class="question-switch prev" id="prevQuestion" aria-label="上一题">‹</button><article class="card question-card"><div class="question-meta"><span id="questionMeta">2026 模拟 · 第 1 题 · 2 分</span><span class="question-position"><b id="currentQuestionNo">1</b> / <span id="totalQuestionNo">3</span></span><span>☆ 收藏</span></div><div class="rec"><b id="recommendTitle">为什么推荐这道题？</b><small id="recommendReason">你之前在 LRU 缺页次数统计中多次遗漏页面更新，本题用于专项巩固。</small></div><h3 class="question-title" id="questionTitle">某系统为进程分配 3 个页框，页面访问序列为 1, 2, 3, 1, 4, 2, 5。采用 LRU 算法时，缺页次数为多少？</h3><div id="options">${["A. 4 次","B. 5 次","C. 6 次","D. 7 次"].map(x=>`<div class="option">${x}</div>`).join("")}</div><div class="tools"><button class="soft" data-drawer="hint">💡 分步提示</button><button class="soft" data-drawer="video">▶ 推荐视频</button><button class="primary" id="submitAnswer">✓ 提交答案</button></div><div class="drawer" id="hint"><h4>提示 1 / 3</h4><p id="hintText">本题考查 LRU 页面置换算法。先画出 3 个页框，再逐项处理访问序列。</p><button class="ghost" id="nextHint">下一层提示</button></div><div class="drawer" id="video"><h4>相关公开视频</h4><div id="videoContent"></div></div><div class="drawer" id="answer"><h4>批改结果：回答错误</h4><p id="answerText">你的答案：B · 5 次。标准答案：C · 6 次。系统初步判断可能存在计算遗漏，请由用户确认真实错因。</p></div><div class="wrong-action" id="wrongAction"><b>这道题为什么答错？</b><p>请选择一个或多个最符合的原因。用户确认的错因将作为高可信证据写入长期学习记忆。</p><button class="primary" id="openCause">选择错因</button><div class="cause-detail" id="causeDetail"><div class="cause-options">${causes.map(x=>`<button data-cause="${x}">${x}</button>`).join("")}</div><div class="field"><label>补充说明（可选）</label><textarea id="causeNote" style="min-height:70px" placeholder="例如：我忘记在页面命中时更新最近访问顺序"></textarea></div><button class="primary" id="confirmCause">确认错因并记录到长期学习</button></div><div class="cause-summary" id="causeSummary"></div></div><div class="mastery"><span class="tag">本题掌握情况</span><button>掌握</button><button>不熟</button><button>不会</button></div></article><button class="question-switch next" id="nextQuestion" aria-label="下一题">›</button></div>${questionDrawersHTML()}</section>`}
function questionDrawersHTML(){
  return `<div class="drawer-mask" id="questionDrawerMask"></div>
<aside class="side-drawer left" id="manualDrawer">
    <div class="side-drawer-head">
      <div><h2>自由选择出题</h2><p>从完整 408 知识体系中任意组合训练条件</p></div>
      <button class="close-drawer" data-close-question>×</button>
    </div>
    <div class="select-block">
      <label>选择科目</label>
      <div class="choice-grid" data-choice-group="manualSubject">${["数据结构","计算机组成原理","操作系统","计算机网络"].map((x,i)=>`<button class="${i===2?"selected":""}" data-value="${x}">${x}</button>`).join("")}</div>
    </div>
    <div class="select-block">
      <label>选择章节 / 知识点</label>
      <div class="choice-list" data-choice-group="manualPoint"><div class="conversation-empty" style="grid-column:1/-1">切换科目后自动加载知识点</div></div>
    </div>
    <div class="select-block">
      <label>难度</label>
      <div class="choice-grid" data-choice-group="manualDifficulty">${["简单","中等","较难","真题难度"].map((x,i)=>`<button class="${i===1?"selected":""}" data-value="${x}">${x}</button>`).join("")}</div>
    </div>
    <div class="select-block">
      <label>题型</label>
      <div class="choice-grid" data-choice-group="manualType">${["选择题","填空题","简答题","综合题"].map((x,i)=>`<button class="${i===0?"selected":""}" data-value="${x}">${x}</button>`).join("")}</div>
    </div>
    <div class="select-block">
      <label>出题数量</label>
      <div class="choice-grid" data-choice-group="manualCount">${["1 道","3 道","5 道","10 道"].map((x,i)=>`<button class="${i===0?"selected":""}" data-value="${x}">${x}</button>`).join("")}</div>
    </div>
    <div class="drawer-footer">
      <button class="ghost" data-close-question>取消</button>
      <button class="primary" id="generateManual">按所选条件生成</button>
    </div>
  </aside>
  <aside class="side-drawer right" id="smartDrawer">
    <div class="side-drawer-head">
      <div><h2>智能推荐出题</h2><p>选择一种学习目标，Agent 自动确定具体条件</p></div>
      <button class="close-drawer" data-close-question>×</button>
    </div>
    <div class="select-block">
      <label>推荐方式</label>
      <div class="choice-list" data-choice-group="smartMode">
        <button class="selected" data-value="薄弱点强化" data-subject="操作系统" data-point="页面置换算法" data-difficulty="中等"><b>薄弱点强化</b><small>页面置换算法 · 最近 3 次答错 · 推荐中等题</small></button>
        <button data-value="最近错题复练" data-subject="计算机网络" data-point="TCP 三次握手" data-difficulty="简单"><b>最近错题复练</b><small>TCP 标志位顺序 · 2 次相似错误</small></button>
        <button data-value="高频提问专项" data-subject="数据结构" data-point="二叉树遍历" data-difficulty="中等"><b>高频提问专项</b><small>根据最近问答记录生成相关训练</small></button>
        <button data-value="已改善复测" data-subject="数据结构" data-point="线性表复杂度" data-difficulty="较难"><b>已改善知识点复测</b><small>验证掌握状态是否稳定，适当提高难度</small></button>
        <button data-value="四科随机综合" data-subject="408 综合" data-point="随机知识点" data-difficulty="混合"><b>四科随机综合</b><small>按考纲比例随机抽取，模拟阶段检测</small></button>
      </div>
    </div>
    <div class="select-block">
      <label>训练规模</label>
      <div class="choice-grid" data-choice-group="smartCount">${["3 道","5 道","10 道","20 道"].map((x,i)=>`<button class="${i===0?"selected":""}" data-value="${x}">${x}</button>`).join("")}</div>
    </div>
    <div class="select-block">
      <label>Agent 将参考</label>
      <div class="rec"><b>长期学习记忆</b><small>薄弱权重、错误模式、连续答对情况</small></div>
      <div class="rec"><b>最近学习行为</b><small>错题、问答、提示使用和掌握反馈</small></div>
    </div>
    <div class="drawer-footer">
      <button class="ghost" data-close-question>取消</button>
      <button class="primary" id="generateSmart">生成智能推荐题</button>
    </div>
  </aside>`
}
function ocrHTML(){
  return `<section class="page" id="ocr">
    <div class="ocr-steps">
      <span class="on">1 上传图片</span><span>2 PaddleOCR</span><span>3 人工校对</span><span>4 Agent 分析</span><span>5 更新记忆</span>
    </div>
    <div class="ocr-grid">
      <article class="card">
        <div class="head"><h3>上传错题图片</h3><span class="tag">PaddleOCR</span></div>
        <div class="drop" id="ocrDrop">
          <div>▣<br><b>拖拽试卷截图或笔记照片</b><br><small>支持 PNG / JPG · 建议只保留一道题</small></div>
        </div>
        <div class="tools">
          <button class="primary" id="ocrMock">选择图片并上传</button>
          <button class="ghost" id="ocrManualText">手动输入文本</button>
        </div>
      </article>
      <article class="card">
        <div class="head"><h3>识别文字与人工校对</h3><span class="tag" id="ocrStatus">等待识别</span></div>
        <div class="field"><textarea id="ocrText" placeholder="OCR 识别结果会显示在这里，可手动修正"></textarea></div>
        <div class="field"><label>你的答案</label><input id="ocrUserAnswer" placeholder="Agent 会根据题目自动推断标准答案"></div>
        <button class="primary" id="ocrAnalyze">提交错题分析 Agent</button>
      </article>
    </div>
    <article class="card" style="margin-top:14px">
      <div class="head"><h3>记忆增强错题分析</h3><span class="tag">mistake_summary + user_memory</span></div>
      <div class="analysis-grid">
        <div class="analysis-item wide"><small>状态</small><b>提交后由 Agent 自动推断标准答案、分析错因并写入长期记忆。</b></div>
      </div>
    </article>
  </section>`
}
function mistakeHTML(){
  return `<section class="page" id="mistake">
    <div class="book-toolbar">
      <div>
        <h2 id="mistakeTitle">我的题本</h2>
        <p id="mistakeSubtitle" style="font-size:9px;color:var(--muted);margin:5px 0 0">智能出题中标记“不熟”和“不会”的题目会自动进入对应题本</p>
      </div>
    </div>
    <div class="book-view active" id="book-overview">
      <div class="book-overview">
        <div class="book-entry" data-open-book="unfamiliar">
          <div class="book-icon">◉</div>
          <div><b>不熟题本</b><p>理解不够稳定，需要通过同类题巩固</p><span class="tag" id="unfamiliarTag">加载中…</span></div>
          <span class="book-count" id="unfamiliarCount">-</span>
        </div>
        <div class="book-entry" data-open-book="unknown">
          <div class="book-icon">×</div>
          <div><b>不会题本</b><p>尚未掌握，需要重新学习知识点</p><span class="tag">优先复习</span></div>
          <span class="book-count" id="unknownCount">-</span>
        </div>
        <div class="book-entry ocr-entry" data-open-book="ocr">
          <div class="book-icon">▣</div>
          <div><b>OCR 导入错题</b><p>上传试卷截图，识别、校对并分析后加入题本</p><span class="tag">PaddleOCR + Agent</span></div>
          <span class="book-count" style="font-size:14px">进入 →</span>
        </div>
      </div>
      <article class="card">
        <div class="head"><h3>题本使用建议</h3></div>
        <div class="plan-item"><i>01</i><div><b>先处理“不会题本”</b><small>结合知识讲解、分步提示和视频资源重新学习。</small></div></div>
        <div class="plan-item"><i>02</i><div><b>再处理“不熟题本”</b><small>通过同类练习验证是否真正掌握，连续答对后移出题本。</small></div></div>
        <div class="plan-item"><i>03</i><div><b>纸质错题使用 OCR 导入</b><small>识别后先人工校对，再提交 Agent 分析并更新长期记忆。</small></div></div>
      </article>
    </div>
    <div class="book-view" id="book-unfamiliar">
      <button class="ghost book-back" data-return-books>← 返回我的题本</button>
      <div class="book-list" id="unfamiliarBookList"><div class="conversation-empty">正在加载不熟题本…</div></div>
    </div>
    <div class="book-view" id="book-unknown">
      <button class="ghost book-back" data-return-books>← 返回我的题本</button>
      <div class="book-list" id="unknownBookList"><div class="conversation-empty">正在加载不会题本…</div></div>
    </div>
    <div class="book-view" id="book-ocr">${ocrWorkspaceHTML()}</div>
  </section>`
}
function ocrWorkspaceHTML(){
  return `<div class="ocr-workspace-head">
    <button class="ghost" id="backToBooks">← 返回题本列表</button>
    <div>
      <h2>OCR 导入</h2>
      <p>PaddleOCR 识别 → 校对 → Agent 推断答案 → 错题分析与记忆更新</p>
    </div>
  </div>
  <div class="ocr-steps">
    <span class="on">1 上传图片</span><span>2 PaddleOCR</span><span>3 人工校对</span><span>4 Agent 分析</span><span>5 更新记忆</span>
  </div>
  <div class="ocr-grid">
    <article class="card ocr-upload-card">
      <div class="head"><h3>上传错题图片</h3><span class="tag" id="ocrEngineTag">等待上传</span></div>
      <div class="drop ocr-preview-drop" id="ocrDrop">
        <div class="ocr-scan-line"></div>
        <img id="ocrPreviewImage" alt="已上传的错题图片">
        <div class="ocr-drop-placeholder" id="ocrDropPlaceholder">
          <span>▣</span><b>拖拽图片到这里</b><small>支持 PNG / JPG / WEBP / BMP，上传后由后端 OCR 返回识别文本</small>
        </div>
      </div>
      <div class="ocr-upload-meta" id="ocrUploadMeta">
        <b>尚未选择图片</b><small>上传完成后会显示文件名、大小和后端 OCR 引擎。</small>
      </div>
      <div class="tools">
        <button class="primary" id="ocrMock">选择图片并上传</button>
        <button class="ghost" id="ocrManualText">手动输入文本</button>
      </div>
    </article>
    <article class="card">
      <div class="head"><h3>识别文字与人工校对</h3><span class="tag" id="ocrStatus">等待识别</span></div>
      <div class="field"><textarea id="ocrText" placeholder="OCR 识别结果会显示在这里，可手动修正"></textarea></div>
      <div class="field"><label>你的答案</label><input id="ocrUserAnswer" placeholder="填写你当时的作答，Agent 会自行推断标准答案"></div>
      <button class="primary" id="ocrAnalyze">提交错题分析 Agent</button>
    </article>
  </div>
  <article class="card ocr-analysis-card" id="ocrAnalysisCard">
    <div class="head"><h3>记忆增强错题分析</h3><span class="tag">后端 Agent</span></div>
    <div class="analysis-grid" id="ocrAnalysisGrid">
      <div class="analysis-item wide"><small>状态</small><b>等待 OCR 识别与 Agent 分析</b></div>
    </div>
    <div class="tools" id="ocrAnalysisTools" style="display:none">
      <button class="primary" id="saveOcrMistake">返回题本列表</button>
      <button class="ghost" id="generateOcrPractice">生成 3 道同类题</button>
    </div>
  </article>`
}
let notebookCache = null;
async function loadMistakeNotebook(){
  try{
    const data = await apiRequest("/api/mistakes/notebook?status=不熟,不会");
    notebookCache = data;
    const payload = data.data || data;
    const stats = payload.stats || {};
    const el1 = document.getElementById("unfamiliarCount");
    const el2 = document.getElementById("unknownCount");
    const tag = document.getElementById("unfamiliarTag");
    if(el1) el1.textContent = stats.unfamiliar || 0;
    if(el2) el2.textContent = stats.unknown || 0;
    if(tag) tag.textContent = stats.total ? "已同步后端" : "暂无数据";
    return data;
  }catch(error){
    console.error(error);
    const el1 = document.getElementById("unfamiliarCount");
    const el2 = document.getElementById("unknownCount");
    if(el1) el1.textContent = "0";
    if(el2) el2.textContent = "0";
    return null;
  }
}
function renderMistakeCards(items, type){
  const container = document.getElementById(`${type}BookList`);
  if(!container) return;
  if(!items || !items.length){
    container.innerHTML = `<div class="conversation-empty">暂无${type==="unfamiliar"?"不熟":"不会"}的题目</div>`;
    return;
  }
  container.innerHTML = items.map(item => {
    const optionsHtml = item.options_json ? (() => {
      try{
        const opts = JSON.parse(item.options_json);
        return `<div class="book-options">${opts.map((x,j)=>`<div class="book-option"><b>${String.fromCharCode(65+j)}</b>${x.replace(/^[A-D]\.\s*/,"")}</div>`).join("")}</div>`;
      }catch(e){ return ""; }
    })() : "";
    const mStatus = item.mastery_status;
    return `<article class="book-question" data-book-type="${type}" data-mistake-id="${item.id}">
      <div class="book-question-head">
        <div class="book-labels">
          <span>${escapeHtml(item.subject)}</span><span>${escapeHtml(item.knowledge_point)}</span>
        </div>
        <span class="tag">${mStatus === "不熟" ? "不熟" : "不会"}</span>
      </div>
      <h3>${escapeHtml(item.question_text || "题目加载失败")}</h3>
      ${optionsHtml}
      <div class="book-tools">
        <div class="book-tools-left">
          ${item.question_id ? `<button class="soft" data-mistake-hint="${item.question_id}">💡 提示</button><button class="soft" data-mistake-video="${item.question_id}">▶ 视频</button>` : ""}
          <button class="soft" data-book-answer>查看答案</button>
        </div>
        <button class="primary" data-mistake-practice="${escapeHtml(item.subject)}|${escapeHtml(item.knowledge_point)}">重新练习</button>
      </div>
      <div class="book-answer">
        <b>答案与解析</b><br>
        标准答案：${escapeHtml(item.standard_answer || "暂无")}${item.explanation ? " · " + escapeHtml(item.explanation) : ""}<br>
        <span style="color:var(--danger)">错因：${escapeHtml(item.error_type || "待确认")}</span>
      </div>
      <div class="book-mastery">
        <button data-book-mastery="掌握" data-mistake-id="${item.id}">✓<br>掌握</button>
        <button class="${mStatus === "不熟" ? "current" : ""}" data-book-mastery="不熟" data-mistake-id="${item.id}">◉<br>不熟</button>
        <button class="${mStatus === "不会" ? "current" : ""}" data-book-mastery="不会" data-mistake-id="${item.id}">×<br>不会</button>
      </div>
    </article>`;
  }).join("");
  container.querySelectorAll("[data-book-answer]").forEach(b=>b.onclick=()=>b.closest(".book-question").querySelector(".book-answer").classList.toggle("show"));
  container.querySelectorAll("[data-book-mastery]").forEach(b=>b.onclick=()=>submitBookMastery(b));
  container.querySelectorAll("[data-mistake-hint]").forEach(b=>b.onclick=()=>loadMistakeHint(b.dataset.mistakeHint));
  container.querySelectorAll("[data-mistake-video]").forEach(b=>b.onclick=()=>loadMistakeVideo(b.dataset.mistakeVideo));
  container.querySelectorAll("[data-mistake-practice]").forEach(b=>{
    const parts = b.dataset.mistakePractice.split("|");
    b.onclick=()=>startPracticeForPoint(parts[0], parts[1]);
  });
}
async function submitBookMastery(button){
  const group = button.parentElement;
  group.querySelectorAll("button").forEach(x=>x.classList.remove("current"));
  button.classList.add("current");
  const status = button.dataset.bookMastery;
  const mistakeId = button.dataset.mistakeId;
  try{
    await apiRequest(`/api/mistakes/${mistakeId}/mastery`, {method:"POST", body:JSON.stringify({status})});
    toast(status==="掌握"?"已标记掌握，将移出题本":`已归入"${status}题本"`,"success");
    notebookCache = null;
    setTimeout(() => loadMistakeNotebook(), 300);
  }catch(error){
    toast(error.message, "error");
  }
}
async function loadMistakeHint(questionId){
  try{
    const data = await apiRequest(`/api/questions/${questionId}/hints`);
    const hint = (data.hints && data.hints[0]) || "暂无提示";
    toast("💡 " + hint);
  }catch(error){ toast("提示加载失败", "error"); }
}
async function loadMistakeVideo(questionId){
  try{
    const data = await apiRequest(`/api/questions/${questionId}/videos`);
    const items = data.items || [];
    if(!items.length) return toast("暂无推荐视频");
    const v = items[0];
    if(v.url) window.open(v.url, "_blank");
    toast("▶ " + v.title);
  }catch(error){ toast("视频加载失败", "error"); }
}
async function startPracticeForPoint(subject, point){
  toast("正在为该知识点生成训练题…");
  showPage("question");
  const payload = {mode:"自由选择", subject, knowledge_point:point, difficulty:"中等", question_type:"选择题", count:3};
  await generateQuestionsFromApi(payload, "已按知识点生成题目");
}
function reportHTML(){
  return `<section class="page" id="report">
    <div class="stats">
      <div class="card stat"><small>答题总数</small><strong>36</strong></div>
      <div class="card stat"><small>答对</small><strong>27</strong></div>
      <div class="card stat"><small>答错</small><strong>9</strong></div>
      <div class="card stat"><small>正确率</small><strong>75%</strong></div>
    </div>
    <div class="report-grid report-main-grid">
      <article class="card report-main-card">
        <div class="head"><h3>四科掌握趋势</h3><span class="tag">本周</span></div>
        <div class="chart">
          <div class="bar" style="height:72%"><span>数据结构</span></div>
          <div class="bar" style="height:56%"><span>组成原理</span></div>
          <div class="bar" style="height:48%"><span>操作系统</span></div>
          <div class="bar" style="height:64%"><span>计算机网络</span></div>
        </div>
      </article>
      <article class="card report-plan-card">
        <div class="head">
          <h3>下一轮个性化训练计划</h3>
          <button class="primary" onclick="toast('报告已导出')">导出报告</button>
        </div>
        <div class="plan-item"><i>01</i><div><b>页面置换算法专项 · 3 道中等题</b><small>针对 LRU 缺页统计遗漏 · 预计 25 分钟</small></div></div>
        <div class="plan-item"><i>02</i><div><b>TCP 握手与挥手对比复习</b><small>结合最近高频提问 · 预计 15 分钟</small></div></div>
        <div class="plan-item"><i>03</i><div><b>二叉树遍历间隔复习</b><small>验证已改善状态是否稳定 · 预计 10 分钟</small></div></div>
      </article>
    </div>
    <div class="report-section-title">
      <div><h2>学习画像</h2><p>基于答题、错题、问答与掌握反馈形成的长期学习特征</p></div>
    </div>
    <div class="learning-profile-grid">
      <article class="card learning-user-card">
        <div class="profile-avatar">林</div>
        <h3>林同学</h3>
        <p>目标：2026 计算机考研 · 408</p>
        <div><span class="trait">连续学习 7 天</span><span class="trait">分步型学习者</span><span class="trait">计算易遗漏</span></div>
      </article>
      <article class="card learning-memory-card">
        <div class="head"><h3>长期记忆权重</h3></div>
        ${[["页面置换算法",8],["TCP 三次握手",5],["同步与互斥",4],["二叉树遍历",1]].map(x=>`
          <div class="weight-row">
            <span>${x[0]}</span>
            <div class="weight-track"><span style="width:${x[1]*10}%"></span></div>
            <b>${x[1]}</b>
          </div>
        `).join("")}
        <p class="memory-rule">规则：答错 +1，点击"不会" +2，连续答对 -1，低于 0 标记为已掌握。</p>
      </article>
    </div>
  </section>`
}
function profileHTML(){
  return `<section class="page" id="profile">
    <div class="profile-grid">
      <article class="card profile-card">
        <div class="profile-avatar">林</div>
        <h3>林同学</h3>
        <p style="color:var(--muted);font-size:10px">目标：2026 计算机考研 · 408</p>
        <span class="trait">连续学习 7 天</span>
        <span class="trait">分步型学习者</span>
        <span class="trait">计算易遗漏</span>
      </article>
      <article class="card">
        <div class="head">
          <h3>长期记忆权重</h3>
        </div>
        ${[["页面置换算法",8],["TCP 三次握手",5],["同步与互斥",4],["二叉树遍历",1]].map(x=>`
          <div class="weight-row">
            <span>${x[0]}</span>
            <div class="weight-track">
              <span style="width:${x[1]*10}%"></span>
            </div>
            <b>${x[1]}</b>
          </div>
        `).join("")}
        <div class="notice" style="font-size:9px;color:var(--muted)">
          规则：答错 +1；点击"不会" +2；连续答对 -1；低于 0 标记为已掌握。
        </div>
      </article>
    </div>
  </section>`
}
function devHTML(){
  return `<aside class="dev-panel" id="devPanel">
    <div class="head">
      <h2>前端倒推清单</h2>
      <button class="ghost" onclick="toggleDev()">关闭</button>
    </div>
    <p style="font-size:9px;color:var(--muted)">
      当前页面的每一次交互，都对应后续需要确定的接口、实体与 Agent 节点。
    </p>
    <div id="devContent"></div>
  </aside>`
}
const mapping={
home:["GET /api/home/overview · GET /api/knowledge/graph?scope=all","knowledge_point（完整四科层级）, answer_record, mistake, user_memory","knowledge_retrieve → recommendation；个人状态作为 overlay 单独返回"],
qa:["POST /api/qa/chat · GET /api/conversations","conversation, conversation_message, qa_record, user_memory","memory_load → semantic_retrieve → knowledge_retrieve → qa → memory_update"],
question:["POST /api/questions/generate · POST /api/answers/check · POST /api/mistakes/cause-confirm","question, answer_record, mistake, mistake_cause, video_resource, user_memory","question_generate → hint → answer_check → user_cause_confirm → memory_update"],
 mistake:["GET /api/mistakes · GET /api/mistakes/similar · POST /api/ocr/upload · POST /api/mistakes/analyze","mistake, answer_record, upload, user_memory, mistake_summary","semantic_memory_retrieve / ocr → mistake_analyze → memory_update"],
 forum:["GET /api/forum/posts?search=&category= · POST /api/forum/posts · POST /api/forum/posts/:id/like · POST /api/forum/posts/:id/unlike · GET /api/forum/posts/:id/comments · POST /api/forum/posts/:id/comments · POST /api/forum/posts/:id/ai-answer · POST /api/forum/posts/:id/ai-followup · GET /api/forum/hot · GET /api/forum/checkin/status · POST /api/forum/checkin","forum_post, forum_comment, forum_checkin, ForumCheckin","ai_answer_for_post → content_moderation → knowledge_tagging"],
 report:["POST /api/reports/generate","report, answer_record, mistake, qa_record, video_view_record, user_memory","report → conversation_summary → semantic_write"],
profile:["GET /api/memory/profile · PATCH /api/memory/:id","user, user_memory","memory_load / memory_update"]
};
let ocrPreviewUrl=null;
let ocrUploadState={};
function setOcrStep(activeIndex){
  document.querySelectorAll(".ocr-steps span").forEach((x,i)=>x.classList.toggle("on",i<=activeIndex))
}
function resetOcrAnalysis(){
  const grid=document.getElementById("ocrAnalysisGrid")
  const tools=document.getElementById("ocrAnalysisTools")
  if(grid){
    grid.innerHTML=`<div class="analysis-item wide"><small>状态</small><b>等待 OCR 识别与 Agent 分析</b></div>`
  }
  if(tools){
    tools.style.display="none"
  }
}
function renderOcrUploadMeta(data={}){
  const meta=document.getElementById("ocrUploadMeta")
  const tag=document.getElementById("ocrEngineTag")
  if(meta){
    const size=data.size?`${Math.max(1,Math.round(data.size/1024))} KB`:"等待后端返回"
    meta.innerHTML=`<b>${escapeHtml(String(data.filename||"图片已选择"))}</b>
      <small>${size} · ${escapeHtml(String(data.engine||"正在识别"))}${data.warning?` · ${escapeHtml(String(data.warning))}`:""}</small>`
  }
  if(tag){
    tag.textContent=data.engine||"识别中"
  }
}
function previewOcrImage(file){
  const image=document.getElementById("ocrPreviewImage")
  const placeholder=document.getElementById("ocrDropPlaceholder")
  const drop=document.getElementById("ocrDrop")
  if(!image)return
  if(ocrPreviewUrl)URL.revokeObjectURL(ocrPreviewUrl)
  ocrPreviewUrl=URL.createObjectURL(file)
  image.src=ocrPreviewUrl
  image.classList.add("show")
  if(placeholder)placeholder.classList.add("hide")
  if(drop)drop.classList.add("has-image")
}
async function ocrUploadFile(file){
 if(!file)return;
 if(!file.type.startsWith("image/"))return toast("请选择图片文件","error");
 previewOcrImage(file);
 ocrUploadState={filename:file.name,size:file.size};
 renderOcrUploadMeta({filename:file.name,size:file.size,engine:"上传中"});
 resetOcrAnalysis();
 setOcrStep(1);
 const status=document.getElementById("ocrStatus");
 if(status)status.textContent="正在上传并识别";
 toast("正在上传图片…");
 try{
  const form=new FormData();form.append("file",file);
  const data=await apiRequest("/api/ocr/upload",{method:"POST",body:form});
  ocrUploadState=data;
  document.getElementById("ocrText").value=data.recognized_text||"";
  document.getElementById("ocrStatus").textContent=(data.ocr_available===false?"进入人工校对":"识别完成")+" · "+(data.engine||"后端 OCR");
  renderOcrUploadMeta(data);
  setOcrStep(2);
  toast(data.warning||"图片上传并识别完成",data.ocr_available===false?"info":"success");
 }catch(error){console.error(error);setOcrStep(0);if(status)status.textContent="上传失败";toast(error.message||"上传失败","error")}
}
function bindAll(){
 enhanceKnowledgeGraph();
 document.querySelectorAll(".nav button").forEach(b=>b.onclick=()=>showPage(b.dataset.page));
 document.querySelectorAll(".subject-tabs button").forEach(b=>b.onclick=()=>{if(b.id==="masteryLayer"||b.id==="structureLayer")return;b.parentElement.querySelectorAll("button").forEach(x=>x.classList.remove("active"));b.classList.add("active");toast("已切换 Mock 数据视图")});
 const masteryLayer=document.getElementById("masteryLayer"),structureLayer=document.getElementById("structureLayer");
 masteryLayer.onclick=()=>{masteryLayer.classList.add("active");structureLayer.classList.remove("active");document.getElementById("layerNote").textContent="已叠加个人掌握状态：红色为薄弱点，绿色为已掌握";document.querySelectorAll(".graph-point").forEach((p,i)=>{p.classList.remove("weak-state","master-state");if([2,7,11,13].includes(i))p.classList.add("weak-state");else if([0,5,15].includes(i))p.classList.add("master-state")});toast("全局知识结构保持不变，仅叠加个人状态图层")};
 structureLayer.onclick=()=>{structureLayer.classList.add("active");masteryLayer.classList.remove("active");document.getElementById("layerNote").textContent="当前展示完整知识结构";document.querySelectorAll(".graph-point").forEach(p=>p.classList.remove("weak-state","master-state"));toast("已切回纯知识结构图")};
 document.querySelectorAll("[data-graph-filter]").forEach(button=>button.onclick=()=>{document.querySelectorAll("[data-graph-filter]").forEach(x=>x.classList.toggle("active",x===button));const filter=button.dataset.graphFilter,canvas=document.getElementById("knowledgeGraphCanvas");canvas.classList.toggle("single-view",filter!=="all");document.querySelectorAll("[data-graph-group]").forEach(group=>group.classList.toggle("hidden",filter!=="all"&&group.dataset.graphGroup!==filter));document.getElementById("layerNote").textContent=filter==="all"?"当前展示四科完整知识结构":`当前聚焦：${filter}`;toast(filter==="all"?"已切换到全局知识图谱":`已切换到${filter}图谱`)});
 bindQuestionOptions();
 document.querySelectorAll("[data-drawer]").forEach(b=>b.onclick=()=>document.getElementById(b.dataset.drawer).classList.toggle("show"));
 document.querySelectorAll(".mastery button").forEach(b=>b.onclick=()=>{b.parentElement.querySelectorAll("button").forEach(x=>x.classList.remove("chosen"));b.classList.add("chosen");const status=b.textContent.trim();if(status==="不熟")toast("已加入“不熟题本”，并记录到长期学习状态");else if(status==="不会")toast("已加入“不会题本”，薄弱权重 +2");else toast("已标记掌握，将从不熟/不会题本移出")});
 let hint=1;document.getElementById("nextHint").onclick=()=>{hint=Math.min(3,hint+1);document.querySelector("#hint h4").textContent=`提示 ${hint} / 3`;document.getElementById("hintText").textContent=hint===2?"按序列逐项访问：命中时更新最近访问顺序；缺页时淘汰最久未访问页面。":"关键提醒：初始装入页面也算缺页。你之前曾遗漏这一点。"};
 document.getElementById("submitAnswer").onclick=()=>{const selected=document.querySelector(".option.selected");if(!selected)return toast("请先选择一个答案");document.getElementById("answer").classList.add("show");document.getElementById("wrongAction").classList.add("show");toast("回答错误，请选择真实错因")};
 document.getElementById("prevQuestion").onclick=()=>switchQuestion(-1);
 document.getElementById("nextQuestion").onclick=()=>switchQuestion(1);
 document.getElementById("openManualDrawer").onclick=()=>openQuestionDrawer("manualDrawer");
 document.getElementById("openSmartDrawer").onclick=()=>openQuestionDrawer("smartDrawer");
 document.getElementById("changeConfig").onclick=()=>openQuestionDrawer("manualDrawer");
 document.querySelectorAll("[data-close-question]").forEach(b=>b.onclick=closeQuestionDrawers);
 document.getElementById("questionDrawerMask").onclick=closeQuestionDrawers;
 document.querySelectorAll("[data-choice-group]").forEach(group=>group.querySelectorAll("button").forEach(b=>b.onclick=()=>{group.querySelectorAll("button").forEach(x=>x.classList.remove("selected"));b.classList.add("selected")}));
 document.getElementById("generateManual").onclick=generateManualQuestions;
 document.getElementById("generateSmart").onclick=generateSmartQuestions;
 document.getElementById("openCause").onclick=()=>document.getElementById("causeDetail").classList.toggle("show");
 document.querySelectorAll("[data-cause]").forEach(b=>b.onclick=()=>b.classList.toggle("chosen"));
 document.getElementById("confirmCause").onclick=()=>{const selected=[...document.querySelectorAll("[data-cause].chosen")].map(x=>x.dataset.cause);if(!selected.length)return toast("请至少选择一种错因");const note=document.getElementById("causeNote").value.trim();document.getElementById("causeSummary").classList.add("show");document.getElementById("causeSummary").innerHTML=`<b>已形成结构化长期记忆证据</b><br>错因：${selected.join(" + ")}${note?`<br>用户说明：${escapeHtml(note)}`:""}<br>写入建议：mistake.error_types；user_memory.error_pattern；evidence_source=user_confirmed；可信度=high；对应知识点权重 +1。`;toast("错因已确认，将作为高可信长期记忆记录")};
 document.getElementById("sendQa").onclick=sendQa;document.getElementById("qaInput").onkeydown=e=>{if(e.key==="Enter")sendQa()};
  document.getElementById("ocrMock").onclick=()=>{let input=document.createElement("input");input.type="file";input.accept="image/*";input.style.display="none";document.body.appendChild(input);input.onchange=e=>{ocrUploadFile(e.target.files[0]);document.body.removeChild(input);input=null};input.click()};
  const ocrDrop=document.getElementById("ocrDrop");
  if(ocrDrop){
   ocrDrop.addEventListener("dragover",e=>{e.preventDefault();ocrDrop.classList.add("drag-over")});
   ocrDrop.addEventListener("dragenter",e=>{e.preventDefault();ocrDrop.classList.add("drag-over")});
   ocrDrop.addEventListener("dragleave",()=>ocrDrop.classList.remove("drag-over"));
   ocrDrop.addEventListener("drop",e=>{e.preventDefault();ocrDrop.classList.remove("drag-over");ocrUploadFile(e.dataTransfer.files&&e.dataTransfer.files[0])});
  }
  document.getElementById("ocrManualText").onclick=()=>{document.getElementById("ocrText").focus();document.getElementById("ocrStatus").textContent="人工校对中";setOcrStep(2);toast("请在文本框内直接输入或粘贴题目文字")};
  let ocrState={};
  document.getElementById("ocrAnalyze").onclick=async()=>{
    const text=document.getElementById("ocrText").value.trim();
    if(!text)return toast("请先上传图片或输入识别文本","error");
    const subject=document.getElementById("configSubject")?.textContent||"操作系统";
    const point=document.getElementById("configPoint")?.textContent||"页面置换算法";
    const user_answer=document.getElementById("ocrUserAnswer")?.value.trim()||"";
    setOcrStep(3);
    document.getElementById("ocrStatus").textContent="Agent 分析中";
    toast("Agent 正在分析…");
    try{
      const data=await apiRequest("/api/ocr/analyze",{method:"POST",body:JSON.stringify({text,subject,knowledge_point:point,user_answer})});
      ocrState=data;
      const analysis=data.analysis||{};
      const grid=document.getElementById("ocrAnalysisGrid");
      if(grid)grid.innerHTML=`<div class="analysis-item"><small>知识点</small><b>${escapeHtml(String(analysis.subject||subject))} / ${escapeHtml(String(analysis.knowledge_point||point))}</b></div><div class="analysis-item"><small>掌握状态</small><b>${escapeHtml(String(analysis.mastery_status||"已同步后端"))}</b></div><div class="analysis-item wide"><small>Agent 推断标准答案</small><b>${escapeHtml(String(analysis.correct_answer||"待校对"))}</b></div><div class="analysis-item wide"><small>答案解析</small><b>${escapeHtml(String(analysis.answer_explanation||"暂无解析"))}</b></div><div class="analysis-item"><small>判断结果</small><b>${analysis.is_correct===true?"用户答案正确":analysis.is_correct===false?"用户答案错误":"用户答案待校对"}</b></div><div class="analysis-item"><small>主要错因</small><b>${escapeHtml(String(analysis.error_type||"OCR 导入待确认"))}</b></div>`+(analysis.possible_causes||["OCR 导入待确认"]).map(c=>`<div class="analysis-item"><small>可能错因</small><b>${escapeHtml(String(c))}</b></div>`).join("")+`<div class="analysis-item wide"><small>具体分析</small><b>${escapeHtml(String(analysis.error_reason||"Agent 已保存本次 OCR 错题，等待进一步校对。"))}</b></div><div class="analysis-item wide"><small>复习建议</small><b>${escapeHtml(String(analysis.suggestion||"先校对 OCR 文本，再围绕该知识点完成同类训练。"))}</b></div><div class="analysis-item wide"><small>后端记录</small><b>${escapeHtml(String(data.message||"已写入错题分析 Agent 结果"))} · mistake_id：${escapeHtml(String(data.mistake_id||"未返回"))} · memory_id：${escapeHtml(String(data.memory_id||"未返回"))} · ${data.llm_used?`AI 大模型 ${escapeHtml(String(data.llm_model||""))}`:`后端保底规则：${escapeHtml(String(data.llm_error||"大模型不可用"))}`}</b></div>`;
      const tools=document.getElementById("ocrAnalysisTools");
      if(tools)tools.style.display="flex";
      document.getElementById("ocrStatus").textContent="分析完成";
      setOcrStep(4);
      toast(data.llm_used?"错题分析已提交并写入记忆（AI 大模型）":"错题分析已提交并写入记忆（保底规则）","success");
    }catch(error){toast(error.message,"error");document.getElementById("ocrStatus").textContent="分析失败";setOcrStep(2);}
  };
  document.querySelectorAll("[data-book-tab]").forEach(b=>b.onclick=()=>openBookView(b.dataset.bookTab));
  document.querySelectorAll("[data-open-book]").forEach(b=>b.onclick=()=>openBookView(b.dataset.openBook));
  document.querySelectorAll("[data-return-books]").forEach(b=>b.onclick=()=>openBookView("overview"));
  document.getElementById("backToBooks").onclick=()=>{openBookView("overview");loadMistakeNotebook()};
  document.getElementById("saveOcrMistake").onclick=async()=>{
    if(!ocrState.mistake_id)return toast("请先完成 OCR 分析","error");
    setOcrStep(4);
    toast("已返回题本列表","success");
    setTimeout(()=>{openBookView("overview");loadMistakeNotebook()},500);
  };
  document.getElementById("generateOcrPractice").onclick=()=>{
    const subject=document.getElementById("configSubject")?.textContent||"操作系统";
    const point=document.getElementById("configPoint")?.textContent||"页面置换算法";
    startPracticeForPoint(subject,point);
  };
 bindAccountSettings();
 bindForum();
 renderQuestion();
 startExamCountdown();
}
function bindAccountSettings(){
 const panel=document.getElementById("accountPanel"),mask=document.getElementById("accountMask");
 const open=()=>{panel.classList.add("open");mask.classList.add("show");panel.setAttribute("aria-hidden","false");document.body.classList.add("account-open")};
 const close=()=>{panel.classList.remove("open");mask.classList.remove("show");panel.setAttribute("aria-hidden","true");document.body.classList.remove("account-open")};
 document.getElementById("openAccount").onclick=open;
 document.getElementById("closeAccount").onclick=close;
 mask.onclick=close;
 const saveName=()=>{const input=document.getElementById("accountName"),name=input.value.trim()||"林同学",avatar=name.slice(0,1);input.value=name;document.getElementById("topUserName").textContent=name;document.getElementById("topAvatar").textContent=avatar;document.querySelectorAll(".learning-user-card h3").forEach(x=>x.textContent=name);toast("账号昵称已保存")};
 document.getElementById("accountName").onblur=saveName;
 document.getElementById("accountName").onkeydown=e=>{if(e.key==="Enter"){e.preventDefault();saveName();e.currentTarget.blur()}};
 const savePassword=()=>{const oldPwd=document.getElementById("oldPassword").value,newPwd=document.getElementById("newPassword").value,confirmPwd=document.getElementById("confirmPassword").value;if(!oldPwd)return toast("请输入当前密码");if(newPwd.length<8)return toast("新密码至少需要 8 位");if(newPwd!==confirmPwd)return toast("两次输入的新密码不一致");["oldPassword","newPassword","confirmPassword"].forEach(id=>document.getElementById(id).value="");toast("密码修改成功")};
 document.getElementById("confirmPassword").onkeydown=e=>{if(e.key==="Enter"){e.preventDefault();savePassword()}};
 document.onkeydown=e=>{if(e.key==="Escape"&&panel.classList.contains("open"))close()};
}
function bindForum(){
  const modal=document.getElementById("forumModal"),mask=document.getElementById("forumModalMask");
  const open=()=>{modal.classList.add("show");mask.classList.add("show")},close=()=>{modal.classList.remove("show");mask.classList.remove("show")};
  document.getElementById("openForumComposer").onclick=open;document.getElementById("closeForumComposer").onclick=close;document.getElementById("cancelForumPost").onclick=close;mask.onclick=close;
  document.getElementById("publishForumPost").onclick=submitForumPost;
  document.getElementById("forumCheckin").onclick=doForumCheckin;
  document.getElementById("forumSearch").oninput=debounceForumSearch;
}
function debounceForumSearch(){
  clearTimeout(window._forumSearchTimer);
  window._forumSearchTimer=setTimeout(()=>{
    const category=document.querySelector("[data-forum-category].active")?.dataset.forumCategory||"全部";
    const keyword=document.getElementById("forumSearch").value.trim();
    loadForumPosts(category,keyword);
  },300);
}
function submitForumPost(){
  const title=document.getElementById("forumTitle").value.trim();
  const content=document.getElementById("forumContent").value.trim();
  const subject=document.getElementById("forumSubject").value;
  if(!title||!content)return toast("请填写标题和讨论内容");
  const category=subject;
  apiRequest("/api/forum/posts",{method:"POST",body:JSON.stringify({category,subject,title,content})}).then(data=>{
    document.getElementById("forumTitle").value="";
    document.getElementById("forumContent").value="";
    document.querySelector("#forumModal .forum-modal-actions button.ghost").click();
    const post=data.post;
    document.getElementById("forumFeed").insertAdjacentHTML("afterbegin",forumPostCardHTML(post));
    bindForumDynamic(document.querySelector(".forum-feed .forum-post"));
    toast("讨论已发布");
  }).catch(err=>toast(err.message,"error"));
}
function bindForumDynamic(post){
  if(!post)return;
  const like=post.querySelector("[data-forum-like]");
  const comment=post.querySelector("[data-forum-comment]");
  const submit=post.querySelector("[data-submit-comment]");
  const ai=post.querySelector("[data-forum-ai]");
  const aiPanel=post.querySelector(".forum-ai-answer");
  const closeAi=post.querySelector("[data-close-ai]");
  const followup=post.querySelector("[data-ai-followup]");
  const postId=post.dataset.postId;
  if(like)like.onclick=()=>likeForumPost(postId,like);
  if(comment)comment.onclick=()=>{
    const box=post.querySelector(".forum-comment-box");
    const list=post.querySelector(".forum-comments-list");
    box.classList.toggle("show");
    if(list&&list.style.display!=="block"){list.style.display="block";loadComments(postId,post);}
  };
  if(submit)submit.onclick=()=>{
    const input=submit.closest(".forum-comment-box").querySelector("input");
    if(!input.value.trim())return toast("请输入回复内容");
    submitComment(postId,input.value.trim(),post);
    input.value="";
  };
  if(ai)ai.onclick=()=>{
    const opening=!aiPanel.classList.contains("show");
    aiPanel.classList.toggle("show");
    ai.classList.toggle("active",opening);
    ai.lastChild.textContent=opening?" 收起解答":" 小助手解答";
    if(opening)loadAiAnswer(postId,post);
  };
  if(closeAi)closeAi.onclick=()=>{
    aiPanel.classList.remove("show");
    ai.classList.remove("active");
    ai.lastChild.textContent=" 小助手解答";
  };
  if(followup)followup.onclick=()=>submitAiFollowup(postId,followup);
}
async function loadForum(){
  try{
    const category=document.querySelector("[data-forum-category].active")?.dataset.forumCategory||"全部";
    await Promise.all([loadForumPosts(category,""),loadHotTopics(),loadCheckinStatus()]);
    document.querySelectorAll("[data-forum-category]").forEach(button=>button.onclick=()=>{
      document.querySelectorAll("[data-forum-category]").forEach(x=>x.classList.toggle("active",x===button));
      const cat=button.dataset.forumCategory;
      const keyword=document.getElementById("forumSearch").value.trim();
      loadForumPosts(cat,keyword);
    });
  }catch(err){console.error(err);}
}
async function loadForumPosts(category,search){
  const feed=document.getElementById("forumFeed");
  if(!feed)return;
  feed.innerHTML="<div class='card' style='text-align:center;padding:40px;color:var(--muted);font-size:10px'>正在加载…</div>";
  try{
    let url="/api/forum/posts";
    const params=[];
    if(category&&category!=="全部")params.push(`category=${encodeURIComponent(category)}`);
    if(search)params.push(`search=${encodeURIComponent(search)}`);
    if(params.length)url+="?"+params.join("&");
    const data=await apiRequest(url);
    const items=data.items||[];
    if(!items.length){
      feed.innerHTML="<div class='card' style='text-align:center;padding:40px;color:var(--muted);font-size:10px'>暂无讨论，快来发布第一条吧</div>";
      return;
    }
    feed.innerHTML=items.map(p=>forumPostCardHTML(p)).join("");
    feed.querySelectorAll(".forum-post").forEach(post=>bindForumDynamic(post));
  }catch(err){
    feed.innerHTML=`<div class='card' style='text-align:center;padding:40px;color:var(--danger);font-size:10px'>加载失败：${escapeHtml(err.message)}</div>`;
  }
}
async function loadHotTopics(){
  const list=document.getElementById("hotList");
  if(!list)return;
  try{
    const data=await apiRequest("/api/forum/hot");
    const items=data.items||[];
    if(!items.length){
      list.innerHTML="<li style='text-align:center;color:var(--muted);font-size:9px;padding:15px 0;border:0'>暂无热门讨论</li>";
      return;
    }
    list.innerHTML=items.slice(0,5).map((item,i)=>`<li><b>${String(i+1).padStart(2,"0")}</b><span>${escapeHtml(item.title)}<small>${item.like_count} 人点赞 · ${item.comment_count} 人评论</small></span></li>`).join("");
    const tag=document.getElementById("hotTag");
    if(tag)tag.textContent="TOP "+Math.min(items.length,5);
  }catch(err){
    const list=document.getElementById("hotList");
    if(list)list.innerHTML="<li style='text-align:center;color:var(--muted);font-size:9px;padding:15px 0;border:0'>加载失败</li>";
  }
}
async function loadCheckinStatus(){
  const count=document.getElementById("checkinCount");
  const btn=document.getElementById("forumCheckin");
  if(!count)return;
  try{
    const data=await apiRequest("/api/forum/checkin/status");
    count.textContent=data.weekly_count||0;
    if(data.checked_today){
      btn.textContent="今日已打卡";
      btn.disabled=true;
    }
  }catch(err){
    count.textContent="-";
  }
}
async function doForumCheckin(){
  const btn=document.getElementById("forumCheckin");
  const count=document.getElementById("checkinCount");
  if(!btn)return;
  btn.disabled=true;
  btn.textContent="打卡中...";
  try{
    const data=await apiRequest("/api/forum/checkin",{method:"POST"});
    if(count)count.textContent=data.weekly_count||0;
    btn.textContent="今日已打卡";
    toast(data.message||"打卡成功","success");
  }catch(err){
    btn.disabled=false;
    btn.textContent="今日打卡";
    toast(err.message||"打卡失败","error");
  }
}
async function likeForumPost(postId,button){
  try{
    const liked=button.classList.toggle("liked");
    if(liked){
      const data=await apiRequest(`/api/forum/posts/${postId}/like`,{method:"POST"});
      button.nextElementSibling.textContent=data.like_count;
      button.textContent="❤";
    }else{
      const data=await apiRequest(`/api/forum/posts/${postId}/unlike`,{method:"POST"});
      button.nextElementSibling.textContent=data.like_count;
      button.textContent="♡";
    }
  }catch(err){
    button.classList.toggle("liked");
    toast(err.message,"error");
  }
}
async function loadComments(postId,post){
  const container=post.querySelector(".forum-comments-items");
  if(!container)return;
  container.innerHTML="<div style='font-size:9px;color:var(--muted);padding:10px;text-align:center'>正在加载评论…</div>";
  try{
    const data=await apiRequest(`/api/forum/posts/${postId}/comments`);
    const items=data.items||[];
    if(!items.length){
      container.innerHTML="<div style='font-size:9px;color:var(--muted);padding:10px;text-align:center'>暂无评论，快来抢沙发</div>";
      return;
    }
    container.innerHTML=items.map(c=>`<div style="padding:10px 0;border-bottom:1px solid var(--line);font-size:9px"><span style="color:var(--brand);font-weight:800">${escapeHtml(c.author)}</span> <span style="color:var(--muted)">${c.create_time}</span><p style="margin:5px 0 0;color:var(--ink)">${escapeHtml(c.content)}</p></div>`).join("");
  }catch(err){
    container.innerHTML="<div style='font-size:9px;color:var(--danger);padding:10px'>评论加载失败</div>";
  }
}
async function submitComment(postId,content,post){
  try{
    await apiRequest(`/api/forum/posts/${postId}/comments`,{method:"POST",body:JSON.stringify({content})});
    toast("评论已发布");
    post.querySelector(".forum-comment-box").classList.remove("show");
    loadComments(postId,post);
    const btn=post.querySelector("[data-forum-comment]");
    if(btn){
      const match=btn.textContent.match(/(\d+)/);
      btn.textContent="评论 "+(match?parseInt(match[1])+1:1);
    }
  }catch(err){toast(err.message,"error");}
}
async function loadAiAnswer(postId,post){
  const content=document.getElementById(`forumAiContent${postId}`);
  if(!content)return;
  content.innerHTML="<p style='color:var(--muted)'>AI 小助手正在分析题目…</p>";
  try{
    const data=await apiRequest(`/api/forum/posts/${postId}/ai-answer`,{method:"POST"});
    content.innerHTML=data.answer||"<p>AI 小助手暂时无法回答，请稍后重试。</p>";
  }catch(err){
    content.innerHTML=`<p style='color:var(--danger)'>AI 小助手暂时不可用：${escapeHtml(err.message)}</p>`;
  }
}
async function submitAiFollowup(postId,button){
  const input=button.previousElementSibling;
  const question=input.value.trim();
  if(!question)return toast("请输入想继续追问的问题");
  const content=document.getElementById(`forumAiContent${postId}`);
  if(content)content.insertAdjacentHTML("beforeend",`<div class="ai-followup-question"><b>你的追问</b><p>${escapeHtml(question)}</p></div><div class="ai-followup-reply"><b>AI 小助手补充</b><p>正在思考…</p></div>`);
  input.value="";
  try{
    const data=await apiRequest(`/api/forum/posts/${postId}/ai-followup`,{method:"POST",body:JSON.stringify({content:question})});
    const reply=content?.querySelector(".ai-followup-reply:last-child p");
    if(reply)reply.innerHTML=data.answer||"暂无更多回答";
  }catch(err){
    const reply=content?.querySelector(".ai-followup-reply:last-child p");
    if(reply)reply.textContent="追问失败："+err.message;
    toast(err.message,"error");
  }
}
function startExamCountdown(){const target=new Date("2026-12-19T00:00:00+08:00").getTime();const update=()=>{const diff=Math.max(0,target-Date.now()),days=Math.floor(diff/86400000),hours=Math.floor(diff%86400000/3600000),minutes=Math.floor(diff%3600000/60000),seconds=Math.floor(diff%60000/1000);const set=(id,value)=>{const el=document.getElementById(id);if(el)el.textContent=String(value).padStart(2,"0")};set("countdownDays",days);set("countdownHours",hours);set("countdownMinutes",minutes);set("countdownSeconds",seconds);const subtitle=document.getElementById("pageSub");if(subtitle&&["qa","question","mistake","forum","report"].some(id=>document.getElementById(id)?.classList.contains("active")))subtitle.textContent=`距离 408 初试还有 ${days} 天 · 今日计划完成 3 / 5`};update();if(countdownTimer)clearInterval(countdownTimer);countdownTimer=setInterval(update,1000)}
function openBookView(name){
  document.querySelectorAll(".book-view").forEach(v=>v.classList.toggle("active",v.id===`book-${name}`));
  const titles={overview:["我的题本","智能出题中标记“不熟”和“不会”的题目会自动进入对应题本"],unfamiliar:["不熟题本","理解不稳定的题目，以单列卡片形式集中巩固"],unknown:["不会题本","尚未掌握的题目，优先重新学习与练习"],ocr:["OCR 导入","PaddleOCR 识别 → 校对 → 错题分析 → 记忆更新"]};
  document.getElementById("mistakeTitle").textContent=titles[name][0];
  document.getElementById("mistakeSubtitle").textContent=titles[name][1];
  window.scrollTo(0,0);
  if(name==="overview"){loadMistakeNotebook();}
  if((name==="unfamiliar"||name==="unknown")&&notebookCache){
    const items = (notebookCache.data || notebookCache).items || [];
    const filtered=items.filter(i=>i.mastery_status===(name==="unfamiliar"?"不熟":"不会"));
    renderMistakeCards(filtered,name);
  }else if(name==="unfamiliar"||name==="unknown"){
    loadMistakeNotebook().then(data=>{
      if(!data)return;
      const filtered=((data.data||data).items||[]).filter(i=>i.mastery_status===(name==="unfamiliar"?"不熟":"不会"));
      renderMistakeCards(filtered,name);
    });
  }
}
function bindQuestionOptions(){document.querySelectorAll("#options .option").forEach(o=>o.onclick=()=>{document.querySelectorAll("#options .option").forEach(x=>x.classList.remove("selected"));o.classList.add("selected")})}
function switchQuestion(direction){const next=currentQuestionIndex+direction;if(next<0||next>=activeQuestions.length)return;currentQuestionIndex=next;renderQuestion();toast(direction>0?"已切换到下一题":"已切换到上一题")}
function renderQuestion(){const q=activeQuestions[currentQuestionIndex];if(!q||!document.getElementById("questionTitle"))return;document.getElementById("questionMeta").textContent=q.meta.replace(/第 \d+ 题/,`第 ${currentQuestionIndex+1} 题`);document.getElementById("currentQuestionNo").textContent=currentQuestionIndex+1;document.getElementById("totalQuestionNo").textContent=activeQuestions.length;document.getElementById("questionTitle").textContent=q.title;document.getElementById("options").innerHTML=q.options.map(x=>`<div class="option">${x}</div>`).join("");document.getElementById("recommendReason").textContent=q.reason;document.getElementById("hintText").textContent=q.hint;document.getElementById("answerText").textContent=q.answer;document.getElementById("prevQuestion").disabled=currentQuestionIndex===0;document.getElementById("nextQuestion").disabled=currentQuestionIndex===activeQuestions.length-1;["hint","video","answer"].forEach(id=>document.getElementById(id).classList.remove("show"));document.getElementById("wrongAction").classList.remove("show");document.getElementById("causeDetail").classList.remove("show");document.getElementById("causeSummary").classList.remove("show");document.querySelectorAll("[data-cause]").forEach(x=>x.classList.remove("chosen"));document.getElementById("causeNote").value="";document.querySelectorAll(".mastery button").forEach(x=>x.classList.remove("chosen"));bindQuestionOptions()}
function openQuestionDrawer(id){document.getElementById("questionDrawerMask").classList.add("show");document.getElementById(id).classList.add("open")}
function closeQuestionDrawers(){document.getElementById("questionDrawerMask").classList.remove("show");document.getElementById("manualDrawer").classList.remove("open");document.getElementById("smartDrawer").classList.remove("open")}
function selectedValue(group){const selected=document.querySelector(`[data-choice-group="${group}"] .selected`);return selected?selected.dataset.value:""}

function showPage(id){document.querySelectorAll(".page").forEach(p=>p.classList.toggle("active",p.id===id));document.querySelectorAll(".nav button").forEach(b=>b.classList.toggle("active",b.dataset.page===id));const greetingPages=["qa","question","mistake","forum","report"],title=document.getElementById("pageTitle"),subtitle=document.getElementById("pageSub");if(greetingPages.includes(id)){title.textContent="早上好，继续向目标前进 👋";const days=document.getElementById("countdownDays")?.textContent||"180";subtitle.textContent=`距离 408 初试还有 ${Number(days)} 天 · 今日计划完成 3 / 5`}else{const p=pages.find(x=>x[0]===id);title.textContent=p[2];subtitle.textContent={home:"基于长期记忆生成的个性化学习空间"}[id]||""}if(id==="qa")loadConversations();if(id==="mistake")loadMistakeNotebook();if(id==="forum")loadForum();renderMapping(id);window.scrollTo(0,0)}
function renderMapping(id){const panel=document.getElementById("devContent");if(!panel)return;const m=mapping[id];panel.innerHTML=`<div class="mapping"><h4>建议接口</h4><code>${m[0]}</code></div><div class="mapping"><h4>核心数据实体</h4><code>${m[1]}</code></div><div class="mapping"><h4>Agent / LangGraph 节点</h4><code>${m[2]}</code></div>`}
function toggleDev(){document.getElementById("devPanel").classList.toggle("open")}function toast(t){const el=document.getElementById("toast");el.textContent=t;el.style.opacity=1;setTimeout(()=>el.style.opacity=0,2000)}function escapeHtml(s){return s.replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]))}

/* ========= 可运行后端接口接入 + 统一报错机制 ========= */
const API_BASE=location.protocol==="file:"?"http://127.0.0.1:8000":location.origin;
let lastAnswerRecordId=null;
const originalBindAll=bindAll;
const originalRenderQuestion=renderQuestion;
const originalToast=toast;

toast=function(message,type="info"){
 const el=document.getElementById("toast");
 if(!el)return;
 el.textContent=message;
 el.dataset.type=type;
 el.style.opacity=1;
 clearTimeout(el._timer);
 el._timer=setTimeout(()=>el.style.opacity=0,2600);
};

window.addEventListener("error",event=>{
 console.error(event.error||event.message);
 toast("页面脚本出现异常，已记录到控制台，可继续使用本地演示数据","error");
});
window.addEventListener("unhandledrejection",event=>{
 console.error(event.reason);
 toast("接口或异步任务异常，已自动启用降级方案","error");
});

async function apiRequest(path,options={}){
 const isFormData=options.body instanceof FormData;
 const headers=isFormData?{}:{"Content-Type":"application/json"};
 Object.assign(headers,options.headers||{});
 const token=localStorage.getItem("turing408_token");
 if(token)headers.Authorization=`Bearer ${token}`;
 let response,payload;
 try{
  response=await fetch(`${API_BASE}${path}`,{...options,headers});
  payload=await response.json();
 }catch(error){
  throw new Error("无法连接后端服务，请先启动 backend/main.py");
 }
 if(!response.ok||payload.ok===false){
  const err=payload.error||{};
  throw new Error(`${err.message||"接口请求失败"}${err.request_id?`（请求号：${err.request_id}）`:""}`);
 }
 return payload.data;
}

function normalizeQuestion(q,index=0){
 const vt=q.variant_type||({"选择题":"choice","填空题":"fill","简答题":"essay","综合题":"comprehensive"})[q.question_type]||"choice";
 return {
  id:q.id||q.question_id||null,
  meta:q.meta||`2026 模拟 · 第 ${index+1} 题 · 2 分`,
  title:q.title||q.question_text,
  options:q.options||["A. 正确","B. 错误","C. 需要补充条件","D. 无法判断"],
  reason:q.reason||q.recommend_reason||"Agent 根据当前掌握状态推荐。",
  hint:q.hint||(q.hints&&q.hints[0])||"先定位题目考查的知识点，再按步骤分析。",
  answer:q.answer||`标准答案：${q.standard_answer||""} · ${q.explanation||""}`,
  standard_answer:q.standard_answer||String(q.answer||"").match(/[A-D]/)?.[0]||"C",
  subject:q.subject||document.getElementById("configSubject")?.textContent||"操作系统",
  knowledge_point:q.knowledge_point||document.getElementById("configPoint")?.textContent||"页面置换算法",
  hints:q.hints||[q.hint||"先定位题目考查的知识点。"],
  variant_type:vt,
  sub_questions:q.sub_questions||null
 };
}

renderQuestion=function(){
 if(activeQuestions.length)activeQuestions=activeQuestions.map(normalizeQuestion);
 const q=activeQuestions[currentQuestionIndex];
 if(!q||!document.getElementById("questionTitle"))return;
 const type=q.variant_type||({"选择题":"choice","填空题":"fill","简答题":"essay","综合题":"comprehensive"})[q.question_type]||"choice";
 document.getElementById("questionMeta").textContent=(q.meta||"").replace(/第 \d+ 题/,`第 ${currentQuestionIndex+1} 题`);
 document.getElementById("currentQuestionNo").textContent=currentQuestionIndex+1;
 document.getElementById("totalQuestionNo").textContent=activeQuestions.length;
 document.getElementById("questionTitle").textContent=q.title;
 document.getElementById("recommendReason").textContent=q.reason;
 document.getElementById("hintText").textContent=q.hint;
 document.getElementById("answerText").textContent=q.answer;
 const answerBox=document.getElementById("answer");
 if(answerBox){
  const heading=answerBox.querySelector("h4");
  if(heading)heading.textContent="批改结果";
 }
 document.getElementById("prevQuestion").disabled=currentQuestionIndex===0;
 document.getElementById("nextQuestion").disabled=currentQuestionIndex===activeQuestions.length-1;
 ["hint","video","answer"].forEach(id=>{const el=document.getElementById(id);if(el)el.classList.remove("show")});
 const wrongEl=document.getElementById("wrongAction");if(wrongEl)wrongEl.classList.remove("show");
 const causeEl=document.getElementById("causeDetail");if(causeEl)causeEl.classList.remove("show");
 const summaryEl=document.getElementById("causeSummary");if(summaryEl)summaryEl.classList.remove("show");
 document.querySelectorAll("[data-cause]").forEach(x=>x.classList.remove("chosen"));
 const noteEl=document.getElementById("causeNote");if(noteEl)noteEl.value="";
 document.querySelectorAll(".mastery button").forEach(x=>x.classList.remove("chosen"));
 const optionsContainer=document.getElementById("options");
 if(!optionsContainer)return;
 if(type==="fill"){
  optionsContainer.innerHTML=`<div class="fill-answer"><label style="font-size:10px;color:var(--muted)">输入你的答案</label><input id="fillInput" placeholder="在此输入答案…" style="width:100%;border:1px solid var(--line);background:var(--panel2);color:var(--ink);padding:12px;border-radius:10px;outline:none;margin-top:8px"></div>`;
 }else if(type==="essay"){
  optionsContainer.innerHTML=`<div class="essay-answer"><label style="font-size:10px;color:var(--muted)">输入你的解答</label><textarea id="essayInput" placeholder="在此输入详细解答过程…" style="width:100%;min-height:160px;border:1px solid var(--line);background:var(--panel2);color:var(--ink);padding:12px;border-radius:10px;outline:none;margin-top:8px;resize:vertical"></textarea></div>`;
 }else if(type==="comprehensive"&&q.sub_questions){
  optionsContainer.innerHTML=`<div class="comprehensive-answers">${q.sub_questions.map((sq,i)=>`<div class="sub-question" style="margin:12px 0;padding:12px;border:1px solid var(--line);border-radius:10px;background:var(--panel2)"><b style="font-size:10px">第 ${i+1} 问</b><p style="font-size:10px;color:var(--muted);margin:6px 0">${escapeHtml(sq.title||sq.question_text||"")}</p>${sq.options?sq.options.map((o,j)=>`<div class="option sub-option" data-sub="${i}">${o}</div>`).join(""):`<textarea class="sub-input" data-sub="${i}" placeholder="输入第 ${i+1} 问答案…" style="width:100%;min-height:80px;border:1px solid var(--line);background:var(--panel);color:var(--ink);padding:10px;border-radius:8px;outline:none;resize:vertical"></textarea>`}</div>`).join("")}</div>`;
  optionsContainer.querySelectorAll(".sub-option").forEach(o=>o.onclick=()=>{const parent=o.closest(".sub-question");parent.querySelectorAll(".sub-option").forEach(x=>x.classList.remove("selected"));o.classList.add("selected");});
 }else{
  optionsContainer.innerHTML=(q.options||["A. 正确","B. 错误","C. 需要补充条件","D. 无法判断"]).map(x=>`<div class="option">${x}</div>`).join("");
  optionsContainer.querySelectorAll(".option").forEach(o=>o.onclick=()=>{optionsContainer.querySelectorAll(".option").forEach(x=>x.classList.remove("selected"));o.classList.add("selected")});
 }
};

bindAll=function(){
 originalBindAll();
 bindBackendAwareActions();
};

let hasGeneratedQuestionBatch=false;
let smartRecommendationItems=[];
let knowledgeGraphCache=null;

async function loadHint(questionId){
 const el=document.getElementById("hintText");
 const head=document.querySelector("#hint h4");
 if(!el||!head)return;
 try{
  const data=await apiRequest(`/api/questions/${questionId}/hints`);
  const hints=data.hints||["先定位题目考查的知识点。"];
  window._currentHints=hints;
  window._currentHintIdx=0;
  el.textContent=hints[0];
  head.textContent=`提示 1 / ${hints.length}`;
 }catch(error){
  el.textContent="提示加载失败，请稍后重试。";
  head.textContent="提示";
 }
}
async function loadVideo(questionId){
 const el=document.getElementById("videoContent");
 if(!el)return;
 try{
  const data=await apiRequest(`/api/questions/${questionId}/videos`);
  const items=data.items||[];
  el.innerHTML=items.length?items.map(v=>`<div style="margin:8px 0"><a href="${escapeHtml(v.url||'#')}" target="_blank" rel="noopener" style="text-decoration:none;color:inherit;display:block"><b>▶ ${escapeHtml(v.title)}</b><p style="font-size:10px;color:var(--muted);margin:2px 0 0">${escapeHtml(v.reason||"")}</p></a></div>`).join(""):`<div class="conversation-empty">暂无推荐视频</div>`;
 }catch(error){
  el.innerHTML=`<div class="conversation-empty">视频加载失败</div>`;
 }
}

function bindBackendAwareActions(){
 if(!hasGeneratedQuestionBatch)prepareQuestionEmptyState();
 const submit=document.getElementById("submitAnswer");
 if(submit)submit.onclick=submitCurrentAnswer;
 const confirm=document.getElementById("confirmCause");
 if(confirm)confirm.onclick=confirmCurrentCause;
 document.querySelectorAll(".mastery button").forEach(button=>{
  button.onclick=()=>submitMasteryFeedback(button);
 });
 const openSmart=document.getElementById("openSmartDrawer");
 if(openSmart)openSmart.onclick=async()=>{openQuestionDrawer("smartDrawer");await loadSmartRecommendations();};
 
 // Hint / Video: load from API
 document.querySelectorAll("[data-drawer]").forEach(b=>{
  const targetId=b.dataset.drawer;
  b.onclick=()=>{
   const drawer=document.getElementById(targetId);
   if(!drawer)return;
   const opening=!drawer.classList.contains("show");
   drawer.classList.toggle("show");
   if(opening){
    const q=activeQuestions[currentQuestionIndex];
    if(!q||!q.id)return;
    if(targetId==="hint")loadHint(q.id);
    if(targetId==="video")loadVideo(q.id);
   }
  };
 });
 const nextHint=document.getElementById("nextHint");
 if(nextHint)nextHint.onclick=()=>{
  const hints=window._currentHints;
  if(!hints||!hints.length)return;
  const idx=Math.min(hints.length-1,(window._currentHintIdx||0)+1);
  window._currentHintIdx=idx;
  const head=document.querySelector("#hint h4");
  if(head)head.textContent=`提示 ${idx+1} / ${hints.length}`;
  const el=document.getElementById("hintText");
  if(el)el.textContent=hints[idx];
 };
 
 // Manual drawer: subject → knowledge points
 const subjectGroup=document.querySelector('[data-choice-group="manualSubject"]');
 if(subjectGroup&&!subjectGroup.dataset.bound){
  subjectGroup.dataset.bound="true";
  subjectGroup.querySelectorAll("button").forEach(b=>{
   b.onclick=()=>{
    subjectGroup.querySelectorAll("button").forEach(x=>x.classList.remove("selected"));
    b.classList.add("selected");
    loadKnowledgePoints(b.dataset.value);
   };
  });
  loadKnowledgePoints(subjectGroup.querySelector(".selected")?.dataset.value||"操作系统");
 }
 
 // QA bindings
 const newConv=document.getElementById("newConversation");
 if(newConv)newConv.onclick=createNewConversation;
 const sendBtn=document.getElementById("sendQa");
 if(sendBtn)sendBtn.onclick=sendQa;
 const qaInput=document.getElementById("qaInput");
 if(qaInput)qaInput.onkeydown=e=>{if(e.key==="Enter")sendQa()};
 loadConversations();
}

function prepareQuestionEmptyState(){
 activeQuestions=[];
 const meta=document.getElementById("questionMeta"),title=document.getElementById("questionTitle"),options=document.getElementById("options"),reason=document.getElementById("recommendReason");
 if(meta)meta.textContent="等待生成训练题";
 if(title)title.textContent="从首页开始个性化训练，或在上方选择自由出题 / 智能推荐出题。";
 if(options)options.innerHTML=`<div class="home-empty-state">生成后，题目与答题记录会同步到数据库。</div>`;
 if(reason)reason.textContent="系统会根据当前用户的掌握状态、错题、问答和长期记忆实时计算推荐条件。";
 ["configMode","configSubject","configPoint","configDifficulty","configType"].forEach(id=>{const el=document.getElementById(id);if(el)el.textContent="待生成";});
 const current=document.getElementById("currentQuestionNo"),total=document.getElementById("totalQuestionNo");
 if(current)current.textContent="0";
 if(total)total.textContent="0";
}

async function generateManualQuestions(){
 const count=parseInt(selectedValue("manualCount"))||1;
 const payload={mode:"自由选择",subject:selectedValue("manualSubject"),knowledge_point:selectedValue("manualPoint"),difficulty:selectedValue("manualDifficulty"),question_type:selectedValue("manualType"),count};
 await generateQuestionsFromApi(payload,"已按所选条件生成题目");
}

async function generateSmartQuestions(){
 const mode=document.querySelector('[data-choice-group="smartMode"] .selected'),count=parseInt(selectedValue("smartCount"))||1;
 if(!mode)return toast("当前没有可用的智能推荐，请先完成一次基线诊断","error");
 const payload={mode:mode.dataset.value,count};
 await generateQuestionsFromApi(payload,"已根据智能推荐生成题目","/api/questions/generate-smart",{recommend_mode:payload.mode,count});
}

async function generateQuestionsFromApi(payload,successMessage,endpoint="/api/questions/generate",requestPayload=payload){
 try{
  toast("Agent 正在生成题目，请稍候…");
  const data=await apiRequest(endpoint,{method:"POST",body:JSON.stringify(requestPayload)});
  if(!data.questions||!Array.isArray(data.questions)||!data.questions.length)throw new Error("后端没有返回题目列表");
  const resolved=data.recommendation||payload;
  hasGeneratedQuestionBatch=true;
  activeQuestions=data.questions.map((q,index)=>normalizeQuestion({...q,source:data.llm_used?"AI 大模型":"后端保底题"},index));
  currentQuestionIndex=0;
  document.getElementById("configMode").textContent=resolved.mode;
  document.getElementById("configSubject").textContent=resolved.subject;
  document.getElementById("configPoint").textContent=resolved.knowledge_point;
  document.getElementById("configDifficulty").textContent=resolved.difficulty;
  document.getElementById("configType").textContent=`${resolved.question_type||"选择题"} · ${requestPayload.count} 道 · ${data.llm_used?"AI 生成":"规则题库"}`;
  document.getElementById("recommendTitle").textContent=resolved.mode==="自由选择"?"当前为自由选择出题":"为什么智能推荐这组题？";
  renderQuestion();
  const reason=document.getElementById("recommendReason");
  if(reason)reason.textContent=resolved.reason||data.config||"系统已根据当前学习画像生成本批题目。";
  bindBackendAwareActions();
  closeQuestionDrawers();
  toast(data.llm_used?`${successMessage}（AI 生成）`:`${successMessage}（后端规则题库）`,data.llm_used?"success":"info");
 }catch(error){
  console.error(error);
  toast(`${error.message}。本次未生成题目，也不会使用前端 Mock 冒充结果。`,"error");
 }
}

async function loadKnowledgePoints(subject){
 const container=document.querySelector('[data-choice-group="manualPoint"]');
 if(!container)return;
 container.innerHTML=`<div class="conversation-empty" style="grid-column:1/-1">正在加载知识点…</div>`;
 try{
  if(!knowledgeGraphCache)knowledgeGraphCache=await apiRequest("/api/knowledge/graph");
  const points=knowledgeGraphCache.subjects?.[subject]||[];
  if(!points.length){
   container.innerHTML=`<div class="conversation-empty" style="grid-column:1/-1">该科目暂无知识点</div>`;
   return;
  }
  container.innerHTML=points.map((p,i)=>`<button class="${i===0?"selected":""}" data-value="${escapeHtml(p.name)}"><b>${escapeHtml(p.name)}</b>${p.content?`<small>${escapeHtml(p.content)}</small>`:""}</button>`).join("");
  container.querySelectorAll("button").forEach(b=>b.onclick=()=>{container.querySelectorAll("button").forEach(x=>x.classList.remove("selected"));b.classList.add("selected");});
 }catch(error){
  container.innerHTML=`<div class="conversation-empty" style="grid-column:1/-1">加载失败：${escapeHtml(error.message)}</div>`;
 }
}

async function loadSmartRecommendations(){
 const list=document.querySelector('[data-choice-group="smartMode"]');
 if(!list)return;
 list.innerHTML=`<div class="home-empty-state">正在分析薄弱点、错题、问答和长期记忆…</div>`;
 try{
  const data=await apiRequest("/api/questions/recommendations");
  smartRecommendationItems=data.items||[];
  const firstAvailable=smartRecommendationItems.findIndex(item=>item.available);
  list.innerHTML=smartRecommendationItems.map((item,index)=>`<button ${item.available?"":"disabled"} class="${index===firstAvailable?"selected":""}" data-value="${escapeHtml(item.mode)}"><b>${escapeHtml(item.mode)}</b><small>${escapeHtml(item.knowledge_point)} · ${escapeHtml(item.reason)}</small></button>`).join("");
  list.querySelectorAll("button:not([disabled])").forEach(button=>button.onclick=()=>{list.querySelectorAll("button").forEach(item=>item.classList.remove("selected"));button.classList.add("selected");});
 }catch(error){
  list.innerHTML=`<div class="home-empty-state">推荐接口暂不可用：${escapeHtml(error.message)}</div>`;
 }
}

async function submitCurrentAnswer(){
 const q=activeQuestions[currentQuestionIndex];
 const type=q.variant_type||({"选择题":"choice","填空题":"fill","简答题":"essay","综合题":"comprehensive"})[q.question_type]||"choice";
 let userAnswer="";
 if(type==="fill"){
  const input=document.getElementById("fillInput");
  if(!input||!input.value.trim())return toast("请先填写答案","error");
  userAnswer=input.value.trim();
 }else if(type==="essay"){
  const input=document.getElementById("essayInput");
  if(!input||!input.value.trim())return toast("请先填写解答内容","error");
  userAnswer=input.value.trim();
 }else if(type==="comprehensive"){
  const subInputs=[];
  document.querySelectorAll(".sub-question").forEach(sq=>{
   const selected=sq.querySelector(".sub-option.selected");
   const textarea=sq.querySelector(".sub-input");
   if(selected)subInputs.push(selected.textContent.trim().match(/^[A-D]/)?.[0]||selected.textContent.trim());
   else if(textarea)subInputs.push(textarea.value.trim());
   else subInputs.push("");
  });
  if(subInputs.some(s=>!s))return toast("请完成所有子问题","error");
  userAnswer=subInputs.join(" | ");
 }else{
  const selected=document.querySelector(".option.selected");
  if(!selected)return toast("请先选择一个答案","error");
  userAnswer=(selected.textContent.trim().match(/^[A-D]/)||[""])[0];
 }
 if(!q.id){
  document.getElementById("answer").classList.add("show");
  document.getElementById("wrongAction").classList.add("show");
  return toast("本地演示题无法写入后端，已展示模拟批改结果","error");
 }
 try{
  const data=await apiRequest("/api/answers/check",{method:"POST",body:JSON.stringify({question_id:q.id,user_answer:userAnswer})});
  lastAnswerRecordId=data.answer_record_id;
  document.getElementById("answer").classList.add("show");
  document.getElementById("answer").querySelector("h4").textContent=data.is_correct?"批改结果：回答正确":"批改结果：回答错误";
  document.getElementById("answerText").textContent=data.feedback;
  document.getElementById("wrongAction").classList.toggle("show",!data.is_correct);
  toast(data.is_correct?"回答正确，掌握状态已更新":"回答错误，请选择真实错因",data.is_correct?"success":"error");
 }catch(error){
  console.error(error);
  document.getElementById("answer").classList.add("show");
  document.getElementById("wrongAction").classList.add("show");
  toast(`${error.message}，已展示本地模拟批改`,"error");
 }
}

async function confirmCurrentCause(){
 const selected=[...document.querySelectorAll("[data-cause].chosen")].map(x=>x.dataset.cause);
 if(!selected.length)return toast("请至少选择一种错因","error");
 const note=document.getElementById("causeNote").value.trim();
 document.getElementById("causeSummary").classList.add("show");
 document.getElementById("causeSummary").innerHTML=`<b>正在写入长期记忆</b><br>错因：${selected.join(" + ")}${note?`<br>用户说明：${escapeHtml(note)}`:""}`;
 if(!lastAnswerRecordId){
  document.getElementById("causeSummary").innerHTML+=`<br>本地演示模式：未产生真实 answer_record_id。`;
  return toast("错因已在页面记录；启动后端后可写入数据库","error");
 }
 try{
  const data=await apiRequest("/api/mistakes/cause-confirm",{method:"POST",body:JSON.stringify({answer_record_id:lastAnswerRecordId,error_types:selected,user_note:note,agent_suggested_types:["计算错误"],evidence_source:"user_confirmed"})});
  document.getElementById("causeSummary").innerHTML=`<b>已形成结构化长期记忆证据</b><br>错因：${selected.join(" + ")}${note?`<br>用户说明：${escapeHtml(note)}`:""}<br>${data.message}`;
  toast("错因已写入长期学习记忆","success");
 }catch(error){
  console.error(error);
  document.getElementById("causeSummary").innerHTML+=`<br>接口写入失败：${escapeHtml(error.message)}`;
  toast(error.message,"error");
 }
}

async function submitMasteryFeedback(button){
 const group=button.parentElement;
 group.querySelectorAll("button").forEach(x=>x.classList.remove("chosen"));
 button.classList.add("chosen");
 const q=activeQuestions[currentQuestionIndex];
 const status=button.textContent.trim();
 try{
  await apiRequest("/api/questions/mastery",{method:"POST",body:JSON.stringify({subject:q.subject,knowledge_point:q.knowledge_point,status})});
  toast(status==="掌握"?"已标记掌握":`已加入“${status}题本”，知识点状态已更新`,"success");
 }catch(error){
  console.error(error);
  toast(`${error.message}，页面已先保留你的选择`,"error");
 }
}

async function sendQa(){
 const input=document.getElementById("qaInput");
 if(!input.value.trim())return;
 const question=input.value.trim(),messages=document.getElementById("messages");
 const emptyState=messages.querySelector(".chat-empty-state");
 if(emptyState)emptyState.remove();
 messages.insertAdjacentHTML("beforeend",`<div class="bubble user">${escapeHtml(question)}</div><div class="bubble ai" data-loading="qa">Agent 正在读取长期记忆并生成回答…</div>`);
 input.value="";
 messages.scrollTop=messages.scrollHeight;
 try{
  const data=await apiRequest("/api/qa/chat",{method:"POST",body:JSON.stringify({question,conversation_id:currentConversationId})});
  const cid=data.conversation_id;
  if(cid&&!currentConversationId){
   currentConversationId=cid;
   document.getElementById("currentChatTitle").textContent=question.slice(0,30);
   loadConversations();
  }
  const answer=(data.answer||"").trim()||"后端没有返回可展示回答，已保留本次问题，请稍后重试。";
  const source=data.llm_used?"AI 大模型":"后端保底";
  const memory=data.agent_steps?.[1]?.output||"已读取本地学习记忆";
  const actions=(data.related_actions||["生成专项题"]).join(" / ");
  messages.querySelector("[data-loading='qa']").innerHTML=`${answer}<div class="answer-sections"><span>${source}</span><span>${memory}</span><span>${actions}</span></div>`;
  toast(data.llm_used?"AI 回答已生成":"已使用后端保底回答","success");
 }catch(error){
  console.error(error);
  messages.querySelector("[data-loading='qa']").innerHTML="我已结合当前会话摘要、最近对话和你的长期记忆理解了这个追问。<br><br><b>降级提醒：</b>后端未连接，当前显示本地演示回答。";
  toast(error.message,"error");
 }
 messages.scrollTop=messages.scrollHeight;
}

async function loadConversations(){
 const container=document.getElementById("conversationItems");
 if(!container)return;
 try{
  const data=await apiRequest("/api/conversation/list");
  const items=data.items||[];
  if(!items.length){
   container.innerHTML=`<div class="conversation-empty">暂无历史会话</div>`;
   return;
  }
  container.innerHTML=items.map(item=>{
   const active=item.id===currentConversationId?" active":"";
   return `<div class="conversation-item${active}" data-conversation-id="${item.id}"><b>${escapeHtml(item.title||"408 问答")}</b>${item.summary?`<small>${escapeHtml(item.summary.slice(0,40))}</small>`:""}</div>`;
  }).join("");
  container.querySelectorAll(".conversation-item").forEach(el=>{
   el.onclick=()=>switchConversation(Number(el.dataset.conversationId));
  });
 }catch(error){
  console.error(error);
 }
}

async function switchConversation(id){
 currentConversationId=id;
 const messages=document.getElementById("messages");
 const emptyState=messages.querySelector(".chat-empty-state");
 if(emptyState)emptyState.remove();
 messages.innerHTML=`<div class="bubble ai" data-loading="qa">正在加载会话记录…</div>`;
 try{
  const data=await apiRequest(`/api/conversation/detail/${id}`);
  const conv=data.conversation||{};
  document.getElementById("currentChatTitle").textContent=conv.title||"知识问答";
  messages.innerHTML=(data.messages||[]).map(m=>{
   const cls=m.role==="user"?"bubble user":"bubble ai";
   return `<div class="${cls}">${m.content}</div>`;
  }).join("")||`<div class="chat-empty-state"><p>该会话暂无消息</p></div>`;
  messages.scrollTop=messages.scrollHeight;
  loadConversations();
 }catch(error){
  console.error(error);
  messages.innerHTML=`<div class="chat-empty-state"><p>加载失败：${escapeHtml(error.message)}</p><p>请确认后端服务已启动</p></div>`;
 }
}

function createNewConversation(){
 currentConversationId=null;
 const messages=document.getElementById("messages");
 messages.innerHTML=`<div class="chat-empty-state"><p>点击「＋」开始新的知识问答会话</p><p>输入 408 相关问题，AI Agent 将结合知识库和你的学习记忆回答</p></div>`;
 document.getElementById("currentChatTitle").textContent="知识问答";
 loadConversations();
 const input=document.getElementById("qaInput");
 if(input)input.focus();
}

/* ========= 首页真实数据接入：今日计划 / 倒计时 / 推荐 / 统计 / 知识图谱 ========= */
let currentHomeOverview=null;
let homeCountdownTarget=new Date("2026-12-19T00:00:00+08:00").getTime();

homeHTML=function(){
 return `<section class="page" id="home"><div class="home-focus-grid"><article class="card hero-main"><div class="hero-task"><span class="eyebrow">TODAY'S AGENT PLAN</span><h2 id="homePlanTitle">正在读取今日计划…</h2><p id="homePlanReason">Agent 正在根据答题记录、错题、长期记忆和知识点掌握状态计算今日优先训练内容。</p><button class="primary" id="startPersonalTraining" onclick="startPersonalizedTraining()">开始个性化训练 →</button></div></article><article class="card countdown-card"><div class="exam-countdown"><span>考研 408 初试倒计时</span><div class="countdown-days"><b id="countdownDays">--</b><small>天</small></div><div class="countdown-clock"><div><b id="countdownHours">--</b><small>时</small></div><i>:</i><div><b id="countdownMinutes">--</b><small>分</small></div><i>:</i><div><b id="countdownSeconds">--</b><small>秒</small></div></div><p id="examDateLabel">目标日期：读取中</p></div></article><article class="card today-recommend-card"><div class="head"><h3>今日推荐</h3></div><div class="recommend" id="todayRecommendList"><div class="rec"><b>正在匹配推荐训练</b><small>系统会优先匹配薄弱点、错题复练、高频考点和未学知识点。</small></div></div></article></div><div class="stats" id="homeStats"><div class="card stat"><small>本周答题</small><strong>--</strong><span class="delta">读取中</span></div><div class="card stat"><small>综合正确率</small><strong>--</strong><span class="delta">读取中</span></div><div class="card stat"><small>长期薄弱点</small><strong>--</strong><span class="delta">读取中</span></div><div class="card stat"><small>记忆条目</small><strong>--</strong><span class="delta">读取中</span></div></div><div class="home-knowledge-layout"><article class="card knowledge-graph-card"><div class="kg-toolbar"><div><h3>408 全局知识图谱</h3><p>严格按 PDF 的 5 类状态叠加颜色：未学、掌握、不熟、不会、薄弱点。</p></div><div class="kg-tabs" id="kgTabs"><button class="active" data-graph-filter="all">总览</button></div></div><div class="kg-actions"><button id="structureLayer">知识结构</button><button id="masteryLayer" class="active">掌握状态</button><span id="layerNote">默认展示数据库中的最终掌握状态</span></div><div class="kg-canvas" id="knowledgeGraphCanvas"><div class="home-empty-state">正在加载知识图谱…</div></div><div class="kg-legend" id="kgLegend"></div></article><article class="card home-memory-card"><div class="head"><h3>最近学习记忆</h3></div><div class="memory-list" id="homeMemoryList"><div class="memory"><b>还没有长期学习记忆</b><p>完成一次问答、出题或错题确认后，这里会同步数据库中的长期记忆。</p></div></div></article></div></section>`;
};

const homeBindAll=bindAll;
bindAll=function(){
 homeBindAll();
 bindHomeActions();
 loadHomeOverview();
};

function bindHomeActions(){
 const start=document.getElementById("startPersonalTraining");
 if(start)start.onclick=()=>startPersonalizedTraining();
}

async function loadHomeOverview(){
 if(!document.getElementById("home"))return;
 try{
  const data=await apiRequest("/api/home/overview");
  currentHomeOverview=data;
  renderHomeOverview(data);
 }catch(error){
  console.error(error);
  renderHomeError(error.message);
 }
}

function renderHomeOverview(data){
 renderHomePlan(data.today_plan);
 renderHomeCountdown(data.countdown);
 renderHomeRecommendations(data.recommendations||[]);
 renderHomeStats(data.stats?.cards||[]);
 renderHomeGraph(data.knowledge_graph);
 renderHomeMemories(data.memories||[]);
}

function renderHomePlan(plan){
 const title=document.getElementById("homePlanTitle"),reason=document.getElementById("homePlanReason");
 if(!title||!reason)return;
 title.innerHTML=escapeHtml(plan?.title||"先完成一次\n408 基线诊断").replace(/\n/g,"<br>");
 reason.textContent=plan?.reason||"当前暂无错题记录，先完成一组高频基础题，系统会自动建立初始学习画像。";
}

function renderHomeCountdown(countdown){
 if(!countdown)return;
 homeCountdownTarget=new Date(`${countdown.target_date}T00:00:00+08:00`).getTime();
 const label=document.getElementById("examDateLabel");
 if(label)label.textContent=`目标日期：${countdown.target_label||countdown.target_date}`;
 startExamCountdown();
}

function renderHomeRecommendations(items){
 const list=document.getElementById("todayRecommendList");
 if(!list)return;
 if(!items.length){
  list.innerHTML=`<div class="rec"><b>先完成一次基线诊断</b><small>暂无可用学习行为，系统会从高频知识点开始推荐。</small></div>`;
  return;
 }
 list.innerHTML=items.slice(0,3).map((item,index)=>`<button class="rec home-rec-button" ${item.available?"":"disabled"} data-home-rec="${index}"><b>${escapeHtml(item.subject)} · ${escapeHtml(item.knowledge_point)}</b><small>${escapeHtml(item.mode)} · ${escapeHtml(item.reason)}</small></button>`).join("");
 document.querySelectorAll("[data-home-rec]:not([disabled])").forEach(button=>button.onclick=()=>startPersonalizedTraining(items[Number(button.dataset.homeRec)]));
}

function renderHomeStats(cards){
 const stats=document.getElementById("homeStats");
 if(!stats)return;
 const fallback=[
  {label:"本周答题",value:0,delta:"开始答题后自动统计"},
  {label:"综合正确率",value:"待生成",delta:"暂无答题记录"},
  {label:"长期薄弱点",value:0,delta:"按 weak_score 与错题同步"},
  {label:"记忆条目",value:0,delta:"问答和错题会写入这里"}
 ];
 stats.innerHTML=(cards.length?cards:fallback).map(card=>`<div class="card stat"><small>${escapeHtml(card.label)}</small><strong>${escapeHtml(String(card.value))}</strong><span class="delta">${escapeHtml(card.delta)}</span></div>`).join("");
}

function renderHomeMemories(items){
 const list=document.getElementById("homeMemoryList");
 if(!list)return;
 list.innerHTML=items.map(item=>`<div class="memory"><b>${escapeHtml(item.title)}</b><p>${escapeHtml(item.content)}</p></div>`).join("");
}

function renderHomeGraph(graph){
 const canvas=document.getElementById("knowledgeGraphCanvas"),tabs=document.getElementById("kgTabs"),legend=document.getElementById("kgLegend");
 if(!canvas||!tabs||!graph?.subjects)return;
 const subjects=Object.keys(graph.subjects);
 const colors={数据结构:"#7da2e3",计算机组成原理:"#d9b16f",操作系统:"#df9fbb",计算机网络:"#72c2a9"};
 const positions=[[50,14],[27,28],[22,51],[29,74],[53,78],[77,66],[82,42],[72,22]];
 tabs.innerHTML=`<button class="active" data-graph-filter="all">总览</button>${subjects.map(s=>`<button data-graph-filter="${escapeHtml(s)}">${escapeHtml(s)}</button>`).join("")}`;
 canvas.innerHTML=subjects.map((subject,groupIndex)=>{
  const nodes=(graph.subjects[subject]||[]).slice(0,8);
  return `<section class="kg-quadrant kg-q${groupIndex+1}" data-graph-group="${escapeHtml(subject)}" style="--kg-color:${colors[subject]||"#91a2bb"}"><div class="kg-watermark">${escapeHtml(subject)}</div><svg class="kg-lines" viewBox="0 0 100 100" preserveAspectRatio="none">${nodes.map((_,i)=>`<line x1="50" y1="50" x2="${positions[i%positions.length][0]}" y2="${positions[i%positions.length][1]}"></line>`).join("")}</svg><div class="kg-center">${escapeHtml(subject)}</div>${nodes.map((node,i)=>knowledgeNodeHTML(node,positions[i%positions.length])).join("")}</section>`;
 }).join("");
 const styles=graph.status_style||{};
 legend.innerHTML=Object.keys(styles).map(status=>`<span><i style="background:${styles[status].color};border-color:${styles[status].color}"></i>${status}</span>`).join("");
 bindHomeGraphControls();
}

function knowledgeNodeHTML(node,pos){
 const status=node.status||"未学";
 const color=node.style?.color||"#9aa5b1";
 const className=node.style?.class_name||"unlearned";
 return `<button class="graph-point kg-node show-status status-${className}" style="--x:${pos[0]}%;--y:${pos[1]}%;--status-color:${color}" data-status="${escapeHtml(status)}" data-subject="${escapeHtml(node.subject)}" title="${escapeHtml(node.name)}：${escapeHtml(status)}"><span>${escapeHtml(node.name)}</span><i class="kg-status">${escapeHtml(status)}</i></button>`;
}

function bindHomeGraphControls(){
 const structure=document.getElementById("structureLayer"),mastery=document.getElementById("masteryLayer"),note=document.getElementById("layerNote");
 if(structure)structure.onclick=()=>{structure.classList.add("active");mastery?.classList.remove("active");document.querySelectorAll(".kg-node").forEach(node=>node.classList.remove("show-status"));if(note)note.textContent="当前展示完整知识结构，状态颜色已保留为淡色提示";};
 if(mastery)mastery.onclick=()=>{mastery.classList.add("active");structure?.classList.remove("active");document.querySelectorAll(".kg-node").forEach(node=>node.classList.add("show-status"));if(note)note.textContent="已叠加个人掌握状态：灰=未学，绿=掌握，黄=不熟，橙=不会，红=薄弱点";};
 document.querySelectorAll("[data-graph-filter]").forEach(button=>button.onclick=()=>{document.querySelectorAll("[data-graph-filter]").forEach(x=>x.classList.toggle("active",x===button));const filter=button.dataset.graphFilter,canvas=document.getElementById("knowledgeGraphCanvas");canvas.classList.toggle("single-view",filter!=="all");document.querySelectorAll("[data-graph-group]").forEach(group=>group.classList.toggle("hidden",filter!=="all"&&group.dataset.graphGroup!==filter));if(note)note.textContent=filter==="all"?"当前展示四科完整知识结构":`当前聚焦：${filter}`;});
}

async function startPersonalizedTraining(item){
 const plan=item||currentHomeOverview?.today_plan;
 if(!plan)return toast("首页推荐还在加载，请稍后再试","error");
 showPage("question");
 const payload={mode:plan.mode||"四科随机综合",count:plan.count||3};
 await generateQuestionsFromApi(payload,"已根据首页智能推荐生成题目","/api/questions/generate-smart",{recommend_mode:payload.mode,count:payload.count});
}

function renderHomeError(message){
 const reason=document.getElementById("homePlanReason");
 if(reason)reason.textContent=`首页数据接口暂不可用：${message}`;
 const list=document.getElementById("todayRecommendList");
 if(list)list.innerHTML=`<div class="rec"><b>接口暂不可用</b><small>请确认后端服务已启动，首页不会再使用固定 mock 数据冒充真实推荐。</small></div>`;
}
window.startPersonalizedTraining=startPersonalizedTraining;

startExamCountdown=function(){
 const update=()=>{
  const diff=Math.max(0,homeCountdownTarget-Date.now()),days=Math.floor(diff/86400000),hours=Math.floor(diff%86400000/3600000),minutes=Math.floor(diff%3600000/60000),seconds=Math.floor(diff%60000/1000);
  const set=(id,value)=>{const el=document.getElementById(id);if(el)el.textContent=String(value).padStart(2,"0")};
  set("countdownDays",days);set("countdownHours",hours);set("countdownMinutes",minutes);set("countdownSeconds",seconds);
  const subtitle=document.getElementById("pageSub");
  if(subtitle&&["qa","question","mistake","forum","report"].some(id=>document.getElementById(id)?.classList.contains("active")))subtitle.textContent=`距离 408 初试还有 ${days} 天 · 今日计划完成 3 / 5`;
 };
 update();
 if(countdownTimer)clearInterval(countdownTimer);
 countdownTimer=setInterval(update,1000);
};

/* ========= 不会/不熟题本真实接口对接 ========= */
async function loadMistakeNotebook(statuses="不熟,不会"){
 try{
  const data=await apiRequest(`/api/mistakes/notebook?status=${encodeURIComponent(statuses)}`);
  const payload=data.data||data;
  if(statuses==="不熟,不会")notebookCache=payload;
  const stats=payload.stats||{};
  const el1=document.getElementById("unfamiliarCount");
  const el2=document.getElementById("unknownCount");
  const tag=document.getElementById("unfamiliarTag");
  if(el1)el1.textContent=stats.unfamiliar||0;
  if(el2)el2.textContent=stats.unknown||0;
  if(tag)tag.textContent=(stats.total||0)>0?"已同步后端":"暂无数据";
  return payload;
 }catch(error){
  console.error(error);
  const el1=document.getElementById("unfamiliarCount");
  const el2=document.getElementById("unknownCount");
  if(el1)el1.textContent="0";
  if(el2)el2.textContent="0";
  toast(error.message||"题本加载失败","error");
  return null;
 }
}

async function submitBookMastery(button){
 const group=button.parentElement;
 group.querySelectorAll("button").forEach(x=>x.classList.remove("current"));
 button.classList.add("current");
 const status=button.dataset.bookMastery;
 const mistakeId=button.dataset.mistakeId;
 try{
  await apiRequest(`/api/mistakes/${mistakeId}/mastery`,{method:"POST",body:JSON.stringify({status})});
  notebookCache=null;
  toast(status==="掌握"?"已标记掌握，将移出题本":`已归入${status}题本`,"success");
  const current=document.querySelector(".book-view.active")?.id?.replace("book-","");
  await loadMistakeNotebook();
  if(current==="unfamiliar"||current==="unknown")openBookView(current);
 }catch(error){
  toast(error.message||"状态更新失败","error");
 }
}

async function openBookView(name){
 document.querySelectorAll(".book-view").forEach(v=>v.classList.toggle("active",v.id===`book-${name}`));
 const titles={
  overview:["我的题本","智能出题、错因确认和 OCR 导入中标记“不熟/不会”的题目会进入对应题本"],
  unfamiliar:["不熟题本","理解不稳定的题目，集中做同类巩固"],
  unknown:["不会题本","尚未掌握的题目，优先重新学习与练习"],
  ocr:["OCR 导入","PaddleOCR 识别 → 校对 → Agent 分析 → 记忆更新"]
 };
 const title=document.getElementById("mistakeTitle");
 const subtitle=document.getElementById("mistakeSubtitle");
 if(title)title.textContent=titles[name]?.[0]||"我的题本";
 if(subtitle)subtitle.textContent=titles[name]?.[1]||"";
 window.scrollTo(0,0);
 if(name==="overview"){
  await loadMistakeNotebook();
  return;
 }
 if(name==="unfamiliar"||name==="unknown"){
  const status=name==="unfamiliar"?"不熟":"不会";
  const container=document.getElementById(`${name}BookList`);
  if(container)container.innerHTML=`<div class="conversation-empty">正在加载${status}题本…</div>`;
  const payload=await loadMistakeNotebook(status);
  renderMistakeCards((payload?.items||[]).filter(i=>i.mastery_status===status),name);
 }
}

async function submitMasteryFeedback(button){
 const group=button.parentElement;
 group.querySelectorAll("button").forEach(x=>x.classList.remove("chosen"));
 button.classList.add("chosen");
 const q=activeQuestions[currentQuestionIndex];
 const status=button.textContent.trim();
 if(!q)return toast("当前没有可记录的题目","error");
 try{
  await apiRequest("/api/questions/mastery",{method:"POST",body:JSON.stringify({subject:q.subject,knowledge_point:q.knowledge_point,status,question_id:q.id||null})});
  notebookCache=null;
  toast(status==="掌握"?"已标记掌握":`已加入${status}题本，知识点状态已更新`,"success");
 }catch(error){
  console.error(error);
  toast(`${error.message}，页面已先保留你的选择`,"error");
 }
}

function updateForumPostCounts(post,counts={}){
 if(!post)return;
 if(counts.like_count!==undefined){
  const likeEl=post.querySelector("[data-forum-like-count]");
  if(likeEl)likeEl.textContent=Number(counts.like_count||0);
 }
 if(counts.comment_count!==undefined){
  const commentEl=post.querySelector("[data-forum-comment-count]");
  if(commentEl)commentEl.textContent=Number(counts.comment_count||0);
 }
}

async function refreshForumPostCounts(postId,post){
 try{
  const data=await apiRequest(`/api/forum/posts/${postId}`);
  if(data.post)updateForumPostCounts(post,data.post);
 }catch(error){
  console.error(error);
 }
}

async function likeForumPost(postId,button){
 const post=button.closest(".forum-post");
 const wasLiked=button.classList.contains("liked");
 button.disabled=true;
 try{
  const data=await apiRequest(`/api/forum/posts/${postId}/${wasLiked?"unlike":"like"}`,{method:"POST"});
  button.classList.toggle("liked",!wasLiked);
  button.textContent=wasLiked?"赞":"已赞";
  updateForumPostCounts(post,{like_count:data.like_count});
  loadHotTopics();
 }catch(err){
  toast(err.message||"点赞失败","error");
 }finally{
  button.disabled=false;
 }
}

async function submitComment(postId,content,post){
 try{
  const data=await apiRequest(`/api/forum/posts/${postId}/comments`,{method:"POST",body:JSON.stringify({content})});
  toast("评论已发布","success");
  post.querySelector(".forum-comment-box")?.classList.remove("show");
  await loadComments(postId,post);
  if(data.comment_count!==undefined)updateForumPostCounts(post,{comment_count:data.comment_count});
  else await refreshForumPostCounts(postId,post);
  loadHotTopics();
 }catch(err){
  toast(err.message||"评论发布失败","error");
 }
}

/* ========= 学习报告真实数据对接 ========= */
reportHTML=function(){
 return `<section class="page" id="report"><div class="stats" id="reportStats"><div class="card stat"><small>答题总数</small><strong>--</strong></div><div class="card stat"><small>答对</small><strong>--</strong></div><div class="card stat"><small>答错</small><strong>--</strong></div><div class="card stat"><small>正确率</small><strong>--</strong></div></div><div class="report-grid report-main-grid"><article class="card report-main-card"><div class="head"><h3>四科掌握趋势</h3><span class="tag">后端统计</span></div><div class="chart" id="reportSubjectTrend"><div class="home-empty-state">正在读取四科掌握趋势...</div></div></article><article class="card report-plan-card"><div class="head"><h3>下一轮个性化训练计划</h3><button class="primary" id="exportReport">导出报告</button></div><div id="reportPlanList"><div class="home-empty-state">正在计算下一轮训练计划...</div></div></article></div><div class="report-section-title"><div><h2>学习画像</h2><p>基于答题、错题、问答、论坛与长期记忆生成</p></div></div><div class="learning-profile-grid"><article class="card learning-user-card" id="reportProfile"><div class="profile-avatar">--</div><h3>读取中</h3><p>正在同步后端学习画像</p><div></div></article><article class="card learning-memory-card"><div class="head"><h3>长期记忆权重</h3></div><div id="reportMemoryWeights"><div class="home-empty-state">正在读取长期记忆权重...</div></div></article></div></section>`;
};

async function loadReportOverview(){
 const report=document.getElementById("report");
 if(!report)return;
 try{
  const data=await apiRequest("/api/reports/overview");
  renderReportOverview(data);
 }catch(error){
  console.error(error);
  const stats=document.getElementById("reportStats");
  if(stats)stats.innerHTML=`<div class="card stat"><small>报告加载失败</small><strong>--</strong><span class="delta">${escapeHtml(error.message)}</span></div>`;
  toast(error.message||"学习报告加载失败","error");
 }
}

function renderReportOverview(data){
 renderReportStats(data.stats||{});
 renderSubjectTrend(data.subject_trends||[]);
 renderReportPlan(data.next_plan||[]);
 renderMemoryWeights(data.memory_weights||[]);
 renderLearningProfile(data.profile||{});
 const exportButton=document.getElementById("exportReport");
 if(exportButton)exportButton.onclick=exportLearningReport;
}

function renderReportStats(stats){
 const box=document.getElementById("reportStats");
 if(!box)return;
 box.innerHTML=[
  ["答题总数",stats.total??0],
  ["答对",stats.correct??0],
  ["答错",stats.wrong??0],
  ["正确率",`${stats.accuracy??0}%`],
 ].map(([label,value])=>`<div class="card stat"><small>${label}</small><strong>${value}</strong></div>`).join("");
}

function renderSubjectTrend(items){
 const chart=document.getElementById("reportSubjectTrend");
 if(!chart)return;
 if(!items.length){
  chart.innerHTML=`<div class="home-empty-state">暂无四科掌握记录</div>`;
  return;
 }
 chart.innerHTML=items.map(item=>{
  const height=Math.max(6,Number(item.score||0));
  return `<div class="bar" style="height:${height}%" title="${escapeHtml(String(item.score||0))}%"><span>${escapeHtml(String(item.subject))}</span></div>`;
 }).join("");
}

function renderReportPlan(items){
 const list=document.getElementById("reportPlanList");
 if(!list)return;
 if(!items.length){
  list.innerHTML=`<div class="home-empty-state">暂无训练计划，完成一次答题后自动生成</div>`;
  return;
 }
 list.innerHTML=items.slice(0,3).map((item,index)=>`<div class="plan-item"><i>${String(index+1).padStart(2,"0")}</i><div><b>${escapeHtml(String(item.subject))} · ${escapeHtml(String(item.knowledge_point))} · ${escapeHtml(String(item.count))} 道${escapeHtml(String(item.question_type))}</b><small>${escapeHtml(String(item.mode))} · ${escapeHtml(String(item.difficulty))} · ${escapeHtml(String(item.reason))}</small></div></div>`).join("");
}

function renderMemoryWeights(items){
 const box=document.getElementById("reportMemoryWeights");
 if(!box)return;
 if(!items.length){
  box.innerHTML=`<div class="home-empty-state">暂无长期记忆权重，问答、错题和 OCR 导入后会自动形成</div>`;
  return;
 }
 const max=Math.max(...items.map(item=>Number(item.weight||0)),1);
 box.innerHTML=items.map(item=>{
  const width=Math.max(6,Math.round(Number(item.weight||0)*100/max));
  return `<div class="weight-row"><span>${escapeHtml(String(item.knowledge_point))}</span><div class="weight-track"><span style="width:${width}%"></span></div><b>${escapeHtml(String(item.weight))}</b><small>${escapeHtml(String(item.status||""))}</small></div>`;
 }).join("");
}

async function exportLearningReport(){
 const button=document.getElementById("exportReport");
 if(button)button.disabled=true;
 try{
  toast("正在调用报告 Agent 生成分析...","success");
  const report=await apiRequest("/api/reports/generate",{method:"POST"});
  const lines=[
   report.title||"Turing 408 学习报告",
   `生成时间：${report.create_time||new Date().toISOString()}`,
   `分析来源：${report.llm_used?"AI 大模型分析":"后端保底分析"}`,
   "",
   "阶段总结",
   report.summary||"暂无总结",
   "",
   "薄弱知识点",
   report.weak_points||"暂无明显薄弱点",
   "",
   "主要错误类型",
   report.main_error_type||"暂无",
   "",
   "问答关注",
   report.qa_focus||"暂无",
   "",
   "论坛关注",
   report.forum_focus||"暂无",
   "",
   "视频建议",
   report.video_suggestion||"暂无",
   "",
   "下一轮训练计划",
   ...(report.plan||[]).map((item,index)=>`${index+1}. ${item}`),
   "",
   "长期记忆摘要",
   ...((report.memories||[]).length?report.memories.map(item=>`- ${item.knowledge_point||"知识点"}：${item.content||""}`):["暂无长期记忆摘要"]),
  ];
  const blob=new Blob([lines.join("\n")],{type:"text/plain;charset=utf-8"});
  const url=URL.createObjectURL(blob);
  const link=document.createElement("a");
  link.href=url;
  link.download=`Turing408学习报告-${new Date().toISOString().slice(0,10)}.txt`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
  toast("学习报告已导出","success");
  await loadReportOverview();
 }catch(error){
  console.error(error);
  toast(error.message||"报告导出失败","error");
 }finally{
  if(button)button.disabled=false;
 }
}

function renderLearningProfile(profile){
 const card=document.getElementById("reportProfile");
 if(!card)return;
 const tags=profile.tags||[];
 card.innerHTML=`<div class="profile-avatar">${escapeHtml(String(profile.avatar||"图"))}</div><h3>${escapeHtml(String(profile.name||"学习者"))}</h3><p>${escapeHtml(String(profile.target||"408 学习画像"))}</p><div>${tags.length?tags.map(tag=>`<span class="trait">${escapeHtml(String(tag))}</span>`).join(""):`<span class="trait">暂无学习画像</span>`}</div>`;
}

const reportAwareShowPage=showPage;
showPage=function(id){
 reportAwareShowPage(id);
 if(id==="report")loadReportOverview();
};
