/**
 * Jyotish Deep Analysis Engine v1.0
 * 核心计算：Raman功能吉凶 · PACDARES · 宫位互影响 · 分盘交叉验证 · Vargottama · 频率分析
 */
import { SIGNS, SIGNS_CN, SIGN_LORDS, PLANET_CN, PLANET_SYMBOLS, EXALTATION, DEBILITATION, PLANET_ASPECTS, getPlanetStatus } from './jyotish-engine.js';
import { VARGA_DEFS } from './jyotish-advanced.js';

// ============================================================================
// 一、B.V. Raman 功能吉凶星表
// ============================================================================
export const RAMAN_TABLES = {
  Aries:       { best:['Jupiter'], good:['Mars','Sun'], bad:['Saturn','Mercury','Venus'], worst:['Mercury'], neutral:[], yk:null, maraka:['Saturn','Mercury'] },
  Taurus:      { best:['Saturn'], good:['Mercury','Mars','Sun'], bad:['Jupiter','Venus','Moon'], worst:[], neutral:['Venus'], yk:null, maraka:['Mercury','Jupiter'] },
  Gemini:      { best:['Venus'], good:[], bad:['Mars'], worst:[], neutral:['Moon','Mercury'], yk:null, maraka:['Moon','Jupiter'] },
  Cancer:      { best:['Mars'], good:['Jupiter'], bad:['Saturn','Mercury'], worst:[], neutral:['Venus'], yk:'Mars', maraka:['Sun','Saturn'] },
  Leo:         { best:['Mars'], good:['Sun','Jupiter'], bad:['Venus','Saturn'], worst:[], neutral:['Moon'], yk:'Mars', maraka:['Mercury','Venus'] },
  Virgo:       { best:['Venus'], good:[], bad:['Mars','Jupiter','Moon'], worst:['Mars'], neutral:['Mercury'], yk:null, maraka:['Venus','Mars'] },
  Libra:       { best:['Saturn'], good:['Mercury','Venus'], bad:['Jupiter','Sun','Mars'], worst:['Jupiter'], neutral:['Moon'], yk:'Saturn', maraka:['Mars','Jupiter'] },
  Scorpio:     { best:['Jupiter'], good:['Moon','Sun','Mars'], bad:['Venus','Mercury'], worst:['Venus'], neutral:[], yk:null, maraka:['Jupiter','Venus'] },
  Sagittarius: { best:['Mars','Sun'], good:[], bad:['Venus','Saturn','Mercury'], worst:[], neutral:['Jupiter','Moon'], yk:null, maraka:['Saturn','Mercury'] },
  Capricorn:   { best:['Venus'], good:['Mercury','Saturn'], bad:['Mars','Jupiter','Moon'], worst:['Mars'], neutral:['Sun'], yk:'Venus', maraka:['Saturn','Moon'] },
  Aquarius:    { best:['Venus'], good:['Sun','Mars'], bad:['Jupiter','Moon'], worst:[], neutral:['Mercury'], yk:'Venus', maraka:['Mercury','Sun'] },
  Pisces:      { best:['Moon','Mars'], good:[], bad:['Saturn','Sun','Venus','Mercury'], worst:[], neutral:['Jupiter'], yk:null, maraka:['Venus','Mars'] },
};

export const HOUSE_DOMAINS = {
  1:  {name:'自我·身体·人格',themes:['身体健康','人格特质','人生方向']},
  2:  {name:'财富·语言·家庭',themes:['财富积累','语言能力','家庭背景']},
  3:  {name:'沟通·兄弟·勇气',themes:['沟通表达','兄弟姐妹','勇气行动']},
  4:  {name:'家庭·房产·母亲',themes:['母亲','房产土地','内心安全感']},
  5:  {name:'创造·子女·恋爱',themes:['子女','恋爱','创造力','投资']},
  6:  {name:'职场·健康·服务',themes:['职场冲突','疾病健康','敌人对手']},
  7:  {name:'婚姻·伴侣·合作',themes:['婚姻关系','商业合作','伴侣特质']},
  8:  {name:'转化·遗产·神秘',themes:['死亡转化','遗产继承','他人资源']},
  9:  {name:'宗教·哲学·导师',themes:['长途旅行','导师上师','父亲']},
  10: {name:'事业·社会·权威',themes:['事业职业','社会地位','职业成就']},
  11: {name:'收入·朋友·愿望',themes:['收入财富','朋友社交','愿望实现']},
  12: {name:'灵性·损失·解脱',themes:['灵性修行','隐藏事物','外国事务']},
};

