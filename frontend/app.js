const theme=document.body.dataset.theme;
const themeName={cockpit:"智能学习驾驶舱",workspace:"轻量学习工作台",study:"沉浸式研习空间"}[theme];
const pages=[
 ["home","⌂","学习首页"],["knowledge","◈","知识点导航"],["qa","✦","知识问答"],["question","✎","智能出题"],["mistake","!","错题本"],["forum","◎","学习论坛"],["report","▥","学习报告"]
];

// ============ 实时动态问候语（按东八区/Asia/Shanghai 时段变化） ============
const TIME_GREETINGS = [
 { start: 0,  end: 5,  text: "夜深了，注意休息", emoji: "🌙" },
 { start: 6,  end: 11, text: "早上好，继续向目标前进", emoji: "☀️" },
 { start: 12, end: 13, text: "中午好，记得午休", emoji: "🍱" },
 { start: 14, end: 17, text: "下午好，保持节奏", emoji: "☕" },
 { start: 18, end: 22, text: "晚上好，回顾一下今天", emoji: "🌆" },
 { start: 23, end: 23, text: "夜深了，早点休息", emoji: "🌙" },
];

function getTimeBasedGreeting(){
 // 强制使用东八区时间，避免用户系统时区漂移
 let hour;
 try{
  hour = Number(new Intl.DateTimeFormat("zh-CN",{timeZone:"Asia/Shanghai",hour:"numeric",hour12:false}).format(new Date()));
 }catch(e){
  hour = new Date().getHours();   // 兜底：用户系统时间
 }
 for(const g of TIME_GREETINGS){
  if(hour >= g.start && hour <= g.end) return `${g.text} ${g.emoji}`;
 }
 return "继续加油 ✨";   // 理论不会到
}

let greetingTimer = null;
function startGreetingAutoUpdate(){
 if(greetingTimer) return;   // 防止重复启动
 const update = () => {
  const t = getTimeBasedGreeting();
  const title = document.getElementById("pageTitle");
  if(title) title.textContent = t;
 };
 update();   // 立即刷一次
 // 每 30 秒检查一次（够用，跨小时段最多 30 秒延迟）
 greetingTimer = setInterval(update, 30 * 1000);
}
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

async function initApp(){
  // 强制重新登录入口：来自首页/指南页"登录 / 注册"链接 (?login=1)
  if(new URLSearchParams(location.search).get("login")==="1"){
    localStorage.removeItem("turing408_token");
    localStorage.removeItem("turing408_user");
    // 清理 URL 上的 query，避免刷新或分享时残留
    const cleanUrl=location.pathname+location.hash;
    history.replaceState(null,"",cleanUrl);
    app.innerHTML=applyBrandName(loginHTML());
    return;
  }
  const token=localStorage.getItem("turing408_token");
  const userStr=localStorage.getItem("turing408_user");
  if(token&&userStr){
    let parsedUser=null;
    try{parsedUser=JSON.parse(userStr)}catch(e){}
    try{
      // 先验证token是否有效
      const meData = await apiRequest("/api/auth/me");
      const user = meData.user || parsedUser;
      app.innerHTML=applyBrandName(shellHTML());
      repairPagePlacement();
      bindAll();
      if(user?.nickname){
        const nameEl=document.getElementById("topUserName");
        const avatarEl=document.getElementById("topAvatar");
        if(nameEl)nameEl.textContent=user.nickname;
        if(avatarEl)avatarEl.textContent=user.nickname[0];
      }
      showPage("home");
      return;
    }catch(e){
      // 修复：仅在 401（INVALID_TOKEN / 登录态失效）时清除 localStorage。
      // 网络错误 / 后端未起 / 5xx 等临时性错误不应让用户掉线。
      const msg=String(e?.message||"");
      const isAuthFail=/INVALID_TOKEN|UNAUTHORIZED|登录|401/.test(msg);
      if(isAuthFail){
        localStorage.removeItem("turing408_token");
        localStorage.removeItem("turing408_user");
      } else if(parsedUser){
        // 临时性错误：降级到本地缓存 user 继续使用，等后端恢复后下一次 api 调用会自然重连。
        app.innerHTML=applyBrandName(shellHTML());
        repairPagePlacement();
        bindAll();
        if(parsedUser?.nickname){
          const nameEl=document.getElementById("topUserName");
          const avatarEl=document.getElementById("topAvatar");
          if(nameEl)nameEl.textContent=parsedUser.nickname;
          if(avatarEl)avatarEl.textContent=parsedUser.nickname[0];
        }
        showPage("home");
        // 不再弹"后端暂不可用"toast:当后端实际可用时(后续接口成功)这条 toast 是误导;
        // 当后端真不可用时,后续接口的"接口暂不可用"提示会自然告知用户,无需在初始化阶段多此一举。
        return;
      }
    }
  }
  app.innerHTML=applyBrandName(loginHTML());
}
initApp();
/* ========= 退出登录:右上角个人账户面板触发 ========= */
async function handleLogout(){
 const btn=document.getElementById("logoutBtn");
 if(btn){btn.disabled=true;btn.textContent="退出中…";}
 // 1. 通知后端把 token 加入黑名单(忽略失败,前端清缓存同样能登出)
 try{
  await apiRequest("/api/auth/logout",{method:"POST"});
 }catch(e){
  console.warn("logout api failed:",e?.message);
 }
 // 2. 关闭面板 + 清理所有本地状态 + 缓存
 try{
  document.getElementById("accountPanel")?.classList.remove("open");
  document.getElementById("accountMask")?.classList.remove("show");
  document.body.classList.remove("account-open");
 }catch(e){}
 localStorage.removeItem("turing408_token");
 localStorage.removeItem("turing408_user");
 // 清理内存缓存
 if(typeof knowledgeOverviewCache!=="undefined"){knowledgeOverviewCache=null;knowledgeOverviewCacheAt=0;}
 if(typeof knowledgeGraphCache!=="undefined")knowledgeGraphCache=null;
 if(typeof notebookCache!=="undefined")notebookCache=null;
 if(typeof currentHomeOverview!=="undefined")currentHomeOverview=null;
 if(typeof reportCache!=="undefined"){reportCache=null;reportCacheAt=0;}
 if(btn){btn.disabled=false;btn.textContent="退出登录";}
 toast("已退出登录","success");
 // 3. 重新渲染登录页
 app.innerHTML=applyBrandName(loginHTML());
}

/* ========= 手机端导航抽屉 ========= */
function openMobileNav(){
  const sidebar=document.getElementById("appSidebar");
  const mask=document.getElementById("sidebarMask");
  if(sidebar)sidebar.classList.add("open");
  if(mask)mask.classList.add("show");
  document.body.classList.add("nav-open");
}
function closeMobileNav(){
  const sidebar=document.getElementById("appSidebar");
  const mask=document.getElementById("sidebarMask");
  if(sidebar)sidebar.classList.remove("open");
  if(mask)mask.classList.remove("show");
  document.body.classList.remove("nav-open");
}
function bindMobileNav(){
  const toggle=document.getElementById("sidebarToggle");
  const close=document.getElementById("sidebarClose");
  const mask=document.getElementById("sidebarMask");
  if(toggle)toggle.onclick=openMobileNav;
  if(close)close.onclick=closeMobileNav;
  if(mask)mask.onclick=closeMobileNav;
  // ESC 关闭
  document.addEventListener("keydown",e=>{
    if(e.key==="Escape")closeMobileNav();
  });
}

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
        <span>数据结构</span>
        <span>计算机组成原理</span>
        <span>操作系统</span>
        <span>计算机网络</span>
      </div>
    </div>
    <div class="login-form">
      <div class="form-card" id="loginFormCard">
        <span class="eyebrow">TURING 408 AGENT</span>
        <h2>欢迎回来，未来的计算机先驱</h2>
        <p>继续这场由图灵本人亲自参加的 408 备考计划</p>
        <div class="field">
          <label>账号</label>
          <input id="loginAccount" placeholder="请输入账号">
        </div>
        <div class="field">
          <label>密码</label>
          <input id="loginPassword" type="password" placeholder="请输入密码" oninput="this.style.borderColor=''">
        </div>
        <button class="primary full" onclick="enterApp()">进入图灵学习空间</button>
        <button class="ghost full" onclick="showRegisterForm()">创建新账号</button>
      </div>
    </div>
  </section>`
}
function showRegisterForm(){
  const card=document.getElementById("loginFormCard");
  if(!card)return;
  card.innerHTML=`
    <span class="eyebrow">TURING 408 AGENT</span>
    <h2>开启你的 408 备考之旅</h2>
    <p>加入图灵学习空间，系统备考计算机专业基础综合</p>
    <div class="field">
      <label>账号</label>
      <input id="regAccount" placeholder="请输入账号">
    </div>
    <div class="field">
      <label>密码</label>
      <input id="regPassword" type="password" placeholder="设置密码（至少8位）">
    </div>
    <button class="primary full" onclick="registerNewAccount()">注册并进入</button>
    <button class="ghost full" onclick="showLoginForm()">已有账号？去登录</button>
  `;
}
function showLoginForm(){
  const card=document.getElementById("loginFormCard");
  if(!card)return;
  card.innerHTML=`
    <span class="eyebrow">TURING 408 AGENT</span>
    <h2>欢迎回来，未来的计算机先驱</h2>
    <p>继续这场由图灵本人亲自参加的 408 备考计划</p>
    <div class="field">
      <label>账号</label>
      <input id="loginAccount" placeholder="请输入账号">
    </div>
    <div class="field">
      <label>密码</label>
      <input id="loginPassword" type="password" placeholder="请输入密码" oninput="this.style.borderColor=''">
    </div>
    <button class="primary full" onclick="enterApp()">进入图灵学习空间</button>
    <button class="ghost full" onclick="showRegisterForm()">创建新账号</button>
  `;
}
async function registerNewAccount(){
  const account = document.getElementById("regAccount")?.value;
  const password = document.getElementById("regPassword")?.value;
  
  if (!account || !password) {
    toast("请输入账号和密码", "error");
    return;
  }
  
  const isEmail = account.includes("@");
  const username = isEmail ? account.split("@")[0] : account;
  const nickname = username;
  
  const regBtn = document.querySelector(".login-form button.primary");
  if (regBtn) { regBtn.disabled = true; regBtn.textContent = "注册中..."; }
  
  try {
    const data = await apiRequest("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({
        email: isEmail ? account : username + "@turing408.ai",
        username: username,
        password: password,
        nickname: nickname
      })
    });
    const token = data.access_token;
    const user = data.user;
    localStorage.setItem("turing408_token", token);
    localStorage.setItem("turing408_user", JSON.stringify(user));
    
    app.innerHTML = applyBrandName(shellHTML());
    repairPagePlacement();
    bindAll();
    
    if (user?.nickname) {
      const nameEl = document.getElementById("topUserName");
      const avatarEl = document.getElementById("topAvatar");
      if (nameEl) nameEl.textContent = user.nickname;
      if (avatarEl) avatarEl.textContent = user.nickname[0];
    }
    
    showPage("home");
    toast("注册成功，欢迎加入图灵学习空间！", "success");
  } catch(err) {
    toast(err.message || "注册失败", "error");
    if (regBtn) { regBtn.disabled = false; regBtn.textContent = "注册并进入"; }
  }
}

async function enterApp(){
  const email = document.querySelectorAll(".login-form input")[0]?.value;
  const password = document.querySelectorAll(".login-form input")[1]?.value;
  
  if (!email || !password) {
    toast("请输入账号和密码", "error");
    return;
  }
  
  const loginBtn = document.querySelector(".login-form button.primary");
  if (loginBtn) { loginBtn.disabled = true; loginBtn.textContent = "登录中..."; }
  
  try {
    const data = await apiRequest("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ account: email, password: password })
    });
    const token = data.access_token;
    const user = data.user;
    localStorage.setItem("turing408_token", token);
    localStorage.setItem("turing408_user", JSON.stringify(user));
    
    app.innerHTML = applyBrandName(shellHTML());
    repairPagePlacement();
    bindAll();
    
    if (user?.nickname) {
      const nameEl = document.getElementById("topUserName");
      const avatarEl = document.getElementById("topAvatar");
      if (nameEl) nameEl.textContent = user.nickname;
      if (avatarEl) avatarEl.textContent = user.nickname[0];
    }
    
    showPage("home");
    toast("登录成功，欢迎回来！", "success");
  } catch(err) {
    toast(err.message || "登录失败", "error");
    const pwdInput = document.getElementById("loginPassword");
    if (pwdInput) pwdInput.style.borderColor = "#ef4444";
    if (loginBtn) { loginBtn.disabled = false; loginBtn.textContent = "进入图灵学习空间"; }
  }
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
  return `<article class="card knowledge-graph-card"><div class="kg-toolbar"><div><h3>408 全局知识图谱</h3><p>按四科完整考纲展示知识点关系，可切换单科视图或总览。</p></div><div class="kg-tabs"><button class="active" data-graph-filter="all">总览</button>${Object.keys(groups).map(x=>`<button data-graph-filter="${x}">${x}</button>`).join("")}</div></div><div class="kg-actions"><button id="structureLayer" class="active">知识结构</button><button id="masteryLayer">叠加掌握状态</button><span id="layerNote">当前展示完整知识结构</span></div><div class="kg-canvas" id="knowledgeGraphCanvas">${Object.entries(groups).map(([subject,nodes],groupIndex)=>`<section class="kg-quadrant kg-q${groupIndex+1}" data-graph-group="${subject}" style="--kg-color:${colors[subject]}"><div class="kg-watermark">${subject}</div><svg class="kg-lines" viewBox="0 0 100 100" preserveAspectRatio="none">${nodes.map(n=>`<line x1="50" y1="50" x2="${n[1]}" y2="${n[2]}"></line>`).join("")}</svg><div class="kg-center">${subject}</div>${nodes.map((n,nodeIndex)=>`<button class="graph-point kg-node ${n[3]}" style="--x:${n[1]}%;--y:${n[2]}%" data-subject="${subject}" data-level="${n[3]==="hot"?"high":"key"}"><span>${n[0]}</span>${children[subject].slice(nodeIndex,nodeIndex+2).map((child,childIndex)=>`<i class="kg-child c${childIndex+1}">${child}</i>`).join("")}</button>`).join("")}</section>`).join("")}</div><div class="kg-legend kg-legend-status"><span><i style="background:#2fbf7a"></i>掌握 ≥80 分</span><span><i style="background:#f5bd22"></i>不熟 50~79 分</span><span><i style="background:#ff9f43"></i>不会 20~49 分</span><span><i style="background:#ff6262"></i>薄弱点 1~19 分</span><span><i style="background:#a8b0bf"></i>未学 0 分</span><span><i class="normal"></i>普通知识点</span><span><i class="important"></i>重点知识点</span></div></article>`
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
    <div class="sidebar-mask" id="sidebarMask"></div>
    <aside class="sidebar" id="appSidebar">
      <div class="sidebar-head">
        <div class="brand-lockup">
          <div class="brand-mark">图</div>
          <div class="logo">
            重生之我是图灵
            <small>TURING 408 AGENT</small>
          </div>
        </div>
        <button class="sidebar-close" id="sidebarClose" aria-label="关闭导航">×</button>
      </div>
      <nav class="nav">
        ${pages.map(p=>`<button data-page="${p[0]}"><i>${p[1]}</i>${p[2]}</button>`).join("")}
      </nav>
      <div class="memory-chip">
        <b>🔥 连续学习 <span id="sidebarStreakDays">--</span> 天</b>
        <span id="sidebarStreakText">长期记忆已加载。</span>
      </div>
    </aside>
    <div class="main">
      <header class="topbar">
        <button class="hamburger" id="sidebarToggle" aria-label="打开导航">
          <span></span><span></span><span></span>
        </button>
        <div class="topbar-title">
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
      ${knowledgeHTML()}
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
          </div>
        </section>
      </div>
      <div class="account-save-row">
        <button class="primary" id="accountSaveBtn">保存修改</button>
      </div>
      <div class="account-logout-row">
        <button class="ghost danger" id="logoutBtn">退出登录</button>
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
  const liked=!!p.liked;
  return `<article class="card forum-post" data-post-id="${p.id}" data-forum-subject="${escapeHtml(String(p.subject||""))}">
    <div class="forum-vote">
<button data-forum-like aria-label="点赞" class="${liked?"liked":""}"><svg width="16" height="16" viewBox="0 0 24 24" fill="${liked?"currentColor":"none"}" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3m7-2V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14Z"/></svg></button>      <b data-forum-like-count>${likeCount}</b>
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
          <button data-forum-comment="${p.id}">评论 <span data-forum-comment-count>${commentCount}</span></button>
        </div>
      </div>
      <div class="forum-ai-answer" id="forumAi${p.id}">
        <div class="forum-ai-head">
          <span class="forum-ai-mark">AI</span>
          <div><b>图灵 AI 小助手</b><small>结合 408 考纲、用户薄弱点与 RAG 检索生成</small></div>
          <div class="forum-ai-head-actions">
            <span class="forum-ai-confidence" id="forumAiConf${p.id}" data-confidence="unknown"></span>
            <button data-toggle-ai-steps="${p.id}" title="查看思维链">⚙</button>
            <button data-close-ai>收起</button>
          </div>
        </div>
        <div class="forum-ai-content" id="forumAiContent${p.id}">
          <p style="color:var(--muted)">点击「小助手解答」生成 AI 回答…</p>
        </div>
        <div class="forum-ai-feedback" id="forumAiFeedback${p.id}" style="display:none">
          <span>对回答有帮助：</span>
          <button data-ai-like="${p.id}">👍 有用</button>
          <button data-ai-dislike="${p.id}">👎 不准确</button>
          <span class="forum-ai-likes" id="forumAiLikes${p.id}"></span>
        </div>
        <div class="forum-ai-steps" id="forumAiSteps${p.id}" style="display:none"></div>
        <div class="forum-ai-followup">
          <input placeholder="继续追问这个问题…">
          <button data-ai-followup="${p.id}">发送</button>
        </div>
        <div class="forum-ai-followup-hint" id="forumAiHint${p.id}" style="display:none"></div>
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

/* ========= 知识点导航页面 ========= */
let kpNavSubjects=[];
let kpNavActiveSubjectId=null;

function knowledgeHTML(){
 return `<section class="page" id="knowledge">
  <div class="home-knowledge-layout" id="knKnowledgeLayout">
    <!-- 科目卡片区 -->
    <div class="kn-subject-bar" id="knSubjectBar">
      <div class="kn-subject-bar-title">选择科目</div>
      <div class="kn-subject-bar-list" id="knSubjectBarList"></div>
    </div>
    <button class="kn-mobile-tree-toggle" id="knMobileTreeToggle" type="button" aria-expanded="false" aria-controls="knTreePanel">
      <span>查看知识点目录</span>
      <b>展开</b>
    </button>
    <!-- 三栏：左侧树 + 右侧详情 -->
    <div class="kn-three-col">
      <aside class="kn-tree-panel" id="knTreePanel">
        <div class="kn-tree-panel-head">
          <div class="kn-tree-panel-title-row">
            <h3>知识点目录</h3>
            <button class="kn-mobile-tree-close" id="knMobileTreeClose" type="button" aria-label="收起知识点目录">收起</button>
          </div>
          <div class="kn-tree-legend" id="knTreeLegend"></div>
        </div>
        <div class="kn-tree-panel-body" id="knTreePanelBody">
          <div class="kn-loading">加载中…</div>
        </div>
      </aside>
      <main class="kn-detail-panel" id="knDetailPanel">
        <div class="kn-loading">请从左侧选择知识点查看详情</div>
      </main>
    </div>
  </div>
</section>`;
}

let knActiveTab="graph";

function bindKnPageTabs(){}

function renderKnowledgeTab(tabName){}

function setKnMobileTreeOpen(open){
 const panel=document.getElementById("knTreePanel");
 const toggle=document.getElementById("knMobileTreeToggle");
 if(panel)panel.classList.toggle("mobile-open",open);
 if(toggle){
  toggle.setAttribute("aria-expanded",open?"true":"false");
  const label=toggle.querySelector("span");
  const state=toggle.querySelector("b");
  if(label)label.textContent=open?"收起知识点目录":"查看知识点目录";
  if(state)state.textContent=open?"收起":"展开";
 }
}

function bindKnMobileTreeToggle(){
 const toggle=document.getElementById("knMobileTreeToggle");
 const close=document.getElementById("knMobileTreeClose");
 if(toggle)toggle.onclick=()=>setKnMobileTreeOpen(!document.getElementById("knTreePanel")?.classList.contains("mobile-open"));
 if(close)close.onclick=()=>setKnMobileTreeOpen(false);
}

function closeKnMobileTreeAfterPick(){
 if(window.matchMedia&&window.matchMedia("(max-width: 679px)").matches){
  setKnMobileTreeOpen(false);
 }
}

/* 知识导航页:挂起的跳转目标(供 loadKnowledgeNavPage 消费,避免被默认加载覆盖) */
let knPendingNavTarget=null;

async function loadKnowledgeNavPage(){
 const main=document.getElementById("knKnowledgeLayout");
 if(!main)return;
 bindKnMobileTreeToggle();
 setKnMobileTreeOpen(false);
 try{
  const overview=await apiRequest("/api/knowledge/overview");
  const subjects=overview.subjects||[];
  window.knSubjectCardsCache=subjects;
  if(!subjects.length){
   document.getElementById("knSubjectBarList").innerHTML='<div class="kn-empty">暂无科目数据</div>';
   return;
  }
  // 渲染顶部科目卡片
  renderSubjectBar(subjects);
  // 优先消费挂起目标(从知识图谱跳转而来),否则默认第一个科目
  const pending=knPendingNavTarget;
  knPendingNavTarget=null;
  if(pending&&pending.subjectId){
   const opts={};
   if(pending.chapterId)opts.targetChapterId=pending.chapterId;
   if(pending.pointId)opts.targetPointId=pending.pointId;
   await switchKnSubject(pending.subjectId,opts);
  }else{
   await switchKnSubject(subjects[0].subject_id);
  }
 }catch(error){
  console.error(error);
  const list=document.getElementById("knSubjectBarList");
  if(list)list.innerHTML=`<div class="kn-empty">加载失败：${escapeHtml(error.message||"")}</div>`;
 }
}

/* 渲染顶部科目卡片横向列表 */
function renderSubjectBar(subjects){
 const list=document.getElementById("knSubjectBarList");
 if(!list)return;
 list.innerHTML=subjects.map(s=>`
  <button class="kn-subject-card-h" data-kn-subject-id="${s.subject_id}" style="--subject-color:${s.style?.color||statusPalette(s.status)}">
   <i class="kn-subject-dot"></i>
   <div class="kn-subject-card-h-info">
     <b>${escapeHtml(s.subject_name)}</b>
     <small>掌握度 ${s.mastery_percent||0}%</small>
   </div>
  </button>
 `).join("");
 list.querySelectorAll("[data-kn-subject-id]").forEach(btn=>{
  btn.onclick=()=>{
   setKnMobileTreeOpen(false);
   switchKnSubject(Number(btn.dataset.knSubjectId));
  };
 });
}

/* 切换当前科目：更新卡片高亮、刷新目录树、默认选中第一个知识点 */
async function switchKnSubject(subjectId,opts={}){
 kpNavActiveSubjectId=subjectId;
 const targetChapterId=opts.targetChapterId?Number(opts.targetChapterId):null;
 const targetPointId=opts.targetPointId?Number(opts.targetPointId):null;
 // 高亮当前科目卡片
 document.querySelectorAll("#knSubjectBarList [data-kn-subject-id]").forEach(btn=>{
  btn.classList.toggle("active",Number(btn.dataset.knSubjectId)===subjectId);
 });
 // 加载目录树
 const treeBody=document.getElementById("knTreePanelBody");
 if(treeBody)treeBody.innerHTML='<div class="kn-loading">加载目录中…</div>';
 try{
  const graph=await apiRequest(`/api/knowledge/subject/${subjectId}/graph`);
  activeSubjectGraph=graph;
  renderKnTreePanel(treeBody,graph,{targetChapterId,targetPointId});
  // 目标定位:知识点 → 该点;章节 → 第一节;无目标 → 第一个知识点
  if(targetPointId){
   await loadKnPointDetail(targetPointId);
  }else if(targetChapterId){
   const targetChapter=(graph.chapters||[]).find(ch=>ch.id===targetChapterId);
   const firstPoint=targetChapter?.children?.[0];
   if(firstPoint){
    await loadKnPointDetail(firstPoint.id);
   }else{
    const detail=document.getElementById("knDetailPanel");
    if(detail)detail.innerHTML='<div class="kn-empty">该章节暂无知识点数据</div>';
   }
  }else{
   const firstPoint=findFirstPoint(graph);
   if(firstPoint){
    await loadKnPointDetail(firstPoint.id);
   }else{
    const detail=document.getElementById("knDetailPanel");
    if(detail)detail.innerHTML='<div class="kn-empty">该科目暂无知识点数据</div>';
   }
  }
 }catch(error){
  if(treeBody)treeBody.innerHTML=`<div class="kn-empty">加载失败：${escapeHtml(error.message||"")}</div>`;
 }
}

function findFirstPoint(graph){
 for(const ch of (graph.chapters||[])){
  if(ch.children&&ch.children.length)return ch.children[0];
 }
 return null;
}

/* 渲染左侧知识点目录树（带掌握度色点） */
function renderKnTreePanel(body,graph,opts={}){
 const subject=graph.subject;
 const targetChapterId=opts.targetChapterId?String(opts.targetChapterId):null;
 const targetPointId=opts.targetPointId?String(opts.targetPointId):null;
 body.innerHTML=`
  <div class="kn-tree-subject" data-kn-tree-subject="${subject.id}">
   <i class="kn-subject-dot" style="background:${statusPalette(subject.status)}"></i>
   <b>${escapeHtml(subject.name)}</b>
   <span>${subject.mastery_percent||0}%</span>
  </div>
  <div class="kn-tree-chapters">
   ${(graph.chapters||[]).map(ch=>{
    const isTargetChapter=targetChapterId!==null&&String(ch.id)===targetChapterId;
    return `
    <div class="kn-tree-chapter${isTargetChapter?" active":""}" data-kn-tree-chapter="${ch.id}">
     <div class="kn-tree-chapter-head" data-kn-tree-chapter-head="${ch.id}">
       <i class="kn-chapter-dot" style="background:${ch.style?.color||statusPalette(ch.status)}"></i>
       <b>${escapeHtml(ch.name)}</b>
       <span class="kn-tree-chapter-pct">${ch.mastery_percent||0}%</span>
       <em class="kn-chapter-toggle">▾</em>
     </div>
     <div class="kn-tree-points" ${isTargetChapter?"":"hidden"}>
       ${(ch.children||[]).map(pt=>{
        const isTargetPoint=targetPointId!==null&&String(pt.id)===targetPointId;
        return `
        <button class="kn-tree-point${isTargetPoint?" active":""}" data-kn-tree-point="${pt.id}" data-kn-point-name="${escapeHtml(pt.name)}" data-kn-point-chapter="${escapeHtml(ch.name)}">
         <i class="kn-point-dot" style="background:${pt.style?.color||statusPalette(pt.status)}"></i>
         <span>${escapeHtml(pt.name)}</span>
         <small class="kn-point-status">${escapeHtml(pt.status_label||statusLabel(pt.status))}</small>
        </button>`;
       }).join("")}
     </div>
    </div>`;
   }).join("")}
  </div>
 `;
 // 三级知识点点击:高亮 + 加载详情
 body.querySelectorAll("[data-kn-tree-point]").forEach(btn=>{
  btn.onclick=()=>{
   body.querySelectorAll("[data-kn-tree-point]").forEach(b=>b.classList.remove("active"));
   btn.classList.add("active");
   loadKnPointDetail(Number(btn.dataset.knTreePoint));
   closeKnMobileTreeAfterPick();
  };
 });
 // 二级章节头部点击:展开/折叠 + 高亮 + 加载第一节
 body.querySelectorAll("[data-kn-tree-chapter-head]").forEach(head=>{
  head.onclick=()=>{
   const chapterEl=head.parentElement;
   const pointsEl=chapterEl.querySelector(".kn-tree-points");
   const isExpanded=!pointsEl.hasAttribute("hidden");
   // 切换展开
   pointsEl.toggleAttribute("hidden");
   head.classList.toggle("collapsed",isExpanded);
   // 切换高亮
   body.querySelectorAll(".kn-tree-chapter").forEach(c=>c.classList.remove("active"));
   chapterEl.classList.add("active");
   // 加载本章节第一个知识点
   if(!isExpanded){
    const firstPoint=pointsEl.querySelector("[data-kn-tree-point]");
    if(firstPoint){
     body.querySelectorAll("[data-kn-tree-point]").forEach(b=>b.classList.remove("active"));
     firstPoint.classList.add("active");
     loadKnPointDetail(Number(firstPoint.dataset.knTreePoint));
     closeKnMobileTreeAfterPick();
    }
   }
  };
 });
 // 目标点滚到可视区
 if(targetPointId){
  const el=body.querySelector(`[data-kn-tree-point="${targetPointId}"]`);
  if(el){
   el.scrollIntoView({behavior:"smooth",block:"nearest"});
  }
 }else if(targetChapterId){
  const el=body.querySelector(`[data-kn-tree-chapter="${targetChapterId}"]`);
  if(el){
   el.scrollIntoView({behavior:"smooth",block:"nearest"});
  }
 }
 // 图例
 const legend=document.getElementById("knTreeLegend");
 if(legend){
  legend.innerHTML=["mastered","unfamiliar","unknown","weak","unlearned"].map(k=>
   `<span><i style="background:${statusPalette(k)}"></i>${statusLabel(k)}</span>`
  ).join("");
 }
}

