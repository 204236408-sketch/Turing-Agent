(function(){
  const state={overview:null,plans:[],txType:"all"};
  const labels={
    earn:"获得",spend:"消耗",grant:"会员赠送",refund:"退款",
    daily_checkin:"每日登录打卡",checkin_streak_3:"连续打卡 3 天",checkin_streak_7:"连续打卡 7 天",
    ai_chat:"AI 知识问答",ai_deep_analysis:"AI 小助手深度解析",generate_questions:"智能出题",
    ai_check_answer:"AI 批改简答题",ocr_import:"OCR 错题导入",mistake_cause_analysis:"错题原因分析",
    ai_report:"学习报告 AI 生成",video_recommendation:"视频资源智能推荐",membership_daily_grant:"会员每日赠送"
  };
  const MODULE_MEDALS=[
    {name:"连续学习者",rule:"连续打卡 7 天获得",type:"streak",target:7,hex:0,tone:"#2f6bff"},
    {name:"错题终结者",rule:"错题本订正 20 题获得",type:"mistake",target:20,hex:1,tone:"#ef4444"},
    {name:"知识探索者",rule:"知识图谱掌握 30 个知识点获得",type:"mastery",target:30,hex:2,tone:"#16a878"},
    {name:"AI提问官",rule:"智能问答提问 50 次获得",type:"qa",target:50,hex:3,tone:"#8b5cf6"},
    {name:"笔记达人",rule:"知识点导航添加 20 条学习笔记获得",type:"note",target:20,hex:4,tone:"#f59e0b"}
  ];
  const POINT_MEDALS=[
    {name:"青铜",threshold:100,tone:"#b87333",hex:0},
    {name:"白银",threshold:500,tone:"#94a3b8",hex:1},
    {name:"黄金",threshold:1500,tone:"#f6b73c",hex:2},
    {name:"钻石",threshold:5000,tone:"#38bdf8",hex:3},
    {name:"图灵之光",threshold:10000,tone:"#7c3aed",hex:4}
  ];
  const PLAN_PRICES={"月度会员":"12.9/月","学期会员":"29.9/季","季度会员":"29.9/季","年度会员":"99.9/年"};
  const PLAN_DISPLAY_NAMES={"月度会员":"月度会员","学期会员":"季度会员","季度会员":"季度会员","年度会员":"年度会员","普通用户":"普通用户"};
  const SPEND_COSTS={
    ai_chat:{label:"知识问答",cost:1,desc:"每次一问一答消耗 1 积分",silent:true},
    ai_deep_analysis:{label:"AI 小助手深度解析",cost:1,desc:"长回答 / 综合解释"},
    generate_questions:{label:"智能出题",cost:3,desc:"每生成一组题"},
    ai_check_answer:{label:"AI 批改简答题",cost:2,desc:"每次批改"},
    ocr_import:{label:"OCR 错题导入",cost:3,desc:"每次图片识别"},
    mistake_cause_analysis:{label:"错题原因分析",cost:6,desc:"每题分析"},
    ai_report:{label:"学习报告 AI 生成",cost:3,desc:"每份报告"},
    video_recommendation:{label:"视频资源智能推荐",cost:3,desc:"每次推荐"}
  };
  let confirmResolver=null;
  let paymentState={plan:null,order:null,timer:null};

  function ready(fn){
    if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",fn);
    else fn();
  }

  function waitForShell(){
    const timer=setInterval(()=>{
      if(document.querySelector(".shell .sidebar .nav")&&document.querySelector(".shell .main")){
        clearInterval(timer);
        installPersonalCenter();
      }
    },300);
  }

  function installPersonalCenter(){
    const nav=document.querySelector(".shell .sidebar .nav");
    const main=document.querySelector(".shell .main");
    if(!nav||!main||document.getElementById("personalCenter"))return;

    const btn=document.createElement("button");
    btn.className="pc-nav-button";
    btn.dataset.page="personal-center";
    btn.innerHTML="<i>♛</i>个人中心";
    btn.onclick=showPersonalCenter;
    nav.appendChild(btn);

    const section=document.createElement("section");
    section.className="page personal-center-page";
    section.id="personalCenter";
    section.innerHTML=personalCenterHTML();
    main.appendChild(section);
    document.body.insertAdjacentHTML("beforeend",upgradeModalHTML());
    bindPersonalCenter();
    installPointCostHooks();
    ensureModuleCostBadges();
  }

  function personalCenterHTML(){
    return `<div class="pc-hero">
      <article class="card pc-balance-card">
        <div class="pc-card-title">
          <div><span class="eyebrow">POINT ACCOUNT</span><h3>我的积分</h3><p>学习打卡获得积分，高成本 AI 功能按模块消耗积分。</p></div>
        </div>
        <div class="pc-metrics">
          <div class="pc-metric pc-metric-primary"><span>目前积分</span><b><span id="pcBalance">--</span></b></div>
          <div class="pc-metric"><span>连续打卡</span><b><span id="pcStreak">0</span> 天</b></div>
          <div class="pc-metric"><span>当前身份</span><b id="pcUserLevel">普通用户</b></div>
          <div class="pc-metric"><span>累计获得</span><b id="pcTotalEarned">--</b></div>
        </div>
        <div class="pc-actions">
          <button class="primary" id="pcCheckinBtn">立即打卡</button>
        </div>
      </article>
      <article class="card pc-medal-card">
        <div class="pc-medal-head">
          <span class="eyebrow">ACHIEVEMENT</span>
          <h3>成就勋章</h3>
        </div>
        <iframe class="pc-medals-frame" src="medals-system.html" title="成就勋章" scrolling="no" onload="this.contentWindow.postMessage({type:'pc-medals-overview',overview:window.__pcLatestOverview||null},'*')"></iframe>
      </article>
    </div>

    <section class="pc-section">
      <div class="pc-card-title"><div><h3>会员套餐</h3><p>升级会员享受更多 AI 功能权益。</p></div></div>
      <div class="pc-plans" id="pcPlans"><div class="card pc-empty">正在加载会员套餐…</div></div>
    </section>

    <section class="pc-section">
      <article class="card pc-record-card">
        <div class="pc-mode-tabs" id="pcModeTabs">
          <button class="active" data-mode="record">积分记录</button>
          <button data-mode="rule">积分规则</button>
        </div>
        <div class="pc-record-view" id="pcRecordView">
          <div class="pc-tabs" id="pcTxTabs">
            <button class="active" data-tx="all">全部</button>
            <button class="pc-tab-earn" data-tx="earn">获得</button>
            <button class="pc-tab-spend" data-tx="spend">消耗</button>
          </div>
          <div id="pcTransactions"><div class="pc-empty">暂无积分流水</div></div>
        </div>
        <div class="pc-rule-mini" id="pcRuleView" hidden>
          <h4>获得积分规则</h4>
          <div class="pc-rule-mini-list" id="pcMiniRules"></div>
        </div>
      </article>
    </section>`;
  }

  function upgradeModalHTML(){
    return `<div class="pc-upgrade-modal" id="pcUpgradeModal">
      <div class="pc-upgrade-box">
        <h3>积分不足</h3>
        <p id="pcUpgradeText">当前功能积分不足，可以通过打卡赚积分，或升级会员获得每日积分和折扣权益。</p>
        <div class="pc-upgrade-actions">
          <button class="ghost" id="pcUpgradeCancel">取消</button>
          <button class="soft" id="pcUpgradeCheckin">去打卡赚积分</button>
          <button class="primary" id="pcUpgradeGo">升级会员</button>
        </div>
      </div>
    </div>
    <div class="pc-upgrade-modal" id="pcCostConfirmModal">
      <div class="pc-upgrade-box pc-cost-confirm-box">
        <h3 id="pcCostConfirmTitle">确认消耗积分</h3>
        <p id="pcCostConfirmText">本次操作将消耗积分。</p>
        <div class="pc-cost-confirm-meta">
          <span>目前积分：<b id="pcCostBalance">--</b></span>
          <span>会员折扣：<b id="pcCostDiscount">--</b></span>
          <span>原价积分：<b id="pcCostBase">--</b></span>
          <span>本次实扣：<b id="pcCostNeed">--</b></span>
        </div>
        <div class="pc-upgrade-actions">
          <button class="ghost" id="pcCostCancel">取消</button>
          <button class="primary" id="pcCostConfirm">确认使用</button>
        </div>
      </div>
    </div>
    <div class="pc-upgrade-modal" id="pcPaymentModal">
      <div class="pc-payment-box">
        <button class="pc-modal-x" id="pcPayClose" type="button">×</button>
        <div class="pc-payment-side">
          <span class="eyebrow">VIP PAYMENT</span>
          <h3 id="pcPayPlanName">会员套餐</h3>
          <p>开通后立即生效，获得每日积分赠送与 AI 功能折扣权益。</p>
          <div class="pc-pay-price">￥<b id="pcPayAmount">--</b></div>
          <label class="pc-agreement"><input type="checkbox" id="pcPayAgree"> 我已阅读并同意《会员服务协议》</label>
        </div>
        <div class="pc-qr-area">
          <div class="pc-qr-wrap" id="pcQrWrap">
            <img class="pc-real-qr" id="pcRealQr" src="assets/membership-payment-12_9.jpg" alt="会员付款收款码">
            <div class="pc-qr-mask" id="pcQrMask">请先同意会员协议</div>
          </div>
          <div class="pc-pay-status" id="pcPayStatus">同意协议后可扫码支付</div>
        </div>
      </div>
    </div>
    <div class="pc-upgrade-modal" id="pcMedalModal">
      <div class="pc-medal-detail-box">
        <button class="pc-modal-x" id="pcMedalClose" type="button">×</button>
        <div class="pc-detail-medal-icon" id="pcDetailMedalIcon"></div>
        <h3 id="pcDetailMedalName">成就勋章</h3>
        <p id="pcDetailMedalRule">完成对应任务即可获得。</p>
        <button class="pc-medal-share" type="button">分享勋章</button>
        <div class="pc-detail-progress">
          <span id="pcDetailMedalProgress">0 / 0</span>
          <i id="pcDetailMedalBar"></i>
        </div>
        <div class="pc-detail-status" id="pcDetailMedalStatus">未获得</div>
      </div>
    </div>
    <div class="pc-upgrade-modal" id="pcCongratsModal">
      <div class="pc-congrats-box">
        <button class="pc-modal-x" id="pcCongratsClose" type="button">×</button>
        <div class="pc-congrats-glow"></div>
        <div class="pc-detail-medal-icon pc-congrats-icon" id="pcCongratsIcon"></div>
        <h3>恭喜你获得</h3>
        <strong id="pcCongratsName">成就勋章</strong>
        <p id="pcCongratsRule">继续保持学习节奏。</p>
      </div>
    </div>`;
  }

  function bindPersonalCenter(){
    document.getElementById("pcCheckinBtn").onclick=handleCheckin;
    document.querySelectorAll("#pcModeTabs button").forEach(btn=>btn.onclick=()=>switchRecordMode(btn.dataset.mode));
    document.querySelectorAll("#pcTxTabs button").forEach(btn=>btn.onclick=()=>switchTx(btn));
    document.getElementById("pcUpgradeCancel").onclick=hideUpgradeModal;
    document.getElementById("pcUpgradeCheckin").onclick=async()=>{hideUpgradeModal();showPersonalCenter();await handleCheckin()};
    document.getElementById("pcUpgradeGo").onclick=()=>{hideUpgradeModal();showPersonalCenter();document.getElementById("pcPlans")?.scrollIntoView({behavior:"smooth",block:"start"})};
    document.getElementById("pcCostCancel").onclick=()=>resolveCostConfirm(false);
    document.getElementById("pcCostConfirm").onclick=()=>resolveCostConfirm(true);
    document.getElementById("pcPayClose").onclick=closePaymentModal;
    document.getElementById("pcPayAgree").onchange=syncPaymentButton;
    const payStart=document.getElementById("pcPayStart");
    if(payStart)payStart.onclick=startQrPayment;
    document.getElementById("pcMedalClose").onclick=closeMedalDetail;
    document.getElementById("pcCongratsClose").onclick=closeMedalCongrats;
    window.addEventListener("message",event=>{
      if(event.data?.type==="pc-open-medal-modal")openParentMedalModal(event.data.medal);
    });
  }

  function showPersonalCenter(){
    document.querySelectorAll(".page").forEach(p=>p.classList.toggle("active",p.id==="personalCenter"));
    document.querySelectorAll(".nav button").forEach(b=>b.classList.toggle("active",b.dataset.page==="personal-center"));
    const title=document.getElementById("pageTitle"),sub=document.getElementById("pageSub");
    if(title){
      // 优先用 app.js 全局提供的 getTimeBasedGreeting，未加载时回落到本地实现
      const greeting = (typeof getTimeBasedGreeting === "function") ? getTimeBasedGreeting() : (function(){
        let h;
        try{ h = Number(new Intl.DateTimeFormat("zh-CN",{timeZone:"Asia/Shanghai",hour:"numeric",hour12:false}).format(new Date())); }
        catch(e){ h = new Date().getHours(); }
        if(h >= 6 && h <= 11) return "早上好，继续向目标前进 ☀️";
        if(h >= 12 && h <= 13) return "中午好，记得午休 🍱";
        if(h >= 14 && h <= 17) return "下午好，保持节奏 ☕";
        if(h >= 18 && h <= 22) return "晚上好，回顾一下今天 🌆";
        return "夜深了，注意休息 🌙";
      })();
      title.textContent = greeting;
    }
    if(sub){
      const days=document.getElementById("countdownDays")?.textContent||"180";
      sub.textContent=`距离 408 初试还有 ${Number(days)} 天`;
    }
    window.scrollTo(0,0);
    loadPersonalCenterData();
  }

  async function api(path,options){
    if(typeof window.apiRequest==="function")return window.apiRequest(path,options);
    throw new Error("前端 API 工具未加载");
  }

  async function loadPersonalCenterData(){
    try{
      const [overview,plans,tx]=await Promise.all([
        api("/api/points/account"),
        api("/api/membership/plans"),
        api(`/api/points/transactions?transaction_type=${state.txType}&limit=30`)
      ]);
      state.overview=overview;
      window.__pcLatestOverview=overview;
      state.plans=(plans.items||[]).filter(p=>!String(p.name||"").includes("普通"));
      renderOverview();
      renderPlans();
      renderMedals();
      syncMedalsFrame();
      showNewMedalCongrats();
      renderMiniRules();
      renderTransactions(tx.items||[]);
      ensureModuleCostBadges();
    }catch(err){
      toastSafe(err.message||"个人中心数据加载失败");
    }
  }

  function renderOverview(){
    const o=state.overview||{},account=o.account||{},member=o.membership||{};
    setText("pcBalance",fmtPoint(account.balance??0));
    setText("pcTotalEarned",account.total_earned??0);
    setText("pcStreak",o.streak_days??0);
    setText("pcUserLevel",displayPlanName(member));
    const checkBtn=document.getElementById("pcCheckinBtn");
    if(checkBtn){checkBtn.disabled=!!o.today_checkin;checkBtn.textContent=o.today_checkin?"今日已打卡":"立即打卡"}
  }

  function medalDate(){
    return new Date().toISOString().slice(0,10);
  }

  function renderMedals(){
    const o=state.overview||{};
    const totalEarned=Number(state.overview?.account?.total_earned||0);
    const backendModule=(o.medals?.module||[]).reduce((map,item)=>{map[item.type]=item;return map},{});
    const backendPoints=(o.medals?.points||[]).reduce((map,item)=>{map[item.type]=item;return map},{});
    const moduleValues={streak:Number(o.streak_days||0),mistake:Number(o.mistake_fixed_count||0),mastery:Number(o.mastered_count||0),qa:Number(o.qa_count||0),note:Number(o.note_count||0)};
    const moduleList=document.getElementById("pcModuleMedals");
    if(moduleList){
      moduleList.innerHTML=MODULE_MEDALS.map(m=>{
        const backend=backendModule[m.type]||{};
        const value=Number(backend.current ?? moduleValues[m.type] ?? 0);
        const target=Number(backend.target ?? m.target);
        const unlocked=backend.unlocked===true || value>=target;
        const achievedAt=backend.achieved_at||medalDate();
        const rule=backend.rule||m.rule;
        const medal={...m,current:value,target,unlocked,rule,achieved_at:unlocked?achievedAt:null,category:"module"};
        return `<div class="pc-medal-item pc-hex-medal ${unlocked?"unlocked":""}" style="--medal-color:${m.tone}" data-medal='${escapeAttr(JSON.stringify(medal))}'>
          <span class="pc-medal-svg-wrap">${medalSvg(medal)}</span>
          <span class="pc-medal-item-name">${escapeSafe(m.name)}</span>
          <span class="pc-medal-item-need">${unlocked?`获得于 ${escapeSafe(achievedAt)}`:escapeSafe(rule)}</span>
        </div>`;
      }).join("");
    }
    const pointList=document.getElementById("pcPointMedals");
    if(!pointList)return;
    pointList.innerHTML=POINT_MEDALS.map(m=>{
      const type={100:"point_bronze",500:"point_silver",1500:"point_gold",5000:"point_diamond",10000:"point_turing"}[m.threshold];
      const backend=backendPoints[type]||{};
      const value=Number(backend.current ?? totalEarned);
      const target=Number(backend.target ?? m.threshold);
      const unlocked=backend.unlocked===true || value>=target;
      const achievedAt=backend.achieved_at||medalDate();
      const rule=backend.rule||`累计获得 ${target} 积分`;
      const medal={...m,type,current:value,target,unlocked,rule,achieved_at:unlocked?achievedAt:null,category:"points"};
      return `<div class="pc-medal-item pc-hex-medal ${unlocked?"unlocked":""}" style="--medal-color:${m.tone}" data-medal='${escapeAttr(JSON.stringify(medal))}'>
        <span class="pc-medal-svg-wrap">${medalSvg(medal)}</span>
        <span class="pc-medal-item-name">${m.name}</span>
        <span class="pc-medal-item-need">${unlocked?`获得于 ${escapeSafe(achievedAt)}`:escapeSafe(rule)}</span>
      </div>`;
    }).join("");
    document.querySelectorAll(".pc-medal-item[data-medal]").forEach(el=>el.onclick=()=>openMedalDetail(JSON.parse(el.dataset.medal)));
  }

  function syncMedalsFrame(){
    const frame=document.querySelector(".pc-medals-frame");
    if(!frame?.contentWindow||!state.overview)return;
    frame.contentWindow.postMessage({type:"pc-medals-overview",overview:state.overview},"*");
  }

  function renderPlans(){
    const currentName=state.overview?.membership?.name||"";
    const wrap=document.getElementById("pcPlans");
    if(!wrap)return;
    if(!state.plans.length){wrap.innerHTML="<div class='pc-empty'>暂无会员套餐</div>";return}
    wrap.innerHTML=state.plans.map(plan=>{
      const active=plan.name===currentName;
      const price=plan.price_label||PLAN_PRICES[plan.name]||"";
      const displayName=displayPlanName(plan);
      return `<article class="pc-plan ${active?"active":""}">
        <div class="pc-plan-header">
          <h4>${escapeSafe(displayName)}</h4>
          <span class="pc-plan-price">${price}</span>
        </div>
        <p>${escapeSafe(plan.description||"")}</p>
        <button class="${active?"soft":"primary"}" data-plan-id="${plan.id}" ${active?"disabled":""}>${active?"当前套餐":"开通会员"}</button>
      </article>`;
    }).join("");
    wrap.querySelectorAll("button[data-plan-id]").forEach(btn=>btn.onclick=()=>openPaymentModal(Number(btn.dataset.planId)));
  }

  function medalGlyph(name){
    return {
      "连续学习者":"火",
      "错题终结者":"靶",
      "知识探索者":"书",
      "AI提问官":"AI",
      "笔记达人":"记",
      "青铜":"铜",
      "白银":"银",
      "黄金":"金",
      "钻石":"钻",
      "图灵之光":"图"
    }[name]||"奖";
  }

  function medalSvg(medal,{large=false}={}){
    const tone=medal.tone||"var(--brand)";
    const glyph=medalGlyph(medal.name);
    const locked=medal.unlocked?0:1;
    const opacity=locked?".42":"1";
    const id=`rough${String(medal.type||medal.name).replace(/\W/g,"")}${large?"L":"S"}`;
    return `<svg class="pc-medal-svg ${large?"large":""}" viewBox="0 0 100 120" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style="--medal-color:${tone};opacity:${opacity}">
      <defs>
        <filter id="${id}" x="-5%" y="-5%" width="110%" height="110%">
          <feTurbulence type="fractalNoise" baseFrequency="0.022" numOctaves="2" seed="3"/>
          <feDisplacementMap in="SourceGraphic" scale="1.1"/>
        </filter>
        <linearGradient id="${id}Fill" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="#ffffff"/>
          <stop offset="100%" stop-color="#f5f6f9"/>
        </linearGradient>
        <radialGradient id="${id}Glow" cx="35%" cy="25%" r="75%">
          <stop offset="0%" stop-color="#ffffff" stop-opacity=".9"/>
          <stop offset="55%" stop-color="${tone}" stop-opacity=".26"/>
          <stop offset="100%" stop-color="${tone}" stop-opacity=".08"/>
        </radialGradient>
      </defs>
      <path d="M40 102 L38 116 L48 110 L50 113 L52 110 L62 116 L60 102 Z" fill="#fff" stroke="#a8aeb6" stroke-width="1.4" stroke-linejoin="round"/>
      <path d="M50 6 L94 30 L94 90 L50 114 L6 90 L6 30 Z" fill="url(#${id}Fill)" stroke="#a8aeb6" stroke-width="1.8" stroke-linejoin="round" filter="url(#${id})"/>
      <path d="M50 6 L94 30 L94 90 L50 114 L6 90 L6 30 Z" fill="url(#${id}Glow)" stroke="none"/>
      <path d="M50 18 L82 36 L82 84 L50 102 L18 84 L18 36 Z" fill="none" stroke="${tone}" stroke-width="1" stroke-dasharray="2.5 2.5" opacity=".55"/>
      <circle cx="50" cy="15" r="3" fill="none" stroke="#a8aeb6" stroke-width="1.2"/>
      <circle cx="50" cy="60" r="24" fill="${tone}" opacity=".13"/>
      <circle cx="50" cy="60" r="18" fill="${tone}" opacity=".2"/>
      <text x="50" y="${glyph.length>1?66:68}" text-anchor="middle" font-size="${glyph.length>1?17:24}" font-weight="800" fill="${tone}" font-family="Inter, Noto Sans SC, sans-serif">${escapeSafe(glyph)}</text>
      <path d="M20 30 L24 32M80 30 L76 32M20 90 L24 88M80 90 L76 88" stroke="#a8aeb6" stroke-width="1.2" stroke-linecap="round" opacity=".7"/>
      <circle cx="12" cy="60" r="1.2" fill="#a8aeb6" opacity=".65"/>
      <circle cx="88" cy="60" r="1.2" fill="#a8aeb6" opacity=".65"/>
    </svg>`;
  }

  function renderMiniRules(){
    const rules=state.overview?.rules?.earn||{};
    const wrap=document.getElementById("pcMiniRules");
    if(!wrap)return;
    const allowed=["daily_checkin","checkin_streak_3","checkin_streak_7"];
    const entries=Object.entries(rules).filter(([k])=>allowed.includes(k));
    wrap.innerHTML=entries.map(([key,rule])=>{
      const points=Number(rule.points||0);
      return `<div class="pc-rule-mini-item">
        <b>${escapeSafe(rule.label||labels[key]||key)}</b>
        <span>${escapeSafe(rule.limit||rule.description||"")}</span>
        <b class="pc-points-plus">+${points}</b>
      </div>`;
    }).join("")||"<div class='pc-empty'>暂无规则</div>";
  }

  function renderTransactions(items){
    const wrap=document.getElementById("pcTransactions");
    if(!wrap)return;
    if(!items.length){wrap.innerHTML="<div class='pc-empty'>暂无积分流水</div>";return}
    wrap.innerHTML=items.map(item=>{
      const points=Number(item.points||0);
      const day=String(item.created_at||"").slice(0,10);
      return `<div class="pc-tx-row">
        <div><b>${escapeSafe(item.description||labels[item.action_type]||item.action_type)}</b><span>${day} · ${labels[item.transaction_type]||item.transaction_type}</span></div>
        <b class="${points>=0?"pc-points-plus":"pc-points-minus"}">${points>0?"+":""}${fmtPoint(points)}</b>
        <span>余额：${fmtPoint(item.balance_after||0)}</span>
      </div>`;
    }).join("");
  }

  async function handleCheckin(){
    try{
      const data=await api("/api/points/checkin",{method:"POST"});
      if(data.success)toastSafe(`打卡成功 +${data.earned} 积分`);
      else toastSafe(data.message||"今日已完成打卡");
      await loadPersonalCenterData();
    }catch(err){toastSafe(err.message||"打卡失败")}
  }

  async function handleSpend(actionType,targetType,targetId){
    try{
      const data=await api("/api/points/spend",{method:"POST",body:JSON.stringify({action_type:actionType,target_type:targetType,target_id:targetId})});
      if(!data.success){showUpgradeModal(data.need_points,data.balance);return data}
      toastSafe(`已消耗 ${fmtPoint(data.spent)} 积分`);
      await loadPersonalCenterData();
      return data;
    }catch(err){toastSafe(err.message||"积分扣除失败");return {success:false,message:err.message}}
  }

  async function getPointOverview(){
    try{
      const overview=await api("/api/points/account");
      state.overview=overview;
      renderOverview();
      ensureModuleCostBadges();
      return overview;
    }catch(err){
      toastSafe(err.message||"积分余额读取失败");
      return state.overview||{};
    }
  }

  function getDiscountInfo(overview=state.overview){
    const membership=overview?.membership||{};
    const rate=Number(membership.discount_rate||1);
    const name=displayPlanName(membership);
    return {rate,name,label:rate>=1?"无折扣":`${Math.round(rate*10)} 折`};
  }

  function getFinalCost(baseCost,overview=state.overview){
    const {rate}=getDiscountInfo(overview);
    return Number((Number(baseCost||0)*rate).toFixed(1));
  }

  function fmtPoint(value){
    const num=Number(value||0);
    return Number.isInteger(num)?String(num):num.toFixed(1);
  }

  function showCostConfirm(rule,balance,overview){
    const discount=getDiscountInfo(overview);
    const finalCost=getFinalCost(rule.cost,overview);
    setText("pcCostConfirmTitle",`确认使用${rule.label}`);
    setText("pcCostConfirmText",`${rule.desc}。${discount.name} ${discount.label}，请确认是否继续。`);
    setText("pcCostBalance",fmtPoint(balance));
    setText("pcCostDiscount",discount.label);
    setText("pcCostBase",fmtPoint(rule.cost));
    setText("pcCostNeed",fmtPoint(finalCost));
    document.getElementById("pcCostConfirmModal")?.classList.add("show");
    return new Promise(resolve=>{confirmResolver=resolve});
  }

  function resolveCostConfirm(ok){
    document.getElementById("pcCostConfirmModal")?.classList.remove("show");
    if(confirmResolver){confirmResolver(ok);confirmResolver=null}
  }

  async function confirmAndSpend(actionType,targetType,targetId,{silent=false}={}){
    const rule=SPEND_COSTS[actionType]||{label:labels[actionType]||"AI 功能",cost:1,desc:"本次操作将消耗积分"};
    const overview=await getPointOverview();
    const balance=Number(overview?.account?.balance||0);
    const finalCost=getFinalCost(rule.cost,overview);
    if(balance<finalCost){
      showUpgradeModal(finalCost,balance,rule.cost,overview);
      return false;
    }
    if(!silent){
      const ok=await showCostConfirm(rule,balance,overview);
      if(!ok)return false;
    }
    const spent=await handleSpend(actionType,targetType,targetId);
    return !!spent?.success;
  }

  function ensureModuleCostBadges(){
    const balance=Number(state.overview?.account?.balance||0);
    const cost=fmtPoint(getFinalCost(SPEND_COSTS.ai_chat.cost,state.overview));
    const head=document.querySelector("#qa .chat .head");
    if(head&&!document.getElementById("qaPointCost")){
      const box=document.createElement("div");
      box.id="qaPointCost";
      box.className="pc-module-cost";
      head.appendChild(box);
    }
    const qa=document.getElementById("qaPointCost");
    if(qa)qa.innerHTML=`<span>目前积分 <b>${fmtPoint(balance)}</b></span><span>本次将消耗 <b>${cost}</b> 积分</span>`;
  }

  function guardedRun(el,event,actionType,targetType,targetId,options={}){
    const original=el.onclick;
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();
    confirmAndSpend(actionType,targetType,targetId,options).then(ok=>{
      if(!ok)return;
      if(typeof original==="function")original.call(el,event);
    });
  }

  function installPointCostHooks(){
    if(window.__pointCostHooksInstalled)return;
    window.__pointCostHooksInstalled=true;
    document.addEventListener("click",event=>{
      const el=event.target.closest("button,[data-drawer]");
      if(!el)return;
      if(el.id==="sendQa"){
        guardedRun(el,event,"ai_chat","qa",null,{silent:true});
      }else if(el.matches("[data-forum-ai]")||el.matches("[data-ai-followup]")){
        if(el.matches("[data-forum-ai]")){
          const panel=document.getElementById(`forumAi${el.dataset.forumAi}`);
          if(panel?.classList.contains("show"))return;
        }
        guardedRun(el,event,"ai_deep_analysis","forum_post",Number(el.dataset.forumAi||el.dataset.aiFollowup||0));
      }else if(el.id==="generateManual"||el.id==="generateSmart"){
        guardedRun(el,event,"generate_questions","question_session",null);
      }else if(el.id==="ocrMock"){
        guardedRun(el,event,"ocr_import","ocr_upload",null);
      }else if(el.id==="submitAnswer"){
        if(!document.querySelector(".option.selected"))return;
        guardedRun(el,event,"ai_check_answer","answer",null);
      }else if(el.id==="openCause"){
        if(document.getElementById("causeDetail")?.classList.contains("show"))return;
        guardedRun(el,event,"mistake_cause_analysis","mistake",null);
      }else if(el.dataset?.drawer==="video"){
        const drawer=document.getElementById("video");
        if(drawer?.classList.contains("show"))return;
        guardedRun(el,event,"video_recommendation","video",null);
      }else if(el.id==="exportReport"){
        guardedRun(el,event,"ai_report","report",null);
      }
    },true);
    document.addEventListener("keydown",event=>{
      if(event.key!=="Enter"||event.target?.id!=="qaInput")return;
      const send=document.getElementById("sendQa");
      if(send)guardedRun(send,event,"ai_chat","qa",null,{silent:true});
    },true);
    document.addEventListener("drop",event=>{
      const drop=event.target.closest("#ocrDrop");
      if(!drop)return;
      const file=event.dataTransfer?.files?.[0];
      if(!file)return;
      event.preventDefault();
      event.stopPropagation();
      event.stopImmediatePropagation();
      confirmAndSpend("ocr_import","ocr_upload",null).then(ok=>{
        if(ok&&typeof window.ocrUploadFile==="function")window.ocrUploadFile(file);
      });
    },true);
  }

  async function subscribePlan(planId){
    try{
      const data=await api("/api/membership/subscribe",{method:"POST",body:JSON.stringify({plan_id:planId})});
      toastSafe(`已开通 ${data.plan?.name||"会员"}`);
      await loadPersonalCenterData();
    }catch(err){toastSafe(err.message||"开通会员失败")}
  }

  function openPaymentModal(planId){
    const plan=state.plans.find(p=>Number(p.id)===Number(planId));
    if(!plan)return;
    paymentState={plan,order:null,timer:null};
    const displayName=displayPlanName(plan);
    const amount=plan.price||String(plan.price_label||PLAN_PRICES[plan.name]||"").split("/")[0]||"0";
    const qrMap={"12.9":"assets/membership-payment-12_9.jpg","29.9":"assets/membership-payment-29_9.jpg","99.9":"assets/membership-payment-99_9.jpg"};
    const qr=document.getElementById("pcRealQr");
    if(qr)qr.src=qrMap[String(amount)]||"assets/membership-payment-12_9.jpg";
    setText("pcPayPlanName",displayName);
    setText("pcPayAmount",amount);
    setText("pcPayStatus","支付成功后审核通过，会员机制生效");
    document.getElementById("pcPayAgree").checked=false;
    const payBtn=document.getElementById("pcPayStart");
    if(payBtn){payBtn.disabled=true;payBtn.textContent="扫码支付"}
    document.getElementById("pcQrWrap").classList.remove("paying","paid");
    setText("pcQrMask","请先同意会员协议");
    document.getElementById("pcPaymentModal")?.classList.add("show");
  }

  function closePaymentModal(){
    if(paymentState.timer)clearTimeout(paymentState.timer);
    document.getElementById("pcPaymentModal")?.classList.remove("show");
  }

  function syncPaymentButton(){
    const agreed=document.getElementById("pcPayAgree")?.checked;
    const btn=document.getElementById("pcPayStart");
    const wrap=document.getElementById("pcQrWrap");
    if(btn)btn.disabled=!agreed;
    if(wrap)wrap.classList.toggle("agreed",!!agreed);
    setText("pcQrMask",agreed?"":"请先同意会员协议");
    setText("pcPayStatus",agreed?"支付成功后审核通过，会员机制生效":"同意协议后可扫码支付");
  }

  async function startQrPayment(){
    if(!paymentState.plan)return;
    if(paymentState.order?.order_no){
      await checkQrPaymentStatus();
      return;
    }
    const agreed=document.getElementById("pcPayAgree")?.checked;
    if(!agreed){toastSafe("请先同意会员服务协议");return}
    try{
      const order=await api("/api/membership/payment/create",{method:"POST",body:JSON.stringify({plan_id:paymentState.plan.id,agreed:true})});
      paymentState.order=order;
      const wrap=document.getElementById("pcQrWrap");
      wrap?.classList.add("paying");
      setText("pcQrMask","等待付款确认");
      setText("pcPayStatus",`请扫码支付 ￥${order.amount}。系统确认到账后才会开通会员。`);
      const btn=document.getElementById("pcPayStart");
      if(btn){btn.disabled=false;btn.textContent="我已付款，检查支付状态"}
      if(paymentState.timer)clearInterval(paymentState.timer);
      paymentState.timer=setInterval(checkQrPaymentStatus,3000);
    }catch(err){
      toastSafe(err.message||"创建支付订单失败");
    }
  }

  async function checkQrPaymentStatus(){
    if(!paymentState.order?.order_no)return;
    try{
      const btn=document.getElementById("pcPayStart");
      if(btn){btn.disabled=true;btn.textContent="正在检查支付状态"}
      const data=await api(`/api/membership/payment/status/${encodeURIComponent(paymentState.order.order_no)}`);
      if(data.paid&&data.activated){
        if(paymentState.timer){clearInterval(paymentState.timer);paymentState.timer=null}
        document.getElementById("pcQrWrap")?.classList.add("paid");
        setText("pcQrMask","支付成功");
        setText("pcPayStatus","支付已确认，会员已开通");
        toastSafe(`已开通 ${displayPlanName(data.membership)||"会员"}`);
        setTimeout(()=>{closePaymentModal();loadPersonalCenterData()},700);
        return;
      }
      setText("pcQrMask","等待付款确认");
      setText("pcPayStatus","系统暂未确认到账，请完成支付后稍等，会员不会提前开通。");
      if(btn){btn.disabled=false;btn.textContent="我已付款，检查支付状态"}
    }catch(err){
      setText("pcPayStatus",err.message||"支付状态检查失败，请稍后重试");
      const btn=document.getElementById("pcPayStart");
      if(btn){btn.disabled=false;btn.textContent="重新检查支付状态"}
    }
  }

  function openMedalDetail(medal){
    const unlocked=normalizeMedalOwned(medal);
    medal.unlocked=unlocked;
    if(unlocked&&!medal.achieved_at)medal.achieved_at=medalDate();
    setText("pcDetailMedalName",medal.name);
    setText("pcDetailMedalRule",medal.rule);
    setText("pcDetailMedalProgress",`${Number(medal.current||0)} / ${Number(medal.target||0)}`);
    setText("pcDetailMedalStatus",unlocked?`已获得 · ${medal.achieved_at||medalDate()}`:"暂未获得");
    const progress=document.querySelector("#pcMedalModal .pc-detail-progress");
    const status=document.getElementById("pcDetailMedalStatus");
    if(progress)progress.hidden=false;
    if(status)status.hidden=false;
    const percent=Math.min(100,Math.round(Number(medal.current||0)/Math.max(1,Number(medal.target||1))*100));
    const bar=document.getElementById("pcDetailMedalBar");
    if(bar)bar.style.width=`${percent}%`;
    const icon=document.getElementById("pcDetailMedalIcon");
    if(icon){icon.className="pc-detail-medal-icon";icon.innerHTML=medalSvg(medal,{large:true})}
    document.getElementById("pcMedalModal")?.classList.add("show");
  }

  function closeMedalDetail(){document.getElementById("pcMedalModal")?.classList.remove("show")}

  function openParentMedalModal(medal){
    const owned=normalizeMedalOwned(medal);
    setText("pcDetailMedalName",`${owned?"恭喜解锁新勋章！":"继续努力解锁新勋章！"}🏆`);
    setText("pcDetailMedalRule",medal?.desc||"七天不间断,日日点灯。一支微笑的小火苗,记录你与知识之间最稳定的约定。");
    const progress=document.querySelector("#pcMedalModal .pc-detail-progress");
    const status=document.getElementById("pcDetailMedalStatus");
    if(progress)progress.hidden=true;
    if(status){
      status.hidden=false;
      status.textContent=owned?"已获得":"暂未获得";
    }
    const icon=document.getElementById("pcDetailMedalIcon");
    if(icon){icon.className="pc-detail-medal-icon pc-parent-medal-icon";icon.innerHTML=medal?.svg||""}
    document.getElementById("pcMedalModal")?.classList.add("show");
  }

  function showNewMedalCongrats(){
    const medals=[...document.querySelectorAll(".pc-medal-item[data-medal]")].map(el=>JSON.parse(el.dataset.medal)).filter(m=>normalizeMedalOwned(m));
    const found=medals.find(m=>{
      const key=`pc_medal_seen_${m.type||m.name}`;
      if(localStorage.getItem(key))return false;
      localStorage.setItem(key,"1");
      return true;
    });
    if(!found)return;
    setText("pcCongratsName",found.name);
    setText("pcCongratsRule",found.rule);
    const icon=document.getElementById("pcCongratsIcon");
    if(icon){icon.className="pc-detail-medal-icon pc-congrats-icon";icon.innerHTML=medalSvg(found,{large:true})}
    document.getElementById("pcCongratsModal")?.classList.add("show");
  }

  function closeMedalCongrats(){document.getElementById("pcCongratsModal")?.classList.remove("show")}

  function switchTx(btn){
    document.querySelectorAll("#pcTxTabs button").forEach(b=>b.classList.remove("active"));
    btn.classList.add("active");
    state.txType=btn.dataset.tx;
    api(`/api/points/transactions?transaction_type=${state.txType}&limit=30`).then(data=>renderTransactions(data.items||[])).catch(err=>toastSafe(err.message||"流水加载失败"));
  }

  function switchRecordMode(mode){
    document.querySelectorAll("#pcModeTabs button").forEach(b=>b.classList.toggle("active",b.dataset.mode===mode));
    const record=document.getElementById("pcRecordView");
    const rule=document.getElementById("pcRuleView");
    if(record)record.hidden=mode!=="record";
    if(rule)rule.hidden=mode!=="rule";
  }

  function showUpgradeModal(need,balance,baseCost=null,overview=state.overview){
    const discount=getDiscountInfo(overview);
    const baseText=baseCost!==null?`原价 ${fmtPoint(baseCost)} 积分，${discount.name} ${discount.label} 后需 ${fmtPoint(need)} 积分。`:`当前功能需要 ${fmtPoint(need)} 积分。`;
    setText("pcUpgradeText",`${baseText}你的余额仅剩 ${fmtPoint(balance)} 积分，请打卡获取积分或升级会员。`);
    document.getElementById("pcUpgradeModal")?.classList.add("show");
  }
  function hideUpgradeModal(){document.getElementById("pcUpgradeModal")?.classList.remove("show")}
  function setText(id,value){const el=document.getElementById(id);if(el)el.textContent=value}
  function toastSafe(message){if(typeof window.toast==="function")window.toast(message);else console.log(message)}
  function displayPlanName(plan){
    const raw=plan?.display_name||plan?.name||"普通用户";
    return PLAN_DISPLAY_NAMES[raw]||raw;
  }
  function normalizeMedalOwned(medal){
    if(!medal)return false;
    const current=Number(medal.current??medal.progress??0);
    const target=Number(medal.target??medal.total??1);
    if(medal.unlocked===true||medal.owned===true)return true;
    if(target>0&&current>=target)return true;
    return false;
  }
  function escapeSafe(value){return String(value??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]))}
  function escapeAttr(value){return escapeSafe(value).replace(/`/g,"&#096;")}

  window.showPointUpgradeModal=showUpgradeModal;
  window.spendPoints=handleSpend;
  ready(waitForShell);
})();