// ============================================================================
// 二、工具函数
// ============================================================================
const P_NAMES = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'];

export function getFunctionalNature(p, asc) {
  const t = RAMAN_TABLES[asc]; if(!t) return 'neutral';
  if(t.yk===p) return 'yogakaraka';
  if(t.best.includes(p)) return 'best_benefic';
  if(t.good.includes(p)) return 'benefic';
  if(t.neutral.includes(p)) return 'neutral';
  if(t.worst.includes(p)) return 'worst';
  if(t.bad.includes(p)) return 'malefic';
  return 'neutral';
}

export function getHousesRuled(p, asc) {
  const ai=SIGNS.indexOf(asc); const h=[];
  for(let i=1;i<=12;i++) if(SIGN_LORDS[SIGNS[(ai+i-1)%12]]===p) h.push(i);
  return h;
}

export function getHouseType(h) {
  if([1,4,7,10].includes(h)) return 'Kendra角宫';
  if([5,9].includes(h)) return 'Trikona三方';
  if([3,6,10,11].includes(h)) return 'Upachaya成长';
  if([6,8,12].includes(h)) return 'Dusthana凶宫';
  return '普通';
}

function vargaSI(degIS, si, d) {
  const sw=30/d, seg=Math.floor(degIS/sw);
  switch(d){
    case 1:return si; case 2:return(si%2===0)?(degIS<15?4:3):(degIS<15?3:4);
    case 3:return(si+seg*4)%12; case 4:return(si+seg)%12;
    case 7:return(si%2===0)?seg%12:(seg+6)%12;
    case 9:return[0,3,6,9].includes(si)?(si+seg)%12:[1,4,7,10].includes(si)?(si+8+seg)%12:(si+4+seg)%12;
    case 10:return(si%2===0?(9+seg):seg)%12;
    case 12:return(si+seg)%12; case 16:return seg%12; case 20:return(si+seg)%12;
    case 24:return(4+seg)%12;
    case 30:return si%2===0?(seg<5?0:seg<10?5:seg<18?2:seg<25?6:8):(seg<5?4:seg<10?11:seg<18?8:seg<25?1:6);
    case 40:return(si%2===0?seg:seg+3)%12;
    case 45:return((si%3===0?0:si%3===1?4:8)+seg)%12;
    case 60:return seg%12; default:return(si+seg)%12;
  }
}

function planetStatus(pn, sign) {
  return getPlanetStatus(pn, sign);
}