async function loadDefaultSubjectDetail(subjectId,cachedSubjects){
 window.knSubjectCardsCache=cachedSubjects||window.knSubjectCardsCache||null;
 await switchKnSubject(subjectId);
}

async function renderKnGraphTab(body){
 body.innerHTML='<div class="kn-loading">正在加载 408 知识目录…</div>';
 try{
  const overview=await apiRequest("/api/knowledge/overview");
  const subjects=overview.subjects||[];
  if(!subjects.length){body.innerHTML='<div class="kn-empty">暂无科目数据</div>';return}
  const graphs=await Promise.all(subjects.map(async s=>{
   try{return await apiRequest(`/api/knowledge/subject/${s.subject_id}/graph`)}catch(e){return null}
  }));
  const totalKp=subjects.reduce((a,s)=>a+(s.knowledge_count||0),0);
  const masteredCount=subjects.reduce((a,s)=>a+(s.mastered_count||0),0);
  body.innerHTML=`
   <div class="kn-overview-banner">
     <div class="kn-overview-item"><span class="kn-overview-num">${subjects.length}</span><small>个科目</small></div>
     <div class="kn-overview-item"><span class="kn-overview-num">${totalKp}</span><small>个知识点</small></div>
     <div class="kn-overview-item"><span class="kn-overview-num">${masteredCount}</span><small>已掌握</small></div>
     <div class="kn-overview-item"><span class="kn-overview-num">${totalKp-masteredCount}</span><small>待学习</small></div>
   </div>
   <div class="kn-subject-grid">${subjects.map((s,idx)=>{const g=graphs[idx];const chapters=(g?.chapters)||[];return`
    <div class="kn-subject-card" data-kn-subject-id="${s.subject_id}" style="--subject-color:${s.style?.color||statusPalette(s.status)}">
      <div class="kn-subject-card-head">
        <i class="kn-subject-dot"></i>
        <div class="kn-subject-card-title">
          <b>${escapeHtml(s.subject_name)}</b>
          <span>${chapters.length} 章节 · ${s.knowledge_count||0} 知识点</span>
        </div>
      </div>
      <div class="kn-subject-card-meta">
        <div class="kn-mastery-row">
          <small>掌握度</small>
          <b>${s.mastery_percent||0}%</b>
        </div>
        <div class="kn-mastery-bar"><div class="kn-mastery-bar-fill" style="width:${s.mastery_percent||0}%"></div></div>
      </div>
      <div class="kn-subject-card-chapters">
        ${chapters.slice(0,3).map(ch=>`<span class="kn-subject-chapter-tag" title="${escapeHtml(ch.name)}"><i style="background:${ch.style?.color||statusPalette(ch.status)}"></i>${escapeHtml(ch.name)}</span>`).join("")}
        ${chapters.length>3?`<span class="kn-subject-chapter-tag more">+${chapters.length-3} 更多</span>`:""}
      </div>
      <div class="kn-subject-card-actions">
        <button class="kn-btn-open" data-kn-open-subject="${s.subject_id}">查看章节</button>
        <button class="kn-btn-graph" data-kn-open-graph="${s.subject_id}">知识图谱</button>
      </div>
    </div>`}).join("")}
   </div>`;
  body.querySelectorAll("[data-kn-open-subject]").forEach(btn=>{
   btn.onclick=()=>openSubjectChapters(btn.dataset.knOpenSubject);
  });
  body.querySelectorAll("[data-kn-open-graph]").forEach(btn=>{
   btn.onclick=()=>openSubjectGraph(btn.dataset.knOpenGraph);
  });
 }catch(e){
  body.innerHTML=`<div class="kn-empty">加载失败：${escapeHtml(e.message||"")}，请刷新重试</div>`;
 }
}

async function openSubjectChapters(subjectId){
 const body=document.getElementById("knPageBody");
 if(!body)return;
 body.innerHTML='<div class="kn-loading">加载章节中…</div>';
 try{
  const graph=await apiRequest(`/api/knowledge/subject/${subjectId}/graph`);
  const subjectName=graph.subject_name||graph.subject||"";
  const subjectColor=graph.style?.color||"#5b8def";
  const chapters=graph.chapters||[];
  if(!chapters.length){body.innerHTML='<div class="kn-empty">暂无章节数据</div>';return}
  body.innerHTML=`
   <div class="kn-back-bar">
     <button class="kn-back-btn" data-kn-back-graph>← 返回知识图谱</button>
     <span class="kn-back-title" style="color:${subjectColor}">${escapeHtml(subjectName)}</span>
   </div>
   <div class="kn-chapter-list">${chapters.map(ch=>`
    <div class="kn-chapter-row" data-kn-load-chapter="${ch.id}" data-kn-practice-subject="${escapeHtml(subjectName)}" data-kn-practice-point="${escapeHtml(ch.name)}">
      <div class="kn-chapter-row-head">
        <i class="kn-chapter-dot" style="background:${ch.style?.color||statusPalette(ch.status)}"></i>
        <div class="kn-chapter-row-info">
          <b>${escapeHtml(ch.name)}</b>
          <span>${ch.knowledge_count||0} 个三级知识点 · 掌握度 ${ch.mastery_percent||0}% · ${escapeHtml(ch.status_label||statusLabel(ch.status))}</span>
        </div>
        <div class="kn-chapter-row-bar"><div class="kn-bar-fill" style="width:${ch.mastery_percent||0}%;background:${ch.style?.color||statusPalette(ch.status)}"></div></div>
        <div class="kn-chapter-row-actions">
          <button class="kn-btn-start" data-kd-start-practice-chapter="${ch.id}" data-kd-practice-subject="${escapeHtml(subjectName)}" data-kd-practice-point="${escapeHtml(ch.name)}">开始训练</button>
          <span class="kn-arrow">→</span>
        </div>
      </div>
      ${(ch.children&&ch.children.length)?`<div class="kn-chapter-row-points">${ch.children.map(pt=>`<button class="kn-point-chip" data-kn-load-point="${pt.id}" data-kn-practice-subject="${escapeHtml(subjectName)}" data-kn-practice-point="${escapeHtml(pt.name)}" title="${escapeHtml(pt.status_label||statusLabel(pt.status))}"><i style="background:${pt.style?.color||statusPalette(pt.status)}"></i><span>${escapeHtml(pt.name)}</span></button>`).join("")}</div>`:""}
    </div>`).join("")}
   </div>`;
  body.querySelector("[data-kn-back-graph]").onclick=()=>renderKnGraphTab(body);
  body.querySelectorAll("[data-kn-load-chapter]").forEach(div=>{
   const chapterId=div.dataset.knLoadChapter;
   const openChapter=()=>{
    const ch=chapters.find(c=>String(c.id)===String(chapterId));
    const firstPoint=ch?.children?.[0];
    if(firstPoint){
     loadKnPointDetail(firstPoint.id);
    }else{
     toast("该章节暂无知识点","info");
    }
   };
   div.querySelector(".kn-chapter-row-head")?.addEventListener("click",e=>{
    if(e.target.closest(".kn-btn-start"))return;
    openChapter();
   });
   div.querySelector(".kn-arrow")?.addEventListener("click",e=>{e.stopPropagation();openChapter()});
  });
  body.querySelectorAll("[data-kn-load-point]").forEach(btn=>{btn.onclick=e=>{e.stopPropagation();loadKnPointDetail(btn.dataset.knLoadPoint)}});
  body.querySelectorAll("[data-kd-start-practice-chapter]").forEach(btn=>{btn.onclick=e=>{e.stopPropagation();autoStartPractice(btn)}});
 }catch(e){
  body.innerHTML=`<div class="kn-empty">加载失败：${escapeHtml(e.message||"")}</div>`;
 }
}

function openSubjectGraph(subjectId){
 toast("即将打开"+(subjectId||"")+"的完整图谱视图");
}

async function renderKnDetailTab(body){
 body.innerHTML='<div class="kn-loading">正在加载所有知识点…</div>';
 try{
  const overview=await apiRequest("/api/knowledge/overview");
  const subjects=overview.subjects||[];
  const graphs=await Promise.all(subjects.map(async s=>{
   try{return {subject:s,graph:await apiRequest(`/api/knowledge/subject/${s.subject_id}/graph`)};}catch(e){return {subject:s,graph:null}}
  }));
  let allPoints=[];
  graphs.forEach(({subject,graph})=>{
   if(!graph)return;
   (graph.chapters||[]).forEach(ch=>{
    (ch.children||[]).forEach(pt=>{
     allPoints.push({
      id:pt.id,
      name:pt.name,
      subject:subject.subject_name,
      subject_id:subject.subject_id,
      chapter:ch.name,
      chapter_id:ch.id,
      status:pt.status,
      status_label:pt.status_label||statusLabel(pt.status),
      style:pt.style||{color:statusPalette(pt.status)},
     });
    });
   });
  });
  body.innerHTML=`
   <div class="kn-detail-toolbar">
     <input class="kn-detail-search" id="knDetailSearch" placeholder="🔍 搜索知识点名称…">
     <div class="kn-detail-filter" id="knDetailFilter">
       <button class="kn-filter-btn active" data-filter-subject="all">全部</button>
       ${subjects.map(s=>`<button class="kn-filter-btn" data-filter-subject="${escapeHtml(s.subject_name)}">${escapeHtml(s.subject_name)}</button>`).join("")}
     </div>
   </div>
   <div class="kn-detail-meta" id="knDetailMeta">共 ${allPoints.length} 个知识点</div>
   <div class="kn-detail-grid" id="knDetailGrid">${allPoints.map(pt=>`
    <div class="kn-point-card" data-kn-point-id="${pt.id}" data-kn-point-name="${escapeHtml(pt.name)}" data-kn-point-subject="${escapeHtml(pt.subject)}" data-kn-point-chapter="${escapeHtml(pt.chapter)}">
      <div class="kn-point-card-head">
        <span class="kn-point-card-status" style="background:${pt.style.color||statusPalette(pt.status)}">${escapeHtml(pt.status_label)}</span>
      </div>
      <b class="kn-point-card-name">${escapeHtml(pt.name)}</b>
      <div class="kn-point-card-meta">
        <span class="kn-point-card-subject" style="--subject-color:${pt.style.color||statusPalette(pt.status)}">${escapeHtml(pt.subject)}</span>
        <span class="kn-point-card-chapter">${escapeHtml(pt.chapter)}</span>
      </div>
      <button class="kn-point-card-btn">查看详情 →</button>
    </div>`).join("")}
   </div>`;
  const searchInput=document.getElementById("knDetailSearch");
  const filterBtns=document.querySelectorAll("#knDetailFilter .kn-filter-btn");
  const applyFilter=()=>{
   const kw=(searchInput.value||"").trim().toLowerCase();
   const activeBtn=document.querySelector("#knDetailFilter .kn-filter-btn.active");
   const subject=activeBtn?activeBtn.dataset.filterSubject:"all";
   let visible=0;
   document.querySelectorAll("#knDetailGrid .kn-point-card").forEach(card=>{
    const name=(card.dataset.knPointName||"").toLowerCase();
    const cardSubj=card.dataset.knPointSubject||"";
    const matchKw=!kw||name.includes(kw);
    const matchSubj=subject==="all"||cardSubj===subject;
    const show=matchKw&&matchSubj;
    card.style.display=show?"":"none";
    if(show)visible++;
   });
   document.getElementById("knDetailMeta").textContent=`显示 ${visible} / ${allPoints.length} 个知识点`;
  };
  searchInput.oninput=applyFilter;
  filterBtns.forEach(btn=>{
   btn.onclick=()=>{filterBtns.forEach(b=>b.classList.remove("active"));btn.classList.add("active");applyFilter();};
  });
  document.querySelectorAll(".kn-point-card").forEach(card=>{
   card.onclick=()=>{
    const id=card.dataset.knPointId;
    const name=card.dataset.knPointName;
    const subject=card.dataset.knPointSubject;
    const chapter=card.dataset.knPointChapter;
    window.currentGraphPointName=name;
    window.currentGraphPointSubject=subject;
    window.currentGraphChapterName=chapter;
    window.currentGraphChapterSubject=subject;
    loadKnPointDetail(id);
   };
  });
 }catch(e){
  body.innerHTML=`<div class="kn-empty">加载失败：${escapeHtml(e.message||"")}</div>`;
 }
}

async function renderKnVideoTab(body){
 body.innerHTML='<div class="kn-loading">正在加载视频库…</div>';
 try{
  const overview=await apiRequest("/api/knowledge/overview");
  const subjects=overview.subjects||[];
  const videoLists=await Promise.all(subjects.map(async s=>{
   try{
    const data=await apiRequest(`/api/videos/recommend?subject=${encodeURIComponent(s.subject_name)}&limit=8`);
    return {subject:s,items:data.items||[]};
   }catch(e){return {subject:s,items:[]}}
  }));
  const totalVideos=videoLists.reduce((a,v)=>a+v.items.length,0);
  body.innerHTML=`
   <div class="kn-video-meta">共 ${totalVideos} 个视频，按科目分类</div>
   <div class="kn-video-by-subject">${videoLists.map(({subject,items})=>`
    <div class="kn-video-section">
      <div class="kn-video-section-head">
        <h4>${escapeHtml(subject.subject_name)}</h4>
        <span>${items.length} 个视频</span>
      </div>
      <div class="kn-video-grid">${items.length?items.map(v=>`
       <a class="kn-video-card" href="${escapeHtml(v.url||"#")}" target="_blank" rel="noopener">
        <div class="kn-video-cover">
          ${v.cover_url?`<img src="${escapeHtml(v.cover_url)}" alt="${escapeHtml(v.title||"")}" loading="lazy" referrerpolicy="no-referrer" onerror="this.style.display='none'">`:""}
          <span class="kn-video-play">▶</span>
          ${v.duration?`<span class="kn-video-duration">${escapeHtml(v.duration)}</span>`:""}
        </div>
        <div class="kn-video-info">
          <b>${escapeHtml(v.title||"")}</b>
          <small>${escapeHtml(v.author||"")}</small>
        </div>
       </a>`).join(""):'<div class="kn-empty">暂无视频</div>'}
      </div>
    </div>`).join("")}
   </div>`;
 }catch(e){
  body.innerHTML=`<div class="kn-empty">加载失败：${escapeHtml(e.message||"")}</div>`;
 }
}

async function autoStartPractice(btn){
 const subject=btn.dataset.kdPracticeSubject||"";
 const chapter=btn.dataset.kdPracticePoint||"";
 const pointId=btn.dataset.knLoadPoint||"";
 const progressId="kn-practice-"+Date.now();
 const prefix="正在为「"+(pointId?chapter:chapter||subject||"章节")+"」";
 const prog=startGenerationProgress(progressId,prefix);
 try{
  const payload={mode:pointId?"知识点专项":"章节训练",scope:pointId?"point":"chapter",subject:subject,knowledge_point:chapter,chapter:pointId?"":chapter,chapter_id:pointId?null:Number(btn.dataset.kdStartPracticeChapter||btn.dataset.knLoadChapter||0)||null,count:3,difficulty:"自适应",question_type:"混合"};
  const data=await apiRequest("/api/questions/generate",{method:"POST",body:JSON.stringify(payload)});
  prog.stop();
  if(data.all_refused&&(!data.questions||!data.questions.length)){errorProgressBar(progressId,"知识库暂无该知识点");toast("当前网络问题，请稍后重试或换一个知识点","error");return}
  if(!data.questions||!Array.isArray(data.questions)||!data.questions.length){errorProgressBar(progressId,"暂无题目");toast("Agent 暂未生成题目，请稍后重试","error");return}
  showPage("question");
  hasGeneratedQuestionBatch=true;
  activeQuestions=data.questions.map((q,i)=>normalizeQuestion({...q,source:pointId?"知识点专项练习":"章节训练"},i));
  currentQuestionIndex=0;
  renderQuestion();
  const tag=data.llm_used?"（AI 智能出题）":(data.llm_error?"（使用保底题库："+data.llm_error+"）":"（使用本地题库）");
  completeProgressBar(progressId,"已生成 "+data.questions.length+" 道题");
  toast("已生成 "+data.questions.length+" 道练习题 "+tag);
 }catch(e){prog.stop();errorProgressBar(progressId,"生成失败");toast("生成题目失败: "+e.message,"error")}
}

async function loadKnPointDetail(pointId){
 const body=document.getElementById("knDetailPanel");
 if(!body)return;
 window.knDetailActive=true;
 body.innerHTML='<div class="kn-loading">加载知识点详情中…</div>';
 try{
  /* 第一阶段：并发请求 3 个核心数据（视频推荐单独异步加载） */
  const [detail,related,notes]=await Promise.all([
   apiRequest(`/api/knowledge/point/${pointId}`),
   apiRequest(`/api/knowledge/point/${pointId}/related`),
   apiRequest(`/api/notes?knowledge_point_id=${pointId}`)
  ]);
  if(!detail?.point){body.innerHTML='<div class="kn-empty">知识点不存在</div>';return}
  const graph=await apiRequest(`/api/knowledge/subject/${detail.point.subject_id}/graph`);
  activeSubjectGraph=graph;
  const point=detail.point;
  window.currentKnowledgePointId=point.id;
  window.currentGraphPointName=point.name||"";
  window.currentGraphPointSubject=point.subject_name||"";
  window.currentKnowledgeNotes=notes.items||[];
  // 高亮左侧目录树中当前知识点,同时展开并高亮父章节
  document.querySelectorAll("[data-kn-tree-point]").forEach(b=>{
   b.classList.toggle("active",Number(b.dataset.knTreePoint)===pointId);
  });
  // 高亮 + 展开该知识点所属的父章节
  const targetPointBtn=document.querySelector(`[data-kn-tree-point="${pointId}"]`);
  if(targetPointBtn){
   const parentChapter=targetPointBtn.closest(".kn-tree-chapter");
   if(parentChapter){
    const pointsEl=parentChapter.querySelector(".kn-tree-points");
    if(pointsEl)pointsEl.removeAttribute("hidden");
    const head=parentChapter.querySelector("[data-kn-tree-chapter-head]");
    if(head)head.classList.remove("collapsed");
    document.querySelectorAll(".kn-tree-chapter").forEach(c=>{
     c.classList.toggle("active",c===parentChapter);
    });
   }
  }
  // 如果当前科目与知识点所属科目不一致，自动切换到该科目
  if(kpNavActiveSubjectId!==point.subject_id){
   const subjectExists=(window.knSubjectCardsCache||[]).some(s=>s.subject_id===point.subject_id);
   if(subjectExists){
    kpNavActiveSubjectId=point.subject_id;
    document.querySelectorAll("#knSubjectBarList [data-kn-subject-id]").forEach(btn=>{
     btn.classList.toggle("active",Number(btn.dataset.knSubjectId)===point.subject_id);
    });
    const treeBody=document.getElementById("knTreePanelBody");
    if(treeBody){
     renderKnTreePanel(treeBody,graph);
     document.querySelectorAll("[data-kn-tree-point]").forEach(b=>{
      b.classList.toggle("active",Number(b.dataset.knTreePoint)===pointId);
     });
    }
   }
  }
  const noteItems=notes.items||[];
  const relatedItems=related.items||[];

  /* 立即渲染页面（视频部分显示 loading 状态）— 仅更新 #knDetailPanel */
  body.innerHTML=`<div class="kd-canvas-wrap">${knowledgePointNavDetailHTML(point,graph,relatedItems,[],[],[],noteItems,true)}</div>`;
  bindKnowledgeDetailInteractions();

  /* 第二阶段：异步加载视频推荐（不阻塞主页面） */
  loadPointVideosAsync(pointId);
 }catch(e){body.innerHTML=`<div class="kn-empty">加载失败：${escapeHtml(e.message||"")}</div>`}
}

async function loadPointVideosAsync(pointId){
 const container=document.getElementById("kdTabVideos");
 if(!container)return;
 try{
  const videos=await apiRequest(`/api/videos/recommend?knowledge_point_id=${pointId}&scene=knowledge&limit=3`);
  const items=videos.items||[];
  window.currentKnowledgeVideos=items;
  const newContainer=document.getElementById("kdTabVideos");
  if(!newContainer)return;
  if(items.length===0){
   newContainer.innerHTML="<p>暂无匹配视频资源</p>";
  }else{
   newContainer.innerHTML=items.map(videoCardHTML).join("");
  }
 }catch(e){
  console.error("视频推荐异步加载失败:",e);
  const newContainer=document.getElementById("kdTabVideos");
  if(newContainer){
   newContainer.innerHTML=`<p class="kd-video-error">视频推荐加载失败：${escapeHtml(e.message||"")} <button class="kd-video-retry" data-kd-video-retry="${pointId}">重试</button></p>`;
   newContainer.querySelector("[data-kd-video-retry]")?.addEventListener("click",()=>loadPointVideosAsync(pointId));
  }
 }
}

function knowledgePointNavDetailHTML(point,graph,related,videos,history,mistakes,notes,isVideoLoading=true){
 const safeArr=(v)=>Array.isArray(v)?v:[];
 const relatedSafe=safeArr(related);
 const notesSafe=safeArr(notes);
 const videosSafe=safeArr(videos);
 const videosContent=isVideoLoading
  ? `<div class="kd-video-loading" id="kdVideoLoading">
      <div class="kd-video-spinner"></div>
      <p>正在匹配王道官方 408 课程视频…</p>
      <small>仅展示与该知识点强相关的王道分 P，无关视频已过滤</small>
     </div>`
  : (videosSafe.map(videoCardHTML).join("")||"<p>暂无匹配视频资源</p>");
 return `<div class="kd-layout kd-point-nav-layout">
  <main class="kd-main kd-main-full">
   <div class="kd-breadcrumb"><button data-kg-back>返回知识目录</button><span>${escapeHtml(point.subject_name||"")} / ${escapeHtml(point.chapter_name||"")} / ${escapeHtml(point.name||"")}</span></div>
   <section class="kd-point-head">
    <div><span class="kd-badge">${escapeHtml(point.status_label||statusLabel(point.status))}</span><h2>${escapeHtml(point.name||"")}</h2><p>${escapeHtml(point.subject_name||"")} / ${escapeHtml(point.chapter_name||"")}</p></div>
    <div class="kd-head-actions"><button class="primary" data-open-note="${point.id}">添加笔记</button><button class="ghost" data-kd-start-practice="${point.id}" data-kd-practice-subject="${escapeHtml(point.subject_name||"")}" data-kd-practice-point="${escapeHtml(point.name||"")}">开始练习</button></div>
   </section>
   <section class="kd-section"><h3>知识点正文</h3>${knowledgeBodyHTML(point)}</section>
   <section class="kd-section"><h3>相关知识点</h3><div class="kd-related">${relatedSafe.map(item=>`<button data-kd-point="${item.id}"><b>${escapeHtml(item.name||"")}</b><span>${escapeHtml(item.status_label||statusLabel(item.status))}</span></button>`).join("")||"<p>暂无相关知识点</p>"}</div></section>
   <section class="kd-section kd-tabs-section">
    <div class="kd-tab-bar"><button class="kd-tab active" data-kd-tab="videos">学习资源</button><button class="kd-tab" data-kd-tab="notes">学习笔记</button></div>
    <div class="kd-tab-content" id="kdTabVideos">${videosContent}</div>
    <div class="kd-tab-content" id="kdTabNotes" style="display:none"><div class="kd-note-list" id="kdNoteList">${notesSafe.map(noteCardHTML).join("")||"<p>暂无笔记，点击右上角添加。</p>"}</div></div>
   </section>
  </main>
 </div>${noteModalHTML(point)}`;
}
function qaHTML(){
  return `<section class="page" id="qa">
    <div class="chat-layout">
      <button class="qa-mobile-history-toggle" id="qaHistoryToggle" type="button" aria-expanded="false" aria-controls="qaHistoryPanel">
        <span>历史记录</span>
        <b>展开</b>
      </button>
      <aside class="card conversation-list" id="qaHistoryPanel">
        <div class="head">
          <h3>历史会话</h3>
          <button class="soft qa-mobile-history-close" id="qaHistoryClose" type="button">收起</button>
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
      </div>
      <div class="launch-or">OR</div>
      <div class="launch-card">
        <span>✦</span>
        <div><b>智能推荐出题</b><small>根据薄弱点、错题和高频提问生成</small></div>
      </div>
    </div><div class="question-config"><span class="tag">当前出题条件</span><span class="config-chip" id="configMode">智能推荐</span><span class="config-chip" id="configSubject">操作系统</span><span class="config-chip" id="configPoint">页面置换算法</span><span class="config-chip" id="configDifficulty">中等</span><span class="config-chip" id="configType">选择题 · 3 道</span><button class="ghost" id="changeConfig">重新选择</button></div><div class="question-stage"><article class="card question-card"><button class="question-switch prev" id="prevQuestion" aria-label="上一题">‹</button><button class="question-switch next" id="nextQuestion" aria-label="下一题">›</button><div class="question-meta"><span id="questionMeta">2026 模拟 · 第 1 题 · 2 分</span><span id="questionQualityBadges"></span><span class="question-position"><b id="currentQuestionNo">1</b> / <span id="totalQuestionNo">3</span></span></div><div class="rec"><b id="recommendTitle">为什么推荐这道题？</b><small id="recommendReason">你之前在 LRU 缺页次数统计中多次遗漏页面更新，本题用于专项巩固。</small></div><h3 class="question-title" id="questionTitle">某系统为进程分配 3 个页框，页面访问序列为 1, 2, 3, 1, 4, 2, 5。采用 LRU 算法时，缺页次数为多少？</h3><div id="options">${["A. 4 次","B. 5 次","C. 6 次","D. 7 次"].map(x=>`<div class="option">${x}</div>`).join("")}</div><div class="easy-mistakes-box" id="easyMistakesBox" style="display:none"><b>⚠ 易错点</b><small id="easyMistakesText"></small></div><div class="tools"><button class="soft" data-drawer="hint">💡 分步提示</button><button class="soft" data-drawer="video">▶ 推荐视频</button><button class="soft" id="openFeedbackDrawer">⚐ 反馈题</button><button class="primary" id="submitAnswer">✓ 提交答案</button></div><div class="drawer" id="hint"><h4>提示 1 / 3</h4><p id="hintText">本题考查 LRU 页面置换算法。先画出 3 个页框，再逐项处理访问序列。</p><button class="ghost" id="nextHint">下一层提示</button></div><div class="drawer" id="video"><h4>相关公开视频</h4><div id="videoContent"></div></div><div class="drawer" id="answer"><h4>批改结果：回答错误</h4><p id="answerText">你的答案：B · 5 次。标准答案：C · 6 次。系统初步判断可能存在计算遗漏，请由用户确认真实错因。</p></div><div class="wrong-action" id="wrongAction"><b>这道题为什么答错？</b><p>请选择一个或多个最符合的原因。用户确认的错因将作为高可信证据写入长期学习记忆。</p><button class="primary" id="openCause">选择错因</button><div class="cause-detail" id="causeDetail"><div class="cause-options">${causes.map(x=>`<button data-cause="${x}">${x}</button>`).join("")}</div><div class="field"><label>补充说明（可选）</label><textarea id="causeNote" style="min-height:70px" placeholder="例如：我忘记在页面命中时更新最近访问顺序"></textarea></div><button class="primary" id="confirmCause">确认错因并记录到长期学习</button></div><div class="cause-summary" id="causeSummary"></div></div><div class="mastery"><span class="tag">本题掌握情况</span><button>掌握</button><button>不熟</button><button>不会</button></div></article></div>${questionDrawersHTML()}</section>`}
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
  </aside>
  <aside class="side-drawer right" id="feedbackDrawer">
    <div class="side-drawer-head">
      <div><h2>题目质量反馈</h2><p>反馈会写入后端；累计 3 次"答案有误"将自动下线该题</p></div>
      <button class="close-drawer" data-close-question>×</button>
    </div>
    <div class="select-block">
      <label>反馈类型</label>
      <div class="choice-list" data-choice-group="feedbackType">
        <button class="selected" data-value="wrong_answer"><b>答案有误</b><small>标准答案/解析有事实错误</small></button>
        <button data-value="off_topic"><b>偏题</b><small>题目与指定知识点不匹配</small></button>
        <button data-value="typo"><b>错别字</b><small>题干或选项有笔误</small></button>
        <button data-value="other"><b>其他</b><small>补充说明</small></button>
      </div>
    </div>
    <div class="select-block">
      <label>补充说明（可选）</label>
      <textarea id="feedbackContent" placeholder="如有具体描述可写在这里" style="width:100%;min-height:120px;border:1px solid var(--line);background:var(--panel2);color:var(--ink);padding:12px;border-radius:10px;outline:none;resize:vertical"></textarea>
    </div>
    <div class="select-block">
      <label>当前题目</label>
      <div class="rec" style="margin:0"><b id="feedbackQuestionTitle">—</b><small id="feedbackQuestionMeta">—</small></div>
    </div>
    <div class="drawer-footer">
      <button class="ghost" data-close-question>取消</button>
      <button class="primary" id="submitFeedback">提交反馈</button>
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
    <h2>OCR 导入</h2>
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
      <div class="field"><textarea id="ocrText" placeholder="OCR 识别结果会显示在这里,可手动修正"></textarea></div>
      <div class="ocr-line-confidence" id="ocrLineConfidence" style="display:none"></div>
      <div class="field"><label>你的答案<span class="ocr-guess-hint" id="ocrGuessHint"></span></label><input id="ocrUserAnswer" placeholder="填写你当时的作答,Agent 会自行推断标准答案"></div>
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
    if(tag) tag.textContent = stats.total ? "多加训练" : "暂无数据";
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
    // 错题状态变化 → 全局刷新(首页统计/知识图谱/报告)
    setTimeout(()=>refreshAfterAnswer("mastery").catch(console.error),400);
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
async function startPracticeForPoint(subject, point, referenceText, referenceAnswer){
  toast("正在为该知识点生成训练题…");
  showPage("question");
  const payload = {mode:"自由选择", subject, knowledge_point:point, difficulty:"中等", question_type:"选择题", count:3};
  if(referenceText)payload.reference_text=referenceText;
  if(referenceAnswer)payload.reference_answer=referenceAnswer;
  payload.source="ocr";
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
            <span class="weight-label">${x[0]}</span>
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
            <span class="weight-label">${x[0]}</span>
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
  // 重新上传时清掉旧的本地缩略图
  clearOcrPreview()
}
function renderOcrUploadMeta(data={}){
  const meta=document.getElementById("ocrUploadMeta")
  const tag=document.getElementById("ocrEngineTag")
  if(meta){
    const size=data.size?`${Math.max(1,Math.round(data.size/1024))} KB`:"等待后端返回"
    const stats=data.stats||{}
    const avg=stats.avg_score?` · 平均置信度 ${(stats.avg_score*100).toFixed(1)}%`:""
    const tms=stats.total_ms?` · 耗时 ${stats.total_ms}ms`:""
    const llmFlag=stats.llm_corrected?" · ✨ LLM 已纠错":""
    meta.innerHTML=`<b>${escapeHtml(String(data.filename||"图片已选择"))}</b>
      <small>${size} · ${escapeHtml(String(data.engine||"正在识别"))}${avg}${tms}${llmFlag}${data.warning?` · ${escapeHtml(String(data.warning))}`:""}</small>`
  }
  if(tag){
    tag.textContent=data.engine||"识别中"
  }
}

