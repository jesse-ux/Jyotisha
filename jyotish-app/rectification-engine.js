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
  results.sort((a,b)=>b.totalScore-a.totalScore);
  if(results.length>0){
    results[0].isBest=true;
    if(results.findIndex(r=>r.offsetMin===0)>0) results[0].correctionEffective=true;
  }
  return {
    birth,events,options:{rangeMin,stepMin,totalCandidates:offsets.length},
    baseChartInfo:{
      time:fmtTime(birth.hour,birth.minute),
      ascSign:baseChart.ascendant.sign,ascDeg:baseChart.ascendant.degree,
      vargaLagnas:baseVL,moonNak:getNakPada(baseMoon),
    },
    results,bestMatch:results[0]||null,
    confidence:calcConf(results,events.length),
  };
}

function calcConf(results, evtCount) {
  if(!results.length) return {level:'不确定',score:0,bestPct:0,gapPct:0,description:'',recommendation:[]};
  const best=results[0],sec=results[1];
  const gap=sec?best.totalScore-sec.totalScore:best.totalScore;
  const gapPct=sec&&sec.totalScore>0?Math.round(gap/sec.totalScore*100):100;
  let level,score;
  if(best.totalScore>=65&&gapPct>=15){level='高';score=3;}
  else if(best.totalScore>=45&&gapPct>=8){level='中';score=2;}
  else if(best.totalScore>=25){level='低';score=1;}
  else{level='不确定';score=0;}
  const recs=[`建议出生时间校正 ${best.offsetMin>=0?'+':''}${best.offsetMin} 分钟`];
  if(best.vargaChanges?.some(v=>v.varga==='D9')) recs.push('⚠️ 此校正会改变Navamsa(D9)上升，影响重大，建议专业验证');
  if(evtCount<3) recs.push('建议提供至少5个以上生命事件以提高准确性');
  if(level==='高') recs.push('多个事件一致指向此时间，可信度较高');
  else if(level==='低'||level==='不确定') recs.push('事件对齐度较低，可能需要更多事件数据或尝试更大时间范围');
  return {level,score,bestPct:best.totalScore,gapPct,description:`最佳匹配评分 ${best.totalScore}%，领先第二名 ${gapPct}%`,recommendation:recs};
}