// ============================================================================
// 三、PACDARES 八维分析
// ============================================================================
export function computePACDARES(planets, asc) {
  const ai=SIGNS.indexOf(asc), t=RAMAN_TABLES[asc];
  const r={P:[],A:[],C:[],D:[],Ar:[],R:[],E:[],S:[]};

  // P: Position
  for(const pn of P_NAMES){const p=planets[pn];if(!p||p.error)continue;
    r.P.push({planet:pn,pcn:PLANET_CN[pn],sign:p.sign,scn:p.sign_cn,house:p.house,deg:p.degree_in_sign?.toFixed(2),status:p.status,retro:p.retrograde,fn:getFunctionalNature(pn,asc),hr:getHousesRuled(pn,asc),ht:p.house?getHouseType(p.house):'',combust:p.combust||false});
  }

  // A: Aspect received
  for(const pn of P_NAMES){const p=planets[pn];if(!p||p.error||p.house==null)continue;
    const recv=[];
    for(const f of P_NAMES){if(f===pn)continue;const fp=planets[f];if(!fp||fp.error||fp.house==null)continue;
      for(const off of(PLANET_ASPECTS[f]||[7])){
        if(((fp.house-1+off)%12)+1===p.house){
          const fn=getFunctionalNature(f,asc);
          recv.push({from:f,fcn:PLANET_CN[f],type:off===7?'对冲':(off===5||off===9)?'三分':off===4?'四分':off===8?'八分':`${off}宫`,fn,impact:['best_benefic','benefic','yogakaraka'].includes(fn)?'吉':['malefic','worst'].includes(fn)?'凶':'中'});
        }
      }
    }
    if(recv.length)r.A.push({planet:pn,pcn:PLANET_CN[pn],house:p.house,received:recv});
  }

  // C: Conjunction
  for(let i=0;i<P_NAMES.length;i++){const p1=planets[P_NAMES[i]];if(!p1||p1.error)continue;
    for(let j=i+1;j<P_NAMES.length;j++){const p2=planets[P_NAMES[j]];if(!p2||p2.error||p1.house!==p2.house)continue;
      const f1=getFunctionalNature(P_NAMES[i],asc),f2=getFunctionalNature(P_NAMES[j],asc);
      const poll=(['malefic','worst'].includes(f1)&&['best_benefic','benefic','yogakaraka'].includes(f2))||(['best_benefic','benefic','yogakaraka'].includes(f1)&&['malefic','worst'].includes(f2));
      r.C.push({p1:P_NAMES[i],p1cn:PLANET_CN[P_NAMES[i]],f1,p2:P_NAMES[j],p2cn:PLANET_CN[P_NAMES[j]],f2,house:p1.house,pollution:poll});
    }
  }

  // D: Dhana Yoga
  const wH=[2,5,9,11],wL=new Set(wH.map(h=>SIGN_LORDS[SIGNS[(ai+h-1)%12]]));
  const wl=[...wL];
  for(let i=0;i<wl.length;i++)for(let j=i+1;j<wl.length;j++){
    const pi=planets[wl[i]],pj=planets[wl[j]];if(!pi||!pj||pi.error||pj.error)continue;
    if(pi.house===pj.house&&wH.includes(pi.house))r.D.push({type:'财富宫主同宫',lcn:`${PLANET_CN[wl[i]]}+${PLANET_CN[wl[j]]}`,house:pi.house,str:'中强'});
    const hi=(ai+pi.house-1)%12,hj=(ai+pj.house-1)%12;
    if(SIGN_LORDS[SIGNS[hi]]===wl[j]&&SIGN_LORDS[SIGNS[hj]]===wl[i])r.D.push({type:'财富宫主互换',lcn:`${PLANET_CN[wl[i]]}+${PLANET_CN[wl[j]]}`,house:`${pi.house}↔${pj.house}`,str:'强'});
  }

  // Ar: Arishta
  for(const pn of['Saturn','Mars','Rahu']){const p=planets[pn];if(!p||p.error||![1,4,7,10].includes(p.house))continue;
    const fn=getFunctionalNature(pn,asc);if(['malefic','worst'].includes(fn))r.Ar.push({type:'凶星角宫',pcn:PLANET_CN[pn],house:p.house,desc:`${PLANET_CN[pn]}(凶星)在角宫H${p.house}`});
  }
  const moon=planets.Moon;if(moon&&!moon.error){
    const h2=moon.house===1?12:moon.house-1,h12=moon.house===12?1:moon.house+1;
    if(!P_NAMES.some(pn=>planets[pn]&&!planets[pn].error&&planets[pn].house===h2)&&!P_NAMES.some(pn=>planets[pn]&&!planets[pn].error&&planets[pn].house===h12))
      r.Ar.push({type:'Kemadruma',pcn:'月亮',house:moon.house,desc:'月亮2/12宫无星 — 情绪孤独'});
  }
  for(const h of[6,8,12]){const lord=SIGN_LORDS[SIGNS[(ai+h-1)%12]];const lp=planets[lord];if(!lp||lp.error||![6,8,12].includes(lp.house))continue;
    r.Ar.push({type:'凶宫主落凶宫',pcn:PLANET_CN[lord],house:lp.house,desc:`H${h}主落H${lp.house}`});
  }

  // R: Raja Yoga
  const kL=new Set([1,4,7,10].map(h=>SIGN_LORDS[SIGNS[(ai+h-1)%12]]));
  const tL=new Set([1,5,9].map(h=>SIGN_LORDS[SIGNS[(ai+h-1)%12]]));
  for(const k of kL)for(const tt of tL){if(k===tt)continue;const pk=planets[k],pt=planets[tt];if(!pk||!pt||pk.error||pt.error||pk.house!==pt.house)continue;
    r.R.push({type:'Raja Yoga',lcn:`${PLANET_CN[k]}+${PLANET_CN[tt]}`,house:pk.house,str:[1,4,7,10].includes(pk.house)?'极强':[5,9].includes(pk.house)?'强':'中'});
  }
  if(t?.yk){const yp=planets[t.yk];if(yp&&!yp.error)r.R.push({type:'Yogakaraka',lcn:PLANET_CN[t.yk],house:yp.house,str:yp.status==='入庙'||yp.status==='入旺'?'极强':'中强'});}

  // E: Exchange
  for(let h1=1;h1<=12;h1++){const l1=SIGN_LORDS[SIGNS[(ai+h1-1)%12]];const lp1=planets[l1];if(!lp1||lp1.error||!lp1.house)continue;
    const h2=lp1.house;const l2=SIGN_LORDS[SIGNS[(ai+h2-1)%12]];if(l2===l1)continue;const lp2=planets[l2];if(!lp2||lp2.error||lp2.house!==h1||h1>=h2)continue;
    r.E.push({type:'Parivartana',houses:[h1,h2],lcn:`${PLANET_CN[l1]}+${PLANET_CN[l2]}`,desc:`H${h1}主(${PLANET_CN[l1]})在H${h2}↔H${h2}主(${PLANET_CN[l2]})在H${h1}`,
      nature:[6,8,12].includes(h1)&&[6,8,12].includes(h2)?'Vipareeta':[6,8,12].includes(h1)||[6,8,12].includes(h2)?'混合':'吉'});
  }

  // S: Special
  for(const pn of P_NAMES){const p=planets[pn];if(!p||p.error)continue;
    if(p.retrograde)r.S.push({type:'逆行',pcn:PLANET_CN[pn],desc:`${PLANET_CN[pn]}逆行 — 能量内化`});
    if(p.combust)r.S.push({type:'燃烧',pcn:PLANET_CN[pn],desc:`${PLANET_CN[pn]}燃烧(${p.combust_degree}°)`});
    if(p.status==='落陷')r.S.push({type:'落陷',pcn:PLANET_CN[pn],desc:`${PLANET_CN[pn]}落陷在${p.sign_cn}`});
    if(p.status==='入旺')r.S.push({type:'入旺',pcn:PLANET_CN[pn],desc:`${PLANET_CN[pn]}入旺在${p.sign_cn}`});
  }
  return r;
}