/* 上传后即时把本地图片缩略图显示到 #ocrDrop 区域（释放旧 ObjectURL 避免内存泄漏） */
function previewOcrImage(file){
  if(!file)return
  const img=document.getElementById("ocrPreviewImage")
  const placeholder=document.getElementById("ocrDropPlaceholder")
  const drop=document.getElementById("ocrDrop")
  if(!img||!drop)return
  // 释放上一张的 ObjectURL
  if(ocrPreviewUrl){
    try{URL.revokeObjectURL(ocrPreviewUrl)}catch(e){}
    ocrPreviewUrl=null
  }
  try{
    ocrPreviewUrl=URL.createObjectURL(file)
    img.src=ocrPreviewUrl
    img.classList.add("show")
    drop.classList.add("has-image","ocr-uploading")
    if(placeholder)placeholder.classList.add("hide")
  }catch(e){
    console.warn("创建本地预览失败",e)
  }
}

/* 停止上传中的扫描线动画（图片已识别完成 / 失败时调用） */
function stopOcrUploading(){
  const drop=document.getElementById("ocrDrop")
  if(drop)drop.classList.remove("ocr-uploading")
}

/* 清除本地预览（用于 reset / 重新上传） */
function clearOcrPreview(){
  if(ocrPreviewUrl){
    try{URL.revokeObjectURL(ocrPreviewUrl)}catch(e){}
    ocrPreviewUrl=null
  }
  const img=document.getElementById("ocrPreviewImage")
  const placeholder=document.getElementById("ocrDropPlaceholder")
  const drop=document.getElementById("ocrDrop")
  if(img){img.removeAttribute("src");img.classList.remove("show")}
  if(drop){drop.classList.remove("has-image","ocr-uploading")}
  if(placeholder)placeholder.classList.remove("hide")
}

/* 在 OCR 文本框下方追加「行级置信度」可视化 */
function renderOcrLineConfidence(lines){
  const box=document.getElementById("ocrLineConfidence")
  if(!box)return
  if(!Array.isArray(lines)||!lines.length){box.style.display="none";return}
  box.style.display="block"
  box.innerHTML=`<div class="ocr-line-conf-head">📊 行级置信度（<b>${lines.length}</b> 行 · 红色需校对）</div>`+
    lines.map(l=>{
      const pct=Math.round((l.score||0)*100)
      const cls=(l.score||0)<0.85?"low":"ok"
      return `<div class="ocr-line-row ${cls}">
        <span class="ocr-line-bar" style="width:${pct}%"></span>
        <span class="ocr-line-pct">${pct}%</span>
        <span class="ocr-line-text">${escapeHtml(String(l.text||""))}</span>
      </div>`
    }).join("")
}

/* 上传后调用 /api/ocr/guess,反推用户答案并预填到「你的答案」 */
async function ocrGuessUserAnswer(){
  const text=(document.getElementById("ocrText")?.value||"").trim()
  if(!text)return
  const subject=document.getElementById("configSubject")?.textContent||"操作系统"
  const point=document.getElementById("configPoint")?.textContent||"页面置换算法"
  const userInput=document.getElementById("ocrUserAnswer")
  if(!userInput||userInput.value.trim())return  // 用户已填，不覆盖
  try{
    const data=await apiRequest("/api/ocr/guess",{method:"POST",body:JSON.stringify({text,subject,knowledge_point:point})})
    if(data&&data.guessed_user_answer){
      userInput.value=data.guessed_user_answer
      userInput.placeholder=`AI 已预填：${data.guessed_user_answer}（可直接修改）`
      const conf=data.confidence?Math.round(data.confidence*100):0
      toast(`AI 推测你的答案（置信度 ${conf}%），可手动修改`,"info")
    }
  }catch(e){console.warn("反推用户答案失败",e)}
}

async function ocrUploadFile(file){
 if(!file)return;
 if(!file.type.startsWith("image/"))return toast("请选择图片文件","error");
 /* 先清掉上一次的本地预览和分析结果,再设置新图的 src,避免顺序反了导致 src 被立刻清空 */
 resetOcrAnalysis();
 ocrUploadState={filename:file.name,size:file.size};
 renderOcrUploadMeta({filename:file.name,size:file.size,engine:"上传中"});
 previewOcrImage(file);
 setOcrStep(1);
 const status=document.getElementById("ocrStatus");
 if(status)status.textContent="正在上传并识别";
 toast("正在上传图片…");
 showProgressBar("上传并识别图片...","ocr-upload");
 try{
  updateProgressBar("ocr-upload",30,"上传图片中...");
  const form=new FormData();form.append("file",file);
  const data=await apiRequest("/api/ocr/upload",{method:"POST",body:form});
  updateProgressBar("ocr-upload",80,"OCR 识别中...");
  ocrUploadState=data;
  document.getElementById("ocrText").value=data.recognized_text||"";
  document.getElementById("ocrStatus").textContent=(data.ocr_available===false?"进入人工校对":"识别完成")+" · "+(data.engine||"后端 OCR");
  renderOcrUploadMeta(data);
  /* 渲染行级置信度 + 自动反推用户答案 */
  renderOcrLineConfidence(data.lines||[])
  if(data.ocr_available!==false&&data.recognized_text){
    setOcrStep(2);
    /* 异步反推用户答案,不阻塞主流程 */
    ocrGuessUserAnswer()
  }else{
    setOcrStep(2);
  }
  /* 上传+识别完成,关闭绿色扫描线 */
  stopOcrUploading();
  completeProgressBar("ocr-upload","图片上传并识别完成");
  toast(data.warning||"图片上传并识别完成",data.ocr_available===false?"info":"success");
 }catch(error){console.error(error);setOcrStep(0);if(status)status.textContent="上传失败";stopOcrUploading();errorProgressBar("ocr-upload",error.message||"上传失败");toast(error.message||"上传失败","error")}
}
function bindAll(){
 updateSidebarStreak();
 enhanceKnowledgeGraph();
 document.querySelectorAll(".nav button").forEach(b=>b.onclick=()=>{showPage(b.dataset.page);closeMobileNav();});
 bindMobileNav();
 document.querySelectorAll(".subject-tabs button").forEach(b=>b.onclick=()=>{if(b.id==="masteryLayer"||b.id==="structureLayer")return;b.parentElement.querySelectorAll("button").forEach(x=>x.classList.remove("active"));b.classList.add("active");toast("已切换 Mock 数据视图")});
 const masteryLayer=document.getElementById("masteryLayer"),structureLayer=document.getElementById("structureLayer");
 masteryLayer.onclick=()=>{masteryLayer.classList.add("active");structureLayer.classList.remove("active");document.getElementById("layerNote").textContent="已叠加个人掌握状态：红色为薄弱点，绿色为已掌握";document.querySelectorAll(".graph-point").forEach((p,i)=>{p.classList.remove("weak-state","master-state");if([2,7,11,13].includes(i))p.classList.add("weak-state");else if([0,5,15].includes(i))p.classList.add("master-state")});toast("全局知识结构保持不变，仅叠加个人状态图层")};
 structureLayer.onclick=()=>{structureLayer.classList.add("active");masteryLayer.classList.remove("active");document.getElementById("layerNote").textContent="当前展示完整知识结构";document.querySelectorAll(".graph-point").forEach(p=>p.classList.remove("weak-state","master-state"));toast("已切回纯知识结构图")};
 document.querySelectorAll("[data-graph-filter]").forEach(button=>button.onclick=()=>{document.querySelectorAll("[data-graph-filter]").forEach(x=>x.classList.toggle("active",x===button));const filter=button.dataset.graphFilter,canvas=document.getElementById("knowledgeGraphCanvas");canvas.classList.toggle("single-view",filter!=="all");document.querySelectorAll("[data-graph-group]").forEach(group=>group.classList.toggle("hidden",filter!=="all"&&group.dataset.graphGroup!==filter));document.getElementById("layerNote").textContent=filter==="all"?"当前展示四科完整知识结构":`当前聚焦：${filter}`;toast(filter==="all"?"已切换到全局知识图谱":`已切换到${filter}图谱`)});
 document.querySelectorAll("#knowledgeGraphCanvas .kg-node").forEach(node=>{
  node.addEventListener("click",()=>{
   const name=node.querySelector("span")?.textContent||"";
   const subject=node.dataset.subject||"";
   if(name&&subject){
    navigateKnowledgeFromGraph(name,subject);
   }
  });
 });
 document.querySelectorAll("#knowledgeGraphCanvas .kg-child").forEach(child=>{
  child.addEventListener("click",e=>{
   e.stopPropagation();
   const name=child.textContent||"";
   const node=child.closest(".kg-node");
   const subject=node?.dataset.subject||"";
   if(name&&subject){
    navigateKnowledgeFromGraph(name,subject);
   }
  });
 });
 bindQuestionOptions();
 document.querySelectorAll("[data-drawer]").forEach(b=>b.onclick=()=>document.getElementById(b.dataset.drawer).classList.toggle("show"));
 document.querySelectorAll(".mastery button").forEach(b=>b.onclick=()=>{b.parentElement.querySelectorAll("button").forEach(x=>x.classList.remove("chosen"));b.classList.add("chosen");const status=b.textContent.trim();if(status==="不熟")toast("已加入“不熟题本”，并记录到长期学习状态");else if(status==="不会")toast("已加入“不会题本”，薄弱权重 +2");else toast("已标记掌握，将从不熟/不会题本移出")});
 let hint=1;document.getElementById("nextHint").onclick=()=>{hint=Math.min(3,hint+1);document.querySelector("#hint h4").textContent=`提示 ${hint} / 3`;document.getElementById("hintText").textContent=hint===2?"按序列逐项访问：命中时更新最近访问顺序；缺页时淘汰最久未访问页面。":"关键提醒：初始装入页面也算缺页。你之前曾遗漏这一点。"};
 document.getElementById("submitAnswer").onclick=()=>{const selected=document.querySelector(".option.selected");if(!selected)return toast("请先选择一个答案");document.getElementById("answer").classList.add("show");document.getElementById("wrongAction").classList.add("show");toast("回答错误，请选择真实错因")};
 document.getElementById("prevQuestion").onclick=()=>switchQuestion(-1);
 document.getElementById("nextQuestion").onclick=()=>switchQuestion(1);
 const lc=document.querySelectorAll(".launch-card");
 if(lc[0])lc[0].onclick=()=>openQuestionDrawer("manualDrawer");
 if(lc[1])lc[1].onclick=()=>openQuestionDrawer("smartDrawer");
 document.getElementById("changeConfig").onclick=()=>openQuestionDrawer("manualDrawer");
 document.querySelectorAll("[data-close-question]").forEach(b=>b.onclick=closeQuestionDrawers);
 document.getElementById("questionDrawerMask").onclick=closeQuestionDrawers;
 document.querySelectorAll("[data-choice-group]").forEach(group=>group.querySelectorAll("button").forEach(b=>b.onclick=()=>{group.querySelectorAll("button").forEach(x=>x.classList.remove("selected"));b.classList.add("selected")}));
 document.getElementById("generateManual").onclick=generateManualQuestions;
 document.getElementById("generateSmart").onclick=generateSmartQuestions;
 document.getElementById("openCause").onclick=()=>document.getElementById("causeDetail").classList.toggle("show");
 document.querySelectorAll("[data-cause]").forEach(b=>b.onclick=()=>b.classList.toggle("chosen"));
 document.getElementById("confirmCause").onclick=()=>{const selected=[...document.querySelectorAll("[data-cause].chosen")].map(x=>x.dataset.cause);if(!selected.length)return toast("请至少选择一种错因");const note=document.getElementById("causeNote").value.trim();document.getElementById("causeSummary").classList.add("show");document.getElementById("causeSummary").innerHTML=`<b>已形成结构化长期记忆证据</b><br>错因：${selected.join(" + ")}${note?`<br>用户说明：${escapeHtml(note)}`:""}<br>写入建议：mistake.error_types；user_memory.error_pattern；evidence_source=user_confirmed；可信度=high；对应知识点权重 +1。`;toast("错因已确认，将作为高可信长期记忆记录")};
 bindQaHistoryToggle();
 setQaHistoryOpen(false);
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
    /* 提取行级置信度低的前若干行,作为 LLM 二次校对的优先级参考 */
    const low_confidence_lines=(ocrUploadState?.lines||[])
      .filter(l=>l.low_confidence||(l.score||1)<0.85)
      .slice(0,10)
      .map(l=>l.text)
    setOcrStep(3);
    document.getElementById("ocrStatus").textContent="Agent 分析中";
    toast("Agent 正在分析…");
    showProgressBar("Agent 分析错题...","ocr-analyze");
    try{
      updateProgressBar("ocr-analyze",30,"提交分析请求...");
      const data=await apiRequest("/api/ocr/analyze",{method:"POST",body:JSON.stringify({text,subject,knowledge_point:point,user_answer,low_confidence_lines})});
      updateProgressBar("ocr-analyze",80,"处理分析结果...");
      ocrState=data;
      notebookCache=null;
      const analysis=data.analysis||{};
      const resolvedSubject=analysis.subject||data.subject||subject;
      const resolvedPoint=analysis.knowledge_point||data.knowledge_point||point;
      /* 写回顶部配置,确保"生成同类题"按钮能拿到真实 subject/point */
      const cs=document.getElementById("configSubject");if(cs)cs.textContent=resolvedSubject;
      const cp=document.getElementById("configPoint");if(cp)cp.textContent=resolvedPoint;
      const grid=document.getElementById("ocrAnalysisGrid");
      if(grid)grid.innerHTML=`<div class="analysis-item"><small>知识点</small><b>${escapeHtml(String(resolvedSubject))} / ${escapeHtml(String(resolvedPoint))}</b></div><div class="analysis-item"><small>掌握状态</small><b>${escapeHtml(String(analysis.mastery_status||"已同步后端"))}</b></div><div class="analysis-item wide"><small>Agent 推断标准答案</small><b>${escapeHtml(String(analysis.correct_answer||"待校对"))}</b></div><div class="analysis-item wide"><small>答案解析</small><b>${escapeHtml(String(analysis.answer_explanation||"暂无解析"))}</b></div><div class="analysis-item"><small>判断结果</small><b>${analysis.is_correct===true?"用户答案正确":analysis.is_correct===false?"用户答案错误":"用户答案待校对"}</b></div><div class="analysis-item"><small>主要错因</small><b>${escapeHtml(String(analysis.error_type||"OCR 导入待确认"))}</b></div>`+(analysis.possible_causes||["OCR 导入待确认"]).map(c=>`<div class="analysis-item"><small>可能错因</small><b>${escapeHtml(String(c))}</b></div>`).join("")+`<div class="analysis-item wide"><small>具体分析</small><b>${escapeHtml(String(analysis.error_reason||"Agent 已保存本次 OCR 错题，等待进一步校对。"))}</b></div><div class="analysis-item wide"><small>复习建议</small><b>${escapeHtml(String(analysis.suggestion||"先校对 OCR 文本，再围绕该知识点完成同类训练。"))}</b></div><div class="analysis-item wide"><small>后端记录</small><b>${escapeHtml(String(data.message||"已写入错题分析 Agent 结果"))} · mistake_id：${escapeHtml(String(data.mistake_id||"未返回"))} · memory_id：${escapeHtml(String(data.memory_id||"未返回"))} · ${data.llm_used?`AI 大模型 ${escapeHtml(String(data.llm_model||""))}`:`后端保底规则：${escapeHtml(String(data.llm_error||"大模型不可用"))}`}</b></div>`;
      const tools=document.getElementById("ocrAnalysisTools");
      if(tools)tools.style.display="flex";
      document.getElementById("ocrStatus").textContent="分析完成";
      setOcrStep(4);
      loadMistakeNotebook();
      // OCR 错题写入会改变掌握度/记忆/统计 → 全局刷新
      refreshAfterAnswer("answer").catch(console.error);
      completeProgressBar("ocr-analyze","错题分析完成");
      toast(data.llm_used?"错题分析已提交并写入记忆（AI 大模型）":"错题分析已提交并写入记忆（保底规则）","success");
    }catch(error){errorProgressBar("ocr-analyze",error.message);toast(error.message,"error");document.getElementById("ocrStatus").textContent="分析失败";setOcrStep(2);}
  };
  document.querySelectorAll("[data-book-tab]").forEach(b=>b.onclick=()=>openBookView(b.dataset.bookTab));
  document.querySelectorAll("[data-open-book]").forEach(b=>b.onclick=()=>openBookView(b.dataset.openBook));
  document.querySelectorAll("[data-return-books]").forEach(b=>b.onclick=()=>openBookView("overview"));
  document.getElementById("backToBooks").onclick=()=>{openBookView("overview");loadMistakeNotebook()};
  document.getElementById("saveOcrMistake").onclick=async()=>{
    if(!ocrState.mistake_id)return toast("请先完成 OCR 分析","error");
    setOcrStep(4);
    notebookCache=null;
    toast("已加入不会题本","success");
    setTimeout(()=>{openBookView("unknown")},500);
  };
  document.getElementById("generateOcrPractice").onclick=()=>{
    const subject=document.getElementById("configSubject")?.textContent||"操作系统";
    const point=document.getElementById("configPoint")?.textContent||"页面置换算法";
    /* 把 OCR 识别出的题目 + Agent 推断的标准答案 一并作为参考传入后端,
       让 LLM 出"与错题同考点/同结构"的同类题(避免凭空出题) */
    const ocrText=document.getElementById("ocrText")?.value?.trim()||"";
    const correctAnswer=(ocrState?.analysis?.correct_answer)||ocrState?.correct_answer||"";
    startPracticeForPoint(subject, point, ocrText, correctAnswer);
  };
 bindAccountSettings();
 bindForum();
 renderQuestion();
 startExamCountdown();
}
function bindAccountSettings(){
 const panel=document.getElementById("accountPanel"),mask=document.getElementById("accountMask");
 const open=()=>{
   panel.classList.add("open");mask.classList.add("show");panel.setAttribute("aria-hidden","false");document.body.classList.add("account-open");
   const userStr=localStorage.getItem("turing408_user");
   if(userStr){
     try{
       const user=JSON.parse(userStr);
       const nameInput=document.getElementById("accountName");
       if(nameInput&&user.nickname) nameInput.value=user.nickname;
     }catch(e){}
   }
   ["oldPassword","newPassword","confirmPassword"].forEach(id=>{const el=document.getElementById(id);if(el) el.value="";});
 };
 const close=()=>{panel.classList.remove("open");mask.classList.remove("show");panel.setAttribute("aria-hidden","true");document.body.classList.remove("account-open")};
 document.getElementById("openAccount").onclick=open;
 document.getElementById("closeAccount").onclick=close;
 mask.onclick=close;
 document.getElementById("logoutBtn").onclick=handleLogout;
 const saveName=()=>{const input=document.getElementById("accountName"),name=input.value.trim()||"林同学",avatar=name.slice(0,1);
  return apiRequest("/api/profile/update",{method:"PUT",body:JSON.stringify({nickname:name})}).then(data=>{
    const userStr=localStorage.getItem("turing408_user");
    if(userStr){try{const u=JSON.parse(userStr);u.nickname=name;localStorage.setItem("turing408_user",JSON.stringify(u))}catch(e){}}
    input.value=name;document.getElementById("topUserName").textContent=name;document.getElementById("topAvatar").textContent=avatar;document.querySelectorAll(".learning-user-card h3").forEach(x=>x.textContent=name);
    // 报告页"学习画像"里的用户名同步刷新
    refreshAfterAnswer("profile").catch(console.error);
    toast("账号昵称已保存")
  }).catch(err=>{toast(err.message||"保存失败","error");throw err})
 };
 const savePassword=()=>{const oldPwd=document.getElementById("oldPassword").value,newPwd=document.getElementById("newPassword").value,confirmPwd=document.getElementById("confirmPassword").value;if(!oldPwd)return toast("请输入当前密码");if(newPwd.length<6)return toast("新密码至少需要 6 位");if(newPwd!==confirmPwd)return toast("两次输入的新密码不一致");
  return apiRequest("/api/auth/change-password",{method:"POST",body:JSON.stringify({old_password:oldPwd,new_password:newPwd})}).then(data=>{
    ["oldPassword","newPassword","confirmPassword"].forEach(id=>document.getElementById(id).value="");toast("密码修改成功")
  }).catch(err=>{toast(err.message||"密码修改失败","error");throw err})
 };
 document.getElementById("accountSaveBtn").onclick=async()=>{
  try{
    await saveName();
    const oldPwd=document.getElementById("oldPassword").value;
    if(oldPwd) await savePassword();
  }catch(e){}
 };
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
    // 标记当前论坛版本已变,这样 refreshAfterAnswer 不会重复拉
    forumDataVersion++;
    lastSeenForumVersion=forumDataVersion;
    document.getElementById("forumFeed").insertAdjacentHTML("afterbegin",forumPostCardHTML(post));
    bindForumDynamic(document.querySelector(".forum-feed .forum-post"));
    // 刷新热门话题(可能进 TOP)+ 打卡状态(可能解锁连续奖励)
    loadHotTopics();
    loadCheckinStatus();
    // 论坛动作也会影响首页/报告统计 → 全局刷新(论坛页用 diff 跳过自己)
    refreshAfterAnswer("forum").catch(console.error);
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

  // P1-10: 思维链折叠
  const stepsBtn=post.querySelector(`[data-toggle-ai-steps="${postId}"]`);
  if(stepsBtn)stepsBtn.onclick=()=>{
    const box=document.getElementById(`forumAiSteps${postId}`);
    if(box)box.style.display=box.style.display==="block"?"none":"block";
  };

  // P2-12: 点赞/采纳
  const likeBtn=post.querySelector(`[data-ai-like="${postId}"]`);
  const disBtn=post.querySelector(`[data-ai-dislike="${postId}"]`);
  if(likeBtn)likeBtn.onclick=()=>likeAiAnswer(postId,true,likeBtn);
  if(disBtn)disBtn.onclick=()=>likeAiAnswer(postId,false,disBtn);
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
    // 启动论坛轮询(每 30s diff 更新)
    startForumPolling();
  }catch(err){console.error(err);}
}
async function loadForumPosts(category,search,options={}){
 const feed=document.getElementById("forumFeed");
 if(!feed)return;
 const silent=!!options.silent;
 // silent 模式(轮询/diff 刷新):不显示"加载中",避免闪烁
 // 非 silent 模式且 feed 已经有内容:也不清空,改用 diff 更新
 const hasContent=!!feed.querySelector(".forum-post");
 if(!silent&&!hasContent){
  feed.innerHTML="<div class='card' style='text-align:center;padding:40px;color:var(--muted);font-size:10px'>正在加载…</div>";
 }
 try{
  let url="/api/forum/posts";
  const params=[];
  if(category&&category!=="全部")params.push(`category=${encodeURIComponent(category)}`);
  if(search)params.push(`search=${encodeURIComponent(search)}`);
  if(params.length)url+="?"+params.join("&");
  const data=await apiRequest(url);
  const items=data.items||[];
  // 标记版本:这次拉取已包含
  lastSeenForumVersion=forumDataVersion;
  if(!items.length){
   if(!silent)feed.innerHTML="<div class='card' style='text-align:center;padding:40px;color:var(--muted);font-size:10px'>暂无讨论，快来发布第一条吧</div>";
   return;
  }
  // 已有内容 → diff 更新(不重置评论框/已展开状态)
  if(hasContent||silent){
   diffUpdateForumFeed(items);
  }else{
   feed.innerHTML=items.map(p=>forumPostCardHTML(p)).join("");
   feed.querySelectorAll(".forum-post").forEach(post=>bindForumDynamic(post));
  }
 }catch(err){
  if(!silent){
   feed.innerHTML=`<div class='card' style='text-align:center;padding:40px;color:var(--danger);font-size:10px'>加载失败：${escapeHtml(err.message)}</div>`;
  }else{
   console.error("forum silent refresh failed:",err);
  }
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
    // 打卡影响首页统计/报告 → 全局刷新(论坛页本身已是最新的,只刷其他页)
    refreshAfterAnswer("checkin").catch(console.error);
    toast(data.message||"打卡成功","success");
  }catch(err){
    btn.disabled=false;
    btn.textContent="今日打卡";
    toast(err.message||"打卡失败","error");
  }
}
async function likeForumPost(postId,button){
  // 读取当前已点赞状态，切换到目标状态后请求后端
  const wasLiked=button.classList.contains("liked");
  const wantLiked=!wasLiked;
  // 乐观更新：先切 class 改样式和 count
  button.classList.toggle("liked",wantLiked);
  const svg=button.querySelector("svg");
  if(svg)svg.setAttribute("fill",wantLiked?"currentColor":"none");
  const countEl=button.nextElementSibling;
  if(countEl)countEl.textContent=Number(countEl.textContent||0)+(wantLiked?1:-1);
  try{
    const path=wantLiked
      ?`/api/forum/posts/${postId}/like`
      :`/api/forum/posts/${postId}/unlike`;
    const data=await apiRequest(path,{method:"POST"});
    // 用后端返回的真实值校正
    if(countEl&&data.like_count!==undefined)countEl.textContent=Number(data.like_count||0);
  }catch(err){
    // 回滚
    button.classList.toggle("liked",wasLiked);
    if(svg)svg.setAttribute("fill",wasLiked?"currentColor":"none");
    if(countEl)countEl.textContent=Number(countEl.textContent||0)+(wasLiked?1:-1);
    toast(err.message||"点赞失败","error");
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
    renderForumAiAnswer(postId,data,content);
  }catch(err){
    content.innerHTML=`<p style='color:var(--danger)'>AI 小助手暂时不可用：${escapeHtml(err.message)}</p>`;
  }
}

