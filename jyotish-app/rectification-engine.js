/**
 * 生时校正引擎 v2.0 — 专业印度占星方法
 * 基于 K.N. Rao + P.V.R. Narasimha Rao 方法论
 * 多维评分：Dasha(40%) + 分盘一致性(35%) + 宫位变化(15%) + Nakshatra Pada(10%)
 */
import { computeChart, computeDasha, SIGNS, SIGNS_CN, SIGN_LORDS, PLANET_CN, NAKSHATRA_LIST } from './jyotish-engine.js';
import { computeVarga } from './jyotish-advanced.js';

export const VARGA_SENSITIVITY = {
  D1:{min:120,cn:'本命盘',en:'Rasi'},D4:{min:7.5,cn:'房产盘',en:'Chaturthamsa'},
  D7:{min:4.3,cn:'子女盘',en:'Saptamsa'},D9:{min:13.3,cn:'九分盘',en:'Navamsa'},
  D10:{min:12,cn:'事业盘',en:'Dasamsa'},D12:{min:10,cn:'父母盘',en:'Dwadasamsa'},
  D24:{min:5,cn:'教育盘',en:'Siddhamsa'},D30:{min:4,cn:'厄运盘',en:'Trimsamsa'},
  D60:{min:2,cn:'业力盘',en:'Shashtiamsa'},
};

export const EVENT_CATEGORIES = {
  marriage:    {cn:'婚姻/恋爱',  en:'Marriage/Romance', icon:'💍',planets:['Venus','Jupiter'],houses:[7], varga:'D9'},
  divorce:     {cn:'离婚/分离',  en:'Divorce/Separation',icon:'💔',planets:['Rahu','Saturn'],  houses:[7,8],varga:'D9'},
  relationship:{cn:'重要关系',   en:'Key Relationship', icon:'🤝',planets:['Venus','Moon'],   houses:[7,1],varga:'D9'},
  career:      {cn:'事业/升职',  en:'Career/Promotion', icon:'💼',planets:['Sun','Saturn'],   houses:[10], varga:'D10'},
  job_change:  {cn:'工作变动',   en:'Job Change',       icon:'🔄',planets:['Saturn','Sun'],   houses:[10,6],varga:'D10'},
  business:    {cn:'创业/商业',  en:'Business Venture', icon:'🏢',planets:['Mercury','Mars'], houses:[10,7],varga:'D10'},
  education:   {cn:'教育/考试',  en:'Education/Exam',   icon:'📚',planets:['Mercury','Jupiter'],houses:[4,5],varga:'D24'},
  health:      {cn:'健康/手术',  en:'Health/Surgery',   icon:'🏥',planets:['Mars','Rahu'],    houses:[6],  varga:'D30'},
  child:       {cn:'生育/子女',  en:'Childbirth',       icon:'👶',planets:['Jupiter','Sun'],  houses:[5],  varga:'D7'},
  travel:      {cn:'远行/搬迁',  en:'Travel/Relocation',icon:'✈️',planets:['Rahu','Moon'],    houses:[9,12,3],varga:'D1'},
  finance_pos: {cn:'财运/收入',  en:'Income/Gains',     icon:'💰',planets:['Jupiter','Venus'],houses:[2,11],varga:'D2'},
  finance_neg: {cn:'破财/损失',  en:'Financial Loss',   icon:'📉',planets:['Saturn','Rahu'],  houses:[8,12],varga:'D2'},
  property:    {cn:'房产/置业',  en:'Property',         icon:'🏠',planets:['Mars','Venus'],   houses:[4],  varga:'D4'},
  loss:        {cn:'失去/离别',  en:'Loss/Separation',  icon:'🕊️',planets:['Saturn','Rahu'],  houses:[8,12],varga:'D1'},
  spiritual:   {cn:'灵性/修行',  en:'Spiritual Practice',icon:'🙏',planets:['Jupiter','Ketu'],houses:[9,12],varga:'D1'},
  legal:       {cn:'法律/纠纷',  en:'Legal/Dispute',    icon:'⚖️',planets:['Mars','Saturn'],  houses:[6,8], varga:'D1'},
  fame:        {cn:'名声/荣誉',  en:'Fame/Honor',       icon:'🌟',planets:['Sun','Jupiter'],  houses:[1,10,9],varga:'D10'},
};