// ============================================================================
// 四、宫位互影响矩阵
// ============================================================================
export function computeHouseInfluence(planets, asc) {
  const ai=SIGNS.indexOf(asc), matrix=[];
  for(let h=1;h<=12;h++){
    const si=(ai+h-1)%12,sign=SIGNS[si],lord=SIGN_LORDS[sign];
    const items=[];
    // 宫内
    for(const pn of P_NAMES){const p=planets[pn];if(!p||p.error||p.house!==h)continue;
      const fn=getFunctionalNature(pn,asc);
      const sc=fn==='yogakaraka'?3:fn==='best_benefic'?2:fn==='benefic'?1:fn==='neutral'?0:fn==='malefic'?-1:fn==='worst'?-2:0;
      items.push({src:`${PLANET_CN[pn]}(宫内)`,fn,sc,detail:PLANET_CN[pn]+fn});
    }
    // 相位
    for(const f of P_NAMES){const fp=planets[f];if(!fp||fp.error||fp.house==null)continue;
      for(const off of(PLANET_ASPECTS[f]||[7])){
        if(((fp.house-1+off)%12)+1===h){const fn=getFunctionalNature(f,asc);
          const sc=fn==='yogakaraka'?2:fn==='best_benefic'?1.5:fn==='benefic'?1:fn==='neutral'?0:fn==='malefic'?-1:fn==='worst'?-1.5:0;
          items.push({src:`${PLANET_CN[f]}(${off}宫相位)`,fn,sc,detail:PLANET_CN[f]});break;}
      }
    }
    // 宫主
    const lp=planets[lord];if(lp&&!lp.error&&lp.house){
      const sc=[1,4,5,7,9,10,11].includes(lp.house)?1:-0.5;
      items.push({src:`宫主星${PLANET_CN[lord]}(H${lp.house})`,fn:getFunctionalNature(lord,asc),sc,detail:`${PLANET_CN[lord]}${lp.status}在H${lp.house}`});
    }
    const total=Math.round(items.reduce((s,i)=>s+i.sc,0)*10)/10;
    matrix.push({house:h,sign,scn:SIGNS_CN[sign],lord,lcn:PLANET_CN[lord]||lord,items,total,
      verdict:total>=2?'强力':total>=0.5?'吉':total>=-0.5?'中':total>=-2?'弱':'受克'});
  }
  return matrix;
}