/* 渲染结构化 AI 回答（P0-4 + P1-10） */
function renderForumAiAnswer(postId,data,content){
  const structured=data.structured||data.answer||{};
  const retrieval=data.retrieval||{};
  const profile=data.user_profile||{};
  const agentSteps=data.agent_steps||[];
  const shouldFollowup=!!data.should_followup;
  const followupHint=data.followup_hint||"";
  const answerId=data.answer_id;

  /* 1) 置信度标签 */
  const conf=retrieval.confidence||"unknown";
  const confLabels={high:"高置信",medium:"中置信",low:"低置信",none:"无证据",unknown:"检测中"};
  const confEl=document.getElementById(`forumAiConf${postId}`);
  if(confEl){
    confEl.textContent="● "+confLabels[conf]||conf;
    confEl.dataset.confidence=conf;
  }

  /* 2) 4 张主卡片（收敛：问题定位/详细解析/易错陷阱/举一反三）
     不再渲染「结合你的学习画像」「知识库证据」等附加卡片
     主体内容统一走 formatStructuredText 解析，结构化排版 */
  const cards=[
    {icon:"📍",title:"问题定位",body:structured.subject_kp||"",key:"subject_kp"},
    {icon:"🔍",title:"详细解析",body:structured.analysis||"",key:"analysis"},
    {icon:"⚠️",title:"易错陷阱",body:structured.easy_trap||"",key:"easy_trap"},
    {icon:"🎯",title:"举一反三",body:structured.extend_exercise||"",key:"extend_exercise"},
  ];
  const cardHtml=cards.map(c=>{
    const body=formatStructuredText(c.body);
    return `<div class="ai-card" data-ai-card="${c.key}">
      <div class="ai-card-head"><span>${c.icon}</span><b>${c.title}</b></div>
      <div class="ai-card-body">${body}</div>
    </div>`;
  }).join("");

  /* 6) 追问提示 */
  const hintEl=document.getElementById(`forumAiHint${postId}`);
  if(hintEl){
    if(shouldFollowup&&followupHint){
      hintEl.style.display="block";
      hintEl.innerHTML=`<b>💡 AI 追问：</b>${escapeHtml(followupHint)}`;
    }else{
      hintEl.style.display="none";
    }
  }

  /* 7) 思维链 */
  const stepsEl=document.getElementById(`forumAiSteps${postId}`);
  if(stepsEl){
    stepsEl.innerHTML=agentSteps.length?`<b>⚙ 思维链（Agent Steps）</b><ol>${agentSteps.map(s=>`<li><b>${escapeHtml(s.name||"")}</b> <small>${escapeHtml(s.status||"")} · ${s.duration_ms||0}ms</small><div>${escapeHtml(s.output_summary||"")}</div></li>`).join("")}</ol>`:"";
  }

  content.innerHTML=cardHtml;

  /* 8) 反馈按钮 */
  const fbEl=document.getElementById(`forumAiFeedback${postId}`);
  if(fbEl)fbEl.style.display="flex";
  if(answerId){
    const likesEl=document.getElementById(`forumAiLikes${postId}`);
    if(likesEl)likesEl.dataset.answerId=answerId;
    // 直接使用接口返回的反馈状态恢复选中态
    const fb=data.feedback||{};
    applyAiFeedbackState(postId,fb);
  }
}

/* 恢复/应用 AI 反馈的选中态 + 计数 */
function applyAiFeedbackState(postId,fb){
  const likesEl=document.getElementById(`forumAiLikes${postId}`);
  const likeBtn=document.querySelector(`[data-ai-like="${postId}"]`);
  const disBtn=document.querySelector(`[data-ai-dislike="${postId}"]`);
  if(!likesEl)return;
  const state=fb.user_feedback||"";
  const likeCount=Number(fb.like_count||0);
  const disCount=Number(fb.dislike_count||0);
  if(likeBtn)likeBtn.classList.toggle("selected",state==="helpful");
  if(disBtn)disBtn.classList.toggle("selected",state==="unhelpful");
  if(state==="helpful"){
    likesEl.textContent=`已采纳 · 👍 ${likeCount}`;
    likesEl.dataset.state="helpful";
  }else if(state==="unhelpful"){
    likesEl.textContent=`已标记不准确 · 👎 ${disCount}`;
    likesEl.dataset.state="unhelpful";
  }else{
    likesEl.textContent=`👍 ${likeCount} · 👎 ${disCount}`;
    likesEl.dataset.state="";
  }
}

/* 提交 AI 追问（P0-5 + P1-6 + P2-14） */
async function submitAiFollowup(postId,button){
  const input=button.previousElementSibling;
  const question=input.value.trim();
  if(!question)return toast("请输入想继续追问的问题");
  const content=document.getElementById(`forumAiContent${postId}`);
  const followupBlock=`<div class="ai-followup-question"><b>你的追问</b><p>${escapeHtml(question)}</p></div><div class="ai-followup-reply"><b>AI 小助手补充</b><div class="ai-followup-reply-body"><p style='color:var(--muted)'>正在思考…</p></div></div>`;
  if(content)content.insertAdjacentHTML("beforeend",followupBlock);
  input.value="";
  try{
    const data=await apiRequest(`/api/forum/posts/${postId}/ai-followup`,{method:"POST",body:JSON.stringify({content:question})});
    const lastReply=content?.querySelector(".ai-followup-reply:last-child .ai-followup-reply-body");
    if(data&&data.structured){
      const html=renderStructuredAnswer(data.structured);
      if(lastReply)lastReply.innerHTML=html||"<p>暂无更多回答</p>";
    }else if(lastReply){
      lastReply.innerHTML="<p>暂无更多回答</p>";
    }
    /* 追问提示 */
    if(data&&data.should_followup&&data.followup_hint){
      if(content)content.insertAdjacentHTML("beforeend",`<div class="ai-followup-hint">💡 ${escapeHtml(data.followup_hint)}</div>`);
    }
  }catch(err){
    const lastReply=content?.querySelector(".ai-followup-reply:last-child .ai-followup-reply-body");
    if(lastReply)lastReply.innerHTML=`<p style='color:var(--danger)'>追问失败：${escapeHtml(err.message)}</p>`;
    toast(err.message,"error");
  }
}

/* 把追问回复渲染为单独的「详细解析」卡片。
   追问只给出新的详细解答，不要问题定位/易错陷阱/举一反三。
   主体内容走 formatStructuredText，结构化排版。 */
function renderStructuredAnswer(s){
  if(!s)return"";
  const text=s.analysis||"";
  if(!text)return"";
  return `<div class="ai-card" data-ai-card="analysis">
    <div class="ai-card-head"><span>🔍</span><b>详细解析（追问补充）</b></div>
    <div class="ai-card-body">${formatStructuredText(text)}</div>
  </div>`;
}

/* 点赞/采纳 AI 回答（P2-12） */
async function likeAiAnswer(postId,helpful,btn){
  const likesEl=document.getElementById(`forumAiLikes${postId}`);
  const answerId=likesEl?.dataset.answerId;
  if(!answerId){return toast("暂未生成 AI 回答，无法反馈");}
  try{
    const data=await apiRequest("/api/forum/ai-answer/like",{method:"POST",body:JSON.stringify({answer_id:Number(answerId),is_helpful:!!helpful})});
    // 用接口返回的累计计数与用户当前反馈状态更新 UI
    applyAiFeedbackState(postId,{
      user_feedback:data.user_feedback||(helpful?"helpful":"unhelpful"),
      like_count:data.like_count||0,
      dislike_count:data.dislike_count||0,
    });
    toast(helpful?"已采纳为有用回答":"已标记为不准确","success");
  }catch(err){
    toast(err.message||"反馈失败","error");
  }
}

/* 模块联动跳转已下线：4 个跳转按钮（生成专项题/视频讲解/错题本/深入问答）已删除。
   保留 triggerAiAction 占位以避免控制台报错。 */