export const EVENT_COLLECTION_GUIDE = [
  { key: 'relationship', cn: '感情/婚姻/分离', en: 'relationship, marriage, separation', categories: ['marriage', 'divorce', 'relationship'] },
  { key: 'career', cn: '入职/升职/创业/换工作', en: 'job start, promotion, business, job change', categories: ['career', 'job_change', 'business', 'fame'] },
  { key: 'education', cn: '升学/考试/毕业', en: 'education, exam, graduation', categories: ['education'] },
  { key: 'family', cn: '生育/父母/家庭房产', en: 'childbirth, parents, home, property', categories: ['child', 'property'] },
  { key: 'stress', cn: '健康/事故/诉讼/破财', en: 'health, accident, legal dispute, loss', categories: ['health', 'legal', 'finance_neg', 'loss'] },
  { key: 'mobility', cn: '搬家/远行/移民', en: 'relocation, travel, migration', categories: ['travel'] },
];

export const RECTIFICATION_RECOMMENDED_EVENT_QUESTION_MAP = {
  career_change: {
    id: 'recommended_career_change',
    category: 'job_change',
    varga: 'D10',
    label_cn: '事业转折',
    label_en: 'career change',
    question_cn: '你是否有日期比较明确的换工作、项目解散、升职失败或职业转折？',
    question_en: 'Have you had a dated job change, project ending, or career pivot?',
    examples_cn: ['换工作', '项目解散', '升职/落选', '职业转向'],
  },
  education_end: {
    id: 'recommended_education_end',
    category: 'education',
    varga: 'D24',
    label_cn: '学业完成',
    label_en: 'education completion',
    question_cn: '你是否有日期比较明确的毕业、升学、艺考培训结束或重要考试结果？',
    question_en: 'Have you had a dated graduation, admission, or important exam result?',
    examples_cn: ['毕业', '升学', '艺考培训', '考试结果'],
  },
  relocation: {
    id: 'recommended_relocation',
    category: 'travel',
    varga: 'D4',
    label_cn: '迁移搬家',
    label_en: 'relocation',
    question_cn: '你是否有日期比较明确的搬家、长期异地、远行或迁移事件？',
    question_en: 'Have you had a dated move, long-distance stay, or relocation?',
    examples_cn: ['搬家', '异地求学', '外地工作', '迁移'],
  },
  marriage: {
    id: 'recommended_marriage',
    category: 'marriage',
    varga: 'D9',
    label_cn: '婚恋关系',
    label_en: 'marriage relationship',
    question_cn: '你是否有日期比较明确的恋爱开始、订婚、结婚或关系破裂？',
    question_en: 'Have you had a dated romance, engagement, marriage, or breakup?',
    examples_cn: ['恋爱开始', '订婚', '结婚', '分手'],
  },
  windfall: {
    id: 'recommended_windfall',
    category: 'finance_pos',
    varga: 'D2',
    label_cn: '收入起落',
    label_en: 'income change',
    question_cn: '你是否有日期比较明确的奖金、定金、收入明显增加或突然破财？',
    question_en: 'Have you had a dated bonus, deposit, income jump, or sudden loss?',
    examples_cn: ['奖金', '定金', '收入增长', '破财'],
  },
};

const RECTIFICATION_THEME_VARGAS = {
  marriage: ['D9'],
  divorce: ['D9'],
  relationship: ['D9'],
  career: ['D10'],
  job_change: ['D10'],
  business: ['D10'],
  fame: ['D10'],
  child: ['D7'],
  parents: ['D12'],
  education: ['D24'],
  property: ['D4'],
  finance_pos: ['D2'],
  finance_neg: ['D2'],
  health: ['D30'],
  legal: ['D30'],
  loss: ['D30'],
  travel: ['D4'],
};