// ============================================================================
// 五、Vargottama 检测
// ============================================================================
export function detectVargottama(planets) {
  const r=[];
  for(const pn of P_NAMES){const p=planets[pn];if(!p||p.error)continue;
    const psi=SIGNS.indexOf(p.sign),d9si=vargaSI(p.degree_in_sign,psi,9);
    if(p.sign===SIGNS[d9si])r.push({planet:pn,pcn:PLANET_CN[pn],d1:p.sign_cn,d9:SIGNS_CN[SIGNS[d9si]]});
  }
  return r;
}

// ============================================================================
// 六、行星频率分析
// ============================================================================
export function computeFrequency(planets) {
  const r={};
  for(const pn of P_NAMES){const p=planets[pn];if(!p||p.error)continue;
    const psi=SIGNS.indexOf(p.sign),freq={};
    for(const v of VARGA_DEFS){const vsi=v.d===1?psi:vargaSI(p.degree_in_sign,psi,v.d);freq[SIGNS[vsi]]=(freq[SIGNS[vsi]]||0)+1;}
    const sorted=Object.entries(freq).sort((a,b)=>b[1]-a[1]);
    const top=sorted[0],total=VARGA_DEFS.length,pct=Math.round(top[1]/total*100);
    r[pn]={planet:pn,pcn:PLANET_CN[pn],topSign:top[0],topScn:SIGNS_CN[top[0]],count:top[1],pct,
      level:pct>=50?'极高频':pct>=40?'高频':pct>=30?'中高频':pct>=20?'中等':'低频',
      dist:sorted.slice(0,3).map(([s,c])=>({s,scn:SIGNS_CN[s],c,p:Math.round(c/total*100)}))};
  }
  return r;
}

// ============================================================================
// 七、D1 × D9 × D10 三角验证
// ============================================================================
export function computeTriangle(planets) {
  const r=[];
  for(const pn of P_NAMES){const p=planets[pn];if(!p||p.error)continue;
    const psi=SIGNS.indexOf(p.sign);
    const d9si=vargaSI(p.degree_in_sign,psi,9),d10si=vargaSI(p.degree_in_sign,psi,10);
    const d9s=SIGNS[d9si],d10s=SIGNS[d10si];
    const d1st=p.status,d9st=planetStatus(pn,d9s),d10st=planetStatus(pn,d10s);
    let v='一致';
    if(['入庙','入旺'].includes(d1st)&&['落陷'].includes(d9st))v='D1强D9弱(承诺未兑现)';
    else if(['落陷'].includes(d1st)&&['入庙','入旺'].includes(d9st))v='D1弱D9强(绝地反击)';
    else if(['入庙','入旺'].includes(d1st)&&['入庙','入旺'].includes(d9st))v='双重强势';
    else if(['落陷'].includes(d1st)&&['落陷'].includes(d9st))v='双重弱势';
    const vg=p.sign===d9s;
    r.push({planet:pn,pcn:PLANET_CN[pn],d1sign:p.sign_cn,d1st,d9sign:SIGNS_CN[d9s],d9st,d10sign:SIGNS_CN[d10s],d10st,verdict:v,vargottama:vg});
  }
  return r;
}