function triggerAiAction(){/* no-op: 跳转按钮已移除 */}
function startExamCountdown(){const target=new Date("2026-12-19T00:00:00+08:00").getTime();const update=()=>{const diff=Math.max(0,target-Date.now()),days=Math.floor(diff/86400000),hours=Math.floor(diff%86400000/3600000),minutes=Math.floor(diff%3600000/60000),seconds=Math.floor(diff%60000/1000);const set=(id,value)=>{const el=document.getElementById(id);if(el)el.textContent=String(value).padStart(2,"0")};set("countdownDays",days);set("countdownHours",hours);set("countdownMinutes",minutes);set("countdownSeconds",seconds);const subtitle=document.getElementById("pageSub");if(subtitle&&["qa","question","mistake","forum","report"].some(id=>document.getElementById(id)?.classList.contains("active")))subtitle.textContent=`距离 408 初试还有 ${days} 天`};update();if(countdownTimer)clearInterval(countdownTimer);countdownTimer=setInterval(update,1000)}
function openBookView(name){
  document.querySelectorAll(".book-view").forEach(v=>v.classList.toggle("active",v.id===`book-${name}`));
  const toolbar=document.querySelector("#mistake .book-toolbar");
  if(toolbar)toolbar.style.display=name==="ocr"?"none":"";
  const titles={overview:["我的题本","智能出题中标记“不熟”和“不会”的题目会自动进入对应题本"],unfamiliar:["不熟题本","理解不稳定的题目，以单列卡片形式集中巩固"],unknown:["不会题本","尚未掌握的题目，优先重新学习与练习"],ocr:["",""]};
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
function closeQuestionDrawers(){
 const mask=document.getElementById("questionDrawerMask");
 if(mask)mask.classList.remove("show");
 ["manualDrawer","smartDrawer","feedbackDrawer"].forEach(id=>document.getElementById(id)?.classList.remove("open"));
}
function selectedValue(group){const selected=document.querySelector(`[data-choice-group="${group}"] .selected`);return selected?selected.dataset.value:""}

function showPage(id){document.querySelectorAll(".page").forEach(p=>p.classList.toggle("active",p.id===id));document.querySelectorAll(".nav button").forEach(b=>b.classList.toggle("active",b.dataset.page===id));const greetingPages=["qa","question","mistake","forum","report","knowledge"],title=document.getElementById("pageTitle"),subtitle=document.getElementById("pageSub");if(greetingPages.includes(id)){title.textContent=getTimeBasedGreeting();const days=document.getElementById("countdownDays")?.textContent||"180";subtitle.textContent=`距离 408 初试还有 ${Number(days)} 天`;startGreetingAutoUpdate()}else{const p=pages.find(x=>x[0]===id);title.textContent=p[2];subtitle.textContent={home:"基于长期记忆生成的个性化学习空间"}[id]||""}if(id==="qa")loadConversations();if(id==="knowledge"&&!window.knDetailActive)loadKnowledgeNavPage();if(id==="mistake")loadMistakeNotebook();if(id==="forum")loadForum();if(id==="home")reloadHomeKnowledgeIfPending();renderMapping(id);window.scrollTo(0,0);if(id!=="knowledge")window.knDetailActive=false;}
/* 切回 home 时,如果知识图谱 canvas 仍是"正在加载…"占位符(说明之前那次请求没填回来),
   强制重新触发一次,避免页面卡死在 loading 状态。*/
function reloadHomeKnowledgeIfPending(){
 const active=document.querySelector(".page.active");
 if(!active||active.id!=="home")return;
 const canvas=active.querySelector("#knowledgeGraphCanvas");
 if(!canvas)return;
 // 已经有数据(总览卡片/旧版象限任一已渲染)就什么都不做
 if(canvas.querySelector(".kg-overview-card")||canvas.querySelector(".kg-quadrant"))return;
 // cache 命中(切走期间请求已完成并写入了 cache) -> 直接渲染
 if(knowledgeOverviewCache&&knowledgeOverviewCache.subjects){
  renderKnowledgeOverview(knowledgeOverviewCache);
  return;
 }
 // inflight 进行中 -> 等待它完成(不重发)
 if(knowledgeOverviewInflight){
  knowledgeOverviewInflight.then(()=>{
   const live=document.querySelector(".page.active");
   const liveCanvas=live&&live.id==="home"?live.querySelector("#knowledgeGraphCanvas"):null;
   if(liveCanvas&&!liveCanvas.querySelector(".kg-overview-card")&&!liveCanvas.querySelector(".kg-quadrant")&&knowledgeOverviewCache){
    renderKnowledgeOverview(knowledgeOverviewCache);
   }
  });
  return;
 }
 // 都没有 -> 强制重新触发
 loadKnowledgeOverviewGraph(true);
}
function renderMapping(id){const panel=document.getElementById("devContent");if(!panel)return;const m=mapping[id];panel.innerHTML=`<div class="mapping"><h4>建议接口</h4><code>${m[0]}</code></div><div class="mapping"><h4>核心数据实体</h4><code>${m[1]}</code></div><div class="mapping"><h4>Agent / LangGraph 节点</h4><code>${m[2]}</code></div>`}
function toggleDev(){document.getElementById("devPanel").classList.toggle("open")}function toast(t){const el=document.getElementById("toast");el.textContent=t;el.style.opacity=1;setTimeout(()=>el.style.opacity=0,2000)}function escapeHtml(s){if(s===null||s===undefined)return"";return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]))}function escapeAttr(s){return escapeHtml(s).replace(/`/g,"&#96;")}

/* ========= 全局右下角进度条 ========= */
function ensureProgressContainer(){let c=document.getElementById("progressContainer");if(!c){c=document.createElement("div");c.id="progressContainer";c.className="progress-container";document.body.appendChild(c)}return c}
function showProgressBar(label,id){const container=ensureProgressContainer();let bar=document.getElementById("progress-"+id);if(!bar){bar=document.createElement("div");bar.id="progress-"+id;bar.className="progress-bar-item";bar.innerHTML='<div class="progress-bar-header"><span class="progress-bar-label">'+escapeHtml(label)+'</span><span class="progress-bar-pct">0%</span></div><div class="progress-bar-track"><div class="progress-bar-fill" style="width:0%"></div></div>';container.appendChild(bar);requestAnimationFrame(()=>bar.classList.add("show"))}else{bar.querySelector(".progress-bar-label").textContent=label;bar.querySelector(".progress-bar-pct").textContent="0%";bar.querySelector(".progress-bar-fill").style.width="0%";bar.classList.remove("done","error");bar.classList.add("show")}return bar}
function updateProgressBar(id,percent,label){const bar=document.getElementById("progress-"+id);if(!bar)return;if(label)bar.querySelector(".progress-bar-label").textContent=label;bar.querySelector(".progress-bar-pct").textContent=percent+"%";bar.querySelector(".progress-bar-fill").style.width=percent+"%"}
function completeProgressBar(id,message){const bar=document.getElementById("progress-"+id);if(!bar)return;bar.querySelector(".progress-bar-pct").textContent="完成";bar.querySelector(".progress-bar-fill").style.width="100%";if(message)bar.querySelector(".progress-bar-label").textContent=message;bar.classList.add("done");setTimeout(()=>{bar.classList.remove("show");setTimeout(()=>bar.remove(),400)},1200)}
function errorProgressBar(id,message){const bar=document.getElementById("progress-"+id);if(!bar)return;bar.querySelector(".progress-bar-pct").textContent="失败";if(message)bar.querySelector(".progress-bar-label").textContent=message;bar.classList.add("error");setTimeout(()=>{bar.classList.remove("show");setTimeout(()=>bar.remove(),400)},2500)}

/* ========= 出题阶段化进度条 =========
   后端一次请求会经历「出题 → 自检 → 补题」多阶段，前端单接口拿不到阶段回执，
   因此按经验时间切阶段文案，给用户"系统在干活"的体感。
   stages 每项：{at: 距开始毫秒, label, pct}；pct 封顶 90，把 100% 留给 completeProgressBar。*/
function startGenerationProgress(id,prefix){
 const stages=[
  {at:0,label:`${prefix} · 调用出题 Agent…`,pct:18},
  {at:2000,label:`${prefix} · AI 生成题目中…`,pct:48},
  {at:6000,label:`${prefix} · 题目自检中…`,pct:72},
  {at:10000,label:`${prefix} · 补全题库中…`,pct:88},
 ];
 showProgressBar(stages[0].label,id);
 const timers=stages.slice(1).map(s=>setTimeout(()=>updateProgressBar(id,s.pct,s.label),s.at));
 return {stop:()=>timers.forEach(clearTimeout)};
}

/* ========= "分析中"等待进度条 =========
   用户视角只关心"系统在干活"，多阶段文案反而干扰。
   进度条只显示一个固定的"分析中…"，但百分比按时间增长给出"在动"的感觉。*/
function startAnalysisProgress(id,prefix="分析中"){
 const stages=[
  {at:0,label:`${prefix}…`,pct:18},
  {at:2000,label:`${prefix}…`,pct:45},
  {at:6000,label:`${prefix}…`,pct:68},
  {at:10000,label:`${prefix}…`,pct:85},
 ];
 showProgressBar(stages[0].label,id);
 const timers=stages.slice(1).map(s=>setTimeout(()=>updateProgressBar(id,s.pct,s.label),s.at));
 return {stop:()=>timers.forEach(clearTimeout)};
}

/* ========= 论坛 AI 回答结构化文本渲染器（markdown-lite） =========
   输入：LLM 输出的纯文本（已遵守"严格排版规则"，不含 MD 字符）
   输出：语义化 HTML，逻辑清晰、排版美观
   支持的语法：
     - 空行分段
     - ① ② ③ ... 开头的小节 → <h5>
     - 1. 2. 3. ... 整段连续 → <ol>
     - • · - 整段连续 → <ul>
     - 【关键判别】→ 高亮 <b class="hl">
     - 「术语」 → 行内 <code>
     - **bold** / __bold__（防御性兜底） → <b>
     - 多余的 # ## ###（防御性）→ 自动剔除 */
function formatStructuredText(raw){
  if(raw===null||raw===undefined||raw==="")return'<p class="ai-muted">暂无</p>';
  let text=String(raw);
  // 0) 防御性清理：剔除残留的 MD 字符
  text=text
    .replace(/```[\s\S]*?```/g,"")          // 围栏代码块
    .replace(/`([^`\n]+)`/g,"「$1」")        // 行内 `code` 转为「」
    .replace(/^#{1,6}\s*/gm,"")              // 行首井号标题
    .replace(/^\s*[-*_]{3,}\s*$/gm,"")        // 分隔线
    .replace(/\*\*([^*\n]+)\*\*/g,"【$1】")   // **bold** → 【】
    .replace(/__([^_\n]+)__/g,"【$1】")       // __bold__ → 【】
    .replace(/(^|[^*])\*([^*\n]+)\*/g,"$1【$2】") // *italic* → 【】
    .replace(/~~([^~\n]+)~~/g,"【$1】")       // ~~strike~~ → 【】
    .trim();
  if(!text)return'<p class="ai-muted">暂无</p>';
  // 1) 先把全文做 HTML 转义
  const esc=escapeHtml(text);
  // 2) 二次清洗：把英文标点引号替换为中文方括号（防御性兜底）
  const cleaned=esc
    .replace(/&quot;([^&]+?)&quot;/g,"「$1」")
    .replace(/&#039;([^&]+?)&#039;/g,"「$1」");
  // 3) 按空行分段
  const blocks=cleaned.split(/\n{2,}/);
  const html=blocks.map(block=>{
    const t=block.trim();
    if(!t)return"";
    // 3.1) 有序列表：整段由 1. 2. 3. 起头（≥2 项）
    if(/^(?:\s*(?:\d+|[①②-⑨])[\.、]\s).*(\n\s*(?:\d+|[①-⑨])[\.、]\s.*){1,}/m.test(t)){
      const lines=t.split(/\n(?=\s*(?:\d+|[①-⑨])[\.、]\s)/);
      return'<ol class="ai-list ai-list-ol">'+lines.map(l=>'<li>'+l.replace(/^\s*(?:\d+|[①-⑨])[\.、]\s*/,"")+'</li>').join("")+'</ol>';
    }
    // 3.2) 无序列表：整段由 • · - 起头（≥2 项）
    if(/^(?:\s*[•·\-\*]\s).*(\n\s*[•·\-\*]\s.*){1,}/m.test(t)){
      const lines=t.split(/\n(?=\s*[•·\-\*]\s)/);
      return'<ul class="ai-list ai-list-ul">'+lines.map(l=>'<li>'+l.replace(/^\s*[•·\-\*]\s*/,"")+'</li>').join("")+'</ul>';
    }
    // 3.3) 普通段落：单行/多行
    return'<p class="ai-para">'+t.replace(/\n/g,"<br>")+'</p>';
  }).filter(Boolean).join("");
  // 4) 高亮处理：【关键判别】→ <b class="hl">，嵌套
  const withHl=html
    .replace(/【([^】]+)】/g,function(_,inner){
      // 内部不要再次加 <b> 包裹
      return'<b class="hl">【'+inner+'】</b>';
    })
    // 「术语」 → <code>，但不重复包裹已经有的 <b>
    .replace(/「([^」]+)」/g,function(_,inner){
      return'<code>「'+inner+'」</code>';
    });
  return withHl;
}

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
  const reason=event.reason;
  console.error(reason);
  // 短时间(1.2s)同 reason 去重，避免 toast 刷屏
  const key=String(reason&&reason.message||reason||"unknown");
  if(window._lastRejectionKey===key&&Date.now()-(window._lastRejectionTs||0)<1200){
    return;
  }
  window._lastRejectionKey=key;
  window._lastRejectionTs=Date.now();
  // 提取简短原因提示（截断避免过长）
  let hint="";
  try{
    const m=reason&&reason.message?String(reason.message):String(reason);
    hint=m.length>40?m.slice(0,40)+"…":m;
  }catch(e){}
  toast(hint?`接口或异步任务异常：${hint}（已自动降级）`:"接口或异步任务异常，已自动启用降级方案","error");
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
  sub_questions:q.sub_questions||null,
  // 质量画像（后端 question_to_dict 已输出）
  easy_mistakes:q.easy_mistakes||"",
  quality_score:Number(q.quality_score||0),
  quality_flag:q.quality_flag||"normal",
  is_verified:Boolean(q.is_verified),
  source:q.source||"",
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
 // 质量徽标
 renderQualityBadges(q);
 // 易错点
 const emBox=document.getElementById("easyMistakesBox");
 const emText=document.getElementById("easyMistakesText");
 if(emBox&&emText){
  if(q.easy_mistakes&&q.easy_mistakes.trim()){
   emText.textContent=q.easy_mistakes;
   emBox.style.display="";
  }else{
   emBox.style.display="none";
  }
 }
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

// 渲染题目质量徽标（已验证/AI生成/被反馈有误/已下线）
function renderQualityBadges(q){
 const el=document.getElementById("questionQualityBadges");
 if(!el)return;
 const badges=[];
 const score=Number(q.quality_score||0);
 if(q.is_verified){
  badges.push(`<span class="q-badge q-badge-verified" title="已通过验证，质量分 ${score}">✓ 权威题 · ${score}</span>`);
 } else {
  badges.push(`<span class="q-badge q-badge-llm" title="由 AI 生成，质量分 ${score}">✦ AI 出题 · ${score}</span>`);
 }
 if(q.quality_flag==="disputed"){
  badges.push(`<span class="q-badge q-badge-disputed" title="已有用户反馈过该题存在问题">⚠ 被反馈</span>`);
 } else if(q.quality_flag==="deprecated"){
  badges.push(`<span class="q-badge q-badge-deprecated" title="已自动下线，不再进入参考池">✕ 已下线</span>`);
 }
 const reported=Number(q.reported_count||0);
 if(reported>0){
  badges.push(`<span class="q-badge q-badge-disputed" title="本题已被 ${reported} 个用户标记为有误">⚑ 反馈 ${reported}</span>`);
 }
 el.innerHTML=badges.join(" ");
}

// 提交题目质量反馈 → /api/questions/feedback
async function submitQuestionFeedback(){
 const q=activeQuestions[currentQuestionIndex];
 if(!q||!q.id)return toast("当前题目没有 ID，无法反馈","error");
 const fbTypeBtn=document.querySelector('[data-choice-group="feedbackType"] .selected');
 const fbType=fbTypeBtn?.dataset.value||"wrong_answer";
 const content=document.getElementById("feedbackContent")?.value?.trim()||"";
 try{
  const data=await apiRequest("/api/questions/feedback",{
   method:"POST",
   body:JSON.stringify({question_id:q.id, feedback_type:fbType, content}),
  });
  // 同步本地题目的反馈数与质量标记，避免 badge 不更新
  const returned=Number(data?.reported_count||0);
  q.reported_count=Math.max(Number(q.reported_count||0)+1, returned);
  if(data?.quality_flag){q.quality_flag=data.quality_flag}
  if(typeof renderQualityBadges==="function"){renderQualityBadges(q)}
  toast("✅ 反馈已提交，感谢你的帮助");
  closeQuestionDrawers();
  // 清空 textarea
  const ta=document.getElementById("feedbackContent");
  if(ta)ta.value="";
 }catch(error){
  toast("反馈提交失败："+(error?.message||"未知错误"),"error");
 }
}

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
 el.innerHTML=`<div style="padding:12px 0;color:var(--muted);text-align:center">正在匹配相关视频…</div>`;
 try{
  let data, items;
  if(questionId && questionId > 0){
   // 有questionId，调用题目关联的视频接口
   data=await apiRequest(`/api/questions/${questionId}/videos`);
   items=data.items||[];
  } else {
   // 没有questionId（如mock题目），从当前题目提取信息调用推荐接口
   const q=activeQuestions[currentQuestionIndex];
   if(!q)throw new Error("当前没有题目");
   const subject=encodeURIComponent(q.subject||"数据结构");
   const kp=encodeURIComponent(q.knowledge_point||"线性表");
   const qt=encodeURIComponent(q.title||"");
   data=await apiRequest(`/api/videos/recommend?subject=${subject}&knowledge_point=${kp}&question_text=${qt}&limit=3`);
   items=data.items||[];
  }
  if(!items.length){
   el.innerHTML=`<div class="conversation-empty">暂无相关推荐视频<br><small style="color:var(--muted)">可前往B站搜索王道408对应章节</small></div>`;
   return;
  }
  const matchLabel={exact:"<span style='color:#27a978;font-weight:600'>● 精确匹配</span>",alias:"<span style='color:#2f80ed;font-weight:600'>● 章节相关</span>",keyword:"<span style='color:#f7b500;font-weight:600'>● 关键词命中</span>",subject:"<span style='color:#9aa5b1;font-weight:600'>● 同科目推荐</span>"};
  el.innerHTML=`
    <div style="margin-bottom:10px;font-size:11px;color:var(--muted);display:flex;justify-content:space-between;align-items:center">
      <span>为「${escapeHtml(data.knowledge_point||'')}」匹配到 ${items.length} 个讲解视频</span>
      <span style="background:var(--good);color:#fff;padding:2px 8px;border-radius:99px;font-size:9px;font-weight:700">BV直链</span>
    </div>
    ${items.map((v,i)=>{
      const coverUrl=v.cover_url||"";
      const coverHtml=coverUrl
        ? `<div class="video-cover"><img src="${escapeAttr(coverUrl)}" alt="${escapeAttr(v.title||"视频封面")}" loading="lazy" referrerpolicy="no-referrer" onerror="this.onerror=null;this.parentElement.classList.add('video-cover-fallback');this.remove();"><span class="video-cover-play">▶</span><span class="video-cover-duration">${escapeHtml(v.duration||"")}</span></div>`
        : `<div class="video-cover video-cover-fallback"><span class="video-cover-play">▶</span><span class="video-cover-duration">${escapeHtml(v.duration||"")}</span><div class="video-cover-fallback-text">B站视频</div></div>`;
      return `
      <a href="${escapeHtml(v.url||'#')}" target="_blank" rel="noopener noreferrer" class="kd-video-card" data-vid="${escapeHtml(v.id||'')}" data-pos="${i}">
        ${coverHtml}
        <div class="video-info">
          <div class="video-info-top">
            <div class="video-title">${escapeHtml(v.title)}</div>
          </div>
          <div class="video-meta">
            <span class="video-platform">▶ B站</span>
            ${v.author?`<span class="video-tag">👤 ${escapeHtml(v.author)}</span>`:""}
            <span class="video-match">${matchLabel[v.match_level]||""}</span>
          </div>
          ${v.reason?`<p class="video-reason">${escapeHtml(v.reason)}</p>`:""}
          <div class="video-action">去观看 <span>↗</span></div>
        </div>
      </a>
    `;}).join("")}
    <div style="margin-top:14px;font-size:10px;color:var(--muted);text-align:center;line-height:1.6;padding:8px;background:var(--panel2);border-radius:8px">
      🔗 点击卡片将直接在新标签页打开 B 站视频播放页
    </div>
  `;
 // 视频点击埋点 - 记录用户行为用于个性化推荐
 el.querySelectorAll(".video-card").forEach(card=>{
  card.addEventListener("click",()=>{
   const vid=card.getAttribute("data-vid");
   const pos=parseInt(card.getAttribute("data-pos")||"0",10);
   const v=items[pos]||{};
   const q=activeQuestions[currentQuestionIndex]||{};
   fetch("/api/videos/click",{
    method:"POST",
    headers:{"Content-Type":"application/json","Authorization":`Bearer ${localStorage.getItem("turing408_token")||""}`},
    body:JSON.stringify({
     video_id: v.id||null,
     video_url: v.url||"",
     video_title: v.title||"",
     question_id: q.id||null,
     subject: q.subject||v.subject||"",
     knowledge_point: q.knowledge_point||v.knowledge_point||"",
     author: v.author||"",
     click_position: pos,
     match_level: v.match_level||"",
     source: v.source||"",
    })
   }).catch(()=>{});
  });
 });
}catch(error){
 el.innerHTML=`<div class="conversation-empty">视频加载失败<br><small style="color:var(--muted)">${escapeHtml(error.message||"")}</small></div>`;
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
 const lc2=document.querySelectorAll(".launch-card");
 if(lc2[1])lc2[1].onclick=async()=>{openQuestionDrawer("smartDrawer");await loadSmartRecommendations();};
 
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

 // 反馈抽屉：打开时把当前题写入抽屉
 const openFbBtn=document.getElementById("openFeedbackDrawer");
 if(openFbBtn){
  openFbBtn.onclick=()=>{
   const q=activeQuestions[currentQuestionIndex];
   if(!q)return toast("当前没有题目","error");
   if(!q.id)return toast("Mock 题目无 ID，无法反馈","error");
   const titleEl=document.getElementById("feedbackQuestionTitle");
   const metaEl=document.getElementById("feedbackQuestionMeta");
   if(titleEl)titleEl.textContent=(q.title||"").slice(0,80);
   if(metaEl)metaEl.textContent=`ID:${q.id} · ${q.subject||""} / ${q.knowledge_point||""} · 质量分 ${q.quality_score||0}`;
   openQuestionDrawer("feedbackDrawer");
  };
 }
 // 反馈类型选择
 document.querySelectorAll('[data-choice-group="feedbackType"] button').forEach(b=>{
  b.onclick=()=>{
   document.querySelectorAll('[data-choice-group="feedbackType"] button').forEach(x=>x.classList.remove("selected"));
   b.classList.add("selected");
  };
 });
 // 提交反馈
 const submitFbBtn=document.getElementById("submitFeedback");
 if(submitFbBtn)submitFbBtn.onclick=submitQuestionFeedback;
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
 bindQaHistoryToggle();
 setQaHistoryOpen(false);
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
 const progressId="question-generate-"+Date.now();
 const prefix="Agent 出题";
 const prog=startGenerationProgress(progressId,prefix);
 try{
  toast("Agent 正在生成题目，请稍候…");
  const data=await apiRequest(endpoint,{method:"POST",body:JSON.stringify(requestPayload)});
  prog.stop();
  if(data.all_refused&&(!data.questions||!data.questions.length)){errorProgressBar(progressId,"知识库暂无该知识点");toast("当前网络问题，请稍后重试或换一个知识点","error");return}
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
  completeProgressBar(progressId,"题目生成完成");
  toast(data.llm_used?`${successMessage}（AI 生成）`:`${successMessage}（后端规则题库）`,data.llm_used?"success":"info");
 }catch(error){
  console.error(error);
  prog.stop();
  errorProgressBar(progressId,error.message||"出题失败");
  toast(`${error.message}。本次未生成题目，也不会使用前端 Mock 冒充结果。`,"error");
 }
}

async function loadKnowledgePoints(subject){
 const container=document.querySelector('[data-choice-group="manualPoint"]');
 if(!container)return;
 container.innerHTML=`<div class="conversation-empty" style="grid-column:1/-1">正在加载知识点…</div>`;
 try{
  if(!knowledgeGraphCache)knowledgeGraphCache=await apiRequest("/api/knowledge/graph");
  if(!knowledgeGraphCache){
   container.innerHTML=`<div class="conversation-empty" style="grid-column:1/-1">知识图谱加载失败，请刷新重试</div>`;
   return;
  }
  const points=knowledgeGraphCache.subjects?.[subject]||[];
  if(!points.length){
   container.innerHTML=`<div class="conversation-empty" style="grid-column:1/-1">该科目暂无知识点（数据为空）</div>`;
   return;
  }
  container.innerHTML=points.map((p,i)=>`<button class="${i===0?"selected":""}" data-value="${escapeHtml(p.name)}"><b>${escapeHtml(p.name)}</b>${p.content?`<small>${escapeHtml(p.content)}</small>`:""}</button>`).join("");
  container.querySelectorAll("button").forEach(b=>b.onclick=()=>{container.querySelectorAll("button").forEach(x=>x.classList.remove("selected"));b.classList.add("selected");});
 }catch(error){
  container.innerHTML=`<div class="conversation-empty" style="grid-column:1/-1">加载失败：${escapeHtml(error.message||String(error))}</div>`;
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
  // 提交答案 → 后端 AI 批改：用"分析中"等待进度条，避免多阶段文案干扰
  const prog=startAnalysisProgress("submit-answer","分析中");
  const data=await apiRequest("/api/answers/check",{method:"POST",body:JSON.stringify({question_id:q.id,user_answer:userAnswer})});
  prog.stop();
  completeProgressBar("submit-answer","分析完成");
  lastAnswerRecordId=data.answer_record_id;
  document.getElementById("answer").classList.add("show");
  document.getElementById("answer").querySelector("h4").textContent=data.is_correct?"批改结果：回答正确":"批改结果：回答错误";
  document.getElementById("answerText").textContent=data.feedback;
  document.getElementById("wrongAction").classList.toggle("show",!data.is_correct);
  refreshAfterAnswer().catch(console.error);
  toast(data.is_correct?"回答正确，掌握状态已更新":"回答错误，请选择真实错因",data.is_correct?"success":"error");
 }catch(error){
  errorProgressBar("submit-answer","批改失败");
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
  // 错因确认 → 写入长期记忆：同样用"分析中"等待进度条
  const prog=startAnalysisProgress("cause-confirm","分析中");
  const data=await apiRequest("/api/mistakes/cause-confirm",{method:"POST",body:JSON.stringify({answer_record_id:lastAnswerRecordId,error_types:selected,user_note:note,agent_suggested_types:["计算错误"],evidence_source:"user_confirmed"})});
  prog.stop();
  completeProgressBar("cause-confirm","分析完成");
  document.getElementById("causeSummary").innerHTML=`<b>已形成结构化长期记忆证据</b><br>错因：${selected.join(" + ")}${note?`<br>用户说明：${escapeHtml(note)}`:""}<br>${data.message}`;
  // 错因写入长期记忆 → 全局刷新(首页记忆流/报告页记忆权重)
  refreshAfterAnswer("memory").catch(console.error);
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
  await apiRequest("/api/questions/mastery",{method:"POST",body:JSON.stringify({subject:q.subject,knowledge_point:q.knowledge_point,status,question_id:q.id||null})});
  refreshAfterAnswer().catch(console.error);
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
 input.value="";

 // Step 1: 乐观追加：用户气泡 + AI 占位（带步骤指示器 + 答案区）
 const userBubble=document.createElement("div");
 userBubble.className="bubble user";
 userBubble.textContent=question;

 const aiBubble=document.createElement("div");
 aiBubble.className="bubble ai";
 aiBubble.dataset.qaStreaming="true";
 aiBubble.innerHTML=`<div class="qa-steps" id="qaSteps-${Date.now()}">
   <div class="qa-step" data-step="意图识别">⏳ 意图识别</div>
   <div class="qa-step" data-step="检索知识库">⏳ 检索知识库</div>
   <div class="qa-step" data-step="读取长期记忆">⏳ 读取长期记忆</div>
   <div class="qa-step" data-step="加载掌握度">⏳ 加载掌握度</div>
   <div class="qa-step" data-step="LLM 生成回答">⏳ 生成回答</div>
  </div>
  <div class="qa-answer" style="display:none"></div>`;
 const qaStepsEl=aiBubble.querySelector(".qa-steps");
 const qaAnswerEl=aiBubble.querySelector(".qa-answer");
 messages.appendChild(userBubble);
 messages.appendChild(aiBubble);
 messages.scrollTop=messages.scrollHeight;

 const updateStep=function(stepName,status,detail){
  if(!qaStepsEl)return;
  let found=false;
  qaStepsEl.querySelectorAll(".qa-step").forEach(el=>{
   const name=el.dataset.step;
   if(name===stepName){found=true;
    el.className="qa-step qa-step-"+status;
    el.textContent=(status==="success"?"✅":status==="streaming"?"⏳":status==="pending"?"○":"❌")+" "+name+(detail?" · "+detail:"");}
   else if(!found)el.className="qa-step qa-step-success"; // past steps done
   else el.className="qa-step qa-step-pending";
  });
 };

 // 打字机：rAF 批量 flush token，避免逐字符 DOM 抖动
 let fullAnswer="";
 let tokenBuffer=[];
 let rafId=null;
 // 流式过程中始终用 sanitize + innerHTML 渲染（通过 template 元素解析，避免未闭合标签抖动）
 // 模板元素用于"先解析后取 HTML"——浏览器会补全未闭合标签，然后我们只取解析后的 innerHTML
 const _tpl=document.createElement("template");
 const flushTokens=()=>{
  rafId=null;
  if(!tokenBuffer.length)return;
  fullAnswer+=tokenBuffer.join("");
  tokenBuffer=[];
  // 切到 answer 视图
  if(qaStepsEl)qaStepsEl.style.display="none";
  if(qaAnswerEl){
   qaAnswerEl.style.display="block";
   // 关键：用 sanitize + template 解析，避免未闭合标签导致后续内容被加粗
   // template 元素是 inert document fragment，浏览器解析后 innerHTML 是"完整"的
   _tpl.innerHTML=sanitizeLlmHtml(fullAnswer);
   qaAnswerEl.innerHTML=_tpl.innerHTML;
  }
  messages.scrollTop=messages.scrollHeight;
 };
 const pushToken=function(text){
  if(!text)return;
  tokenBuffer.push(text);
  if(rafId==null)rafId=requestAnimationFrame(flushTokens);
 };
 const finishStream=function(extraHtml){
  // 取消未 flush 的 rAF
  if(rafId){cancelAnimationFrame(rafId);rafId=null;}
  flushTokens();
  // 把 textContent 升级为受信任的 HTML（白名单）
  if(qaAnswerEl){
   qaAnswerEl.innerHTML=sanitizeLlmHtml(fullAnswer)+(extraHtml||"");
  }
  messages.scrollTop=messages.scrollHeight;
 };

 try{
  const token=localStorage.getItem("turing408_token");
  const url=`${API_BASE}/api/qa/chat/stream?question=${encodeURIComponent(question)}&conversation_id=${currentConversationId||0}`;
  // AbortController + 超时：30s 内没收到 done 事件就主动中断 + fallback POST
  const controller=new AbortController();
  let sseTimeoutId=null;
  const resetSseTimeout=()=>{
   if(sseTimeoutId)clearTimeout(sseTimeoutId);
   sseTimeoutId=setTimeout(()=>{controller.abort();},30000);
  };
  resetSseTimeout();
  const response=await fetch(url,{headers:token?{Authorization:`Bearer ${token}`}:{},signal:controller.signal});
  if(!response.ok){
   if(sseTimeoutId)clearTimeout(sseTimeoutId);
   const errPayload=await response.json().catch(()=>({}));
   throw new Error(errPayload?.error?.message||`SSE 请求失败 (${response.status})`);
  }
  const reader=response.body.getReader();
  const decoder=new TextDecoder();
  let buffer="",currentEvent="";
  let receivedTokens=0;

  while(true){
   const {done,value}=await reader.read();
   if(done)break;
   buffer+=decoder.decode(value,{stream:true});
   const parts=buffer.split("\n");
   buffer=parts.pop()||"";
   for(const line of parts){
    const trimmed=line.trim();
    if(trimmed.startsWith("event: ")){currentEvent=trimmed.slice(7).trim();}
    else if(trimmed.startsWith("data: ")){
     let data;
     try{data=JSON.parse(trimmed.slice(6));}catch(e){continue;}
     if(currentEvent==="step"){
      updateStep(data.name,data.status,data.output||data.reason||(data.chunks!==undefined?data.chunks+" 片段":data.memories!==undefined?data.memories+" 记忆":""));
      messages.scrollTop=messages.scrollHeight;
      resetSseTimeout();
     }else if(currentEvent==="token"){
      pushToken(data.text||"");
      receivedTokens++;
      resetSseTimeout();
     }else if(currentEvent==="done"){
      if(sseTimeoutId)clearTimeout(sseTimeoutId);
      sseTimeoutId=null;
      const cid=data.conversation_id;
      if(cid&&!currentConversationId){currentConversationId=cid;
       document.getElementById("currentChatTitle").textContent=question.slice(0,30);
      }
      // 渲染 suggested_followups
      let actionsHtml="";
      if(data.suggested_followups&&data.suggested_followups.length){
       actionsHtml=`<div class="answer-sections">${data.suggested_followups.map(a=>`<span>${escapeHtml(a)}</span>`).join("")}</div>`;
      }
      finishStream(actionsHtml);
      // 刷新会话列表（不重置 messages 容器，避免丢上下文）
      loadConversations();
      break;
     }else if(currentEvent==="error"){
      throw new Error(data.message||"流式处理异常");
     }
    }
   }
  }
  // 流自然结束但没收到 done（如异常关闭）
  if(receivedTokens>0&&!aiBubble.dataset.finished){
   aiBubble.dataset.finished="1";
   finishStream("");
  }
 }catch(error){
  console.error("SSE stream failed, falling back to POST",error);
  if(sseTimeoutId){clearTimeout(sseTimeoutId);sseTimeoutId=null;}
  // 取消流式
  if(rafId){cancelAnimationFrame(rafId);rafId=null;}
  try{
   const data=await apiRequest("/api/qa/chat",{method:"POST",body:JSON.stringify({question,conversation_id:currentConversationId})});
   const cid=data.conversation_id;
   if(cid&&!currentConversationId){currentConversationId=cid;
    document.getElementById("currentChatTitle").textContent=question.slice(0,30);
    loadConversations();
   }
   const answer=(data.answer||"").trim()||"后端没有返回可展示回答，已保留本次问题，请稍后重试。";
   if(qaStepsEl)qaStepsEl.style.display="none";
   if(qaAnswerEl){
    qaAnswerEl.style.display="block";
    qaAnswerEl.innerHTML=sanitizeLlmHtml(answer)+
     `<div class="answer-sections"><span>${data.llm_used?"AI 大模型":"后端保底"}</span><span>${escapeHtml(data.knowledge_point||"综合")}</span></div>`;
   }
   aiBubble.dataset.finished="1";
   messages.scrollTop=messages.scrollHeight;
  }catch(fallbackError){
   if(qaStepsEl)qaStepsEl.style.display="none";
   if(qaAnswerEl){
    qaAnswerEl.style.display="block";
    qaAnswerEl.textContent="系统暂时无法处理该问题，请稍后重试。";
   }
   aiBubble.dataset.finished="1";
   toast(fallbackError.message,"error");
  }
 }
 // finally 兜底：无论 SSE / fallback 走哪条路径，只要 fullAnswer 有内容但还没 sanitize 渲染过，就强制 sanitize 一次
 // 解决"流式累积到一半断流/done 事件丢失"导致用户看到字面 HTML 的问题
 if(fullAnswer&&!aiBubble.dataset.finished){
  aiBubble.dataset.finished="1";
  if(rafId){cancelAnimationFrame(rafId);rafId=null;}
  if(qaStepsEl)qaStepsEl.style.display="none";
  if(qaAnswerEl){
   qaAnswerEl.style.display="block";
   qaAnswerEl.innerHTML=sanitizeLlmHtml(fullAnswer);
  }
  messages.scrollTop=messages.scrollHeight;
 }
 aiBubble.dataset.qaStreaming="false";
 messages.scrollTop=messages.scrollHeight;
}

// 把 LLM 输出的"纯文本+简单 HTML 标签"安全渲染：
// 1) escape 所有 HTML
// 2) 还原白名单内的标签
const SANITIZE_WHITELIST=[
 "b","strong","i","em","u","br","p","ol","ul","li",
 "table","thead","tbody","tfoot","tr","th","td","caption",
 "h1","h2","h3","h4","h5","h6",
 "span","div","code","pre","blockquote",
 "sup","sub","small","mark","kbd","abbr","del","ins",
 "font","a",
];
// 模块级缓存正则（避免每次重新编译）
const SANITIZE_TAG_RE=new RegExp("&lt;(\\/?(?:"+SANITIZE_WHITELIST.join("|")+")(?:\\s[^&]*?)?)&gt;","g");
function sanitizeLlmHtml(text){
 if(!text)return "";
 let safe=String(text).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
 // 行首 "## 标题" 转 <h2>（兼容 LLM 偶尔输出 markdown）
 safe=safe.replace(/^##\s+(.+)$/gm,"<h2>$1</h2>");
 // 兼容 markdown 表格分隔行 "---|---|---|"，删除之
 safe=safe.replace(/^\s*\|?[\s:|-]+\|[\s:|-]+\s*$/gm,"");
 safe=safe.replace(SANITIZE_TAG_RE,function(m,inner){
  // 去掉标签内的事件属性、javascript: 等危险内容
  const cleaned=inner
   .replace(/\son[a-z]+="[^"]*"/gi,"")
   .replace(/\son[a-z]+='[^']*'/gi,"")
   .replace(/(href|src)\s*=\s*["']?\s*javascript:[^"'\s]*/gi,"$1=\"#\"");
  return "<"+cleaned+">";
 });
 return safe;
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
   el.onclick=()=>{
    switchConversation(Number(el.dataset.conversationId));
    closeQaHistoryAfterPick();
   };
  });
 }catch(error){
  console.error(error);
 }
}

function setQaHistoryOpen(open){
 const panel=document.getElementById("qaHistoryPanel");
 const toggle=document.getElementById("qaHistoryToggle");
 if(panel)panel.classList.toggle("mobile-open",open);
 if(toggle){
  toggle.setAttribute("aria-expanded",open?"true":"false");
  const label=toggle.querySelector("span");
  const state=toggle.querySelector("b");
  if(label)label.textContent=open?"收起历史记录":"历史记录";
  if(state)state.textContent=open?"收起":"展开";
 }
}

function bindQaHistoryToggle(){
 const toggle=document.getElementById("qaHistoryToggle");
 const close=document.getElementById("qaHistoryClose");
 if(toggle)toggle.onclick=()=>setQaHistoryOpen(!document.getElementById("qaHistoryPanel")?.classList.contains("mobile-open"));
 if(close)close.onclick=()=>setQaHistoryOpen(false);
}

function closeQaHistoryAfterPick(){
 if(window.matchMedia&&window.matchMedia("(max-width: 950px)").matches){
  setQaHistoryOpen(false);
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
   const body=m.role==="user"?escapeHtml(m.content||""):sanitizeLlmHtml(m.content||"");
   return `<div class="${cls}">${body}</div>`;
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
 closeQaHistoryAfterPick();
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
 return `<section class="page" id="home"><div class="home-focus-grid"><article class="card hero-main"><div class="hero-task"><span class="eyebrow">TODAY'S AGENT PLAN</span><h2 id="homePlanTitle">正在读取今日计划…</h2><p id="homePlanReason">Agent 正在根据答题记录、错题、长期记忆和知识点掌握状态计算今日优先训练内容。</p><button class="primary" id="startPersonalTraining" onclick="startPersonalizedTraining()">开始个性化训练 →</button></div></article><article class="card countdown-card"><div class="exam-countdown"><span>考研 408 初试倒计时</span><div class="countdown-days"><b id="countdownDays">--</b><small>天</small></div><div class="countdown-clock"><div><b id="countdownHours">--</b><small>时</small></div><i>:</i><div><b id="countdownMinutes">--</b><small>分</small></div><i>:</i><div><b id="countdownSeconds">--</b><small>秒</small></div></div><p id="examDateLabel">目标日期：读取中</p></div></article><article class="card today-recommend-card"><div class="head"><h3>今日推荐</h3></div><div class="recommend" id="todayRecommendList"><div class="rec"><b>正在匹配推荐训练</b><small>系统会优先匹配薄弱点、错题复练、高频考点和未学知识点。</small></div></div></article></div><div class="stats" id="homeStats"><div class="card stat"><small>本周答题</small><strong>--</strong><span class="delta">读取中</span></div><div class="card stat"><small>综合正确率</small><strong>--</strong><span class="delta">读取中</span></div><div class="card stat"><small>长期薄弱点</small><strong>--</strong><span class="delta">读取中</span></div><div class="card stat"><small>记忆条目</small><strong>--</strong><span class="delta">读取中</span></div></div><div class="home-knowledge-layout"><article class="card knowledge-graph-card"><div class="kg-toolbar"><div><h3>408 全局知识图谱</h3></div><div class="kg-tabs" id="kgTabs"><button class="active" data-graph-filter="all">总览</button></div></div><div class="kg-actions"><button id="structureLayer">知识结构</button><button id="masteryLayer" class="active">掌握状态</button><span id="layerNote">默认展示数据库中的最终掌握状态</span></div><div class="kg-canvas" id="knowledgeGraphCanvas"><div class="home-empty-state">正在加载知识图谱…</div></div><div class="kg-legend" id="kgLegend"></div></article></div></section>`;
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
  maybeShowCheckinModal();
 }catch(error){
  console.error(error);
  renderHomeError(error.message);
 }
}

/* ========= 全局失效 + 智能重渲染 =========
   范围:首页/知识图谱/知识详情/错题本/报告页/论坛
   触发:答题/标记掌握/OCR/错因/打卡/笔记/昵称/QA 记忆写入等
*/
let lastAnswerAt=0;          // 最近一次答题/错题/记忆写入时间戳(ms)
let reportCache=null;        // 报告页缓存
let reportCacheAt=0;         // 报告页缓存时间
let forumDataVersion=0;      // 论坛数据版本号(每次写入自增)
let lastSeenForumVersion=0;  // 上次拉取的版本号(用于"是否过期")
let forumPollTimer=null;     // 论坛轮询定时器

async function refreshAfterAnswer(scope="all"){
 // 1. 失效所有相关缓存
 notebookCache=null;
 knowledgeGraphCache=null;
 knowledgeOverviewCache=null;
 currentHomeOverview=null;
 reportCache=null;
 reportCacheAt=0;
 forumDataVersion++;
 // 全局答题/学习状态时间戳(供 showPage 过期检测用)
 if(scope==="all"||scope==="answer"||scope==="mastery"||scope==="memory"){
  lastAnswerAt=Date.now();
 }

 // 2. 重渲染当前激活页 + 已在 DOM 中的相关卡片
 const active=document.querySelector(".page.active")?.id||"";
 try{
  if(active==="home"||scope==="all"){
   await loadHomeOverview();
  }
  if(active==="knowledge"||scope==="all"){
   if(activeSubjectGraph?.subject?.id){
    await loadSubjectGraph(activeSubjectGraph.subject.id);
   }else{
    await loadKnowledgeOverviewGraph();
   }
   // 详情页打开时同步刷新
   if(window.knDetailActive&&window.currentKnowledgePointId){
    try{ await loadKnPointDetail(window.currentKnowledgePointId); }catch(e){}
   }
  }
  if(active==="mistake"||scope==="all"){
   await loadMistakeNotebook();
  }
  if(active==="report"||scope==="all"){
   if(typeof loadReportOverview==="function")await loadReportOverview();
  }
  if(active==="forum"){
   // 论坛页只在版本变化时静默拉取(避免闪烁)
   if(forumDataVersion!==lastSeenForumVersion){
    await loadForumPosts(getActiveForumCategory(),getForumSearchKeyword(),{silent:true});
    loadHotTopics();
    loadCheckinStatus();
    lastSeenForumVersion=forumDataVersion;
   }
  }
 }catch(error){
  console.error("refreshAfterAnswer error:",error);
 }
}

/* ===== 论坛辅助:getter ===== */
function getActiveForumCategory(){
 return document.querySelector("[data-forum-category].active")?.dataset.forumCategory||"全部";
}
function getForumSearchKeyword(){
 return document.getElementById("forumSearch")?.value?.trim()||"";
}

/* ===== 论坛轮询(30s) ===== */
function startForumPolling(){
 stopForumPolling();
 forumPollTimer=setInterval(async()=>{
  if(document.querySelector(".page.active")?.id!=="forum")return;
  // 仅在论坛页可见时拉取,且仅拉 feed
  try{
   const category=getActiveForumCategory();
   const keyword=getForumSearchKeyword();
   let url="/api/forum/posts";
   const params=[];
   if(category&&category!=="全部")params.push(`category=${encodeURIComponent(category)}`);
   if(keyword)params.push(`search=${encodeURIComponent(keyword)}`);
   if(params.length)url+="?"+params.join("&");
   const data=await apiRequest(url);
   const items=data.items||[];
   diffUpdateForumFeed(items);
  }catch(e){/* 静默失败,不影响用户 */}
 },30000);
}
function stopForumPolling(){
 if(forumPollTimer){clearInterval(forumPollTimer);forumPollTimer=null;}
}

/* ===== 论坛 feed diff 更新 ===== */
function diffUpdateForumFeed(items){
 const feed=document.getElementById("forumFeed");
 if(!feed)return;
 const existing=new Map();
 feed.querySelectorAll(".forum-post").forEach(el=>{if(el.dataset.postId)existing.set(String(el.dataset.postId),el);});
 const incomingIds=new Set(items.map(p=>String(p.id)));
 // 删除:已不在列表中的
 existing.forEach((el,id)=>{if(!incomingIds.has(id))el.remove();});
 // 更新/插入:按顺序处理
 let prev=null;
 items.forEach(post=>{
  const id=String(post.id);
  const html=forumPostCardHTML(post);
  const existingEl=existing.get(id);
  if(existingEl){
   // 用临时 div 解析新 HTML,按需替换评论数/点赞数(避免破坏已展开的评论)
   const tmp=document.createElement("div");
   tmp.innerHTML=html;
   const newEl=tmp.firstElementChild;
   // 评论/点赞数差异更新
   const oldLike=existingEl.querySelector("[data-forum-like-count]")?.textContent;
   const newLike=newEl?.querySelector("[data-forum-like-count]")?.textContent;
   if(oldLike!==newLike&&newLike!==undefined){
    existingEl.querySelector("[data-forum-like-count]")?.replaceWith(newEl.querySelector("[data-forum-like-count]"));
   }
   const oldCmt=existingEl.querySelector("[data-forum-comment-count]")?.textContent;
   const newCmt=newEl?.querySelector("[data-forum-comment-count]")?.textContent;
   if(oldCmt!==newCmt&&newCmt!==undefined){
    existingEl.querySelector("[data-forum-comment-count]")?.replaceWith(newEl.querySelector("[data-forum-comment-count]"));
   }
   // 标题/分类/摘要变化才整块替换
   const oldTitle=existingEl.querySelector(".forum-post-title")?.textContent;
   const newTitle=newEl?.querySelector(".forum-post-title")?.textContent;
   if(oldTitle!==newTitle&&newTitle){
    const newClone=newEl.cloneNode(true);
    bindForumDynamic(newClone);
    existingEl.replaceWith(newClone);
   }
  }else{
   // 新增:插入到正确位置(prev 之后或顶部)
   const tmp=document.createElement("div");
   tmp.innerHTML=html;
   const newEl=tmp.firstElementChild;
   bindForumDynamic(newEl);
   if(prev&&prev.parentNode===feed){
    prev.after(newEl);
   }else{
    feed.prepend(newEl);
   }
  }
  prev=feed.querySelector(`.forum-post[data-post-id="${id}"]`);
 });
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
 // 区分三种状态：
 // 1. 正常：plan.title 已含"今天优先攻克\nxxx"
 // 2. 新手指引：plan.initial_state === true（后端用 initial_state 标识首次引导，不是数据异常）
 // 3. 真实空状态/异常：plan 为空或 reason 含"暂不可用"
 let titleText="先完成一次\n408 基线诊断";
 let reasonText="当前暂无错题记录，先完成一组高频基础题，系统会自动建立初始学习画像。";
 if(plan&&plan.title){
  titleText=plan.title;
 }
 if(plan&&plan.reason){
  reasonText=plan.reason;
 }
 if(plan&&plan.initial_state===true){
  // 新手指引：加一段正向提示
  reasonText=`${reasonText}\n提示：完成 3 道题后,系统会自动定位你的薄弱点并个性化推荐。`;
 }
 title.innerHTML=escapeHtml(titleText).replace(/\n/g,"<br>");
 reason.textContent=reasonText;
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
 const deltaOverride={["长期薄弱点"]:"建议巩固",["记忆条目"]:"训练你的专属agent"};
 const fallback=[
  {label:"本周答题",value:0,delta:"开始答题后自动统计"},
  {label:"综合正确率",value:"待生成",delta:"暂无答题记录"},
  {label:"长期薄弱点",value:0,delta:"建议巩固"},
  {label:"记忆条目",value:0,delta:"训练你的专属agent"}
 ];
 const items=(cards.length?cards:fallback).map(card=>({...card,delta:deltaOverride[card.label]||card.delta}));
 stats.innerHTML=items.map(card=>`<div class="card stat"><small>${escapeHtml(card.label)}</small><strong>${escapeHtml(String(card.value))}</strong><span class="delta">${escapeHtml(card.delta)}</span></div>`).join("");
}

async function updateSidebarStreak(){
  try{
    const data=await apiRequest("/api/points/account");
    const days=data.streak_days??0;
    const el=document.getElementById("sidebarStreakDays");
    if(el)el.textContent=days;
  }catch(e){/* ignore */}
}

/* ========= 首页每日打卡弹窗 ========= */
async function maybeShowCheckinModal(){
  if(!document.getElementById("home"))return;
  const lastKey="checkin_modal_last_date";
  const today=new Date().toLocaleDateString("zh-CN");
  if(localStorage.getItem(lastKey)===today)return;
  try{
    const data=await apiRequest("/api/points/account");
    if(data.today_checkin){localStorage.setItem(lastKey,today);return;}
    showCheckinModal(data.streak_days??0,false);
  }catch(e){/* ignore */}
}

function showCheckinModal(streakDays,todayCheckin){
  const old=document.getElementById("checkinModal");
  if(old)old.remove();
  const html=`
  <div class="checkin-modal-mask" id="checkinModal">
    <div class="checkin-modal-card">
      <button class="checkin-modal-close" id="checkinModalClose">×</button>
      <div class="checkin-modal-icon">🔥</div>
      <h3>每日学习打卡</h3>
      <div class="checkin-modal-streak">连续打卡 <strong id="checkinModalStreak">${streakDays}</strong> 天</div>
      <p class="checkin-modal-tip">坚持打卡，积累积分，解锁更多 AI 学习功能</p>
      <button class="primary" id="checkinModalBtn" ${todayCheckin?"disabled":""}>${todayCheckin?"今日已打卡":"立即打卡"}</button>
    </div>
  </div>`;
  document.body.insertAdjacentHTML("beforeend",html);
  const mask=document.getElementById("checkinModal");
  requestAnimationFrame(()=>mask.classList.add("show"));
  document.getElementById("checkinModalClose").onclick=closeCheckinModal;
  mask.addEventListener("click",e=>{if(e.target===mask)closeCheckinModal()});
  const btn=document.getElementById("checkinModalBtn");
  if(btn&&!todayCheckin)btn.onclick=doHomeCheckin;
}

function closeCheckinModal(){
  const mask=document.getElementById("checkinModal");
  if(!mask)return;
  mask.classList.remove("show");
  setTimeout(()=>mask.remove(),300);
  const today=new Date().toLocaleDateString("zh-CN");
  localStorage.setItem("checkin_modal_last_date",today);
}

async function doHomeCheckin(){
  const btn=document.getElementById("checkinModalBtn");
  if(btn){btn.disabled=true;btn.textContent="打卡中...";}
  try{
    const data=await apiRequest("/api/points/checkin",{method:"POST"});
    if(data.success){
      toast("打卡成功 +" + (data.earned||0) + " 积分","success");
      const streakEl=document.getElementById("checkinModalStreak");
      if(streakEl){
        const newStreak=(parseInt(streakEl.textContent,10)||0)+1;
        streakEl.textContent=newStreak;
      }
      if(btn){btn.textContent="今日已打卡";btn.disabled=true;}
      updateSidebarStreak();
      syncPersonalCenterCheckin();
      setTimeout(closeCheckinModal,1200);
    }else{
      toast(data.message||"今日已完成打卡","info");
      if(btn){btn.textContent="今日已打卡";btn.disabled=true;}
    }
  }catch(err){
    toast(err.message||"打卡失败","error");
    if(btn){btn.textContent="立即打卡";btn.disabled=false;}
  }
}

async function syncPersonalCenterCheckin(){
  try{
    const data=await apiRequest("/api/points/account");
    const days=data.streak_days??0;
    const pcStreak=document.getElementById("pcStreak");
    if(pcStreak)pcStreak.textContent=days;
    const pcCheckinBtn=document.getElementById("pcCheckinBtn");
    if(pcCheckinBtn){pcCheckinBtn.disabled=true;pcCheckinBtn.textContent="今日已打卡";}
    const pcBalance=document.getElementById("pcBalance");
    if(pcBalance&&data.account)pcBalance.textContent=String(data.account.balance??0).replace(/\B(?=(\d{3})+(?!\d))/g,",");
    const pcTotalEarned=document.getElementById("pcTotalEarned");
    if(pcTotalEarned&&data.account)pcTotalEarned.textContent=String(data.account.total_earned??0).replace(/\B(?=(\d{3})+(?!\d))/g,",");
    if(data)window.__pcLatestOverview=data;
  }catch(e){/* ignore */}
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

async function navigateKnowledgeFromGraph(pointName,subjectName){
 try{
  const overview=await apiRequest("/api/knowledge/overview");
  const subjects=overview.subjects||[];
  const subject=subjects.find(s=>String(s.subject_name)===String(subjectName));
  if(!subject){
   toast("未找到对应科目："+subjectName,"error");
   return;
  }
  window.knSubjectCardsCache=subjects;
  const graph=await apiRequest(`/api/knowledge/subject/${subject.subject_id}/graph`);
  const chapters=graph.chapters||[];
  let targetChapter=null;
  for(const ch of chapters){
   if(String(ch.name)===String(pointName)){
    targetChapter=ch;
    break;
   }
   if(ch.children&&ch.children.length){
    for(const child of ch.children){
     if(String(child.name)===String(pointName)){
      window.knDetailActive=true;
      showPage("knowledge");
      await loadKnPointDetail(child.id);
      return;
     }
    }
   }
  }
  if(targetChapter){
   const children=targetChapter.children||[];
   const firstPoint=children[0];
   window.knDetailActive=true;
   showPage("knowledge");
   if(firstPoint){
    await loadKnPointDetail(firstPoint.id);
   }else{
    toast("该章节暂无知识点","info");
   }
  }else{
   window.knDetailActive=false;
   showPage("knowledge");
   loadDefaultSubjectDetail(subject.subject_id,subjects);
   toast("未找到精确匹配的知识点，已跳转到知识导航首页");
  }
 }catch(e){
  console.error(e);
  toast("跳转失败："+e.message,"error");
 }
}

function bindHomeGraphControls(){
 const structure=document.getElementById("structureLayer"),mastery=document.getElementById("masteryLayer"),note=document.getElementById("layerNote");
 if(structure)structure.onclick=()=>{structure.classList.add("active");mastery?.classList.remove("active");document.querySelectorAll(".kg-node").forEach(node=>node.classList.remove("show-status"));if(note)note.textContent="当前展示完整知识结构，状态颜色已保留为淡色提示";};
 if(mastery)mastery.onclick=()=>{mastery.classList.add("active");structure?.classList.remove("active");document.querySelectorAll(".kg-node").forEach(node=>node.classList.add("show-status"));if(note)note.textContent="已叠加个人掌握状态：灰=未学，绿=掌握，黄=不熟，橙=不会，红=薄弱点";};
 document.querySelectorAll("[data-graph-filter]").forEach(button=>button.onclick=()=>{document.querySelectorAll("[data-graph-filter]").forEach(x=>x.classList.toggle("active",x===button));const filter=button.dataset.graphFilter,canvas=document.getElementById("knowledgeGraphCanvas");canvas.classList.toggle("single-view",filter!=="all");document.querySelectorAll("[data-graph-group]").forEach(group=>group.classList.toggle("hidden",filter!=="all"&&group.dataset.graphGroup!==filter));if(note)note.textContent=filter==="all"?"当前展示四科完整知识结构":`当前聚焦：${filter}`;});
 document.querySelectorAll("#knowledgeGraphCanvas .kg-node").forEach(node=>{
  node.addEventListener("click",()=>{
   const name=node.querySelector("span")?.textContent||"";
   const subject=node.dataset.subject||"";
   if(name&&subject){
    navigateKnowledgeFromGraph(name,subject);
   }
  });
 });
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
  if(subtitle&&["qa","question","mistake","forum","report"].some(id=>document.getElementById(id)?.classList.contains("active")))subtitle.textContent=`距离 408 初试还有 ${days} 天`;
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
  if(tag)tag.textContent=(stats.total||0)>0?"加强巩固":"暂无数据";
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
 const toolbar=document.querySelector("#mistake .book-toolbar");
 if(toolbar)toolbar.style.display=name==="ocr"?"none":"";
 const titles={
   overview:["我的题本","智能出题、错因确认和 OCR 导入中标记“不熟/不会”的题目会进入对应题本"],
   unfamiliar:["不熟题本","理解不稳定的题目，集中做同类巩固"],
   unknown:["不会题本","尚未掌握的题目，优先重新学习与练习"],
   ocr:["",""]
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
  refreshAfterAnswer().catch(console.error);
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
  button.innerHTML=wasLiked?'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3m7-2V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14Z"/></svg>':'<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3m7-2V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14Z"/></svg>';  updateForumPostCounts(post,{like_count:data.like_count});
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
  // 评论也会让首页"论坛活跃度"等统计变化
  refreshAfterAnswer("forum").catch(console.error);
 }catch(err){
  toast(err.message||"评论发布失败","error");
 }
}

/* ========= 学习报告真实数据对接 ========= */
reportHTML=function(){
 return `<section class="page" id="report"><div class="stats" id="reportStats"><div class="card stat"><small>答题总数</small><strong>--</strong></div><div class="card stat"><small>答对</small><strong>--</strong></div><div class="card stat"><small>答错</small><strong>--</strong></div><div class="card stat"><small>正确率</small><strong>--</strong></div></div><div class="report-grid report-main-grid"><article class="card report-main-card"><div class="head"><h3>四科掌握趋势</h3></div><div class="chart" id="reportSubjectTrend"><div class="home-empty-state">正在读取四科掌握趋势...</div></div></article><article class="card report-plan-card"><div class="head"><h3>下一轮个性化训练计划</h3><button class="primary" id="exportReport">导出报告</button></div><div id="reportPlanList"><div class="home-empty-state">正在计算下一轮训练计划...</div></div></article></div><div class="report-section-title"><div><h2>学习画像</h2><p>基于答题、错题、问答、论坛与长期记忆生成</p></div></div><div class="learning-profile-grid"><article class="card learning-user-card" id="reportProfile"><div class="profile-avatar">--</div><h3>读取中</h3><p>正在同步后端学习画像</p><div></div></article><article class="card learning-memory-card"><div class="head"><h3>长期记忆权重</h3></div><div id="reportMemoryWeights"><div class="home-empty-state">正在读取长期记忆权重...</div></div></article></div></section>`;
};

async function loadReportOverview(){
 const report=document.getElementById("report");
 if(!report)return;
 try{
  const data=await apiRequest("/api/reports/overview");
  reportCache=data;
  reportCacheAt=Date.now();
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
 if(exportButton)exportButton.onclick=showExportModal;
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
  return `<div class="weight-row"><span class="weight-label">${escapeHtml(String(item.knowledge_point))}</span><div class="weight-track"><span style="width:${width}%"></span></div><b>${escapeHtml(String(item.weight))}</b><small>${escapeHtml(String(item.status||""))}</small></div>`;
 }).join("");
}

function showExportModal(){
 const old=document.getElementById("exportModal");
 if(old)old.remove();
 document.body.insertAdjacentHTML("beforeend",`
  <div class="export-modal-mask" id="exportModal">
   <div class="export-modal-card">
    <button class="export-modal-close" id="exportModalClose">×</button>
    <h3>选择导出格式</h3>
    <div class="export-modal-actions">
     <button class="export-btn export-pdf" id="exportPDFBtn">📄 导出为 PDF</button>
     <button class="export-btn export-word" id="exportWordBtn">📝 导出为 Word</button>
    </div>
   </div>
  </div>`);
 const mask=document.getElementById("exportModal");
 requestAnimationFrame(()=>mask.classList.add("show"));
 document.getElementById("exportModalClose").onclick=()=>{mask.classList.remove("show");setTimeout(()=>mask.remove(),300)};
 mask.addEventListener("click",e=>{if(e.target===mask){mask.classList.remove("show");setTimeout(()=>mask.remove(),300)}});
 document.getElementById("exportPDFBtn").onclick=()=>{mask.classList.remove("show");setTimeout(()=>mask.remove(),300);exportLearningReport("pdf")};
 document.getElementById("exportWordBtn").onclick=()=>{mask.classList.remove("show");setTimeout(()=>mask.remove(),300);exportLearningReport("word")};
}

async function exportLearningReport(format){
 const button=document.getElementById("exportReport");
 if(button)button.disabled=true;
 showProgressBar("生成学习报告...","report-export");
 try{
  toast("正在调用报告 Agent 生成分析...","success");
  updateProgressBar("report-export",20,"生成报告内容...");
  const report=await apiRequest("/api/reports/generate",{method:"POST"});
  updateProgressBar("report-export",50,"报告生成完成，正在导出文件...");
  const title=report.title||"Turing 408 学习报告";
  const date=report.create_time||new Date().toISOString();
  const source=report.llm_used?"AI 大模型分析":"后端保底分析";
  const sections=[
   ["阶段总结",report.summary||"暂无总结"],
   ["薄弱知识点",report.weak_points||"暂无明显薄弱点"],
   ["主要错误类型",report.main_error_type||"暂无"],
   ["问答关注",report.qa_focus||"暂无"],
   ["论坛关注",report.forum_focus||"暂无"],
   ["视频建议",report.video_suggestion||"暂无"],
  ];
  const plan=(report.plan||[]).map((item,i)=>`${i+1}. ${item}`);
  const memories=(report.memories||[]).map(item=>`- ${item.knowledge_point||"知识点"}：${item.content||""}`);
  if(format==="pdf"){
   await exportPDF(title,date,source,sections,plan,memories,"report-export");
  }else if(format==="word"){
   await exportWord(title,date,source,sections,plan,memories);
  }
  completeProgressBar("report-export","学习报告已导出");
  toast("学习报告已导出","success");
  await loadReportOverview();
 }catch(error){
  console.error(error);
  errorProgressBar("report-export",error.message||"报告导出失败");
  toast(error.message||"报告导出失败","error");
 }finally{
  if(button)button.disabled=false;
 }
}

async function exportPDF(title,date,source,sections,plan,memories,progressId){
 if(progressId)updateProgressBar(progressId,60,"加载 PDF 依赖...");
 await loadScript("https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js");
 const {jsPDF}=await loadJSPDF();
 if(progressId)updateProgressBar(progressId,75,"渲染 PDF 内容...");
 const doc=new jsPDF("p","mm","a4");
 const esc=str=>String(str).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
 const planHtml=plan.length?`<h2 style="font-size:14pt;color:#2f6bff;border-bottom:2px solid #2f6bff;padding-bottom:4px;margin-top:16px">下一轮训练计划</h2><ol>${plan.map(p=>`<li style="margin:4px 0">${esc(p)}</li>`).join("")}</ol>`:"";
 const memHtml=memories.length?`<h2 style="font-size:14pt;color:#2f6bff;border-bottom:2px solid #2f6bff;padding-bottom:4px;margin-top:16px">长期记忆摘要</h2><ul>${memories.map(m=>`<li style="margin:4px 0">${esc(m)}</li>`).join("")}</ul>`:"";
 const secHtml=sections.map(([s,c])=>`<h2 style="font-size:14pt;color:#2f6bff;border-bottom:2px solid #2f6bff;padding-bottom:4px;margin-top:16px">${esc(s)}</h2><p style="line-height:1.8;font-size:11pt">${esc(c)}</p>`).join("");
 const html=`<div style="font-family:'Songti SC','SimSun',serif;padding:30px;max-width:800px;margin:auto;color:#333"><h1 style="text-align:center;font-size:18pt;margin-bottom:4px">${esc(title)}</h1><p style="text-align:center;color:#666;font-size:9pt;margin:2px 0">生成时间：${esc(date)}<br>分析来源：${esc(source)}</p><hr style="border:none;border-top:1px solid #ddd;margin:16px 0">${secHtml}${planHtml}${memHtml}</div>`;
 const wrap=document.createElement("div");
 wrap.innerHTML=html;
 wrap.style.cssText="position:fixed;left:0;top:0;z-index:-1;width:800px;background:#fff";
 document.body.appendChild(wrap);
 try{
  const canvas=await html2canvas(wrap.firstElementChild,{scale:2,useCORS:true,logging:false});
  if(progressId)updateProgressBar(progressId,90,"生成 PDF 文件...");
  const imgData=canvas.toDataURL("image/png");
  const imgWidth=190;
  const pageHeight=277;
  const imgHeight=(canvas.height*imgWidth)/canvas.width;
  let heightLeft=imgHeight;
  let position=0;
  doc.addImage(imgData,"PNG",10,10,imgWidth,imgHeight);
  heightLeft-=pageHeight;
  while(heightLeft>=0){
   position=heightLeft-imgHeight;
   doc.addPage();
   doc.addImage(imgData,"PNG",10,position,imgWidth,imgHeight);
   heightLeft-=pageHeight;
  }
  doc.save(`Turing408学习报告-${date.slice(0,10)}.pdf`);
  if(progressId)updateProgressBar(progressId,99,"保存文件...");
 }finally{document.body.removeChild(wrap)}
}

async function exportWord(title,date,source,sections,plan,memories){
 const esc=str=>String(str).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
 const rows=sections.map(([s,c])=>`<tr><td style="font-weight:700;padding:6px 10px;border:1px solid #ccc;background:#f0f4ff">${esc(s)}</td><td style="padding:6px 10px;border:1px solid #ccc">${esc(c)}</td></tr>`).join("");
 const planHtml=plan.length?`<h3>下一轮训练计划</h3><ol>${plan.map(p=>`<li>${esc(p)}</li>`).join("")}</ol>`:"";
 const memHtml=memories.length?`<h3>长期记忆摘要</h3><ul>${memories.map(m=>`<li>${esc(m)}</li>`).join("")}</ul>`:"";
 const html=`<!DOCTYPE html><html><head><meta charset="utf-8"><title>${esc(title)}</title><style>body{font-family:SimSun,serif;font-size:12pt;line-height:1.8;padding:30px}h1{text-align:center;font-size:18pt}h2{font-size:14pt;color:#2f6bff;border-bottom:2px solid #2f6bff;padding-bottom:4px}table{width:100%;border-collapse:collapse;margin:12px 0}td{font-size:11pt}</style></head><body><h1>${esc(title)}</h1><p style="text-align:center;color:#666">生成时间：${esc(date)}<br>分析来源：${esc(source)}</p><hr>${sections.map(([s,c])=>`<h2>${esc(s)}</h2><p>${esc(c)}</p>`).join("")}${planHtml}${memHtml}</body></html>`;
 const blob=new Blob(["\ufeff"+html],{type:"application/msword;charset=utf-8"});
 const url=URL.createObjectURL(blob);
 const a=document.createElement("a");
 a.href=url;
 a.download=`Turing408学习报告-${date.slice(0,10)}.doc`;
 document.body.appendChild(a);a.click();a.remove();
 setTimeout(()=>URL.revokeObjectURL(url),1000);
}

async function loadJSPDF(){
 if(typeof jspdf!=="undefined"&&jspdf.jsPDF)return {jsPDF:jspdf.jsPDF};
 await loadScript("https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js");
 return new Promise((resolve,reject)=>{
  const s=document.createElement("script");
  s.src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js";
  s.onload=()=>resolve({jsPDF:window.jspdf.jsPDF});
  s.onerror=()=>reject(new Error("加载 jspdf 失败，请检查网络"));
  document.head.appendChild(s);
 });
}
function loadScript(src){
 return new Promise((resolve,reject)=>{
  if(document.querySelector(`script[src="${src}"]`))return resolve();
  const s=document.createElement("script");
  s.src=src;
  s.onload=resolve;
  s.onerror=()=>reject(new Error(`加载 ${src} 失败`));
  document.head.appendChild(s);
 });
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
 // 智能刷新:进入关键页时,如果距上次答题/刷新已经过期,静默重拉
 const now=Date.now();
 const staleAnswer=lastAnswerAt&&(now-lastAnswerAt)<10*60*1000; // 10 分钟内答过题
 if(id==="report"){
  if(staleAnswer||(now-(reportCacheAt||0))>2*60*1000){
   loadReportOverview();
   reportCacheAt=now;
  }
 }else if(id==="home"){
  if(staleAnswer||!currentHomeOverview){
   loadHomeOverview();
  }
  stopForumPolling();
 }else if(id==="knowledge"){
  // 详情页打开时,如果距上次答题在窗口内,重拉详情(掌握度/相关错题)
  if(window.knDetailActive&&window.currentKnowledgePointId&&staleAnswer){
   loadKnPointDetail(window.currentKnowledgePointId);
  }
  stopForumPolling();
 }else if(id==="mistake"){
  if(staleAnswer||!notebookCache){
   loadMistakeNotebook();
  }
  stopForumPolling();
 }else if(id==="forum"){
  // 论坛页进入:如果数据可能过期,先重拉一次(保持 lastSeenForumVersion 同步)
  if(forumDataVersion!==lastSeenForumVersion){
   loadForumPosts(getActiveForumCategory(),getForumSearchKeyword(),{silent:!!document.getElementById("forumFeed")?.querySelector(".forum-post")});
   loadHotTopics();
   loadCheckinStatus();
  }
  startForumPolling();
 }else{
  // 离开论坛页时停止轮询
  stopForumPolling();
 }
};

/* ========= 408 知识图谱：总览二级环形结构 + 单科三层结构 ========= */
let knowledgeOverviewCache=null;
let knowledgeOverviewCacheAt=0;   // 缓存时间戳(ms)
let knowledgeOverviewInflight=null; // 进行中的请求 Promise(去重)
const KNOWLEDGE_OVERVIEW_TTL=5*60*1000; // 5 分钟内存缓存
let activeSubjectGraph=null;

renderHomeGraph=function(){
 // 旧版 home overview 内的 knowledge_graph 是 dict 格式,新版 overview 接口返回 array 格式,
 // 两种数据结构不同,不能直接复用。这里统一走独立接口(命中 5 分钟内存缓存)。
 loadKnowledgeOverviewGraph();
};

async function loadKnowledgeOverviewGraph(force=false){
 // 1. 命中缓存且未过期 -> 直接渲染
 if(!force&&knowledgeOverviewCache&&Date.now()-knowledgeOverviewCacheAt<KNOWLEDGE_OVERVIEW_TTL){
  renderKnowledgeOverview(knowledgeOverviewCache);
  return knowledgeOverviewCache;
 }
 // 2. 正在请求中 -> 复用 in-flight Promise,避免重复触发
 if(knowledgeOverviewInflight){
  return knowledgeOverviewInflight;
 }
 const canvas=document.getElementById("knowledgeGraphCanvas");
 if(canvas)canvas.innerHTML=`<div class="home-empty-state">正在加载 408 知识图谱...</div>`;
 knowledgeOverviewInflight=(async()=>{
  try{
   const data=await apiRequest("/api/knowledge/overview");
   knowledgeOverviewCache=data;
   knowledgeOverviewCacheAt=Date.now();
   renderKnowledgeOverview(data);
   return data;
  }catch(error){
   console.error(error);
   const liveCanvas=document.getElementById("knowledgeGraphCanvas");
   if(liveCanvas)liveCanvas.innerHTML=`<div class="home-empty-state">知识图谱加载失败：${escapeHtml(error.message)}</div>`;
   return null;
  }finally{
   knowledgeOverviewInflight=null;
  }
 })();
 return knowledgeOverviewInflight;
}

function statusPalette(status){
 return {
  mastered:"#2fbf7a",
  unfamiliar:"#f5bd22",
  unknown:"#ff9f43",
  weak:"#ff6262",
  unlearned:"#a8b0bf"
 }[status]||"#a8b0bf";
}

function statusLabel(status){
 return {
  mastered:"掌握",
  unfamiliar:"不熟",
  unknown:"不会",
  weak:"薄弱点",
  unlearned:"未学"
 }[status]||"未学";
}

function ringStyle(percent,color){
 const safe=Math.max(0,Math.min(100,Number(percent)||0));
 return `background:conic-gradient(${color} ${safe}%, #dfe8f7 0)`;
}

function polarPoint(cx,cy,r,angleDeg){
 const angle=(angleDeg-90)*Math.PI/180;
 return {x:cx+r*Math.cos(angle),y:cy+r*Math.sin(angle)};
}

function renderKnowledgeTabs(subjects,active="overview"){
 const tabs=document.getElementById("kgTabs");
 if(!tabs)return;
 tabs.innerHTML=`<button class="${active==="overview"?"active":""}" data-kg-overview>总览</button>${subjects.map(item=>`<button class="${String(item.subject_id)===String(active)?"active":""}" data-kg-subject="${item.subject_id}">${escapeHtml(item.subject_name)}</button>`).join("")}`;
 tabs.querySelector("[data-kg-overview]")?.addEventListener("click",()=>renderKnowledgeOverview(knowledgeOverviewCache));
 tabs.querySelectorAll("[data-kg-subject]").forEach(button=>{
  button.addEventListener("click",()=>loadSubjectGraph(button.dataset.kgSubject));
 });
}

function renderKnowledgeOverview(data){
 const activePage=document.querySelector(".page.active")||document;
 const canvas=activePage.querySelector("#knowledgeGraphCanvas"),legend=activePage.querySelector("#kgLegend");
 if(!canvas||!data?.subjects)return;
 const toolbar=activePage.querySelector(".knowledge-graph-card .kg-toolbar");
 if(toolbar){
  const h3=toolbar.querySelector("h3"),p=toolbar.querySelector("p");
  if(h3)h3.textContent="408 全局知识图谱 - 分科目知识结构总览";
  if(p)p.textContent="";
 }
 renderKnowledgeTabs(data.subjects,"overview");
 canvas.className="kg-canvas kg-overview-canvas";
 canvas.innerHTML=`<div class="kg-overview-grid">${data.subjects.map(subjectOverviewCardHTML).join("")}</div>`;
 if(legend)legend.innerHTML=masteryLegendHTML(true);
 bindKnowledgeGraphInteractions();
}

function subjectOverviewCardHTML(subject){
 const color=subject.style?.color||statusPalette(subject.status);
 const chapters=(subject.chapters||[]).slice(0,10);
 const positions=chapters.map((_,i)=>polarPoint(50,50,35,i*360/Math.max(chapters.length,1)));
 return `<section class="kg-overview-card" style="--subject-color:${color}" data-subject-card="${subject.subject_id}">
  <div class="kg-overview-title">${escapeHtml(subject.subject_name)}</div>
  <div class="kg-overview-stats">
   <div class="mini-ring" style="${ringStyle(subject.mastery_percent,color)}"><span>${subject.mastery_percent}%</span></div>
   <dl>
    <div><dt>总体掌握度</dt><dd>${subject.mastery_percent}%</dd></div>
    <div><dt>二级章节</dt><dd>${subject.chapter_count} 个</dd></div>
    <div><dt>三级知识点</dt><dd>${subject.knowledge_count} 个</dd></div>
    <div><dt>已学习</dt><dd>${subject.learned_count} 个</dd></div>
   </dl>
   <div class="kg-distribution">${distributionBarHTML(subject.status_distribution_percent||{})}</div>
  </div>
  <div class="kg-overview-orbit">
   <button class="kg-subject-ring" data-open-subject="${subject.subject_id}" style="${ringStyle(subject.mastery_percent,color)}"><b>${escapeHtml(subject.subject_name)}</b><span>${subject.mastery_percent}%</span></button>
   <svg class="kg-overview-lines" viewBox="0 0 100 100">${positions.map(p=>`<line x1="50" y1="50" x2="${p.x}" y2="${p.y}"></line>`).join("")}</svg>
   ${chapters.map((chapter,i)=>chapterOverviewNodeHTML(chapter,positions[i],subject.subject_id)).join("")}
  </div>
 </section>`;
}

function chapterOverviewNodeHTML(chapter,pos,subjectId){
 const color=chapter.style?.color||statusPalette(chapter.status);
 return `<button class="kg-chapter-ring" data-open-chapter="${chapter.chapter_id}" data-subject-id="${subjectId}" style="left:${pos.x}%;top:${pos.y}%;${ringStyle(chapter.mastery_percent,color)}" title="${escapeHtml(chapter.chapter_name)}：${chapter.mastery_percent}%">
  <b>${escapeHtml(chapter.chapter_name)}</b><span>${chapter.mastery_percent}%</span>
 </button>`;
}

function distributionBarHTML(distribution){
 const keys=["mastered","unfamiliar","unknown","weak","unlearned"];
 return `<div class="kg-dist-track">${keys.map(key=>`<i style="width:${Number(distribution[key]||0)}%;background:${statusPalette(key)}"></i>`).join("")}</div>`;
}

function masteryLegendHTML(includeLevels=false){
 // 与后端 mastery_service._score_to_status 严格对齐：≥80 掌握 / ≥50 不熟 / ≥20 不会 / >0 薄弱点 / 0 未学
 const statusItems=[
  ["mastered","掌握（≥80 分）"],
  ["unfamiliar","不熟（50~79 分）"],
  ["unknown","不会（20~49 分）"],
  ["weak","薄弱点（1~19 分）"],
  ["unlearned","未学（0 分）"]
 ];
 const levelItems=includeLevels?`<span><i class="level-subject"></i>一级科目</span><span><i class="level-chapter"></i>二级章节</span>`:`<span><i class="level-subject"></i>一级科目</span><span><i class="level-chapter"></i>二级章节</span><span><i class="level-point"></i>三级知识点</span>`;
 return `${levelItems}${statusItems.map(([key,label])=>`<span><i style="background:${statusPalette(key)}"></i>${label}</span>`).join("")}`;
}

async function loadSubjectGraph(subjectId){
 const canvas=document.getElementById("knowledgeGraphCanvas");
 if(canvas)canvas.innerHTML=`<div class="home-empty-state">正在加载单科三层知识图谱...</div>`;
 try{
  const data=await apiRequest(`/api/knowledge/subject/${subjectId}/graph`);
  activeSubjectGraph=data;
  renderSubjectGraph(data);
 }catch(error){
  console.error(error);
  if(canvas)canvas.innerHTML=`<div class="home-empty-state">单科图谱加载失败：${escapeHtml(error.message)}</div>`;
 }
}

function renderSubjectGraph(data){
 const canvas=document.getElementById("knowledgeGraphCanvas"),legend=document.getElementById("kgLegend");
 if(!canvas||!data?.subject)return;
 const toolbar=document.querySelector(".knowledge-graph-card .kg-toolbar");
 if(toolbar){
  const h3=toolbar.querySelector("h3"),p=toolbar.querySelector("p");
  if(h3)h3.textContent=`408 知识图谱 - ${data.subject.name}`;
  if(p)p.textContent="";
 }
 renderKnowledgeTabs(knowledgeOverviewCache?.subjects||[] ,String(data.subject.id));
 canvas.className="kg-canvas kg-subject-canvas";
 canvas.innerHTML=`<div class="kg-subject-layout">
  ${subjectStatsPanelHTML(data)}
  ${threeLevelGraphHTML(data)}
  <aside class="kg-detail-panel" id="kgDetailPanel">${subjectDetailHTML(data)}</aside>
 </div>`;
 if(legend)legend.innerHTML=masteryLegendHTML(false);
 bindKnowledgeGraphInteractions();
}

function subjectStatsPanelHTML(data){
 const subject=data.subject;
 return `<aside class="kg-side-panel">
  <button class="kg-back" data-kg-back>返回总览</button>
  <h3>${escapeHtml(subject.name)}</h3>
  <div class="kg-big-stat"><strong>${subject.mastery_percent}%</strong><span>总体掌握度</span></div>
  <div class="kg-side-metrics">
   <div><b>${subject.chapter_count}</b><span>二级章节</span></div>
   <div><b>${subject.knowledge_count}</b><span>三级知识点</span></div>
   <div><b>${subject.learned_count}</b><span>已学习</span></div>
  </div>
  <h4>二级章节掌握度</h4>
  <div class="kg-chapter-list">${(data.chapters||[]).map(chapter=>`<button data-select-chapter="${chapter.id}" data-subject-id="${subject.id||data.subject?.subject_id||""}"><span>${escapeHtml(chapter.name)}</span><b>${chapter.mastery_percent}%</b></button>`).join("")}</div>
 </aside>`;
}

function threeLevelGraphHTML(data){
 const subject=data.subject;
 const subjectColor=subject.style?.color||statusPalette(subject.status);
 const chapters=data.chapters||[];
 const center={x:50,y:50};
 const chapterRadius=30;
 const chapterPositions=chapters.map((_,i)=>polarPoint(center.x,center.y,chapterRadius,i*360/Math.max(chapters.length,1)));
 const lines=chapters.map((chapter,i)=>{
  const chapterPos=chapterPositions[i];
  const childLines=(chapter.children||[]).map((_,childIndex)=>{
   const childPos=childPointPosition(i,chapters.length,childIndex,chapter.children.length);
   return `<line class="kg-line-point" x1="${chapterPos.x}" y1="${chapterPos.y}" x2="${childPos.x}" y2="${childPos.y}"></line>`;
  }).join("");
  return `<line class="kg-line-chapter" x1="${center.x}" y1="${center.y}" x2="${chapterPos.x}" y2="${chapterPos.y}"></line>${childLines}`;
 }).join("");
 const childNodes=chapters.map((chapter,chapterIndex)=>(chapter.children||[]).map((point,pointIndex)=>{
  const pos=childPointPosition(chapterIndex,chapters.length,pointIndex,chapter.children.length);
  return knowledgePointDotHTML(point,pos,chapter.id,subject.id);
 }).join("")).join("");
 return `<main class="kg-graph-stage">
  <svg class="kg-three-lines" viewBox="0 0 100 100">${lines}</svg>
  <button class="kg-subject-center" data-select-subject style="${ringStyle(subject.mastery_percent,subjectColor)}"><b>${escapeHtml(subject.name)}</b><small>总体掌握度</small><span>${subject.mastery_percent}%</span></button>
  ${chapters.map((chapter,i)=>chapterRingNodeHTML(chapter,chapterPositions[i],subject.id)).join("")}
  ${childNodes}
 </main>`;
}

function childPointPosition(chapterIndex,chapterCount,pointIndex,pointCount){
 const base=chapterIndex*360/Math.max(chapterCount,1);
 const spread=Math.min(34,8+pointCount*2.8);
 const offset=pointCount<=1?0:-spread/2+(spread*pointIndex/Math.max(pointCount-1,1));
 const radius=43+Math.min(10,Math.floor(pointIndex/5)*3);
 return polarPoint(50,50,radius,base+offset);
}

function chapterRingNodeHTML(chapter,pos,subjectId){
 const color=chapter.style?.color||statusPalette(chapter.status);
 return `<button class="kg-chapter-node" data-select-chapter="${chapter.id}" data-subject-id="${subjectId}" style="left:${pos.x}%;top:${pos.y}%;${ringStyle(chapter.mastery_percent,color)}" title="${escapeHtml(chapter.name)}：${chapter.mastery_percent}%">
  <b>${escapeHtml(chapter.name)}</b><span>${chapter.mastery_percent}%</span>
 </button>`;
}

function knowledgePointDotHTML(point,pos,chapterId,subjectId){
 const color=point.style?.color||statusPalette(point.status);
 return `<button class="kg-point-node" data-select-point="${point.id}" data-parent-chapter="${chapterId}" data-subject-id="${subjectId}" style="left:${pos.x}%;top:${pos.y}%;--point-color:${color}" title="${escapeHtml(point.name)}：${escapeHtml(point.status_label||statusLabel(point.status))}">
  <i></i><span>${escapeHtml(point.name)}</span>
 </button>`;
}

function subjectDetailHTML(data){
 const subject=data.subject;
 const weak=(data.weak_chapters||[]).map(item=>`${item.name} ${item.mastery_percent}%`).join("、")||"暂无明显薄弱章节";
 const rec=(data.recommended_chapters||[]).map(item=>`${item.name} ${item.mastery_percent}%`).join("、")||"保持当前节奏";
 return `<h3>${escapeHtml(subject.name)}知识统计</h3>
  <div class="kg-detail-metrics">
   <div><small>总体掌握度</small><b>${subject.mastery_percent}%</b></div>
   <div><small>一级科目</small><b>1 个</b></div>
   <div><small>二级章节</small><b>${subject.chapter_count} 个</b></div>
   <div><small>三级知识点</small><b>${subject.knowledge_count} 个</b></div>
  </div>
  <h4>掌握度分布</h4>
  ${distributionBarHTML(data.status_distribution_percent||{})}
  ${statusDistributionRowsHTML(data.status_distribution_percent||{})}
  <h4>学习建议</h4>
  <div class="kg-advice">
   <p><b>薄弱章节 Top3</b><span>${escapeHtml(weak)}</span></p>
   <p><b>推荐优先学习</b><span>${escapeHtml(rec)}</span></p>
   </div>`;
}

function statusDistributionRowsHTML(){
 const items=[["mastered","掌握（≥80 分）"],["unfamiliar","不熟（50~79 分）"],["unknown","不会（20~49 分）"],["weak","薄弱点（1~19 分）"],["unlearned","未学（0 分）"]];
 return `<div class="kg-status-rows">${items.map(([key,label])=>`<div><i style="background:${statusPalette(key)}"></i><span>${label}</span></div>`).join("")}</div>`;
}

function pointDetailHTML(point){
 return `<h3>${escapeHtml(point.name)}</h3>
  <div class="kg-point-badge" style="--point-color:${point.style?.color||statusPalette(point.status)}">${escapeHtml(point.status_label||statusLabel(point.status))}</div>
  <div class="kg-detail-metrics">
   <div><small>所属科目</small><b>${escapeHtml(point.subject_name||"")}</b></div>
   <div><small>所属章节</small><b>${escapeHtml(point.chapter_name||"")}</b></div>
  </div>
  <h4>知识点解释</h4><p>${escapeHtml(point.content||"暂无解释内容")}</p>
  <h4>常见考法 / 易错点</h4><p>${escapeHtml(_cleanBrackets(point.common_mistakes||point.keywords||"暂无补充说明"))}</p>
  <div class="kg-detail-actions"><button class="primary" onclick="showPage('question')">开始专项训练</button><button class="ghost" onclick="showPage('mistake')">查看相关错题</button></div>`;
}

function bindKnowledgeGraphInteractions(){
 document.querySelectorAll("[data-open-subject]").forEach(button=>button.onclick=()=>loadSubjectGraph(button.dataset.openSubject));
 // 二级章节:跳到知识导航页对应章节(自动展开到第一节)
 document.querySelectorAll("[data-open-chapter]").forEach(button=>button.onclick=()=>navigateKnChapter(Number(button.dataset.subjectId),Number(button.dataset.openChapter)));
 document.querySelector("[data-kg-back]")?.addEventListener("click",()=>renderKnowledgeOverview(knowledgeOverviewCache));
 document.querySelector("[data-select-subject]")?.addEventListener("click",()=>showSubjectDetail());
 // 二级章节:跳到知识导航页对应章节(自动展开到第一节)
 document.querySelectorAll("[data-select-chapter]").forEach(button=>button.onclick=()=>navigateKnChapter(Number(button.dataset.subjectId),Number(button.dataset.selectChapter)));
 // 三级知识点:跳到知识导航页对应知识点
 document.querySelectorAll("[data-select-point]").forEach(button=>button.onclick=()=>navigateKnPoint(Number(button.dataset.subjectId),Number(button.dataset.selectPoint)));
}

function showSubjectDetail(){
 const panel=document.getElementById("kgDetailPanel");
 if(panel&&activeSubjectGraph)panel.innerHTML=subjectDetailHTML(activeSubjectGraph);
}

/* ===== 知识图谱 → 知识导航:章节跳转 =====
   策略:
   - 已在知识页:直接调 switchKnSubject,带 targetChapterId 重新渲染 tree
   - 在其他页:设 knPendingNavTarget 后调 showPage,由 loadKnowledgeNavPage 消费
*/
async function navigateKnChapter(subjectId,chapterId){
 if(!subjectId||!chapterId)return;
 const onKnowledge=document.querySelector(".page.active")?.id==="knowledge"&&kpNavActiveSubjectId;
 if(onKnowledge){
  await switchKnSubject(subjectId,{targetChapterId:chapterId});
 }else{
  knPendingNavTarget={subjectId,chapterId,pointId:null};
  showPage("knowledge");
 }
}

/* ===== 知识图谱 → 知识导航:知识点跳转 ===== */
async function navigateKnPoint(subjectId,pointId){
 if(!subjectId||!pointId)return;
 const onKnowledge=document.querySelector(".page.active")?.id==="knowledge"&&kpNavActiveSubjectId;
 if(onKnowledge){
  await switchKnSubject(subjectId,{targetPointId:pointId});
 }else{
  knPendingNavTarget={subjectId,chapterId:null,pointId};
  showPage("knowledge");
 }
}

async function showPointDetail(pointId){
 const panel=document.getElementById("kgDetailPanel");
 if(!panel)return;
 panel.innerHTML=`<div class="home-empty-state">正在加载知识点详情...</div>`;
 try{
  const data=await apiRequest(`/api/knowledge/point/${pointId}`);
  panel.innerHTML=pointDetailHTML(data.point);
 }catch(error){
  panel.innerHTML=`<div class="home-empty-state">知识点详情加载失败：${escapeHtml(error.message)}</div>`;
 }
}

async function loadChapterDetailPage(chapterId){
 try{
  const detail=await apiRequest(`/api/knowledge/chapter/${chapterId}`);
  if(!detail?.chapter){
   toast("章节不存在","error");
   return;
  }
  const children=detail.chapter.children||[];
  const firstPoint=children[0];
  if(!firstPoint){
   toast("该章节暂无知识点","info");
   return;
  }
  window.knDetailActive=true;
  showPage("knowledge");
  await loadKnPointDetail(firstPoint.id);
 }catch(e){
  console.error(e);
  toast("加载失败："+e.message,"error");
 }
}

async function loadKnowledgePointDetailPage(pointId){
 window.knDetailActive=true;
 showPage("knowledge");
 await loadKnPointDetail(pointId);
}

async function renderKnowledgePointDetailPage(point,related,videos,history,mistakes,notes){
 const activePage=document.querySelector(".page.active")||document;
 const canvas=activePage.querySelector("#knowledgeGraphCanvas"),legend=activePage.querySelector("#kgLegend");
 if(!canvas||!point)return;
 window.currentKnowledgePointId=point.id;
 window.currentGraphPointName=point.name||"";
 window.currentGraphPointSubject=point.subject_name||"";
 window.currentKnowledgeVideos=videos;
 window.currentKnowledgeNotes=notes||[];
 const graph=await apiRequest(`/api/knowledge/subject/${point.subject_id}/graph`);
 activeSubjectGraph=graph;
 setKnowledgeToolbar(`408 知识点详情 - ${point.name}`,"三级知识点页整合讲解、视频、练习、错题、笔记、分享和掌握状态更新。");
 canvas.className="kg-canvas kd-canvas";
 canvas.innerHTML=`<div class="kd-layout kd-layout-2col">
  ${knowledgeTreeHTML(graph,null,point.id)}
  <main class="kd-main">
   <div class="kd-breadcrumb"><button data-kg-back>返回知识图谱</button><span>${escapeHtml(point.subject_name)} / ${escapeHtml(point.chapter_name)} / ${escapeHtml(point.name)}</span></div>
   <section class="kd-point-head">
    <div><span class="kd-badge">${escapeHtml(point.status_label||statusLabel(point.status))}</span><h2>${escapeHtml(point.name)}</h2><p>${escapeHtml(point.subject_name)} / ${escapeHtml(point.chapter_name)}</p></div>
    <div class="kd-head-actions"><button class="primary" data-open-note="${point.id}">添加笔记</button><button class="ghost" data-kd-start-practice="${point.id}" data-kd-practice-subject="${point.subject_name}" data-kd-practice-point="${point.name}">开始练习</button></div>
   </section>
   <section class="kd-section"><h3>知识点正文</h3>${knowledgeBodyHTML(point)}</section>
   <section class="kd-section"><h3>相关知识点</h3><div class="kd-related">${related.map(item=>`<button data-kd-point="${item.id}"><b>${escapeHtml(item.name)}</b><span>${escapeHtml(item.status_label)}</span></button>`).join("")||"<p>暂无相关知识点</p>"}</div></section>
   <section class="kd-section kd-tabs-section"><div class="kd-tab-bar"><button class="kd-tab active" data-kd-tab="videos"><span class="kd-tab-icon">▶</span>学习资源</button><button class="kd-tab" data-kd-tab="notes"><span class="kd-tab-icon">📝</span>学习笔记</button></div><div class="kd-tab-content" id="kdTabVideos">${videos.map(videoCardHTML).join("")||"<p>暂无匹配视频资源</p>"}</div><div class="kd-tab-content" id="kdTabNotes" style="display:none"><div class="kd-note-list" id="kdNoteList">${notes.map(noteCardHTML).join("")||"<p>暂无笔记，点击右上角添加。</p>"}</div></div></section>
  </main>
 </div>${noteModalHTML(point)}`;
 if(legend)legend.innerHTML=masteryLegendHTML(false);
 bindKnowledgeDetailInteractions();
}

function setKnowledgeToolbar(title,subtitle){
 const toolbar=document.querySelector(".knowledge-graph-card .kg-toolbar");
 if(!toolbar)return;
 const h3=toolbar.querySelector("h3"),p=toolbar.querySelector("p");
 if(h3)h3.textContent=title;
 if(p)p.textContent=subtitle;
}

function knowledgeTreeHTML(graph,activeChapterId,activePointId){
 const subject=graph.subject;
 return `<aside class="kd-tree"><h3>知识点目录</h3><div class="kd-tree-legend">${["mastered","unfamiliar","unknown","weak","unlearned"].map(k=>`<span><i style="background:${statusPalette(k)}"></i>${statusLabel(k)}</span>`).join("")}</div>
  <button class="kd-tree-subject" data-kg-subject="${subject.id}"><b>${escapeHtml(subject.name)}</b><span>${subject.mastery_percent}%</span></button>
  ${(graph.chapters||[]).map(ch=>`<div class="kd-tree-chapter ${Number(ch.id)===Number(activeChapterId)?"active":""}"><button data-kd-chapter="${ch.id}"><b>${escapeHtml(ch.name)}</b><span>${ch.mastery_percent}%</span></button><div>${(ch.children||[]).map(pt=>`<button class="kd-tree-point ${Number(pt.id)===Number(activePointId)?"active":""}" data-kd-point="${pt.id}"><i style="background:${pt.style?.color||statusPalette(pt.status)}"></i>${escapeHtml(pt.name)}</button>`).join("")}</div></div>`).join("")}
 </aside>`;
}

// 内容型 section 的"防御性"上限：前端再做一次"防历史脏数据"截断,
// 后端 enrich_kp_content.py 已经做了去重截断,这里只是兜底.
const _FRONTEND_SECTION_CHAR_LIMIT = {
  "核心概念": 600,
  "基本概念": 600,
  "概念": 600,
  "定义": 600,
  "易错点": 400,
  "常见错误": 400,
  "误区": 400,
  "408 重点": 400,
  "408高频考点": 400,
  "常见考法": 400,
  "408 常见考法": 400,
  "考法": 400,
  "考点": 400,
  "解题步骤": 800,
  "例题": 800,
  "总结": 400,
  "重点": 400,
};
const _FRONTEND_SECTION_CHAR_LIMIT_DEFAULT = 600;

function _splitSentences(text){
 if(!text)return [];
 return text.split(/(?<=[。！？!?])\s*/).map(s=>s.trim()).filter(Boolean);
}

function _sentenceJaccard(a,b){
 const sa=new Set(a),sb=new Set(b);
 if(!sa.size||!sb.size)return 0;
 const inter=[...sa].filter(c=>sb.has(c)).length;
 const union=new Set([...sa,...sb]).size;
 return inter/union;
}

// 渲染时按 section 标题"防御性"去重同 title 重复
// 历史脏数据可能含 5-7 个同名【核心概念】,这里合并为 1 个并做句级去重
function _mergeAndDedupeSections(sections){
 const order=[]; // 按首次出现顺序保留
 const byTitle=new Map();
 for(const s of sections){
  if(!byTitle.has(s.title)){
   byTitle.set(s.title,{title:s.title,lines:[]});
   order.push(s.title);
  }
  byTitle.get(s.title).lines.push(...s.lines);
 }
 const merged=[];
 for(const title of order){
  const sec=byTitle.get(title);
  const limit=_FRONTEND_SECTION_CHAR_LIMIT[title]||_FRONTEND_SECTION_CHAR_LIMIT_DEFAULT;
  // 句级去重 + 字符数截断
  const seen=[];
  const out=[];
  let total=0;
  for(const raw of sec.lines){
   for(const sent of _splitSentences(raw)){
    if(seen.some(u=>_sentenceJaccard(sent,u)>=0.72))continue;
    if(total+sent.length>limit&&out.length)continue;
    out.push(sent);
    seen.push(sent);
    total+=sent.length;
   }
  }
  if(out.length)merged.push({title,lines:out});
 }
 return merged;
}

// 清理文本中的引号和方括号
function _cleanBrackets(text){
 if(!text)return text;
 return text.replace(/["""'【】\[\]]/g,'').trim();
}

// 将纯文本按内容特征智能分为5个标准分点
// 核心概念, 考试题型, 解题思路, 例题, 易错点
function _autoSplitByParagraphs(contentLines){
 const fullText=contentLines.join("\n").replace(/\n/g," ").trim();
 if(!fullText)return [];
 // 先按句子拆分
 const sentences=_splitSentences(fullText);
 if(sentences.length===0)return [];
 // 按内容特征识别各段的起始句子索引
 const examStartIdx=_findExamStart(sentences);
 const methodStartIdx=_findMethodStart(sentences,examStartIdx);
 const exampleStartIdx=_findExampleStart(sentences,methodStartIdx);
 const errorStartIdx=_findErrorStart(sentences,exampleStartIdx);
 const sections=[
  {title:"核心概念",start:0,end:examStartIdx},
  {title:"考试题型",start:examStartIdx,end:methodStartIdx},
  {title:"解题思路",start:methodStartIdx,end:exampleStartIdx},
  {title:"例题",start:exampleStartIdx,end:errorStartIdx},
  {title:"易错点",start:errorStartIdx,end:sentences.length}
 ];
 const blocks=[];
 for(const sec of sections){
  const secSents=sentences.slice(sec.start,sec.end).filter(Boolean);
  if(secSents.length===0)continue;
  const text=secSents.join("");
  // 对解题思路：按①②③...或数字编号分割成多行
  if(sec.title==="解题思路"){
   const items=_splitStepItems(text);
   blocks.push({type:"section",title:sec.title,lines:items});
  }
  // 对例题：按题目/解答分割
  else if(sec.title==="例题"){
   const items=_splitExampleText(text);
   blocks.push({type:"section",title:sec.title,lines:items});
  }
  // 对考试题型/易错点：按编号分割成列表项
  else if(sec.title==="考试题型"||sec.title==="易错点"){
   const items=_splitNumberedItems(text);
   blocks.push({type:"section",title:sec.title,lines:items});
  }
  else{
   blocks.push({type:"section",title:sec.title,lines:[text]});
  }
 }
 return blocks;
}

// 智能拆分句子（保留句号、问号等句末标点）
function _splitSentences(text){
 if(!text)return [];
 const result=[];
 let current="";
 for(let i=0;i<text.length;i++){
  const ch=text[i];
  current+=ch;
  if(/[。！？!?]/.test(ch)){
   const next=i+1<text.length?text[i+1]:"";
   const next2=i+2<text.length?text[i+2]:"";
   // 句末判断：下一个字符是中文/英文/数字开头的新句子/括号开头
   // 排除 O(n) 这种括号中的情况
   const isNewSentence=next===""||
    /[\u4e00-\u9fa5A-Za-z]/.test(next)||   // 下一个是中/英文字
    /\d/.test(next)&&/[)、.】]/.test(next2); // 下一个是数字+括号/点（如"1)" "2."）
   if(isNewSentence){
    const trimmed=current.trim();
    if(trimmed)result.push(trimmed);
    current="";
   }
  }
 }
 if(current.trim())result.push(current.trim());
 return result;
}

// 查找考试题型段的起始位置
function _findExamStart(sentences){
 for(let i=1;i<sentences.length;i++){
  const s=sentences[i];
  if(/^(1[)、.]|[①1]|选择题|简答题|计算题|应用题|综合题|第\d+题|20\d+年)/.test(s.trim())){
   // 确保前面有足够的概念内容
   if(i>=1)return i;
  }
 }
 // 如果没找到，大约在1/5处
 return Math.max(1,Math.floor(sentences.length*0.2));
}

// 查找解题思路段的起始位置
function _findMethodStart(sentences,afterIdx){
 for(let i=afterIdx;i<sentences.length;i++){
  const s=sentences[i];
  if(/^(判断|明确|分析|解题|步骤|思路|方法|先|首先|第一步|①)/.test(s.trim())){
   if(i>afterIdx)return i;
  }
 }
 return Math.max(afterIdx+1,Math.floor(sentences.length*0.4));
}

// 查找例题段的起始位置
function _findExampleStart(sentences,afterIdx){
 for(let i=afterIdx;i<sentences.length;i++){
  const s=sentences[i];
  if(/^(已知|例[：1]|例如|举例|设有|假设给定)/.test(s.trim())){
   if(i>afterIdx)return i;
  }
 }
 return Math.max(afterIdx+1,Math.floor(sentences.length*0.65));
}

// 查找易错点段的起始位置
function _findErrorStart(sentences,afterIdx){
 for(let i=afterIdx;i<sentences.length;i++){
  const s=sentences[i];
  if(/^(易错|容易|误认为|误区|常见错误|注意|不要|混淆|1[)、.]\s*误认为|①\s*误)/.test(s.trim())){
   if(i>afterIdx)return i;
  }
 }
 return Math.max(afterIdx+1,Math.floor(sentences.length*0.85));
}

// 智能分割列表项：综合编号、分号、句号等多种策略
function _smartSplitListItems(text){
 if(!text)return [];
 const trimmed=text.trim();
 // 策略1：按带圈数字①②③...分割
 const circled=_splitByCircledNumbers(trimmed);
 if(circled.length>1)return circled;
 // 策略2：按 1. 2. 3. 或 1) 2) 3) 或 1、2、3、分割
 // 更宽松：允许编号在文本任意位置，编号后必须跟中文/英文字母
 const numRegex=/(?:^|[；;。，,\s])\d+[.、)】]\s*(?=[\u4e00-\u9fa5A-Za-z（(])/g;
 const numMatches=[...trimmed.matchAll(numRegex)];
 if(numMatches.length>=2){
  const items=[];
  for(let i=0;i<numMatches.length;i++){
   const m=numMatches[i];
   // 从编号开始的位置（跳过前面的分隔符）
   let start=m.index;
   // 如果前面是分隔符，跳过
   const firstChar=trimmed[start];
   if(/[；;。，,\s]/.test(firstChar))start++;
   const end=i+1<numMatches.length?numMatches[i+1].index:trimmed.length;
   let item=trimmed.substring(start,end).trim();
   // 去掉编号前缀
   item=item.replace(/^\d+[.、)】]\s*/,"").trim();
   // 去掉末尾的分号/句号
   item=item.replace(/[；;。]+$/,"").trim();
   if(item)items.push(item);
  }
  if(items.length>=2)return items;
 }
 // 策略3：按分号分割
 const semiItems=trimmed.split(/[；;]/).map(s=>s.trim()).filter(Boolean);
 if(semiItems.length>=2){
  return semiItems.map(s=>s.replace(/[。]+$/,"").trim()).filter(Boolean);
 }
 // 策略4：按句号分割（过滤掉总结句和太短的句子）
 const sentItems=_splitSentences(trimmed).filter(s=>{
  const t=s.trim();
  if(t.length<8)return false;
  // 过滤总结性句子
  if(/^(这些|以上|综上|因此|所以|总之|总的来说|考点侧|主要考|重点考)/.test(t))return false;
  return true;
 });
 if(sentItems.length>=2){
  return sentItems.map(s=>s.replace(/[。]+$/,"").trim()).filter(Boolean);
 }
 return [trimmed];
}

// 解题思路的条目分割
function _splitStepItems(text){
 if(!text)return [];
 // 先尝试按带圈数字
 const circled=_splitByCircledNumbers(text);
 if(circled.length>1)return circled;
 // 用智能分割
 const smart=_smartSplitListItems(text);
 if(smart.length>1)return smart;
 return [text.trim()];
}

// 按①②③...分割文本
function _splitByCircledNumbers(text){
 if(!text)return [];
 // 匹配①②③...⑳等带圈数字
 const regex=/[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]/g;
 const matches=[...text.matchAll(regex)];
 if(matches.length<=1)return [text.trim()];
 const items=[];
 for(let i=0;i<matches.length;i++){
  const start=matches[i].index;
  const end=i+1<matches.length?matches[i+1].index:text.length;
  let item=text.substring(start,end).trim();
  if(item){
   // 去掉开头的带圈数字前缀（列表渲染自带序号）
   item=item.replace(/^[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]/, "").trim();
   if(item)items.push(item);
  }
 }
 return items.length?items:[text.trim()];
}

// 分割例题文本：题目/解答
function _splitExampleText(text){
 if(!text)return [];
 // 尝试按"解："、"解答："、"答案："、"解析："分割（前面可以是任意字符）
 const parts=text.split(/(解：|解答：|答案：|解析：)/);
 if(parts.length>=3){
  const question=parts[0].trim();
  const answer=(parts[1]+parts.slice(2).join("")).trim();
  return [question,answer].filter(Boolean);
 }
 // 如果没有明显分割标记，尝试按"已知"开头的部分作为题目，后面作为解答
 const solveMatch=text.match(/(.+?)(\s*解：.+)/s);
 if(solveMatch){
  return [solveMatch[1].trim(),solveMatch[2].trim()];
 }
 return [text.trim()];
}

function _formatContentText(raw){
 if(!raw)return {keywords:"",blocks:[]};
 const trimmedRaw=raw;
 // 1. 单独抽出"关键词：xxx"行,作为头部 metadata,不进入正文 blocks
 let keywords="";
 const lines=trimmedRaw.split(/\n/);
 const contentLines=[];
 for(const line of lines){
  const m=line.match(/^关键词[：:]\s*(.*)$/);
  if(m){
   keywords=_cleanBrackets(m[1].trim());
   continue;
  }
  contentLines.push(line);
 }
 // 2. 解析为 section 块（保留原始内容，不在此阶段做列表识别）
 const blocks=[];
 let current={type:"paragraph",lines:[]};
 let hasSectionMarkers=false;
 for(const line of contentLines){
  const t=line.trim();
  if(!t){continue;}
  const headerMatch=t.match(/^【([^】]+)】\s*(.*)/);
  if(headerMatch){
   hasSectionMarkers=true;
   if(current.lines.length>0)blocks.push(current);
   current={type:"section",title:headerMatch[1],lines:[]};
   if(headerMatch[2]){
    current.lines.push(headerMatch[2].trim());
   }
  }else{
   current.lines.push(t);
  }
 }
 if(current.lines.length>0)blocks.push(current);

 // 3. 如果没有【】分点标记，则按段落顺序自动分为5个标准分点
 if(!hasSectionMarkers){
  const autoBlocks=_autoSplitByParagraphs(contentLines);
  if(autoBlocks.length>0){
   return {keywords,blocks:autoBlocks};
  }
 }

 // 4. 标题归一化 + 合并同名 section
 const sectionBlocks=blocks.filter(b=>b.type==="section");
 const paragraphBlocks=blocks.filter(b=>b.type!=="section");
 // 先归一化标题，再合并相同标题的内容
 const normalizedMap=new Map();
 for(const sec of sectionBlocks){
  const normTitle=_normalizeSectionTitle(sec.title);
  if(!normalizedMap.has(normTitle)){
   normalizedMap.set(normTitle,{title:normTitle,rawLines:[]});
  }
  normalizedMap.get(normTitle).rawLines.push(...sec.lines);
 }
 // 按标准顺序排列
 const normalizedSections=[];
 const standardOrder=["核心概念","考试题型","解题思路","例题","易错点","重点内容"];
 for(const t of standardOrder){
  if(normalizedMap.has(t)){
   normalizedSections.push(normalizedMap.get(t));
   normalizedMap.delete(t);
  }
 }
 // 剩余的其他 section 追加在后面
 for(const [title,sec] of normalizedMap){
  normalizedSections.push(sec);
 }
 // 5. 对每个 section 做去重 + 内容格式化（全部走智能分割）
 const finalSections=[];
 for(const sec of normalizedSections){
  const stype=_sectionType(sec.title);
  const rawLines=sec.rawLines.filter(x=>x&&x!=="_bullet_start_"&&x!=="_bullet_");
  // 先拼接原始文本（保留原始编号/分号等结构）
  const rawFullText=rawLines.join(" ");
  // 句子级去重（用于核心概念、例题等段落型内容）
  const limit=_FRONTEND_SECTION_CHAR_LIMIT[sec.title]||_FRONTEND_SECTION_CHAR_LIMIT_DEFAULT;
  const seen=[];
  const dedupSents=[];
  let total=0;
  for(const raw of rawLines){
   for(const sent of _splitSentences(raw)){
    if(seen.some(u=>_sentenceJaccard(sent,u)>=0.72))continue;
    if(total+sent.length>limit&&dedupSents.length)continue;
    dedupSents.push(sent);
    seen.push(sent);
    total+=sent.length;
   }
  }
  const dedupFullText=dedupSents.join("");
  // 根据类型选择分割策略
  let formattedLines;
  if(stype==="exam"||stype==="error"||stype==="key"){
   // 考试题型/易错点/重点：优先用原始文本分割（保留编号结构），失败则用去重后文本
   let result=_smartSplitListItems(rawFullText);
   if(result.length<=1&&rawFullText!==dedupFullText){
    result=_smartSplitListItems(dedupFullText);
   }
   formattedLines=result;
  }else if(stype==="steps"){
   // 解题思路
   let result=_splitStepItems(rawFullText);
   if(result.length<=1&&rawFullText!==dedupFullText){
    result=_splitStepItems(dedupFullText);
   }
   formattedLines=result;
  }else if(stype==="example"){
   // 例题
   let result=_splitExampleText(rawFullText);
   if(result.length<=1&&rawFullText!==dedupFullText){
    result=_splitExampleText(dedupFullText);
   }
   formattedLines=result;
  }else{
   // 核心概念等：段落形式，用去重后的句子
   formattedLines=dedupSents;
  }
  if(formattedLines.length>0){
   finalSections.push({type:"section",title:sec.title,lines:formattedLines});
  }
 }
 return {keywords,blocks:[...paragraphBlocks,...finalSections]};
}
// 5 种 block 类型的视觉分类 + 颜色方案
// - core: 核心概念 (蓝/知识主色)
// - exam: 常见考法 (橙/警示)
// - steps: 解题步骤 (绿/行动)
// - example: 例题 (紫/示例)
// - error: 常见错误/易错点 (红/警告)
// - key: 408重点 (靛/重点)
// - default: 其他
function _sectionType(title){
 const t=title||"";
 if(t.includes("核心概念")||t.includes("基本概念")||t==="概念"||t.includes("定义")||t.includes("概述"))return"core";
 if(t.includes("常见考法")||t.includes("考法")||t.includes("考点")||t.includes("考试题型")||t.includes("题型"))return"exam";
 if(t.includes("解题步骤")||t.includes("解题思路")||t.includes("步骤")||t.includes("思路")||t.includes("方法"))return"steps";
 if(t.includes("例题"))return"example";
 if(t.includes("常见错误")||t.includes("易错点")||t.includes("误区"))return"error";
 if(t.includes("408重点")||t.includes("重点")||t.includes("总结"))return"key";
 return"default";
}

// 将各种不同的 section 标题归一化为 5 个标准分点标题
function _normalizeSectionTitle(title){
 const stype=_sectionType(title);
 const titleMap={
  core:"核心概念",
  exam:"考试题型",
  steps:"解题思路",
  example:"例题",
  error:"易错点",
  key:"重点内容"
 };
 return titleMap[stype]||title;
}

// block 标题的图标(用 CSS 绘制的几何符号,避免 emoji 渲染差异)
function _sectionIcon(type){
 return{
  core:"▣",     // 知识方块
  exam:"◎",     // 靶心
  steps:"▸",    // 三角前进
  example:"◇",  // 菱形
  error:"⚠",   // 警告
  key:"★",      // 五角星
  default:"▷",  // 三角箭头
 }[type]||"▷";
}

// 关键术语高亮: 把"X（Y）"或中文加括号、英语术语、引号短语等识别为术语, 加 mark
function _highlightKeyTerms(text){
 if(!text)return"";
 let html=escapeHtml(text);
 // 1) 双引号包起来的术语
 html=html.replace(/&quot;([^&]{2,15})&quot;/g,'<mark class="kd-term">$1</mark>');
 // 2) 英文术语 (只在全大写或全小写时识别,避免误伤中文)
 html=html.replace(/\b([A-Z][A-Za-z]{1,8}(?:\([A-Z]+\))?)\b/g,function(m,w){
  if(/^[\u4e00-\u9fa5]/.test(w))return m;
  return'<mark class="kd-term">'+w+'</mark>';
 });
 return html;
}

// toggle 折叠: 兼容 .kd-block 与旧 .kd-accordion
function toggleKdAccordion(headEl){
 const card=headEl.parentElement;
 if(!card)return;
 card.classList.toggle("open");
}

function _renderContentBlocks(blocks){
 if(!blocks||blocks.length===0)return "";
 return blocks.map((block,idx)=>{
  if(block.type==="section"){
   const type=_sectionType(block.title);
   const icon=_sectionIcon(type);
   // 内容渲染：根据类型选择不同的展示方式
   let bodyHtml="";
   if(type==="example"){
    // 例题：题目 + 解答 分行显示
    const lines=block.lines.filter(l=>l&&l!=="_bullet_start_"&&!l.startsWith("_bullet_"));
    if(lines.length>=2){
     bodyHtml=`
      <div class="kd-example-item">
       <div class="kd-example-label">题目</div>
       <div class="kd-example-question">${_highlightKeyTerms(lines[0])}</div>
      </div>
      <div class="kd-example-item">
       <div class="kd-example-label">解答</div>
       <div class="kd-example-answer">${_highlightKeyTerms(lines.slice(1).join(""))}</div>
      </div>`;
    }else{
     bodyHtml=`<p class="kd-block-line">${_highlightKeyTerms(lines.join(""))}</p>`;
    }
   }else if(type==="steps"){
    // 解题思路：按①②③用有序列表显示
    const lines=block.lines.filter(l=>l&&l!=="_bullet_start_"&&!l.startsWith("_bullet_"));
    bodyHtml=`<ol class="kd-ol kd-ol-${type}">${lines.map(l=>`<li class="kd-block-li">${_highlightKeyTerms(l)}</li>`).join("")}</ol>`;
   }else if(type==="exam"||type==="error"||type==="key"){
    // 考试题型/易错点/重点：用有序列表显示
    const lines=block.lines.filter(l=>l&&l!=="_bullet_start_"&&!l.startsWith("_bullet_"));
    bodyHtml=`<ol class="kd-ol kd-ol-${type}">${lines.map(l=>`<li class="kd-block-li">${_highlightKeyTerms(l)}</li>`).join("")}</ol>`;
   }else{
    // 核心概念等：段落形式，首行缩进，减少换行
    const lines=block.lines.filter(l=>l&&l!=="_bullet_start_"&&!l.startsWith("_bullet_"));
    // 合并成一个段落，避免过多换行
    const fullText=lines.join("");
    bodyHtml=`<p class="kd-block-line kd-block-core-text">${_highlightKeyTerms(fullText)}</p>`;
   }
   // 统一使用蓝色加粗标题，默认全部展开
   const wrapperClass=`kd-block kd-block-${type} open`;
   return `<div class="${wrapperClass}" data-idx="${idx}" data-type="${type}">
     <div class="kd-block-head">
       <span class="kd-block-icon">${icon}</span>
       <h4 class="kd-block-title">${escapeHtml(block.title)}</h4>
     </div>
     <div class="kd-block-body">${bodyHtml}</div>
   </div>`;
  }
  return `<p class="kd-para">${_highlightKeyTerms(block.lines.join("  "))}</p>`;
 }).join("");
}

// 把"关键词：xxx,yyy,zzz"渲染为带标签条的 header
function _keywordsBarHTML(keywords){
 if(!keywords)return "";
 const tags=keywords.split(/[,，;;\s]+/).map(s=>s.trim()).filter(Boolean);
 if(!tags.length)return "";
 // 去掉每个关键词中的引号和方括号
 const cleanTags=tags.map(t=>t.replace(/["""'【】\[\]]/g,'').trim()).filter(Boolean);
 return `<div class="kd-keywords-bar"><b>关键词</b>${cleanTags.map(t=>`<span class="kd-kw-tag">${escapeHtml(t)}</span>`).join("")}</div>`;
}
window.toggleKdAccordion=function(header){
 header.parentElement.classList.toggle("open");
}

function knowledgeBodyHTML(point){
 const raw=point.content||"";
 const parsed=_formatContentText(raw);  // {keywords, blocks}
 const blocks=parsed.blocks||[];
 const extraKeywords=parsed.keywords||"";
 // 头部关键词：抽出的 _formatContentText.keywords 优先,没有则用 point.keywords
 const headerKeywords=_cleanBrackets(extraKeywords||point.keywords||point.name);
 if(raw){
  return `${_keywordsBarHTML(extraKeywords||point.keywords)}<div class="kd-content-body">${_renderContentBlocks(blocks)}</div>`;
 }
 return `${_keywordsBarHTML(point.keywords||point.name)}<p>${escapeHtml(`${point.name} 是 ${point.chapter_name} 章节下的三级知识点。建议先理解定义、核心概念、常见考法和易错点，再进入专项训练。`)}</p>`;
}

function videoCardHTML(video){
 const matchLabel={exact:"<span style='color:#27a978;font-weight:700'>● 精确匹配</span>",alias:"<span style='color:#2f80ed;font-weight:700'>● 章节相关</span>",keyword:"<span style='color:#f7b500;font-weight:700'>● 关键词命中</span>",subject:"<span style='color:#9aa5b1;font-weight:700'>● 同科目推荐</span>"};
 const matchLevel=video.match_level||"subject";
 const score=Math.round(Number(video.keyword_match_score||video.score||0)*100);
 const coverUrl=video.cover_url||"";
 const coverHtml=coverUrl
  ? `<div class="video-cover"><img src="${escapeAttr(coverUrl)}" alt="${escapeAttr(video.title||"视频封面")}" loading="lazy" referrerpolicy="no-referrer" onerror="this.onerror=null;this.parentElement.classList.add('video-cover-fallback');this.remove();"><span class="video-cover-play">▶</span><span class="video-cover-duration">${escapeHtml(video.duration||"")}</span></div>`
  : `<div class="video-cover video-cover-fallback"><span class="video-cover-play">▶</span><span class="video-cover-duration">${escapeHtml(video.duration||"")}</span><div class="video-cover-fallback-text">${escapeHtml(video.platform||"B站")} 视频</div></div>`;
 return `<a href="${escapeHtml(video.url||'#')}" target="_blank" rel="noopener noreferrer" class="kd-video-card" data-vid="${escapeHtml(video.id||'')}">
  ${coverHtml}
  <div class="video-info">
    <div class="video-info-top">
      <div class="video-title">${escapeHtml(video.title||"视频资源")}</div>
      ${score>0?`<span class="video-score">${score}%</span>`:""}
    </div>
    <div class="video-meta">
      <span class="video-platform">▶ ${escapeHtml(video.platform||"B站")}</span>
      ${video.author?`<span class="video-tag">👤 ${escapeHtml(video.author)}</span>`:""}
      <span class="video-match">${matchLabel[matchLevel]||""}</span>
    </div>
    ${video.match_explanation||video.reason?`<p class="video-reason">${escapeHtml(video.match_explanation||video.reason)}</p>`:""}
    <div class="video-action">去观看 <span>↗</span></div>
  </div>
</a>`;
}

function noteCardHTML(note){
 return `<article class="kd-note-card"><b>${escapeHtml(note.title)}</b><small>${escapeHtml(note.update_time||"")}</small><p>${escapeHtml(note.summary||note.content||"")}</p><div class="kd-note-actions"><button data-note-view="${note.id}">查看</button><button data-note-edit="${note.id}">编辑</button><button data-note-delete="${note.id}">删除</button><button data-note-share="${note.id}">转发</button></div></article>`;
}

function noteModalHTML(point){
 return `<div class="kd-modal" id="kdNoteModal"><div><button class="kd-modal-close" data-close-note>×</button><h3 id="noteModalTitle">添加笔记</h3><input id="noteId" type="hidden" value=""><input id="noteKnowledgeId" type="hidden" value="${point.id||""}"><label>科目<input id="noteSubject" value="${escapeHtml(point.subject_name||"")}"></label><label>章节<input id="noteChapter" value="${escapeHtml(point.chapter_name||"")}"></label><label>知识点<input id="notePoint" value="${escapeHtml(point.name||"")}"></label><label>标题<input id="noteTitle" maxlength="100" placeholder="请输入笔记标题"></label><label>内容<textarea id="noteContent" placeholder="请输入笔记内容"></textarea></label><button class="primary" data-save-note>保存</button></div></div>`;
}

function bindKnowledgeDetailInteractions(){
 bindKnowledgeGraphInteractions();
 // 面包屑返回：滚动到顶部，让左侧目录树可见
 document.querySelectorAll("[data-kg-back]").forEach(btn=>{btn.onclick=()=>{
  if(document.getElementById("knowledge")?.classList.contains("active")){
   window.knDetailActive=false;
   const tree=document.getElementById("knTreePanelBody");
   if(tree)tree.scrollIntoView({behavior:"smooth",block:"start"});
  }
 }});
 document.querySelectorAll("[data-kd-chapter]").forEach(button=>button.onclick=()=>loadChapterDetailPage(Number(button.dataset.kdChapter)));
 document.querySelectorAll("[data-kd-point]").forEach(button=>button.onclick=()=>loadKnowledgePointDetailPage(Number(button.dataset.kdPoint)));
 document.querySelectorAll("[data-open-note]").forEach(button=>button.onclick=()=>openKnowledgeNoteModal());
 document.querySelectorAll("[data-chapter-notes]").forEach(button=>button.onclick=()=>toast("章节页只展示概况；请进入具体知识点后添加或查看笔记","info"));
 document.querySelector("[data-close-note]")?.addEventListener("click",()=>document.getElementById("kdNoteModal")?.classList.remove("show"));
 document.querySelector("[data-save-note]")?.addEventListener("click",saveKnowledgeNote);
 const handleNoteAction=(event)=>{
  const button=event.target.closest("[data-note-view],[data-note-edit],[data-note-delete],[data-note-share]");
  if(!button)return;
  event.preventDefault();
  event.stopPropagation();
  if(button.dataset.noteView)return viewKnowledgeNote(button.dataset.noteView);
  if(button.dataset.noteEdit)return editKnowledgeNote(button.dataset.noteEdit);
  if(button.dataset.noteDelete)return deleteKnowledgeNote(button.dataset.noteDelete);
  if(button.dataset.noteShare)return shareKnowledgeNote(button.dataset.noteShare);
 };
 document.querySelectorAll(".kd-note-actions").forEach(actions=>{
  actions.onclick=handleNoteAction;
  actions.ontouchend=handleNoteAction;
 });
 document.querySelectorAll("[data-note-view],[data-note-edit],[data-note-delete],[data-note-share]").forEach(button=>button.onclick=handleNoteAction);
 document.querySelectorAll("[data-kd-tab]").forEach(button=>button.onclick=()=>{
  const tabName=button.dataset.kdTab;
  const tabSection=button.closest(".kd-tabs-section");
  if(!tabSection)return;
  tabSection.querySelectorAll(".kd-tab").forEach(t=>t.classList.remove("active"));
  button.classList.add("active");
  const tabMap={videos:"kdTabVideos",notes:"kdTabNotes"};
  tabSection.querySelectorAll(".kd-tab-content").forEach(c=>c.style.display="none");
  const target=document.getElementById(tabMap[tabName]);
  if(target)target.style.display="grid";
 });
 document.querySelectorAll(".kd-video-card").forEach(card=>{
  card.addEventListener("click",()=>{
   const vid=card.getAttribute("data-vid");
   const v=(window.currentKnowledgeVideos||[]).find(item=>String(item.id)===vid)||{};
   fetch("/api/videos/click",{method:"POST",headers:{"Content-Type":"application/json","Authorization":`Bearer ${localStorage.getItem("turing408_token")||""}`},body:JSON.stringify({video_id:v.id||null,video_url:v.url||"",video_title:v.title||"",knowledge_point:v.knowledge_point||"",subject:v.subject||"",author:v.author||"",match_level:v.match_level||"",source:v.source||"",click_position:0})}).catch(()=>{});
  });
 });
 document.querySelectorAll("[data-kd-start-practice]").forEach(btn=>{
  btn.onclick=async()=>{
   const subject=btn.dataset.kdPracticeSubject||"";
   const point=btn.dataset.kdPracticePoint||"";
   const progressId="kn-practice-point-"+Date.now();
   const prefix="正在为「"+(point||subject||"知识点")+"」";
   const prog=startGenerationProgress(progressId,prefix);
   try{
    const payload={mode:"知识点专项",subject:subject,knowledge_point:point,count:3,difficulty:"自适应",question_type:"混合"};
    const data=await apiRequest("/api/questions/generate",{method:"POST",body:JSON.stringify(payload)});
    prog.stop();
    if(data.all_refused&&(!data.questions||!data.questions.length)){errorProgressBar(progressId,"知识库暂无该知识点");toast("当前网络问题，请稍后重试或更换知识点","error");return}
    if(!data.questions||!Array.isArray(data.questions)||!data.questions.length){errorProgressBar(progressId,"暂无题目");toast("Agent 暂未生成题目，请稍后重试或更换知识点","error");return}
    showPage("question");
    hasGeneratedQuestionBatch=true;
    activeQuestions=data.questions.map((q,i)=>normalizeQuestion({...q,source:"知识点专项练习"},i));
    currentQuestionIndex=0;
    renderQuestion();
    const tag=data.llm_used?"（AI 智能出题）":(data.llm_error?"（使用保底题库："+data.llm_error+"）":"（使用本地题库）");
    completeProgressBar(progressId,"已生成 "+data.questions.length+" 道题");
    toast("已为「"+point+"」生成 "+data.questions.length+" 道练习题 "+tag);
   }catch(e){prog.stop();errorProgressBar(progressId,"生成失败");toast("生成题目失败: "+e.message,"error")}
  };
 });
 document.querySelectorAll("[data-kd-start-practice-chapter]").forEach(btn=>{
  btn.onclick=async()=>{
   const subject=btn.dataset.kdPracticeSubject||"";
   const chapter=btn.dataset.kdPracticePoint||"";
   const progressId="kn-practice-chapter-"+Date.now();
   const prefix="正在为「"+(chapter||subject||"章节")+"」";
   const prog=startGenerationProgress(progressId,prefix);
   try{
    const payload={mode:"章节训练",scope:"chapter",subject:subject,knowledge_point:chapter,chapter:chapter,chapter_id:Number(btn.dataset.kdStartPracticeChapter||0)||null,count:3,difficulty:"自适应",question_type:"混合"};
    const data=await apiRequest("/api/questions/generate",{method:"POST",body:JSON.stringify(payload)});
    prog.stop();
    if(data.all_refused&&(!data.questions||!data.questions.length)){errorProgressBar(progressId,"知识库暂无该章节");toast("当前网络问题，请稍后重试或更换章节","error");return}
    if(!data.questions||!Array.isArray(data.questions)||!data.questions.length){errorProgressBar(progressId,"暂无题目");toast("Agent 暂未生成题目，请稍后重试或更换章节","error");return}
    showPage("question");
    hasGeneratedQuestionBatch=true;
    activeQuestions=data.questions.map((q,i)=>normalizeQuestion({...q,source:"章节训练"},i));
    currentQuestionIndex=0;
    renderQuestion();
    const tag=data.llm_used?"（AI 智能出题）":(data.llm_error?"（使用保底题库："+data.llm_error+"）":"（使用本地题库）");
    completeProgressBar(progressId,"已生成 "+data.questions.length+" 道题");
    toast("已为「"+chapter+"」生成 "+data.questions.length+" 道练习题 "+tag);
   }catch(e){prog.stop();errorProgressBar(progressId,"生成失败");toast("生成题目失败: "+e.message,"error")}
  };
 });
}

function findKnowledgeNote(noteId){
 return (window.currentKnowledgeNotes||[]).find(item=>Number(item.id)===Number(noteId));
}

function openKnowledgeNoteModal(note){
 const modal=document.getElementById("kdNoteModal");
 if(!modal)return;
 document.getElementById("noteModalTitle").textContent=note?"编辑笔记":"添加笔记";
 document.getElementById("noteId").value=note?.id||"";
 document.getElementById("noteTitle").value=note?.title||"";
 document.getElementById("noteContent").value=note?.content||"";
 modal.classList.add("show");
}

function viewKnowledgeNote(noteId){
 const note=findKnowledgeNote(noteId);
 if(!note)return toast("笔记不存在或已刷新","error");
 openKnowledgeNoteModal(note);
 document.getElementById("noteModalTitle").textContent="笔记详情";
}

function editKnowledgeNote(noteId){
 const note=findKnowledgeNote(noteId);
 if(!note)return toast("笔记不存在或已刷新","error");
 openKnowledgeNoteModal(note);
}

async function saveKnowledgeNote(){
 const noteId=document.getElementById("noteId")?.value||"";
 const payload={knowledge_point_id:Number(document.getElementById("noteKnowledgeId")?.value||0),subject:document.getElementById("noteSubject")?.value||"",chapter:document.getElementById("noteChapter")?.value||"",knowledge_point:document.getElementById("notePoint")?.value||"",title:document.getElementById("noteTitle")?.value||"",content:document.getElementById("noteContent")?.value||""};
 if(!payload.title||!payload.content)return toast("请填写笔记标题和内容","error");
 await apiRequest(noteId?`/api/notes/${noteId}`:"/api/notes",{method:noteId?"PUT":"POST",body:JSON.stringify(payload)});
 toast("笔记已保存","success");
 document.getElementById("kdNoteModal")?.classList.remove("show");
 if(payload.knowledge_point_id)loadKnowledgePointDetailPage(payload.knowledge_point_id);
 // 笔记数变化 → 同步刷新当前激活页
 refreshAfterAnswer("notes").catch(console.error);
}

async function deleteKnowledgeNote(noteId){
 await apiRequest(`/api/notes/${noteId}`,{method:"DELETE"});
 toast("笔记已删除","success");
 if(window.currentKnowledgePointId)loadKnowledgePointDetailPage(window.currentKnowledgePointId);
 refreshAfterAnswer("notes").catch(console.error);
}

async function shareKnowledgeNote(noteId){
 // 主站地址:所有对外链接(二维码/复制链接/打开主站)统一指向这里
 const SITE_URL="https://turing-agent.cloud/";
 // 调用后端接口获取分享链接(仅用于展示/调试,前端不再把分享页 URL 暴露给用户)
 let shareData={share_url:SITE_URL};
 try{
  const data=await apiRequest(`/api/notes/${noteId}/share`,{method:"POST"});
  if(data&&data.share_url)shareData.share_url=data.share_url;
 }catch(e){}
 // 从已加载的笔记列表中获取笔记数据
 let note=findKnowledgeNote(noteId);
 if(!note)note={title:"笔记分享",content:"",update_time:"",subject:"",chapter:"",knowledge_point:""};
 const title=note.title||"笔记分享";
 const content=note.content||note.summary||"";
 const updateTime=note.update_time||"";
 const author=note.author||note.username||"同学";
 // 获取标签（学科、章节、知识点）
 const tags=[];
 if(note.subject)tags.push({text:note.subject,color:"tag-blue",icon:"📚"});
 if(note.chapter)tags.push({text:note.chapter,color:"tag-yellow",icon:"📖"});
 if(note.knowledge_point)tags.push({text:note.knowledge_point,color:"tag-green",icon:"🎯"});
 // 生成分享弹窗
 const tagsHTML=tags.map(t=>`<span class="kd-share-tag ${t.color}">${t.icon} ${escapeHtml(t.text)}</span>`).join("");
 const modalHTML=`
  <div class="kd-share-mask" id="kdShareMask">
   <div class="kd-share-card" id="kdShareCard">
    <button class="kd-share-close" id="kdShareClose">×</button>
    <h2>${escapeHtml(title)}</h2>
    ${tagsHTML?`<div class="kd-share-tags">${tagsHTML}</div>`:""}
    <div class="kd-share-content">${escapeHtml(content)}</div>
    <hr class="kd-share-divider">
    <div class="kd-share-footer">
     <div class="kd-share-author">
      <div class="name">@ ${escapeHtml(author)}</div>
      <div class="time">${escapeHtml(updateTime)}</div>
     </div>
     <div class="kd-share-qr" id="kdShareQR">
      <div style="width:75px;height:75px;background:#f8fafc;display:grid;place-items:center;color:#94a3b8;font-size:9px;border-radius:8px">扫码查看</div>
      <span>扫码访问</span>
     </div>
    </div>
   </div>
   <div class="kd-share-actions">
    <button class="kd-share-btn btn-green" id="kdShareSave">⬇ 保存为图片</button>
    <button class="kd-share-btn btn-blue" id="kdShareCopy">🔗 复制链接</button>
    <button class="kd-share-btn btn-gray" id="kdShareOpen">🌐 打开主站</button>
   </div>
  </div>
 `;
 // 移除已有的弹窗
 const old=document.getElementById("kdShareMask");
 if(old)old.remove();
 document.body.insertAdjacentHTML("beforeend",modalHTML);
 const mask=document.getElementById("kdShareMask");
 requestAnimationFrame(()=>mask.classList.add("show"));
 // 关闭按钮
 document.getElementById("kdShareClose").onclick=closeShareModal;
 // 点击遮罩关闭
 mask.addEventListener("click",e=>{
  if(e.target===mask)closeShareModal();
 });
 // 复制链接(主站地址,用于推广)
 document.getElementById("kdShareCopy").onclick=async ()=>{
  const btn=document.getElementById("kdShareCopy");
  const originalText=btn.innerHTML;
  try{
   await navigator.clipboard.writeText(SITE_URL);
   btn.innerHTML="✓ 已复制";
  }catch(e){
   const ta=document.createElement("textarea");
   ta.value=SITE_URL;
   document.body.appendChild(ta);
   ta.select();
   document.execCommand("copy");
   ta.remove();
   btn.innerHTML="✓ 已复制";
  }
  setTimeout(()=>{btn.innerHTML=originalText;},1500);
 };
 // 打开主站
 document.getElementById("kdShareOpen").onclick=()=>{
  window.open(SITE_URL,"_blank");
 };
  // 保存为图片
  document.getElementById("kdShareSave").onclick=()=>{
   const btn=document.getElementById("kdShareSave");
   const orig=btn.innerHTML;
   btn.disabled=true;
   btn.innerHTML="⏳ 生成图片中...";
   const doCapture=async()=>{
    const card=document.getElementById("kdShareCard");
    if(!card){btn.innerHTML=orig;btn.disabled=false;return}
    try{
     const dataUrl=await htmlToImage.toPng(card,{backgroundColor:"#ffffff",pixelRatio:2});
     const blob=await (await fetch(dataUrl)).blob();
     const url=URL.createObjectURL(blob);
     const a=document.createElement("a");
     const t=(title||"笔记").replace(/[\\/:*?"<>|]/g,"_");
     a.href=url;a.download=`408笔记-${t}-${Date.now()}.png`;
     document.body.appendChild(a);a.click();document.body.removeChild(a);
     setTimeout(()=>URL.revokeObjectURL(url),1000);
     btn.innerHTML="✅ 已下载";
     setTimeout(()=>{btn.innerHTML=orig;btn.disabled=false},1500);
    }catch(e){console.error(e);alert("下载失败："+e.message+". 请尝试使用截图工具。");btn.innerHTML=orig;btn.disabled=false}
   };
   if(typeof htmlToImage==="undefined"){
    const s=document.createElement("script");
    s.src="https://cdn.jsdelivr.net/npm/html-to-image@1.11.11/dist/html-to-image.min.js";
    s.onload=doCapture;
    s.onerror=()=>{alert("加载截图库失败，请检查网络");btn.innerHTML=orig;btn.disabled=false};
    document.head.appendChild(s);
   }else{doCapture()}
  };
 // 生成二维码(指向主站)
 const qrDiv=document.getElementById("kdShareQR");
 const qrUrl=`https://api.qrserver.com/v1/create-qr-code/?size=90x90&data=${encodeURIComponent(SITE_URL)}`;
 const qrImg=new Image();
 qrImg.crossOrigin="anonymous";
 qrImg.onload=()=>{
  qrDiv.innerHTML="";
  qrDiv.appendChild(qrImg);
  const span=document.createElement("span");
  span.textContent="扫码访问";
  qrDiv.appendChild(span);
 };
 qrImg.src=qrUrl;

 function closeShareModal(){
  mask.classList.remove("show");
  setTimeout(()=>mask.remove(),300);
 }
}