// ——— 工具函数 ———
export function getHouseLord(ai, h) { return SIGN_LORDS[SIGNS[(ai + h - 1) % 12]]; }

export function offsetBirth(b, offMin) {
  const t = b.hour * 60 + b.minute + offMin;
  const d = new Date(b.year, b.month - 1, b.day, 0, 0, 0);
  d.setMinutes(d.getMinutes() + t);
  return {year:d.getFullYear(),month:d.getMonth()+1,day:d.getDate(),hour:d.getHours(),minute:d.getMinutes(),lat:b.lat,lon:b.lon,tz:b.tz};
}

export function fmtTime(h,m) { return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}`; }
export function dateToJD(s) { const[y,mo,d]=s.split('-').map(Number); return Date.UTC(y,mo-1,d)/86400000+2440587.5; }

function getVargaLagna(ascSign, degInSign, vId) {
  const fake = {_L:{sign:ascSign,degree_in_sign:degInSign,house:1,error:false}};
  return computeVarga(fake, vId)?.planets?._L?.sign || null;
}

function getAllVL(ascSign, degInSign) {
  const ids=['D1','D4','D7','D9','D10','D12','D24','D30','D60'], r={};
  for(const id of ids) {
    const s = id==='D1' ? ascSign : getVargaLagna(ascSign, degInSign, id);
    r[id] = s ? {sign:s, index:SIGNS.indexOf(s)} : null;
  }
  return r;
}

function getNakPada(deg) {
  if(deg==null)return null;
  const nl=360/27,ni=Math.floor(deg/nl),p=Math.floor((deg-ni*nl)/(nl/4))+1;
  return {nakIdx:ni,pada:p,nakName:NAKSHATRA_LIST[ni]};
}

// ——— Dasha 对齐评分 (40%) ———
function findActiveDasha(dr, evtDate) {
  const ejd=dateToJD(evtDate);
  for(const md of dr.timeline){
    const s=dateToJD(md.start),e=dateToJD(md.end);
    if(ejd>=s&&ejd<e){
      if(md.antardasha) for(const ad of md.antardasha){
        if(ejd>=dateToJD(ad.start)&&ejd<dateToJD(ad.end)) return {mahadasha:md.lord,antardasha:ad.lord};
      }
      return {mahadasha:md.lord,antardasha:null};
    }
  }
  return null;
}

function scoreDasha(evt, di, ascSign) {
  const cat=EVENT_CATEGORIES[evt.category]; if(!cat||!di)return 0;
  let sc=0; const ai=SIGNS.indexOf(ascSign), hl=cat.houses.map(h=>getHouseLord(ai,h));
  const {mahadasha:md,antardasha:ad}=di;
  const mdOk=cat.planets.includes(md)||hl.includes(md);
  if(cat.planets.includes(md))sc+=3; else if(hl.includes(md))sc+=2;
  if(ad){
    const adOk=cat.planets.includes(ad)||hl.includes(ad);
    if(cat.planets.includes(ad))sc+=2; else if(hl.includes(ad))sc+=1.5;
    if(mdOk&&adOk)sc+=2;
  }
  return sc;
}

// ——— 分盘一致性评分 (35%) ———
function scoreVarga(evt, vl, ascSign) {
  const cat=EVENT_CATEGORIES[evt.category]; if(!cat||!cat.varga)return 0;
  const v=vl[cat.varga]; if(!v)return 0;
  const lord=SIGN_LORDS[v.sign],ai=SIGNS.indexOf(ascSign);
  let sc=0;
  if(cat.planets.includes(lord))sc+=3;
  for(const h of cat.houses){if(getHouseLord(ai,h)===lord){sc+=2;break;}}
  const vh=((v.index-ai+12)%12)+1;
  if([1,4,5,7,9,10].includes(vh))sc+=1;
  return sc;
}

// ——— 宫位变化 (15%) ———
function detectHouseChanges(bc, nc) {
  const ch=[];
  for(const pn of Object.keys(bc.planets)){
    const bp=bc.planets[pn],np=nc.planets[pn];
    if(bp.house!==np?.house) ch.push({planet:pn,from:bp.house,to:np?.house});
  }
  return ch;
}

// ——— Nak Pada 变化 (10%) ———
function scoreNak(baseDeg, offDeg) {
  const bp=getNakPada(baseDeg),op=getNakPada(offDeg);
  if(!bp||!op)return 0;
  if(bp.nakIdx!==op.nakIdx)return 2;
  if(bp.pada!==op.pada)return 1;
  return 0;
}

function eventCategoryGroup(category) {
  return EVENT_COLLECTION_GUIDE.find(group => group.categories.includes(category))?.key || category;
}

function summarizeEventCoverage(events) {
  const valid = (events || []).filter(evt => evt?.date && EVENT_CATEGORIES[evt.category]);
  const groups = [...new Set(valid.map(evt => eventCategoryGroup(evt.category)))];
  const categories = [...new Set(valid.map(evt => evt.category))];
  const datedYears = valid.map(evt => Number(String(evt.date).slice(0, 4))).filter(Number.isFinite);
  const yearSpan = datedYears.length ? Math.max(...datedYears) - Math.min(...datedYears) : 0;
  const idealCount = valid.length >= 8;
  const enoughCount = valid.length >= 5;
  const enoughGroups = groups.length >= 3;
  const enoughSpan = yearSpan >= 7 || valid.length >= 8;
  const qualityScore = Math.round(
    Math.min(valid.length / 8, 1) * 40 +
    Math.min(groups.length / 4, 1) * 30 +
    Math.min(yearSpan / 12, 1) * 20 +
    Math.min(categories.length / 5, 1) * 10
  );
  const missing = EVENT_COLLECTION_GUIDE
    .filter(group => !groups.includes(group.key))
    .slice(0, 3)
    .map(group => group.cn);
  return {
    event_count: valid.length,
    category_count: categories.length,
    group_count: groups.length,
    year_span: yearSpan,
    quality_score: qualityScore,
    quality_level: idealCount && enoughGroups && enoughSpan ? 'strong' : enoughCount && enoughGroups ? 'usable' : 'thin',
    missing_groups: missing,
  };
}

function countMatchedEvents(result) {
  return (result?.eventScores || []).filter(es => (es.dashaScore || 0) > 0 || (es.vargaScore || 0) > 0).length;
}

function summarizeCandidateEvidence(result, events) {
  const eventCount = Math.max((events || []).length, 1);
  const matchedEvents = countMatchedEvents(result);
  const strongEvents = (result?.eventScores || []).filter(es => (es.dashaScore || 0) >= 4 || ((es.dashaScore || 0) > 0 && (es.vargaScore || 0) > 0)).length;
  const sensitiveVargas = (result?.vargaChanges || [])
    .filter(v => ['D9', 'D10', 'D24', 'D30', 'D60'].includes(v.varga))
    .map(v => v.varga);
  const changedPlanets = (result?.houseChanges || []).map(c => c.planet);
  return {
    matched_events: matchedEvents,
    strong_events: strongEvents,
    match_rate: Math.round((matchedEvents / eventCount) * 100),
    sensitive_vargas: [...new Set(sensitiveVargas)],
    changed_planets: [...new Set(changedPlanets)],
  };
}

function buildRectificationDecisionPlan(events) {
  const valid = (events || []).filter(evt => evt?.date && EVENT_CATEGORIES[evt.category]);
  const categorySet = [...new Set(valid.map(evt => evt.category))];
  const themeVargas = [];
  for (const category of categorySet) {
    const vargas = RECTIFICATION_THEME_VARGAS[category] || [];
    for (const varga of vargas) {
      if (!themeVargas.includes(varga)) themeVargas.push(varga);
    }
  }

  const eventCount = valid.length;
  const tightenWithSensitive = themeVargas.length > 0;
  const useD30 = themeVargas.includes('D30');
  const useD60 = eventCount >= 8 && themeVargas.length >= 2;

  return {
    principle: 'Dasha 定框，D9/D10 定核心，专项分盘补刀，D30/D60 谨慎后置。',
    ordered_layers: [
      { step: 1, label: 'Dasha + dated events', role: '主引擎', reason: '先用真实事件把时间框住，再决定要不要细分盘。' },
      { step: 2, label: 'D9', role: '核心验证', reason: '婚姻、关系质量、内在成熟路线的第一核心分盘。' },
      { step: 3, label: 'D10', role: '核心验证', reason: '事业显化、职业兑现、升职和名声路径的第一核心分盘。' },
      { step: 4, label: themeVargas.length ? themeVargas.join(' / ') : 'D7 / D12 / D24 / D4 / D2', role: '主题补刀', reason: '按用户真实事件主题调用专项分盘，不一股脑全开。' },
      { step: 5, label: 'Nakshatra / Pada / house shifts', role: '细分钟收口', reason: '用于最后 2-10 分钟缩窄，不适合一开始拍板。' },
      { step: 6, label: useD30 ? 'D30' : 'D30（仅当有健康/事故/创伤事件）', role: '高敏慎用', reason: '高敏但易过拟合，只在明确压力事件时启用。' },
      { step: 7, label: useD60 ? 'D60（仅作最后参考）' : 'D60（默认后置）', role: '超高敏慎用', reason: '只在高收敛后作为最后参考，不反向主导校时结论。' },
    ],
    selected_theme_vargas: themeVargas,
    event_count: eventCount,
    warnings: [
      ...(eventCount < 5 ? ['事件少于 5 个时，不建议过早依赖高敏感分盘。'] : []),
      ...(!tightenWithSensitive ? ['当前事件主题不足以触发专项分盘，先补婚恋/事业/家庭/健康类 dated events。'] : []),
      ...(!useD30 ? ['没有明确健康/事故/创伤事件时，D30 默认不主导结论。'] : []),
      ...(!useD60 ? ['D60 默认后置，只在高收敛后作最后参考。'] : []),
    ],
  };
}

export function buildRectificationInterviewQuestions() {
  return EVENT_COLLECTION_GUIDE.map(group => {
    const category = group.categories.find(key => EVENT_CATEGORIES[key]) || group.categories[0];
    const cat = EVENT_CATEGORIES[category] || {};
    return {
      id: `guided_rectification_interview_${group.key}`,
      group: group.key,
      category,
      varga: cat.varga || 'D1',
      label_cn: group.cn,
      label_en: group.en,
      question_cn: `你的人生中是否发生过日期比较明确的${group.cn}？`,
      question_en: `Have you had a dated ${group.en} event?`,
      examples_cn: group.categories
        .map(key => EVENT_CATEGORIES[key]?.cn)
        .filter(Boolean)
        .slice(0, 4),
    };
  });
}

export function buildRecommendedRectificationQuestions(recommendedEvents = []) {
  const picked = [];
  for (const key of recommendedEvents || []) {
    const question = RECTIFICATION_RECOMMENDED_EVENT_QUESTION_MAP[key];
    if (question && !picked.find(item => item.id === question.id)) picked.push(question);
  }
  if (picked.length) return picked;
  return buildRectificationInterviewQuestions().slice(0, 3);
}

export function rectificationInterviewAnswersToEvents(answers) {
  return (answers || [])
    .filter(answer => answer?.answer === 'yes' && answer.date && EVENT_CATEGORIES[answer.category])
    .map(answer => {
      const cat = EVENT_CATEGORIES[answer.category];
      return {
        date: answer.date,
        category: answer.category,
        desc: (answer.note || '').trim() || cat.cn,
        source: 'guided_rectification_interview',
      };
    });
}

function buildRectificationAudit(best, results, events) {
  const second = results[1] || null;
  const coverage = summarizeEventCoverage(events);
  const evidence = summarizeCandidateEvidence(best, events);
  const cluster = results.filter(r => Math.abs((r.totalScore || 0) - (best?.totalScore || 0)) <= 3).slice(0, 8);
  const clusterOffsets = cluster.map(r => r.offsetMin);
  const clusterSpan = clusterOffsets.length
    ? { min: Math.min(...clusterOffsets), max: Math.max(...clusterOffsets), count: clusterOffsets.length }
    : { min: 0, max: 0, count: 0 };
  const gap = second ? Math.max(0, (best.totalScore || 0) - (second.totalScore || 0)) : best?.totalScore || 0;
  const exactTie = second ? (best.totalScore || 0) === (second.totalScore || 0) : false;
  const shouldStayNearBaseline = exactTie || clusterSpan.count >= 4 || (best?.totalScore || 0) < 45;
  const warnings = [];
  if (coverage.event_count < 5) warnings.push('事件数量不足，建议至少补到5个，理想为8-15个。');
  if (coverage.group_count < 3) warnings.push('事件类型过于集中，容易把结果锁到单一主题。');
  if (coverage.year_span < 7 && coverage.event_count < 8) warnings.push('事件年份跨度偏短，建议补童年/青年/近年事件。');
  if (exactTie) warnings.push('第一名与第二名同分，不应把单一候选时间视为确定校正。');
  if (best?.vargaChanges?.some(v => v.varga === 'D9')) warnings.push('推荐时间会改变D9上升，婚姻与内在成熟判断需二次确认。');
  return {
    coverage,
    evidence,
    runner_up: second ? { offsetMin: second.offsetMin, time: second.time, totalScore: second.totalScore } : null,
    score_gap: gap,
    exact_tie: exactTie,
    top_cluster: clusterSpan,
    should_stay_near_baseline: shouldStayNearBaseline,
    warnings,
  };
}

// ——— 主函数 ———
export async function runRectification(birth, events, options={}) {
  const {rangeMin=15,stepMin=1,onProgress=null}=options;
  if(!events||!events.length) return {error:'请至少添加一个生命事件'};
  const offsets=[]; for(let m=-rangeMin;m<=rangeMin;m+=stepMin) offsets.push(m);
  const results=[];
  const baseChart=await computeChart(birth);
  const baseVL=getAllVL(baseChart.ascendant.sign,baseChart.ascendant.degree_in_sign);
  const baseMoon=baseChart.planets.Moon?.degree;

  for(let i=0;i<offsets.length;i++){
    const off=offsets[i], mod=offsetBirth(birth,off);
    try{
      const chart=await computeChart(mod);
      const ascSign=chart.ascendant.sign, moonLon=chart.planets.Moon?.degree;
      if(!moonLon)continue;
      const vl=getAllVL(ascSign,chart.ascendant.degree_in_sign);
      const bs=`${mod.year}-${String(mod.month).padStart(2,'0')}-${String(mod.day).padStart(2,'0')}`;
      const dashaRes=computeDasha(moonLon,bs,null);
      let dRaw=0,vRaw=0,nRaw=0; const evScores=[];
      for(const evt of events){
        const di=findActiveDasha(dashaRes,evt.date);
        const ds=scoreDasha(evt,di,ascSign), vs=scoreVarga(evt,vl,ascSign);
        dRaw+=ds; vRaw+=vs;
        evScores.push({event:evt,dasha:di,dashaScore:ds,vargaScore:vs});
      }
      nRaw=scoreNak(baseMoon,moonLon);
      const hc=detectHouseChanges(baseChart,chart);
      const vc=[];
      for(const id of Object.keys(baseVL)){
        if(baseVL[id]&&vl[id]&&baseVL[id].sign!==vl[id].sign)
          vc.push({varga:id,from:baseVL[id].sign,to:vl[id].sign});
      }
      const dMax=events.length*9,vMax=events.length*6,hMax=Math.max(events.length,1);
      const dPct=dMax>0?dRaw/dMax:0, vPct=vMax>0?vRaw/vMax:0;
      const hPct=Math.min(hc.length/hMax,1), nPct=nRaw/2;
      const final=Math.round(dPct*40+vPct*35+hPct*15+nPct*10);
      results.push({
        offsetMin:off,time:fmtTime(mod.hour,mod.minute),ascSign,ascDeg:chart.ascendant.degree,
        vargaLagnas:vl,vargaChanges:vc,houseChanges:hc,totalScore:final,
        scores:{
          dasha:{raw:dRaw,max:dMax,pct:Math.round(dPct*100)},
          varga:{raw:vRaw,max:vMax,pct:Math.round(vPct*100)},
          house:{raw:hc.length,pct:Math.round(hPct*100)},
          nak:{raw:nRaw,pct:Math.round(nPct*100)},
        },
        eventScores:evScores, moonNak:getNakPada(moonLon),
      });
    }catch(e){console.warn('[Rect]',off,e);}
    if(onProgress)onProgress(i+1,offsets.length);
  }
  results.sort((a,b)=>(b.totalScore-a.totalScore)||Math.abs(a.offsetMin)-Math.abs(b.offsetMin)||a.offsetMin-b.offsetMin);
  if(results.length>0){
    results[0].isBest=true;
    if(results.findIndex(r=>r.offsetMin===0)>0) results[0].correctionEffective=true;
  }
  const audit = results.length ? buildRectificationAudit(results[0], results, events) : null;
  const decisionPlan = buildRectificationDecisionPlan(events);
  return {
    birth,events,options:{rangeMin,stepMin,totalCandidates:offsets.length},
    baseChartInfo:{
      time:fmtTime(birth.hour,birth.minute),
      ascSign:baseChart.ascendant.sign,ascDeg:baseChart.ascendant.degree,
      vargaLagnas:baseVL,moonNak:getNakPada(baseMoon),
    },
    results,bestMatch:results[0]||null,
    confidence:calcConf(results,events.length,audit),
    audit,
    decisionPlan,
  };
}

function calcConf(results, evtCount, audit=null) {
  if(!results.length) return {level:'不确定',score:0,bestPct:0,gapPct:0,description:'',recommendation:[]};
  const best=results[0],sec=results[1];
  const gap=sec?best.totalScore-sec.totalScore:best.totalScore;
  const gapPct=sec&&sec.totalScore>0?Math.round(gap/sec.totalScore*100):100;
  let level,score;
  const coverageOk = !audit || audit.coverage.quality_level !== 'thin';
  if(best.totalScore>=65&&gapPct>=15&&coverageOk&&!audit?.exact_tie){level='高';score=3;}
  else if(best.totalScore>=45&&gapPct>=8&&!audit?.exact_tie){level='中';score=2;}
  else if(best.totalScore>=25){level='低';score=1;}
  else{level='不确定';score=0;}
  const recs=[`建议出生时间校正 ${best.offsetMin>=0?'+':''}${best.offsetMin} 分钟`];
  if(best.vargaChanges?.some(v=>v.varga==='D9')) recs.push('⚠️ 此校正会改变Navamsa(D9)上升，影响重大，建议专业验证');
  if(audit?.should_stay_near_baseline) recs.push('候选时间仍有聚集或同分现象，建议先保留原始时间为主、把推荐时间作为验证候选。');
  if(evtCount<5) recs.push('建议提供至少5个以上生命事件以提高准确性');
  if(audit?.coverage?.missing_groups?.length) recs.push(`可优先补充：${audit.coverage.missing_groups.join('、')}。`);
  if(level==='高') recs.push('多个事件一致指向此时间，可信度较高');
  else if(level==='低'||level==='不确定') recs.push('事件对齐度较低，可能需要更多事件数据或尝试更大时间范围');
  return {level,score,bestPct:best.totalScore,gapPct,description:`最佳匹配评分 ${best.totalScore}%，领先第二名 ${gapPct}%`,recommendation:recs};
}