// ============================================================================
// 八、Raman 宫位六步法（综合评估每宫吉凶）
// ============================================================================
export function computeRamanHouseScore(planets, asc) {
  const ai=SIGNS.indexOf(asc), scores=[];
  for(let h=1;h<=12;h++){
    const si=(ai+h-1)%12,sign=SIGNS[si],lord=SIGN_LORDS[sign];
    let pos=0,neg=0,details=[];
    // Step1: 宫内行星
    for(const pn of P_NAMES){const p=planets[pn];if(!p||p.error||p.house!==h)continue;
      const fn=getFunctionalNature(pn,asc);
      if(['best_benefic','benefic','yogakaraka'].includes(fn)){pos+=2;details.push(`✓${PLANET_CN[pn]}(吉)在宫内`);}
      else if(['malefic','worst'].includes(fn)){neg+=2;details.push(`✗${PLANET_CN[pn]}(凶)在宫内`);}
      else{pos+=0.5;details.push(`~${PLANET_CN[pn]}(中性)在宫内`);}
    }
    // Step2: 相位
    for(const f of P_NAMES){const fp=planets[f];if(!fp||fp.error||fp.house==null)continue;
      for(const off of(PLANET_ASPECTS[f]||[7])){
        if(((fp.house-1+off)%12)+1===h){
          const fn=getFunctionalNature(f,asc);
          if(['best_benefic','benefic','yogakaraka'].includes(fn)){pos+=1;details.push(`✓${PLANET_CN[f]}吉相位`);}
          else if(['malefic','worst'].includes(fn)){neg+=1;details.push(`✗${PLANET_CN[f]}凶相位`);}
          break;
        }
      }
    }
    // Step3: 宫主星
    const lp=planets[lord];
    if(lp&&!lp.error&&lp.house){
      if([1,4,5,7,9,10,11].includes(lp.house)){pos+=1.5;details.push(`✓宫主${PLANET_CN[lord]}在H${lp.house}(${lp.status})`);}
      else if([6,8,12].includes(lp.house)){neg+=1.5;details.push(`✗宫主${PLANET_CN[lord]}在H${lp.house}(凶宫)`);}
      else{details.push(`~宫主${PLANET_CN[lord]}在H${lp.house}`);}
      if(lp.status==='入庙'||lp.status==='入旺'){pos+=1;details.push(`✓宫主${lp.status}`);}
      if(lp.status==='落陷'){neg+=1;details.push(`✗宫主落陷`);}
    }
    const net=Math.round((pos-neg)*10)/10;
    scores.push({house:h,sign,scn:SIGNS_CN[sign],lord,lcn:PLANET_CN[lord]||lord,pos,neg,net,details,
      grade:net>=3?'A':net>=1?'B':net>=-1?'C':net>=-3?'D':'F'});
  }
  return scores;
}

// ============================================================================
// 七、Trikona-Kendra 三方四正映射分析
// ============================================================================
const SIGNS_LIST = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'];
const LORD_OF = {Aries:'Mars',Taurus:'Venus',Gemini:'Mercury',Cancer:'Moon',Leo:'Sun',Virgo:'Mercury',Libra:'Venus',Scorpio:'Mars',Sagittarius:'Jupiter',Capricorn:'Saturn',Aquarius:'Saturn',Pisces:'Jupiter'};

function lordOfHouse(ascSign, h) {
  const ai = SIGNS_LIST.indexOf(ascSign);
  const signIdx = (ai + h - 1) % 12;
  return LORD_OF[SIGNS_LIST[signIdx]];
}

function signOfHouse(ascSign, h) {
  const ai = SIGNS_LIST.indexOf(ascSign);
  return SIGNS_LIST[(ai + h - 1) % 12];
}

/**
 * 计算三方四正映射分析
 * Trikona(1-5-9) 和 Kendra(1-4-7-10) 宫主星间的互落关系
 */
export function computeTrikonaKendra(planets, ascSign) {
  const trikonaHouses = [1, 5, 9];
  const kendraHouses = [1, 4, 7, 10];
  const allKeyHouses = [1, 4, 5, 7, 9, 10];

  // 计算每个关键宫的主星及其落宫
  const houseLords = {};
  for (const h of allKeyHouses) {
    const lord = lordOfHouse(ascSign, h);
    const lp = planets[lord];
    houseLords[h] = {
      house: h,
      lord,
      lord_cn: PLANET_CN[lord],
      sign: signOfHouse(ascSign, h),
      sign_cn: SIGNS_CN[signOfHouse(ascSign, h)],
      lordInHouse: lp && !lp.error ? lp.house : null,
      lordStatus: lp && !lp.error ? lp.status : null,
      lordRetro: lp && !lp.error ? lp.retrograde : false,
    };
  }

  // 三方映射：1→5→9 的主星互落
  const trikonaConnections = [];
  for (let i = 0; i < trikonaHouses.length; i++) {
    for (let j = i + 1; j < trikonaHouses.length; j++) {
      const h1 = trikonaHouses[i], h2 = trikonaHouses[j];
      const l1 = houseLords[h1], l2 = houseLords[h2];
      // 同宫
      if (l1.lordInHouse === h2 && l2.lordInHouse === h1) {
        trikonaConnections.push({ type: 'mutual', from: h1, to: h2, desc: `${l1.lord_cn}(${h1}主)↔${l2.lord_cn}(${h2}主) 互换`, quality: 'excellent' });
      } else if (l1.lordInHouse === h2) {
        trikonaConnections.push({ type: 'one-way', from: h1, to: h2, desc: `${l1.lord_cn}(${h1}主)落入${h2}宫`, quality: 'good' });
      } else if (l2.lordInHouse === h1) {
        trikonaConnections.push({ type: 'one-way', from: h2, to: h1, desc: `${l2.lord_cn}(${h2}主)落入${h1}宫`, quality: 'good' });
      }
      // 同宫（两主星在同一宫）
      if (l1.lordInHouse && l1.lordInHouse === l2.lordInHouse) {
        trikonaConnections.push({ type: 'conjunction', from: h1, to: h2, desc: `${l1.lord_cn}(${h1}主)+${l2.lord_cn}(${h2}主)同在H${l1.lordInHouse}`, quality: 'strong' });
      }
    }
  }

  // 四正映射：1-4-7-10 的主星互落
  const kendraConnections = [];
  for (let i = 0; i < kendraHouses.length; i++) {
    for (let j = i + 1; j < kendraHouses.length; j++) {
      const h1 = kendraHouses[i], h2 = kendraHouses[j];
      const l1 = houseLords[h1], l2 = houseLords[h2];
      if (l1.lordInHouse === h2 && l2.lordInHouse === h1) {
        kendraConnections.push({ type: 'mutual', from: h1, to: h2, desc: `${l1.lord_cn}(${h1}主)↔${l2.lord_cn}(${h2}主) 互换`, quality: 'excellent' });
      } else if (l1.lordInHouse === h2) {
        kendraConnections.push({ type: 'one-way', from: h1, to: h2, desc: `${l1.lord_cn}(${h1}主)落入${h2}宫`, quality: 'good' });
      } else if (l2.lordInHouse === h1) {
        kendraConnections.push({ type: 'one-way', from: h2, to: h1, desc: `${l2.lord_cn}(${h2}主)落入${h1}宫`, quality: 'good' });
      }
      if (l1.lordInHouse && l1.lordInHouse === l2.lordInHouse) {
        kendraConnections.push({ type: 'conjunction', from: h1, to: h2, desc: `${l1.lord_cn}(${h1}主)+${l2.lord_cn}(${h2}主)同在H${l1.lordInHouse}`, quality: 'strong' });
      }
    }
  }

  // 三方×四正交叉连接
  const crossConnections = [];
  for (const th of trikonaHouses) {
    for (const kh of kendraHouses) {
      if (th === kh) continue; // 跳过1宫（同属两组）
      const tl = houseLords[th], kl = houseLords[kh];
      // 三方主落入四正
      if (tl.lordInHouse === kh) {
        crossConnections.push({ type: 'trikona-to-kendra', from: th, to: kh, desc: `${tl.lord_cn}(${th}主/三方)→H${kh}(四正)`, quality: 'raja' });
      }
      // 四正主落入三方
      if (kl.lordInHouse === th) {
        crossConnections.push({ type: 'kendra-to-trikona', from: kh, to: th, desc: `${kl.lord_cn}(${kh}主/四正)→H${th}(三方)`, quality: 'raja' });
      }
      // 互换 = 大 Raja Yoga
      if (tl.lordInHouse === kh && kl.lordInHouse === th) {
        crossConnections.push({ type: 'mutual-raja', from: th, to: kh, desc: `★ ${tl.lord_cn}(${th}主)↔${kl.lord_cn}(${kh}主) 互换 = Raja Yoga`, quality: 'maha-raja' });
      }
    }
  }

  // 整体评估
  const totalPositive = trikonaConnections.filter(c => c.quality !== 'poor').length
    + kendraConnections.filter(c => c.quality !== 'poor').length
    + crossConnections.length;
  const hasMahaRaja = crossConnections.some(c => c.quality === 'maha-raja');
  const hasRaja = crossConnections.some(c => c.quality === 'raja' || c.quality === 'maha-raja');

  let overallRating = '普通';
  if (hasMahaRaja) overallRating = '卓越 — 大帝王格局';
  else if (hasRaja && totalPositive >= 4) overallRating = '优秀 — 强力 Raja Yoga';
  else if (totalPositive >= 4) overallRating = '良好 — 多重三方四正连接';
  else if (totalPositive >= 2) overallRating = '中等 — 有一定三方四正连接';
  else if (totalPositive >= 1) overallRating = '一般 — 少量连接';

  return {
    houseLords,
    trikonaConnections,
    kendraConnections,
    crossConnections,
    overallRating,
    hasMahaRaja,
    hasRaja,
  };
}
